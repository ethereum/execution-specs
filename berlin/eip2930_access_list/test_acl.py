"""
Test ACL Transaction Source Code Examples
"""

import pytest

from ethereum_test_tools import AccessList, Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Transaction

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2930.md"
REFERENCE_SPEC_VERSION = "c9db53a936c5c9cbe2db32ba0d1b86c4c6e73534"


@pytest.mark.valid_from("Berlin")
def test_access_list(state_test: StateTestFiller):
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
            balance=0x300000,
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
        gas_price=7,
        access_list=[
            AccessList(
                address="0x0000000000000000000000000000000000000000",
                storage_keys=[
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                ],
            )
        ],
        secret_key="0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8",
        protected=True,
    )

    post = {
        "0x000000000000000000000000000000000000aaaa": Account(
            code="0x5854505854",
            balance=4,
            nonce=1,
        ),
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(
            balance=0x2CD931,
            nonce=1,
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
