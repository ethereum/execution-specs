"""
Test_suicide_caller.

Ported from:
state_tests/stSystemOperationsTest/suicideCallerFiller.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stSystemOperationsTest/suicideCallerFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_caller(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_caller."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { [[0]] (CALLER) (SELFDESTRUCT (CALLER))}
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.CALLER)
        + Op.SELFDESTRUCT(address=Op.CALLER)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x26A4C0125CC2AC853D5C04C3A710E7628EE352A3),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(
            storage={0: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297},
            balance=0,
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
