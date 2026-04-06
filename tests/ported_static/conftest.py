"""Shared helpers for ported static tests."""

from typing import Callable

import pytest
from execution_testing.forks import Amsterdam, Fork

TX_MAX_GAS_LIMIT = 16_777_216


def gas_with_state_headroom(fork: Fork, gas: int) -> int:
    """
    Add state gas headroom for forks with 2D gas accounting.

    In Amsterdam+, tx.gas must exceed TX_MAX_GAS_LIMIT so the excess
    funds the state gas reservoir. The original gas value becomes the
    state gas headroom.
    """
    if fork >= Amsterdam:
        return TX_MAX_GAS_LIMIT + gas
    return gas


def block_gas_limit_for_fork(fork: Fork, gas_limit: int) -> int:
    """
    Return a block gas limit large enough for the fork.

    In Amsterdam+, transactions need gas above TX_MAX_GAS_LIMIT for
    state gas, so the block gas limit must accommodate this.
    """
    if fork >= Amsterdam:
        return max(gas_limit, 100_000_000)
    return gas_limit


@pytest.fixture
def state_gas_headroom(fork: Fork) -> Callable[[int], int]:
    """Fixture that returns a gas adjustment function for the current fork."""

    def adjust(gas: int) -> int:
        return gas_with_state_headroom(fork, gas)

    return adjust


@pytest.fixture
def block_gas_limit(fork: Fork) -> Callable[[int], int]:
    """Fixture that returns a block gas limit function for the current fork."""

    def adjust(gas_limit: int) -> int:
        return block_gas_limit_for_fork(fork, gas_limit)

    return adjust
