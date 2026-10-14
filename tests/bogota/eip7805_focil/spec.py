"""Reference spec for [EIP-7805: FOCIL](https://eips.ethereum.org/EIPS/eip-7805)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7805 = ReferenceSpec(
    git_path="EIPS/eip-7805.md",
    version="652e4b2d3e4d957f7fa9d57b70bf3d6b97dfbe71",
)
