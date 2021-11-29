import json
import os
from functools import partial
from typing import Any, Dict, List, Tuple, cast
from unittest.mock import call, patch

from ethereum import rlp
from ethereum.base_types import U256, Bytes0
from ethereum.crypto import Hash32
from ethereum.frontier.eth_types import (
    Account,
    Block,
    Bloom,
    Header,
    Transaction,
)
from ethereum.frontier.spec import BlockChain, state_transition
from ethereum.frontier.state import (
    State,
    close_state,
    set_account,
    set_storage,
)
from ethereum.frontier.utils.hexadecimal import hex_to_address, hex_to_root
from ethereum.rlp import rlp_hash
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_hash,
    hex_to_u256,
    hex_to_uint,
)


def run_blockchain_st_test(
    test_dir: str, test_file: str, network: str
) -> None:
    test_data = load_test(test_dir, test_file, network)

    genesis_header = test_data["genesis_header"]
    genesis_block = Block(
        genesis_header,
        (),
        (),
    )

    assert rlp_hash(genesis_header) == test_data["genesis_header_hash"]
    assert (
        rlp.encode(cast(rlp.RLP, genesis_block))
        == test_data["genesis_block_rlp"]
    )

    chain = BlockChain(
        blocks=[genesis_block],
        state=test_data["pre_state"],
    )

    if not test_data["ignore_pow_validation"]:
        add_blocks_to_chain(chain, test_data)
    else:
        with patch(
            "ethereum.frontier.spec.validate_proof_of_work", autospec=True
        ) as mocked_pow_validator:
            add_blocks_to_chain(chain, test_data)
            mocked_pow_validator.assert_has_calls(
                [call(block.header) for block in test_data["blocks"]],
                any_order=False,
            )

    assert rlp_hash(chain.blocks[-1].header) == test_data["last_block_hash"]
    assert chain.state == test_data["expected_post_state"]
    close_state(chain.state)
    close_state(test_data["expected_post_state"])


def add_blocks_to_chain(chain: BlockChain, test_data: Dict[str, Any]) -> None:
    for idx, block in enumerate(test_data["blocks"]):
        assert rlp_hash(block.header) == test_data["block_header_hashes"][idx]
        assert rlp.encode(cast(rlp.RLP, block)) == test_data["block_rlps"][idx]
        state_transition(chain, block)


def load_test(test_dir: str, test_file: str, network: str) -> Dict[str, Any]:
    # Extract the pure basename of the file without the path to the file.
    # Ex: Extract "world.json" from "path/to/file/world.json"
    pure_test_file = os.path.basename(test_file)
    # Extract the filename without the extension. Ex: Extract "world" from
    # "world.json"
    test_name = os.path.splitext(pure_test_file)[0]
    path = os.path.join(test_dir, test_file)
    with open(path, "r") as fp:
        json_data = json.load(fp)[f"{test_name}_{network}"]

    blocks, block_header_hashes, block_rlps = json_to_blocks(
        json_data["blocks"]
    )

    return {
        "genesis_header": json_to_header(json_data["genesisBlockHeader"]),
        "genesis_header_hash": hex_to_bytes(
            json_data["genesisBlockHeader"]["hash"]
        ),
        "genesis_block_rlp": hex_to_bytes(json_data["genesisRLP"]),
        "last_block_hash": hex_to_bytes(json_data["lastblockhash"]),
        "pre_state": json_to_state(json_data["pre"]),
        "expected_post_state": json_to_state(json_data["postState"]),
        "blocks": blocks,
        "block_header_hashes": block_header_hashes,
        "block_rlps": block_rlps,
        "ignore_pow_validation": json_data["sealEngine"] == "NoProof",
    }


def json_to_blocks(
    json_blocks: Any,
) -> Tuple[List[Block], List[Hash32], List[bytes]]:
    blocks = []
    block_header_hashes = []
    block_rlps = []

    for json_block in json_blocks:
        if "blockHeader" not in json_block and "rlp" in json_block:
            # Some blocks are represented by only the RLP and not the block details
            block_rlp = hex_to_bytes(json_block["rlp"])
            block = rlp.decode_to(Block, block_rlp)
            blocks.append(block)
            block_header_hashes.append(rlp.rlp_hash(block.header))
            block_rlps.append(block_rlp)
            continue

        header = json_to_header(json_block["blockHeader"])
        transactions = tuple(
            json_to_tx(tx) for tx in json_block["transactions"]
        )
        uncles = tuple(
            json_to_header(uncle) for uncle in json_block["uncleHeaders"]
        )

        blocks.append(
            Block(
                header,
                transactions,
                uncles,
            )
        )
        block_header_hashes.append(
            Hash32(hex_to_bytes(json_block["blockHeader"]["hash"]))
        )
        block_rlps.append(hex_to_bytes(json_block["rlp"]))

    return blocks, block_header_hashes, block_rlps


def json_to_header(raw: Any) -> Header:
    return Header(
        hex_to_hash(raw.get("parentHash")),
        hex_to_hash(raw.get("uncleHash")),
        hex_to_address(raw.get("coinbase")),
        hex_to_root(raw.get("stateRoot")),
        hex_to_root(raw.get("transactionsTrie")),
        hex_to_root(raw.get("receiptTrie")),
        Bloom(hex_to_bytes(raw.get("bloom"))),
        hex_to_uint(raw.get("difficulty")),
        hex_to_uint(raw.get("number")),
        hex_to_uint(raw.get("gasLimit")),
        hex_to_uint(raw.get("gasUsed")),
        hex_to_u256(raw.get("timestamp")),
        hex_to_bytes(raw.get("extraData")),
        hex_to_bytes32(raw.get("mixHash")),
        hex_to_bytes8(raw.get("nonce")),
    )


def json_to_tx(raw: Any) -> Transaction:
    return Transaction(
        hex_to_u256(raw.get("nonce")),
        hex_to_u256(raw.get("gasPrice")),
        hex_to_u256(raw.get("gasLimit")),
        Bytes0(b"") if raw.get("to") == "" else hex_to_address(raw.get("to")),
        hex_to_u256(raw.get("value")),
        hex_to_bytes(raw.get("data")),
        hex_to_u256(raw.get("v")),
        hex_to_u256(raw.get("r")),
        hex_to_u256(raw.get("s")),
    )


def json_to_state(raw: Any) -> State:
    state = State()
    for (addr_hex, acc_state) in raw.items():
        addr = hex_to_address(addr_hex)
        account = Account(
            nonce=hex_to_uint(acc_state.get("nonce", "0x0")),
            balance=U256(hex_to_uint(acc_state.get("balance", "0x0"))),
            code=hex_to_bytes(acc_state.get("code", "")),
        )
        set_account(state, addr, account)

        for (k, v) in acc_state.get("storage", {}).items():
            set_storage(
                state,
                addr,
                hex_to_bytes32(k),
                U256.from_be_bytes(hex_to_bytes32(v)),
            )
    return state


run_frontier_blockchain_st_tests = partial(
    run_blockchain_st_test, network="Frontier"
)
