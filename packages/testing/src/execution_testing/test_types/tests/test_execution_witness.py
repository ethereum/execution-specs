"""Tests for execution witness expectations."""

import pytest

from execution_testing.base_types import Bytes
from execution_testing.test_types.execution_witness import (
    ExecutionWitness,
    ExecutionWitnessStateExpectation,
    ExecutionWitnessValidationError,
)
from execution_testing.test_types.execution_witness.modifiers import (
    add_state_node,
    remove_state_node,
)


def test_execution_witness_state_expectation_accepts_sorted_subset() -> None:
    """State expectations should accept sorted witnesses with extras."""
    witness = ExecutionWitness(
        state=[Bytes(b"aa"), Bytes(b"bb")],
        codes=[],
        headers=[],
    )

    ExecutionWitnessStateExpectation(
        nodes_present=[Bytes(b"aa")]
    ).verify_against(witness)


def test_execution_witness_state_expectation_rejects_duplicates() -> None:
    """Duplicate state entries should fail structural validation."""
    witness = ExecutionWitness(
        state=[Bytes(b"aa"), Bytes(b"aa")],
        codes=[],
        headers=[],
    )

    with pytest.raises(
        ExecutionWitnessValidationError, match="contains duplicates"
    ):
        ExecutionWitnessStateExpectation().verify_against(witness)


def test_execution_witness_state_expectation_rejects_unsorted_entries() -> None:
    """Unsorted state entries should fail structural validation."""
    witness = ExecutionWitness(
        state=[Bytes(b"bb"), Bytes(b"aa")],
        codes=[],
        headers=[],
    )

    with pytest.raises(
        ExecutionWitnessValidationError, match="not sorted"
    ):
        ExecutionWitnessStateExpectation().verify_against(witness)


def test_execution_witness_state_expectation_rejects_missing_node() -> None:
    """Missing required nodes should fail validation."""
    witness = ExecutionWitness(state=[Bytes(b"aa")], codes=[], headers=[])

    with pytest.raises(
        ExecutionWitnessValidationError, match="not found in witness state"
    ):
        ExecutionWitnessStateExpectation(
            nodes_present=[Bytes(b"bb")]
        ).verify_against(witness)


def test_execution_witness_state_modifiers_add_and_remove() -> None:
    """State modifiers should update the witness state list."""
    witness = ExecutionWitness(state=[Bytes(b"aa")], codes=[], headers=[])

    modified = add_state_node(Bytes(b"bb"))(witness)
    assert modified.state == [Bytes(b"aa"), Bytes(b"bb")]

    restored = remove_state_node(Bytes(b"bb"))(modified)
    assert restored.state == [Bytes(b"aa")]
