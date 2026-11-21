"""Helpers used to return fork-specific values."""

from typing import Sized


def count_or_len(list_or_count: Sized | int | None) -> int:
    """Return the count behind a list-or-count calculator argument."""
    if list_or_count is None:
        return 0
    if isinstance(list_or_count, Sized):
        return len(list_or_count)
    return list_or_count


def ceiling_division(a: int, b: int) -> int:
    """
    Calculate the ceil without using floating point.
    Used by many of the EVM's formulas.
    """
    return -(a // -b)


def fake_exponential(factor: int, numerator: int, denominator: int) -> int:
    """Calculate the blob gas cost."""
    i = 1
    output = 0
    numerator_accumulator = factor * denominator
    while numerator_accumulator > 0:
        output += numerator_accumulator
        numerator_accumulator = (numerator_accumulator * numerator) // (
            denominator * i
        )
        i += 1
    return output // denominator
