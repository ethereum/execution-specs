"""Shared helpers for the EIP-8279 tests."""

from typing import Callable

from execution_testing import Bytes

from ...prague.eip7623_increase_calldata_cost.helpers import (
    find_floor_cost_threshold,
)


def floor_dominating_calldata(
    total_cost: Callable[[int], int],
    floor_cost: Callable[[int], int],
) -> Bytes:
    """
    Return zero-byte calldata sized so the transaction's static floor
    strictly exceeds everything else it pays.

    ``total_cost`` and ``floor_cost`` map a calldata byte count to the
    transaction's full non-floor cost (intrinsic, top-frame charges,
    execution) and to its static floor. The shared EIP-7623 threshold
    search finds the last size where the floor does not yet dominate;
    one byte past it the floor strictly binds, so any runtime floor
    extension shows up in the gas used. Empty calldata suffices when the
    floor already dominates without any.
    """
    if floor_cost(0) > total_cost(0):
        return Bytes(b"")
    threshold = find_floor_cost_threshold(
        floor_data_gas_cost_calculator=floor_cost,
        intrinsic_gas_cost_calculator=total_cost,
    )
    byte_count = threshold + 1
    assert floor_cost(byte_count) > total_cost(byte_count)
    return Bytes(b"\x00" * byte_count)
