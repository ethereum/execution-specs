"""Test gas-budget searches independently of fork gas schedules."""

import pytest

from execution_testing import max_count_with_gas_limit


@pytest.mark.parametrize(
    "gas_limit,expected", [(20, 0), (29, 0), (30, 1), (50, 3)]
)
def test_base_cost(gas_limit: int, expected: int) -> None:
    """Include fixed costs and find exact and in-between boundaries."""
    assert (
        max_count_with_gas_limit(lambda n: 20 + 10 * n, gas_limit) == expected
    )


def test_step_cost() -> None:
    """Find the last count on a cost plateau."""
    assert max_count_with_gas_limit(lambda n: (n // 3) * 10, 20) == 8


@pytest.mark.parametrize("max_count", [0, 2, 100])
def test_input_bound(max_count: int) -> None:
    """Respect a protocol bound even when every input is affordable."""
    assert (
        max_count_with_gas_limit(lambda _: 0, 0, max_count=max_count)
        == max_count
    )


def test_insufficient_gas() -> None:
    """Reject a budget that cannot cover the fixed cost."""
    with pytest.raises(ValueError, match="count zero"):
        max_count_with_gas_limit(lambda n: 20 + n, 19)


def test_negative_bound() -> None:
    """Reject a negative input bound."""
    with pytest.raises(ValueError, match="nonnegative"):
        max_count_with_gas_limit(lambda n: n, 20, max_count=-1)
