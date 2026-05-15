"""Strict witness comparison helper for the engine-witness simulator."""

from typing import Iterable, List

from execution_testing.base_types import Bytes
from execution_testing.test_types.execution_witness import ExecutionWitness


def _preview(value: bytes | None) -> str:
    """Return a compact hex preview for a witness item."""
    if value is None:
        return "<missing>"
    return "0x" + value.hex()[:16]


def _diff_ordered(
    field: str, expected: Iterable[Bytes], actual: Iterable[Bytes]
) -> List[str]:
    """Return human-readable diff messages for a single witness field."""
    exp = [bytes(x) for x in expected]
    act = [bytes(x) for x in actual]

    if exp == act:
        return []

    if len(exp) > len(act) and exp[: len(act)] == act:
        missing_count = len(exp) - len(act)
        preview = ", ".join(_preview(item) for item in exp[len(act) :][:5])
        return [
            (
                f"{field}: {missing_count} missing "
                f"(not emitted by client): {preview}"
            )
        ]

    if len(act) > len(exp) and act[: len(exp)] == exp:
        extra_count = len(act) - len(exp)
        preview = ", ".join(_preview(item) for item in act[len(exp) :][:5])
        return [
            (
                f"{field}: {extra_count} extra "
                f"(over-collected by client): {preview}"
            )
        ]

    first_mismatch = next(
        (
            i
            for i, (expected_item, actual_item) in enumerate(zip(exp, act))
            if expected_item != actual_item
        ),
        min(len(exp), len(act)),
    )
    expected_item = (
        exp[first_mismatch] if first_mismatch < len(exp) else None
    )
    actual_item = act[first_mismatch] if first_mismatch < len(act) else None

    return [
        (
            f"{field}: ordered mismatch "
            f"(expected {len(exp)} items, got {len(act)}); "
            f"first mismatch at index {first_mismatch}: "
            f"expected {_preview(expected_item)}, got {_preview(actual_item)}"
        )
    ]


class WitnessMismatchError(AssertionError):
    """Raised when a client-emitted witness does not match the fixture's."""


def assert_witness_matches(
    expected: ExecutionWitness, actual: ExecutionWitness
) -> None:
    """
    Assert the client-emitted `actual` witness matches the fixture `expected`
    witness exactly on each of `state`, `codes`, and `headers`.

    Ordering and duplicate entries are significant.
    """
    messages: List[str] = []
    messages += _diff_ordered("state", expected.state, actual.state)
    messages += _diff_ordered("codes", expected.codes, actual.codes)
    messages += _diff_ordered("headers", expected.headers, actual.headers)

    if messages:
        raise WitnessMismatchError(
            "client witness does not match fixture witness:\n  "
            + "\n  ".join(messages)
        )
