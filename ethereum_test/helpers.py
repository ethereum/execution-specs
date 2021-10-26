"""
Helper functions for generating Ethereum tests.
"""

from typing import Mapping

from ethereum.base_types import U256

from .code import Code
from .common import AddrAA, Big0, Big1, TestAddress
from .filler import StateTest
from .types import Account, Environment, Transaction


def TestCode(
    code: Code, expected: Mapping[U256, U256], gas_limit: U256 = U256(100000)
):
    """
    Test that `code` produces the `expected` storage output.
    """
    env = Environment()

    pre = {
        AddrAA: Account(nonce=Big1, balance=Big0, code=code, storage={}),
        TestAddress: Account(
            nonce=Big0,
            balance=U256(1000000000000000),
            code=Code(""),
            storage={},
        ),
    }

    post = {
        AddrAA: Account(nonce=Big1, balance=Big0, code=code, storage=expected)
    }

    tx = Transaction(to=AddrAA, gas_limit=gas_limit)

    return StateTest(env, pre, post, [tx])
