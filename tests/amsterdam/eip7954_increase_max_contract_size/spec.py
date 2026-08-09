"""Reference spec for [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7954 = ReferenceSpec(
    git_path="EIPS/eip-7954.md",
    version="1dc9bc870f864d7ad1095fc73ba8ca098d02c732",
)
