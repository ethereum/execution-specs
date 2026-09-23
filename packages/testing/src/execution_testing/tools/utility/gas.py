"""Search for gas-bounded test inputs using fork-aware cost calculators."""

from typing import Callable


def max_count_with_gas_limit(
    cost_fn: Callable[[int], int],
    gas_limit: int,
    *,
    max_count: int | None = None,
) -> int:
    """
    Return the largest affordable count for a nondecreasing cost function.

    Require count zero to fit. Without ``max_count``, the cost must eventually
    exceed ``gas_limit``. Supply a bound for inputs limited by protocol rules
    such as maximum initcode size.
    """
    if max_count is not None and max_count < 0:
        raise ValueError("max_count must be nonnegative")
    if cost_fn(0) > gas_limit:
        raise ValueError("Gas limit does not cover the cost at count zero")

    low = 0
    if max_count is None:
        high = 1
        while cost_fn(high) <= gas_limit:
            low = high
            high *= 2
    else:
        high = max_count

    while low < high:
        mid = (low + high + 1) // 2
        if cost_fn(mid) <= gas_limit:
            low = mid
        else:
            high = mid - 1
    return low
