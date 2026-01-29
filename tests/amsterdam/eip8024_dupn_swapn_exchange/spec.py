"""Reference spec for [EIP-8024: Stack Access Instructions](https://eips.ethereum.org/EIPS/eip-8024)."""

from dataclasses import dataclass
from typing import Tuple

from ethereum_types.numeric import U8

from ethereum.forks.amsterdam.vm.stack import decode_pair as _decode_pair
from ethereum.forks.amsterdam.vm.stack import decode_single as _decode_single


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8024 = ReferenceSpec(
    git_path="EIPS/eip-8024.md",
    version="b54accd182b0e2e040ce2ba1a8a61bff6ca9fa0e",
)


@dataclass(frozen=True)
class Spec:
    """Constants and parameters from EIP-8024."""

    # Gas cost for DUPN, SWAPN, and EXCHANGE
    GAS_COST: int = 3

    # DUPN/SWAPN stack index range (after decoding)
    MIN_STACK_INDEX: int = 17
    MAX_STACK_INDEX: int = 235

    # EXCHANGE constraints: 1 <= n < m <= 29, n + m <= 30
    EXCHANGE_MIN_N: int = 1
    EXCHANGE_MAX_N: int = 13
    EXCHANGE_MAX_M: int = 29
    EXCHANGE_MAX_SUM: int = 30


def decode_pair(x: int) -> Tuple[int, int]:
    """Decode a pair with proper typing for tests."""
    m, n = _decode_pair(U8(x))
    return int(m), int(n)


def decode_single(x: int) -> int:
    """Decode single with proper typing for tests."""
    return int(_decode_single(U8(x)))
