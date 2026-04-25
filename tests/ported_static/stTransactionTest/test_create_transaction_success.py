"""
Test_create_transaction_success.

Ported from:
state_tests/stTransactionTest/CreateTransactionSuccessFiller.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stTransactionTest/CreateTransactionSuccessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_create_transaction_success(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_transaction_success."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x5F5E100)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0x22]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xE0))
        + Op.JUMPI(pc=0x14, condition=Op.EQ(0xF8A8FD6D, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x1A]
        + Op.JUMP(pc=0x20)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.JUMP,
        gas_limit=70000,
        value=100,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={},
            code=bytes.fromhex(
                "60e060020a600035048063f8a8fd6d14601457005b601a6020565b60006000f35b56"  # noqa: E501
            ),
            balance=100,
            nonce=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
