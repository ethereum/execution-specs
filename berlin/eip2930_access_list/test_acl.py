"""
Test ACL Transaction Source Code Examples
"""

import pytest

from ethereum_test_tools import AccessList, Account, Alloc, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Transaction

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2930.md"
REFERENCE_SPEC_VERSION = "c9db53a936c5c9cbe2db32ba0d1b86c4c6e73534"


@pytest.mark.valid_from("Berlin")
def test_access_list(state_test: StateTestFiller, pre: Alloc):
    """
    Test type 1 transaction.
    """
    env = Environment()

    contract_address = pre.deploy_contract(
        Op.PC + Op.SLOAD + Op.POP + Op.PC + Op.SLOAD,
        balance=0x03,
    )
    sender = pre.fund_eoa(0x300000)

    tx = Transaction(
        ty=1,
        chain_id=0x01,
        to=contract_address,
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
        sender=sender,
    )

    post = {
        contract_address: Account(
            code="0x5854505854",
            balance=4,
            nonce=1,
        ),
        sender: Account(
            balance=0x2CD931,
            nonce=1,
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
