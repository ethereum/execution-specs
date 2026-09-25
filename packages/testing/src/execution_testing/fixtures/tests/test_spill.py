"""Tests for the disk-backed payload buffer."""

import json
import random
from io import StringIO
from typing import ClassVar, List

import pytest

from execution_testing.base_types import CamelModel
from execution_testing.fixtures.base import BaseFixture
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


class Fixture(BaseFixture):
    """Minimal fixture carrying a payload list."""

    format_name: ClassVar[str] = "spill_test"
    description: ClassVar[str] = "spill test"

    scalar: int = 0
    zed: str = "z"
    payloads: List[Payload] = []


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


def build(payloads: List[Payload], threshold: int) -> tuple:
    """Return (fixture, buffer) for the payloads at the given threshold."""
    buffer = PayloadBuffer(threshold=threshold)
    for payload in payloads:
        buffer.append(payload)
    fixture = Fixture(
        scalar=42,
        zed="hello",
        payloads=[] if buffer.spilled else buffer.buffered,
    )
    if buffer.spilled:
        fixture.spill_field("payloads", buffer)
    return fixture, buffer


@pytest.mark.parametrize("count", [0, 1, 2, 5, 50, 300])
def test_spilled_matches_buffered(count: int) -> None:
    """A spilled fixture hashes and serialises like a buffered one."""
    buffered, buf_a = build(make_payloads(count), threshold=count + 1)
    spilled, buf_b = build(make_payloads(count), threshold=0)
    try:
        assert not buf_a.spilled
        assert buf_b.spilled == (count > 0)

        assert spilled.hash == buffered.hash

        out_a, out_b = StringIO(), StringIO()
        buffered.write_json(out_a)
        spilled.write_json(out_b)
        doc_a = json.loads(out_a.getvalue())
        doc_b = json.loads(out_b.getvalue())
        assert doc_b == doc_a
        assert len(doc_b["payloads"]) == count
    finally:
        buf_a.close()
        buf_b.close()


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
