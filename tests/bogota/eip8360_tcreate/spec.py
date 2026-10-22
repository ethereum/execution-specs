"""Reference spec for [EIP-8360](https://eips.ethereum.org/EIPS/eip-8360)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


# Tracked against ethereum/EIPs#12370 (TCREATE context / opcode rules).
# Update the version hash when that PR merges to master.
ref_spec_8360 = ReferenceSpec(
    git_path="EIPS/eip-8360.md",
    version="8360-tcreate-context-selfdestruct",
)
