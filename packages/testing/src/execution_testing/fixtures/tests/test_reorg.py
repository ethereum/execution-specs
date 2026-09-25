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


def test_outcome_allows_bare_error_expectation() -> None:
    """A plain error expectation, optionally disputed, is unrestricted."""
    Outcome(id="x", error_code=EngineAPIError.InvalidForkchoiceState)
    Outcome(id="x", any_error=True, disputed="issue#1")
