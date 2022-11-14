"""
Helper functions for generating Ethereum tests.
"""

from typing import Dict

from .code import Code
from .common import AddrAA, TestAddress
from .state_test import StateTest
from .types import Account, Environment, Transaction


def TestCode(
    code: Code,
    expected: Dict[str | int, str | int],
    gas_limit: int = 100000,
):
    """
    Test that `code` produces the `expected` storage output.
    """
    env = Environment()
    pre = {
        AddrAA: Account(nonce=1, balance=0, code=code, storage={}),
        TestAddress: Account(
            nonce=0,
            balance=1000000000000000,
            code=Code(""),
            storage={},
        ),
    }
    post = {AddrAA: Account(nonce=1, balance=0, code=code, storage=expected)}
    tx = Transaction(ty=0, to=AddrAA, gas_limit=gas_limit)
    return StateTest(env=env, pre=pre, post=post, txs=[tx])


def to_address(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(20, "big").hex()
    raise Exception("invalid type to convert to account address")


def to_hash(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(32, "big").hex()
    raise Exception("invalid type to convert to hash")
