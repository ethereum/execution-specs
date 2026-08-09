"""Reference spec for [EIP-8024: Stack Access Instructions](https://eips.ethereum.org/EIPS/eip-8024)."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8024 = ReferenceSpec(
    git_path="EIPS/eip-8024.md",
    version="34b49095ca5f7343045da279f04e7ecd1e451393",
)


class Spec:
    """Constants and parameters from EIP-8024."""

    # Gas cost for DUPN, SWAPN, and EXCHANGE
    GAS_COST: int = 3

    # DUPN/SWAPN stack index range (after decoding)
    MIN_STACK_INDEX: int = 17
    MAX_STACK_INDEX: int = 235

    # EXCHANGE constraints: 1 <= n < m <= 29, n + m <= 30
    EXCHANGE_MIN_N: int = 1
    EXCHANGE_MAX_N: int = 14
    EXCHANGE_MAX_M: int = 29
    EXCHANGE_MAX_SUM: int = 30


def decode_single(x: int) -> int:
    """
    Decode the DUPN/SWAPN immediate byte per the EIP-8024 reference code.

    Return n with 17 <= n <= 235.
    """
    assert 0 <= x <= 90 or 128 <= x <= 255
    return (x + 145) % 256


def decode_pair(x: int) -> Tuple[int, int]:
    """
    Decode the EXCHANGE immediate byte per the EIP-8024 reference code.

    Return (n, m) with 1 <= n <= 14 and n < m <= 30 - n.
    """
    assert 0 <= x <= 81 or 128 <= x <= 255
    k = x ^ 143
    q, r = divmod(k, 16)
    if q < r:
        return q + 1, r + 1
    else:
        return r + 1, 29 - q
