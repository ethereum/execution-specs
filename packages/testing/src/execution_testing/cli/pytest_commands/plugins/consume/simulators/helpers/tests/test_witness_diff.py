"""Tests for strict witness comparison helper."""

import pytest

from execution_testing.base_types import Bytes
from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.witness_diff import (  # noqa: E501
    WitnessMismatchError,
    assert_witness_matches,
)
from execution_testing.test_types.execution_witness import ExecutionWitness


def _w(
    state: list[bytes] | None = None,
    codes: list[bytes] | None = None,
    headers: list[bytes] | None = None,
) -> ExecutionWitness:
    return ExecutionWitness(
        state=[Bytes(b) for b in state or []],
        codes=[Bytes(b) for b in codes or []],
        headers=[Bytes(b) for b in headers or []],
    )


def test_matching_witnesses_pass() -> None:
    """Separate byte-equal witnesses match."""
    # Create separate objects so equality is not just object identity.
    expected = _w(state=[b"\xaa", b"\xbb"], codes=[b"\x60"], headers=[b"\xf9"])
    actual = _w(state=[b"\xaa", b"\xbb"], codes=[b"\x60"], headers=[b"\xf9"])
    assert_witness_matches(expected=expected, actual=actual)


def test_reordered_state_fails() -> None:
    """State item comparison is order-sensitive."""
    expected = _w(state=[b"\xaa", b"\xbb"], codes=[b"\x60", b"\x70"])
    actual = _w(state=[b"\xbb", b"\xaa"], codes=[b"\x60", b"\x70"])
    with pytest.raises(WitnessMismatchError, match="state: ordered mismatch"):
        assert_witness_matches(expected=expected, actual=actual)


def test_duplicates_are_significant() -> None:
    """Duplicate items make the witness differ."""
    expected = _w(state=[b"\xaa"])
    actual = _w(state=[b"\xaa", b"\xaa"])
    with pytest.raises(WitnessMismatchError, match="state: 1 extra"):
        assert_witness_matches(expected=expected, actual=actual)


def test_missing_state_node_fails() -> None:
    """Client missing a state node gives a missing diff line."""
    expected = _w(state=[b"\xaa", b"\xbb"])
    actual = _w(state=[b"\xaa"])
    with pytest.raises(WitnessMismatchError, match="state: 1 missing"):
        assert_witness_matches(expected=expected, actual=actual)


def test_extra_code_fails() -> None:
    """Client over-collecting a code gives an extra diff line."""
    expected = _w(codes=[b"\x60"])
    actual = _w(codes=[b"\x60", b"\x70"])
    with pytest.raises(WitnessMismatchError, match=r"codes: 1 extra"):
        assert_witness_matches(expected=expected, actual=actual)


def test_multi_field_mismatch_reports_all() -> None:
    """All mismatching fields are reported in one exception."""
    expected = _w(state=[b"\xaa"], codes=[b"\x60"], headers=[b"\xf9"])
    actual = _w(state=[b"\xbb"], codes=[b"\x61"], headers=[])
    with pytest.raises(WitnessMismatchError) as excinfo:
        assert_witness_matches(expected=expected, actual=actual)
    msg = str(excinfo.value)
    assert "state:" in msg
    assert "codes:" in msg
    assert "headers:" in msg
