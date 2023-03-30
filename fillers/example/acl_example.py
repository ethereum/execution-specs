"""
Test ACL Transaction Source Code Examples
"""

from ethereum_test_forks import Berlin, London
from ethereum_test_tools import AccessList, Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTest, Transaction, test_from_until


@test_from_until(Berlin, London)
def test_access_list(fork):
    """
    Test type 1 transaction.
    """
    env = Environment()

    pre = {
        "0x000000000000000000000000000000000000aaaa": Account(
            balance=0x03,
            code=Op.PC + Op.SLOAD + Op.POP + Op.PC + Op.SLOAD,
            nonce=1,
        ),
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(
            balance=0x100000,
            nonce=0,
        ),
    }

    tx = Transaction(
        ty=1,
        chain_id=0x01,
        nonce=0,
        to="0x000000000000000000000000000000000000aaaa",
        value=1,
        gas_limit=323328,
        gas_price=1,
        access_list=[
            AccessList(
                address="0x0000000000000000000000000000000000000000",
                storage_keys=[
                    "0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
                ],
            )
        ],
        secret_key="0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8",  # noqa: E501
        protected=True,
    )

    post = {
        "0x000000000000000000000000000000000000aaaa": Account(
            code="0x5854505854",
            balance=4,
            nonce=1,
        ),
        "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba": Account(
            balance=0x1BC16D674EC87342
        ),
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(
            balance=0xF8CBD,
            nonce=1,
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx])
