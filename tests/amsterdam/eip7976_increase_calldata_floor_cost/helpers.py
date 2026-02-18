"""Helpers for testing EIP-7976."""

from enum import Enum, auto
from typing import Callable


class DataTestType(Enum):
    """Enum for the different types of data tests."""

    FLOOR_GAS_COST_LESS_THAN_OR_EQUAL_TO_INTRINSIC_GAS = auto()
    FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS = auto()


def find_floor_cost_threshold(
    floor_data_gas_cost_calculator: Callable[[int], int],
    intrinsic_gas_cost_calculator: Callable[[int], int],
) -> int:
    """
    Find the minimum amount of tokens that will trigger the floor gas cost, by
    using a binary search and the intrinsic gas cost and floor data
    calculators.
    """

    def floor_cost(n: int) -> int:
        return floor_data_gas_cost_calculator(n)

    def intrinsic_cost(n: int) -> int:
        return intrinsic_gas_cost_calculator(n)

    # Start with 1000 tokens and if the intrinsic gas cost is greater than the
    # floor gas cost, multiply the number of tokens by 2 until it's not.
    tokens = 1000
    while floor_cost(tokens) < intrinsic_cost(tokens):
        tokens *= 2

    # Binary search to find the minimum number of tokens that will trigger the
    # floor gas cost.
    left = 0
    right = tokens
    while left < right:
        tokens = (left + right) // 2
        if floor_cost(tokens) < intrinsic_cost(tokens):
            left = tokens + 1
        else:
            right = tokens
    tokens = left

    if floor_cost(tokens) > intrinsic_cost(tokens):
        tokens -= 1

    # Verify that increasing the tokens by one would always trigger the floor
    # gas cost.
    assert floor_cost(tokens) <= intrinsic_cost(tokens), "invalid case"
    assert floor_cost(tokens + 1) > intrinsic_cost(tokens + 1), "invalid case"

    return tokens
