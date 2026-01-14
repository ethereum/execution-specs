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

    # Maximum immediate value for DUPN and SWAPN (0x00 to 0xFF)
    MAX_IMMEDIATE: int = 0xFF

    # EXCHANGE immediate encoding: high 4 bits = n, low 4 bits = m
    # n ranges from 1 to 16 (encoded as 0-15)
    # m ranges from 1 to 16 (encoded as 0-15)
    EXCHANGE_MAX_N: int = 16
    EXCHANGE_MAX_M: int = 16
