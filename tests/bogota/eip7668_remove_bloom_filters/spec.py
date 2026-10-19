"""Reference spec for [EIP-7668: Remove bloom filters](https://eips.ethereum.org/EIPS/eip-7668)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7668 = ReferenceSpec(
    git_path="EIPS/eip-7668.md",
    version="fbd998df2618dbc95d60be74c7bdad76f5042bd1",
)
