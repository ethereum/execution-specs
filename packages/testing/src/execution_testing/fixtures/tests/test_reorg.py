"""Tests for the reorg fixture format's `Outcome` model."""

import pytest
from pydantic import ValidationError

from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures.reorg import Outcome


def test_outcome_rejects_error_code_with_head_moved() -> None:
    """An error code plus a result-only constraint is never enforceable."""
    with pytest.raises(ValidationError, match="error_code/any_error"):
        Outcome(
            id="x",
            error_code=EngineAPIError.InvalidForkchoiceState,
            head_moved=True,
        )


def test_outcome_rejects_any_error_with_payload_id() -> None:
    """`anyError` combined with a normal-result field is rejected too."""
    with pytest.raises(ValidationError, match="error_code/any_error"):
        Outcome(id="x", any_error=True, payload_id="nonNull")


@pytest.mark.parametrize(
    "constraints",
    [
        {},
        {"payload_id": "null"},
        {"latest_valid_hash": "any"},
        {"latest_valid_hash": "null"},
        {"validation_error": "none"},
    ],
)
def test_outcome_rejects_unknown_effect(constraints: dict) -> None:
    """
    Without an error, status or headMoved, an outcome also matches a
    SYNCING response, so what the step did is unknown.
    """
    with pytest.raises(ValidationError, match="set status, head_moved"):
        Outcome(id="reply", **constraints)


def test_outcome_allows_head_moved_without_status() -> None:
    """`headMoved` alone settles whether a forkchoice update applied."""
    Outcome(id="x", head_moved=False)


def test_outcome_allows_bare_error_expectation() -> None:
    """A plain error expectation, optionally disputed, is unrestricted."""
    Outcome(id="x", error_code=EngineAPIError.InvalidForkchoiceState)
    Outcome(id="x", any_error=True, disputed="issue#1")


def test_outcome_rejects_unknown_status() -> None:
    """A misspelled status can never match an observed response."""
    with pytest.raises(ValidationError):
        Outcome(id="typo", status="Valid")


def test_outcome_rejects_unknown_error_code() -> None:
    """An error code outside the shared Engine API enum is rejected."""
    with pytest.raises(ValidationError):
        Outcome(id="typo", error_code=-1)


def test_outcome_error_code_round_trips_as_decimal_string() -> None:
    """``errorCode`` serializes as a decimal string and loads back."""
    outcome = Outcome(id="x", error_code=EngineAPIError.TooDeepReorg)
    dumped = outcome.model_dump(by_alias=True, exclude_none=True)
    assert dumped["errorCode"] == "-38006"
    reloaded = Outcome.model_validate(dumped)
    assert reloaded.error_code is EngineAPIError.TooDeepReorg
