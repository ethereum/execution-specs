"""
SELFDESTRUCT a contract holding 1 wei to different kinds of beneficiary.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDEFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToEmpty_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToNonNonZeroBalanceFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json

@manually-enhanced: Do not overwrite. Four fillers parametrized by recipient.
The nonexistent recipient is also covered without a state gas reservoir.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def recipients(fork: Fork) -> list:
    """
    Return the recipient kinds, with the state gas reservoir choice.

    Only the nonexistent recipient is created, which costs state gas on forks
    with the state gas reservoir; there it is covered both paying from the
    reservoir (implicit gas limit above the cap) and from regular gas
    (`state_gas_reservoir=0` pins the gas limit to the cap).
    """
    cases = [
        pytest.param("nonexistent", None, id="nonexistent"),
        pytest.param("funded_eoa", None, id="funded_eoa"),
        pytest.param("eoa_with_storage", None, id="eoa_with_storage"),
    ]
    if fork.state_gas_reservoir_enabled():
        cases.append(
            pytest.param("nonexistent", 0, id="nonexistent_no_reservoir")
        )
    return cases


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDEFiller.json",
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToNonNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize_by_fork("recipient, state_gas_reservoir", recipients)
def test_non_zero_value_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    recipient: str,
    state_gas_reservoir: int | None,
) -> None:
    """SELFDESTRUCT a contract holding 1 wei to `recipient`."""
    sender = pre.fund_eoa()
    storage = Storage()

    if recipient == "nonexistent":
        beneficiary = pre.nonexistent_account()
        expected = Account(balance=1)
    elif recipient == "funded_eoa":
        beneficiary = pre.fund_eoa(amount=1)
        expected = Account(balance_change=1)
    else:
        storage[0] = 1
        beneficiary = pre.fund_eoa(amount=1, storage=storage)
        expected = Account(storage=storage, balance_change=1)

    target_code = Op.SELFDESTRUCT(address=beneficiary) + Op.STOP
    target = pre.deploy_contract(
        code=target_code,
        storage=storage,
        balance=1,
    )

    # Leave the reservoir unset unless the case pins it to zero.
    reservoir_kwargs = (
        {}
        if state_gas_reservoir is None
        else {"state_gas_reservoir": state_gas_reservoir}
    )
    tx = Transaction(sender=sender, to=target, **reservoir_kwargs)

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
