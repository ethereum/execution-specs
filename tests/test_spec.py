import json
import os
from typing import Any, List

from eth1spec.eth_types import (
    Account,
    Block,
    Header,
    State,
    Transaction,
)
from eth1spec.spec import BlockChain, state_transition

from .helpers import (
    hex2address,
    hex2bytes,
    hex2bytes8,
    hex2bytes32,
    hex2hash,
    hex2root,
    hex2u256,
    hex2uint,
)


def test_add() -> None:
    run_test("stExample/add11_d0g0v0.json")
    print("done")


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

    genesis = Block(
        json_to_header(test.get("genesisBlockHeader")),
        [],
        [],
    )

    pre_state = json_to_state(test.get("pre"))
    # post_state = json_to_state(test.get("post"))

    chain = BlockChain(
        blocks=[genesis],
        state=pre_state,
    )

    for block in test.get("blocks"):
        header = json_to_header(block.get("blockHeader"))
        txs = list(map(json_to_tx, block.get("transactions")))
        ommers: List[Header] = []  # TODO

        state_transition(chain, Block(header, txs, ommers))

    print(chain.blocks)


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
    for (addr, vals) in raw.items():
        account = Account(
            nonce=hex2uint(vals.get("nonce", "0x0")),
            balance=hex2uint(vals.get("balance", "0x0")),
            code=hex2bytes(vals.get("code", "")),
            storage={},
        )

        # TODO: Load storage from json (be sure to strip leading 0s of value)
        #  for (k, v) in vals.get("storage", {}).items():
        #      account.storage[hex2bytes32(k)] = b"\x02"  # hex2bytes32(v)

        state[hex2address(addr)] = account

    return state
