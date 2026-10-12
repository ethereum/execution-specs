"""Reference spec for [EIP-7805: FOCIL](https://eips.ethereum.org/EIPS/eip-7805)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7805 = ReferenceSpec(
    git_path="EIPS/eip-7805.md",
    version="3727e348c4e9b56dfe53c2a1580d15102063ca28",
)
