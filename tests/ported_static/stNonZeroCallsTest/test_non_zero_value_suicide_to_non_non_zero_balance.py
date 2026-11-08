"""
Test_non_zero_value_suicide_to_non_non_zero_balance.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToNonNonZeroBalanceFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToNonNonZeroBalanceFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_suicide_to_non_non_zero_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_suicide_to_non_non_zero_balance."""
    addr = Address(0x9089DA66E8BBC08846842A301905501BC8525DC4)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    pre[addr] = Account(balance=100)
    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    target_code = (
        Op.SELFDESTRUCT(address=0x9089DA66E8BBC08846842A301905501BC8525DC4)
        + Op.STOP
    )
    target = pre.deploy_contract(
        code=target_code,
        balance=1,
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
            code=target_code,
            balance=0,
            nonce=1,
        ),
        addr: Account(balance=101),
    }

    state_test(pre=pre, post=post, tx=tx)
