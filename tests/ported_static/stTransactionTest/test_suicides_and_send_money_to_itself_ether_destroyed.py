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

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # {(SELFDESTRUCT <contract:target:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0xCCBD97BED823989BF91C6AC4CEAC020B2881F3A5
        )
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0xCCBD97BED823989BF91C6AC4CEAC020B2881F3A5),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=31700,
        value=10,
    )

    post = {
        target: Account(
            code=bytes.fromhex(
                "73ccbd97bed823989bf91c6ac4ceac020b2881f3a5ff00"
            ),
            balance=1010,
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
