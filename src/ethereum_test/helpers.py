"""
Helper functions for generating Ethereum tests.
"""

from typing import Mapping

from .code import Code
from .common import AddrAA, TestAddress
from .state_test import StateTest
from .types import Account, Environment, Transaction


def TestCode(code: Code, expected: Mapping[str, str], gas_limit: int = 100000):
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
    return StateTest(env, pre, post, [tx])
