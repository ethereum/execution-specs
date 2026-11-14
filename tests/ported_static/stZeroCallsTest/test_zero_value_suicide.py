"""
SELFDESTRUCT a contract holding no balance to different kinds of
beneficiary.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_SUICIDEFiller.json
state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToEmpty_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToNonZeroBalanceFiller.json
state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json

@manually-enhanced: Do not overwrite. Four fillers parametrized by recipient.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stZeroCallsTest/ZeroValue_SUICIDEFiller.json",
        "state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "recipient",
    [
        "nonexistent",
        "funded_eoa",
        pytest.param("eoa_with_storage", marks=pytest.mark.pre_alloc_mutable),
    ],
)
def test_zero_value_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    recipient: str,
) -> None:
    """SELFDESTRUCT a contract holding no balance to `recipient`."""
    sender = pre.fund_eoa()
    storage = Storage()

    if recipient == "nonexistent":
        beneficiary = pre.nonexistent_account()
        expected = Account.NONEXISTENT
    elif recipient == "funded_eoa":
        beneficiary = pre.fund_eoa()
        expected = Account(balance_change=0)
    else:
        storage[0] = 1
        beneficiary = pre.fund_eoa(storage=storage, nonce=0)
        expected = Account(storage=storage, balance_change=0)

    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    target_code = Op.SELFDESTRUCT(address=beneficiary) + Op.STOP
    target = pre.deploy_contract(
        code=target_code,
        storage=storage,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=600000,
    )

    post = {
        target: Account(
            storage=storage,
            code=target_code,
            balance=0,
            nonce=1,
        ),
        beneficiary: expected,
    }

    state_test(pre=pre, post=post, tx=tx)
