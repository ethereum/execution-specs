"""Strict witness comparison helper for the engine-witness simulator."""

from typing import Iterable

from execution_testing.base_types import Bytes
from execution_testing.test_types.execution_witness import ExecutionWitness


def _item_preview(value: bytes) -> str:
    """Return a short hex preview for one witness item."""
    return "0x" + value.hex()[:16]


def _items_preview(items: list[bytes]) -> str:
    """Return previews for the first few witness items."""
    return ", ".join(_item_preview(item) for item in items[:5])


def _ordered_field_mismatch(
    field: str, expected: Iterable[Bytes], actual: Iterable[Bytes]
) -> str | None:
    """Return a human-readable mismatch line for one ordered field."""
    exp = [bytes(x) for x in expected]
    act = [bytes(x) for x in actual]

    if exp == act:
        return None

    common_len = min(len(exp), len(act))
    if exp[:common_len] == act[:common_len]:
        if len(exp) > len(act):
            missing = exp[common_len:]
            return (
                f"{field}: {len(missing)} missing "
                f"(not emitted by client): {_items_preview(missing)}"
            )
        extra = act[common_len:]
        return (
            f"{field}: {len(extra)} extra "
            f"(over-collected by client): {_items_preview(extra)}"
        )

    first_mismatch = next(
        i
        for i, (expected_item, actual_item) in enumerate(
            zip(exp, act, strict=False)
        )
        if expected_item != actual_item
    )

    return (
        f"{field}: ordered mismatch "
        f"(expected {len(exp)} items, got {len(act)}); "
        f"first mismatch at index {first_mismatch}: "
        f"expected {_item_preview(exp[first_mismatch])}, "
        f"got {_item_preview(act[first_mismatch])}"
    )


class WitnessMismatchError(AssertionError):
    """Raised when a client-emitted witness does not match the fixture's."""


def assert_witness_matches(
    expected: ExecutionWitness, actual: ExecutionWitness
) -> None:
    """
    Assert the client-emitted `actual` witness matches the fixture `expected`.

    Each of `state`, `codes`, and `headers` must match exactly. Ordering and
    duplicate entries are significant.
    """
    messages: list[str] = []
    for field, expected_items, actual_items in (
        ("state", expected.state, actual.state),
        ("codes", expected.codes, actual.codes),
        ("headers", expected.headers, actual.headers),
    ):
        mismatch = _ordered_field_mismatch(field, expected_items, actual_items)
        if mismatch is not None:
            messages.append(mismatch)

    if messages:
        raise WitnessMismatchError(
            "client witness does not match fixture witness:\n  "
            + "\n  ".join(messages)
        )
