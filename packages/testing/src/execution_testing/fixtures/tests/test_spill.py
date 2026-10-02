"""Tests for the disk-backed payload buffer."""

import random
from typing import List

import pytest

from execution_testing.base_types import CamelModel
from execution_testing.fixtures.spill import (
    DEFAULT_SPILL_THRESHOLD,
    PayloadBuffer,
)


class Payload(CamelModel):
    """Stand-in for a payload with the shapes that affect serialisation."""

    index: int
    blob: str
    optional: str | None = None
    nested: dict = {}


def make_payloads(count: int) -> List[Payload]:
    """Build a deterministic set of payloads."""
    random.seed(count)
    return [
        Payload(
            index=i,
            blob="0x"
            + "".join(
                random.choices("0123456789abcdef", k=random.randrange(0, 400))
            ),
            # Exercises exclude_none on alternating elements.
            optional=None if i % 3 else 'unicode é "quoted"\n\ttabbed',
            nested={"k": [i, {"deep": "v" * (i % 7)}], "b": True},
        )
        for i in range(count)
    ]


def test_stays_in_memory_under_threshold() -> None:
    """An ordinary fill never touches the disk and keeps the field."""
    buffer = PayloadBuffer()
    for payload in make_payloads(DEFAULT_SPILL_THRESHOLD):
        buffer.append(payload)
    try:
        assert not buffer.spilled
        assert len(buffer.buffered) == DEFAULT_SPILL_THRESHOLD
        assert len(buffer) == DEFAULT_SPILL_THRESHOLD
    finally:
        buffer.close()


def test_spills_past_threshold() -> None:
    """One payload past the threshold moves the whole list to disk."""
    buffer = PayloadBuffer(threshold=4)
    for payload in make_payloads(5):
        buffer.append(payload)
    try:
        assert buffer.spilled
        assert buffer.buffered == []
        assert len(buffer) == 5
        assert [p["index"] for p in buffer] == [0, 1, 2, 3, 4]
    finally:
        buffer.close()


def test_close_removes_the_file() -> None:
    """Closing drops the temp file."""
    buffer = PayloadBuffer(threshold=0)
    buffer.append(make_payloads(1)[0])
    assert buffer.spilled
    path = buffer._path
    assert path is not None and path.exists()
    buffer.close()
    assert not path.exists()
