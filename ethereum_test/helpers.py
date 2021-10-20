from typing import Mapping
from ethereum.base_types import U256

from .code import Code
from .common import AddrAA, Big1, TestAddress
from .filler import StateFiller
from .types import Account, Environment, Transaction


def TestCode(code: Code, expected: Mapping[U256, U256], gas_limit: U256 = U256(100000)):
    env = Environment()

    pre = {
        AddrAA: Account(nonce=Big1, code=code),
        TestAddress: Account(balance=U256(1000000000000000))
    }

    post = {
        AddrAA: Account(nonce=Big1, code=code, storage=expected)
    }

    tx = Transaction(to=AddrAA, gas_limit=gas_limit)

    return StateFiller(env, pre, post, [tx])
