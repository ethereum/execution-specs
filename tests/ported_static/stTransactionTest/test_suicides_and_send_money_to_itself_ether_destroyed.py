"""
Test_suicides_and_send_money_to_itself_ether_destroyed.

Ported from:
state_tests/stTransactionTest/SuicidesAndSendMoneyToItselfEtherDestroyedFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTransactionTest/SuicidesAndSendMoneyToItselfEtherDestroyedFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_and_send_money_to_itself_ether_destroyed(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicides_and_send_money_to_itself_ether_destroyed."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = pre.fund_eoa(amount=0x7459280)

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # {(SELFDESTRUCT <contract:target:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>)}  # noqa: E501
    target_code = Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP
    target = pre.deploy_contract(
        code=target_code,
        balance=1000,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=31700,
        value=10,
    )

    post = {
        target: Account(
            code=(target_code),
            balance=1010,
            nonce=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
