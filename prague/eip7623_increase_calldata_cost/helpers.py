"""Helpers for testing EIP-7623."""

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
    Find the minimum amount of tokens that will trigger the floor gas cost, by using a binary
    search and the intrinsic gas cost and floor data calculators.
    """
    # Start with 1000 tokens and if the intrinsic gas cost is greater than the floor gas cost,
    # multiply the number of tokens by 2 until it's not.
    tokens = 1000
    while floor_data_gas_cost_calculator(tokens) < intrinsic_gas_cost_calculator(tokens):
        tokens *= 2

    # Binary search to find the minimum number of tokens that will trigger the floor gas cost.
    left = 0
    right = tokens
    while left < right:
        tokens = (left + right) // 2
        if floor_data_gas_cost_calculator(tokens) < intrinsic_gas_cost_calculator(tokens):
            left = tokens + 1
        else:
            right = tokens
    tokens = left

    if floor_data_gas_cost_calculator(tokens) > intrinsic_gas_cost_calculator(tokens):
        tokens -= 1

    # Verify that increasing the tokens by one would always trigger the floor gas cost.
    assert (
        floor_data_gas_cost_calculator(tokens) <= intrinsic_gas_cost_calculator(tokens)
    ) and floor_data_gas_cost_calculator(tokens + 1) > intrinsic_gas_cost_calculator(
        tokens + 1
    ), "invalid case"

    return tokens
