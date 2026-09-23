"""Verify total and dimension-specific top-frame gas accounting."""

from typing import Any

import pytest

from execution_testing import AuthorizationTuple, RecipientType
from execution_testing.forks import Amsterdam, Fork, Osaka


@pytest.mark.parametrize("fork", [Osaka, Amsterdam])
@pytest.mark.parametrize("contract_creation", [False, True])
def test_top_frame_account_creation(
    fork: Fork, contract_creation: bool
) -> None:
    """Include account creation in the total without execution-gas charges."""
    kwargs: dict[str, Any] = {
        "contract_creation": contract_creation,
        "sends_value": True,
        "recipient_type": RecipientType.EMPTY_ACCOUNT,
    }
    expected_state = fork.gas_costs().NEW_ACCOUNT if fork == Amsterdam else 0

    assert fork.transaction_top_frame_execution_gas(**kwargs) == 0
    assert fork.transaction_top_frame_state_gas(**kwargs) == expected_state
    assert (
        fork.transaction_top_frame_gas_calculator()(**kwargs) == expected_state
    )


@pytest.mark.parametrize("delegation_warm", [False, True])
@pytest.mark.parametrize("first_write", [False, True])
def test_top_frame_authorization_and_delegation(
    delegation_warm: bool, first_write: bool
) -> None:
    """Include authorization state growth alongside delegated access costs."""
    fork = Amsterdam
    costs = fork.gas_costs()
    authorizations = [
        AuthorizationTuple(
            address=0x100,
            v=0,
            r=0,
            s=0,
            creates_account=first_write,
            writes_delegation=True,
            first_write=first_write,
        )
    ]
    expected_execution = (
        costs.WARM_ACCESS if delegation_warm else costs.COLD_ACCOUNT_ACCESS
    ) + (costs.ACCOUNT_WRITE if first_write else 0)
    expected_state = (
        costs.NEW_ACCOUNT if first_write else 0
    ) + costs.AUTH_BASE

    assert (
        fork.transaction_top_frame_execution_gas(
            recipient_type=RecipientType.DELEGATION_7702,
            delegation_warm=delegation_warm,
            authorizations=authorizations,
        )
        == expected_execution
    )
    assert (
        fork.transaction_top_frame_state_gas(
            authorizations=authorizations,
        )
        == expected_state
    )
    assert (
        fork.transaction_top_frame_gas_calculator()(
            recipient_type=RecipientType.DELEGATION_7702,
            delegation_warm=delegation_warm,
            authorizations=authorizations,
        )
        == expected_execution + expected_state
    )
