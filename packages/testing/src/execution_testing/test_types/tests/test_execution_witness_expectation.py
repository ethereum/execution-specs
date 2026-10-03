"""Unit tests for execution witness code expectations."""

import pytest

from execution_testing.base_types import Bytes
from execution_testing.test_types import (
    ExecutionWitness,
    ExecutionWitnessCodesExpectation,
    ExecutionWitnessValidationError,
)


def test_codes_expectation_rejects_unexpected_codes() -> None:
    """Witness code expectations are always exhaustive."""
    expected_code = Bytes(b"\x60\x00")
    unexpected_code = Bytes(b"\x60\x01")

    expectation = ExecutionWitnessCodesExpectation(
        codes_present=[expected_code]
    )
    actual_witness = ExecutionWitness(codes=[expected_code, unexpected_code])

    with pytest.raises(
        ExecutionWitnessValidationError,
        match="Unexpected bytecodes in witness codes",
    ):
        expectation.verify_against(actual_witness)
