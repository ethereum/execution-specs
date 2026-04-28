"""
Test_codesize_init.

Ported from:
state_tests/stCodeSizeLimit/codesizeInitFiller.json
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
    ["state_tests/stCodeSizeLimit/codesizeInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_codesize_init(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_codesize_init."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SSTORE(key=0x1, value=Op.CODESIZE)
        + Op.SSTORE(key=0x2, value=Op.EXTCODESIZE(address=Op.ADDRESS))
        + Op.STOP,
        gas_limit=15000000,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={1: 10, 2: 0}, balance=0
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
