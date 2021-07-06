import json
import os
from typing import Any, List, cast

from ethereum.base_types import U256
from ethereum.frontier import rlp
from ethereum.frontier.eth_types import (
    Account,
    Block,
    Header,
    State,
    Transaction,
)
from ethereum.frontier.spec import BlockChain, state_transition

from .helpers import (
    hex2address,
    hex2bytes,
    hex2bytes8,
    hex2bytes32,
    hex2hash,
    hex2root,
    hex2u256,
    hex2uint,
    rlp_hash,
)


def test_add() -> None:
    run_test("stExample/add11_d0g0v0.json")


# loads a blockchain test
def load_test(path: str) -> Any:
    with open(path) as f:
        test = json.load(f)

    name = os.path.splitext(os.path.basename(path))[0]
    testname = name + "_Frontier"

    if testname not in test:
        print("test not found")
        raise NotImplementedError

    return test[testname]


def run_test(path: str) -> None:
    base = (
        "tests/fixtures/"
        "LegacyTests/Constantinople/BlockchainTests/GeneralStateTests/"
    )

    test = load_test(base + path)

    genesis_header = json_to_header(test.get("genesisBlockHeader"))
    genesis = Block(
        genesis_header,
        [],
        [],
    )

    assert rlp_hash(genesis_header) == hex2bytes(
        test["genesisBlockHeader"]["hash"]
    )
    assert rlp.encode(cast(rlp.RLP, genesis)) == hex2bytes(
        test.get("genesisRLP")
    )

    pre_state = json_to_state(test.get("pre"))
    expected_post_state = json_to_state(test.get("postState"))

    chain = BlockChain(
        blocks=[genesis],
        state=pre_state,
    )

    block_obj = None
    for block in test.get("blocks"):
        header = json_to_header(block.get("blockHeader"))
        txs: List[Transaction] = [
            json_to_tx(tx_json) for tx_json in block.get("transactions")
        ]
        ommers: List[Header] = [
            json_to_header(ommer_json)
            for ommer_json in block.get("uncleHeaders")
        ]

        assert rlp_hash(header) == hex2bytes(block["blockHeader"]["hash"])
        block_obj = Block(header, txs, ommers)
        assert rlp.encode(cast(rlp.RLP, block_obj)) == hex2bytes(block["rlp"])

        state_transition(chain, block_obj)

    last_block_hash = rlp_hash(chain.blocks[-1].header)
    assert last_block_hash == hex2bytes(test["lastblockhash"])

    assert chain.state == expected_post_state


def json_to_header(raw: Any) -> Header:
    return Header(
        hex2hash(raw.get("parentHash")),
        hex2hash(raw.get("uncleHash")),
        hex2address(raw.get("coinbase")),
        hex2root(raw.get("stateRoot")),
        hex2root(raw.get("transactionsTrie")),
        hex2root(raw.get("receiptTrie")),
        hex2bytes(raw.get("bloom")),
        hex2uint(raw.get("difficulty")),
        hex2uint(raw.get("number")),
        hex2uint(raw.get("gasLimit")),
        hex2uint(raw.get("gasUsed")),
        hex2u256(raw.get("timestamp")),
        hex2bytes(raw.get("extraData")),
        hex2bytes32(raw.get("mixHash")),
        hex2bytes8(raw.get("nonce")),
    )


def json_to_tx(raw: Any) -> Transaction:
    return Transaction(
        hex2u256(raw.get("nonce")),
        hex2u256(raw.get("gasPrice")),
        hex2u256(raw.get("gasLimit")),
        None if raw.get("to") == "" else hex2address(raw.get("to")),
        hex2u256(raw.get("value")),
        hex2bytes(raw.get("data")),
        hex2u256(raw.get("v")),
        hex2u256(raw.get("r")),
        hex2u256(raw.get("s")),
    )


def json_to_state(raw: Any) -> State:
    state = {}
    for (addr, acc_state) in raw.items():
        account = Account(
            nonce=hex2uint(acc_state.get("nonce", "0x0")),
            balance=hex2uint(acc_state.get("balance", "0x0")),
            code=hex2bytes(acc_state.get("code", "")),
            storage={},
        )

        for (k, v) in acc_state.get("storage", {}).items():
            account.storage[hex2bytes32(k)] = U256.from_be_bytes(
                hex2bytes32(v)
            )

        state[hex2address(addr)] = account

    return state
