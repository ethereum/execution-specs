import importlib
import json
import os.path
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Tuple, cast
from unittest.mock import call, patch

from ethereum import rlp
from ethereum.base_types import U256, Bytes0
from ethereum.crypto.hash import Hash32
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_hash,
    hex_to_u256,
    hex_to_uint,
)


class BaseLoad(ABC):
    @property
    @abstractmethod
    def fork_module(self) -> str:
        pass

    @property
    @abstractmethod
    def network(self) -> str:
        pass

    @property
    @abstractmethod
    def Block(self) -> Any:
        pass

    @property
    @abstractmethod
    def BlockChain(self) -> Any:
        pass

    @property
    @abstractmethod
    def state_transition(self) -> Any:
        pass

    @property
    @abstractmethod
    def close_state(self) -> Any:
        pass

    @abstractmethod
    def json_to_header(self, json_data: Any) -> Any:
        pass

    @abstractmethod
    def json_to_state(self, json_data: Any) -> Any:
        pass

    @abstractmethod
    def json_to_blocks(self, json_data: Any) -> Any:
        pass


class Load(BaseLoad):
    _network: str
    _fork_module: str

    @property
    def fork_module(self) -> str:
        return self._fork_module

    @property
    def network(self) -> str:
        return self._network

    @property
    def Block(self) -> Any:
        return self._module("eth_types").Block

    @property
    def Bloom(self) -> Any:
        return self._module("eth_types").Bloom

    @property
    def Header(self) -> Any:
        return self._module("eth_types").Header

    @property
    def state_transition(self) -> Any:
        return self._module("spec").state_transition

    @property
    def BlockChain(self) -> Any:
        return self._module("spec").BlockChain

    @property
    def hex_to_address(self) -> Any:
        return self._module("utils.hexadecimal").hex_to_address

    @property
    def hex_to_root(self) -> Any:
        return self._module("utils.hexadecimal").hex_to_root

    @property
    def close_state(self) -> Any:
        return self._module("state").close_state

    def __init__(self, network: str, fork_name: str):
        self._network = network
        self._fork_module = fork_name

    def _module(self, name: str) -> Any:
        return importlib.import_module(f"ethereum.{self._fork_module}.{name}")

    def json_to_state(self, raw: Any) -> Any:
        state = self._module("state").State()
        set_account = self._module("state").set_account
        set_storage = self._module("state").set_storage

        for (addr_hex, acc_state) in raw.items():
            addr = self.hex_to_address(addr_hex)
            account = self._module("eth_types").Account(
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

    def json_to_tx(self, raw: Any) -> Any:
        return self._module("eth_types").Transaction(
            hex_to_u256(raw.get("nonce")),
            hex_to_u256(raw.get("gasPrice")),
            hex_to_u256(raw.get("gasLimit")),
            Bytes0(b"")
            if raw.get("to") == ""
            else self.hex_to_address(raw.get("to")),
            hex_to_u256(raw.get("value")),
            hex_to_bytes(raw.get("data")),
            hex_to_u256(raw.get("v")),
            hex_to_u256(raw.get("r")),
            hex_to_u256(raw.get("s")),
        )

    def json_to_blocks(
        self,
        json_blocks: Any,
    ) -> Tuple[List[Any], List[Hash32], List[bytes]]:
        blocks = []
        block_header_hashes = []
        block_rlps = []

        for json_block in json_blocks:
            if "blockHeader" not in json_block and "rlp" in json_block:
                # Some blocks are represented by only the RLP and not the block details
                block_rlp = hex_to_bytes(json_block["rlp"])
                block = rlp.decode_to(self.Block, block_rlp)
                blocks.append(block)
                block_header_hashes.append(rlp.rlp_hash(block.header))
                block_rlps.append(block_rlp)
                continue

            header = self.json_to_header(json_block["blockHeader"])
            transactions = tuple(
                self.json_to_tx(tx) for tx in json_block["transactions"]
            )
            uncles = tuple(
                self.json_to_header(uncle)
                for uncle in json_block["uncleHeaders"]
            )

            blocks.append(
                self.Block(
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

    def json_to_header(self, raw: Any) -> Any:
        return self.Header(
            hex_to_hash(raw.get("parentHash")),
            hex_to_hash(raw.get("uncleHash") or raw.get("sha3Uncles")),
            self.hex_to_address(raw.get("coinbase") or raw.get("miner")),
            self.hex_to_root(raw.get("stateRoot")),
            self.hex_to_root(
                raw.get("transactionsTrie") or raw.get("transactionsRoot")
            ),
            self.hex_to_root(
                raw.get("receiptTrie") or raw.get("receiptsRoot")
            ),
            self.Bloom(hex_to_bytes(raw.get("bloom") or raw.get("logsBloom"))),
            hex_to_uint(raw.get("difficulty")),
            hex_to_uint(raw.get("number")),
            hex_to_uint(raw.get("gasLimit")),
            hex_to_uint(raw.get("gasUsed")),
            hex_to_u256(raw.get("timestamp")),
            hex_to_bytes(raw.get("extraData")),
            hex_to_bytes32(raw.get("mixHash")),
            hex_to_bytes8(raw.get("nonce")),
        )


def load_json_fixture(
    test_dir: str, test_file: str, load: BaseLoad
) -> Dict[str, Any]:
    # Extract the pure basename of the file without the path to the file.
    # Ex: Extract "world.json" from "path/to/file/world.json"
    pure_test_file = os.path.basename(test_file)
    # Extract the filename without the extension. Ex: Extract "world" from
    # "world.json"
    test_name = os.path.splitext(pure_test_file)[0]
    path = os.path.join(test_dir, test_file)
    with open(path, "r") as fp:
        data = json.load(fp)

        # Some newer test files have patterns like _d0g0v0_
        # between test_name and network
        keys_to_search = re.compile(
            f"{re.escape(test_name)}.*{re.escape(load.network)}"
        )
        found_keys = list(filter(keys_to_search.match, data.keys()))

        if len(found_keys) > 0:
            json_data = data[found_keys[0]]
        else:
            raise KeyError
    return json_data


def load_test(test_dir: str, test_file: str, load: BaseLoad) -> Dict[str, Any]:
    json_data = load_json_fixture(test_dir, test_file, load)

    blocks, block_header_hashes, block_rlps = load.json_to_blocks(
        json_data["blocks"]
    )

    return {
        "genesis_header": load.json_to_header(json_data["genesisBlockHeader"]),
        "genesis_header_hash": hex_to_bytes(
            json_data["genesisBlockHeader"]["hash"]
        ),
        "genesis_block_rlp": hex_to_bytes(json_data["genesisRLP"]),
        "last_block_hash": hex_to_bytes(json_data["lastblockhash"]),
        "pre_state": load.json_to_state(json_data["pre"]),
        "expected_post_state": load.json_to_state(json_data["postState"]),
        "blocks": blocks,
        "block_header_hashes": block_header_hashes,
        "block_rlps": block_rlps,
        "ignore_pow_validation": json_data["sealEngine"] == "NoProof",
    }


def run_blockchain_st_test(
    test_dir: str, test_file: str, load: BaseLoad
) -> None:
    test_data = load_test(test_dir, test_file, load)

    genesis_header = test_data["genesis_header"]
    genesis_block = load.Block(
        genesis_header,
        (),
        (),
    )

    assert rlp.rlp_hash(genesis_header) == test_data["genesis_header_hash"]
    assert (
        rlp.encode(cast(rlp.RLP, genesis_block))
        == test_data["genesis_block_rlp"]
    )

    chain = load.BlockChain(
        blocks=[genesis_block],
        state=test_data["pre_state"],
    )

    if not test_data["ignore_pow_validation"]:
        add_blocks_to_chain(chain, test_data, load)
    else:
        with patch(
            f"ethereum.{load.fork_module}.spec.validate_proof_of_work",
            autospec=True,
        ) as mocked_pow_validator:
            add_blocks_to_chain(chain, test_data, load)
            mocked_pow_validator.assert_has_calls(
                [call(block.header) for block in test_data["blocks"]],
                any_order=False,
            )

    assert (
        rlp.rlp_hash(chain.blocks[-1].header) == test_data["last_block_hash"]
    )
    assert chain.state == test_data["expected_post_state"]
    load.close_state(chain.state)
    load.close_state(test_data["expected_post_state"])


def add_blocks_to_chain(
    chain: Any, test_data: Dict[str, Any], load: BaseLoad
) -> None:
    for idx, block in enumerate(test_data["blocks"]):
        assert (
            rlp.rlp_hash(block.header) == test_data["block_header_hashes"][idx]
        )
        assert rlp.encode(cast(rlp.RLP, block)) == test_data["block_rlps"][idx]
        load.state_transition(chain, block)


def fetch_state_test_files(
    test_dir: str, slow_test_list: Tuple[str, ...], load: BaseLoad
) -> Generator[str, None, None]:
    for _dir in os.listdir(test_dir):
        test_file_path = os.path.join(test_dir, _dir)
        for _file in os.listdir(test_file_path):
            _test_file = os.path.join(_dir, _file)
            # TODO: provide a way to run slow tests
            if _test_file in slow_test_list:
                continue
            else:
                try:
                    load_json_fixture(test_dir, _test_file, load)
                    yield _test_file
                except KeyError:
                    # file doesn't contain tests for the given fork
                    pass
