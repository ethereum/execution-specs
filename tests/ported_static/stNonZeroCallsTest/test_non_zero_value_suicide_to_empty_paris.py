"""
Test_non_zero_value_suicide_to_empty_paris.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToEmpty_ParisFiller.json
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
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToEmpty_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_suicide_to_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_suicide_to_empty_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    addr = pre.fund_eoa(amount=10)  # noqa: F841
    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=addr) + Op.STOP,
        balance=1,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(
            storage={},
            code=bytes.fromhex(
                "7376fae819612a29489a1a43208613d8f8557b8898ff00"
            ),
            balance=0,
            nonce=0,
        ),
        addr: Account(balance=11),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
