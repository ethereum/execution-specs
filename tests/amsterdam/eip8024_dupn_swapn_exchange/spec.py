"""Reference spec for [EIP-8024: Stack Access Instructions](https://eips.ethereum.org/EIPS/eip-8024)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8024 = ReferenceSpec(
    git_path="EIPS/eip-8024.md",
    version="9842e867b5c75b9624d1e62b4eb532d3b219e70d",
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
