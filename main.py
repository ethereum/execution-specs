# flake8: noqa

import argparse
import json

from . import spec, trie
from .eth_types import Address, Uint


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a state transition.")

    parser.add_argument("--input.alloc", dest="alloc", action="store")
    parser.add_argument("--input.env", dest="env", action="store")
    parser.add_argument("--input.txs", dest="txs", action="store")

    args = parser.parse_args()

    with open(args.alloc) as f:
        alloc = json.load(f)
    with open(args.env) as f:
        env = json.load(f)

    state = {}
    for (addr, vals) in alloc.items():
        account = spec.Account(
            nonce=vals.get("nonce", Uint(0)),
            balance=Uint(int(vals.get("balance", Uint(0)))),
            code=bytes.fromhex(vals.get("code", "")),
            storage={},  # TODO: support storage
        )
        addr = bytes.fromhex(addr)
        state[addr] = account

    gas_used, receipts, state = spec.apply_body(
        state,
        Address(bytes.fromhex(env["currentCoinbase"][2:])),
        Uint(int(env["currentNumber"], 16)),
        Uint(int(env["currentGasLimit"], 16)),
        Uint(int(env["currentTimestamp"], 16)),
        Uint(int(env["currentDifficulty"], 16)),
        [],
        [],
    )

    print(gas_used)
    print(receipts.hex())
    print(trie.TRIE(trie.y(state)).hex())


if __name__ == "__main__":
    main()
