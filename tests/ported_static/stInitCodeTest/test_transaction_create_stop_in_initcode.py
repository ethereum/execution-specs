"""
Test_transaction_create_stop_in_initcode.

Ported from:
state_tests/stInitCodeTest/TransactionCreateStopInInitcodeFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stInitCodeTest/TransactionCreateStopInInitcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction_create_stop_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_transaction_create_stop_in_initcode."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xF4240)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.STOP
        + Op.CALLCODE
        + Op.STOP * 2
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.BYTE(Op.DUP2, Op.CALLDATALOAD(offset=Op.DUP1))
        + Op.DUP2,
        gas_limit=55000,
        value=1,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(balance=1),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
