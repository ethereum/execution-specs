"""Tests for execution witness expectations."""

import pytest

from execution_testing.base_types import Bytes
from execution_testing.test_types.execution_witness import (
    ExecutionWitness,
    ExecutionWitnessStateExpectation,
    ExecutionWitnessValidationError,
)
from execution_testing.test_types.execution_witness.modifiers import (
    add_code,
    add_state_node,
    clear_headers,
    prepend_header,
    remove_code,
    remove_code_at,
    remove_header_at,
    remove_state_node,
    replace_header_at,
    reverse_codes,
    reverse_headers,
    reverse_state_nodes,
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


def test_execution_witness_state_expectation_rejects_unsorted_entries() -> (
    None
):
    """Unsorted state entries should fail structural validation."""
    witness = ExecutionWitness(
        state=[Bytes(b"bb"), Bytes(b"aa")],
        codes=[],
        headers=[],
    )

    with pytest.raises(ExecutionWitnessValidationError, match="not sorted"):
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

    reversed_state = reverse_state_nodes()(modified)
    assert reversed_state.state == [Bytes(b"bb"), Bytes(b"aa")]


def test_execution_witness_code_modifiers() -> None:
    """Code modifiers should update witness codes predictably."""
    witness = ExecutionWitness(
        state=[],
        codes=[Bytes(b"aa"), Bytes(b"bb")],
        headers=[],
    )

    added = add_code(Bytes(b"cc"))(witness)
    assert added.codes == [Bytes(b"aa"), Bytes(b"bb"), Bytes(b"cc")]

    removed = remove_code(Bytes(b"bb"))(added)
    assert removed.codes == [Bytes(b"aa"), Bytes(b"cc")]

    removed_by_index = remove_code_at(0)(added)
    assert removed_by_index.codes == [Bytes(b"bb"), Bytes(b"cc")]

    reversed_codes = reverse_codes()(witness)
    assert reversed_codes.codes == [Bytes(b"bb"), Bytes(b"aa")]


def test_execution_witness_header_modifiers() -> None:
    """Header modifiers should update witness headers predictably."""
    witness = ExecutionWitness(
        state=[],
        codes=[],
        headers=[Bytes(b"aa"), Bytes(b"bb")],
    )

    removed = remove_header_at(-1)(witness)
    assert removed.headers == [Bytes(b"aa")]

    replaced = replace_header_at(0, Bytes(b"cc"))(witness)
    assert replaced.headers == [Bytes(b"cc"), Bytes(b"bb")]

    prepended = prepend_header(Bytes(b"00"))(witness)
    assert prepended.headers == [Bytes(b"00"), Bytes(b"aa"), Bytes(b"bb")]

    reversed_headers = reverse_headers()(witness)
    assert reversed_headers.headers == [Bytes(b"bb"), Bytes(b"aa")]

    cleared = clear_headers()(witness)
    assert cleared.headers == []
