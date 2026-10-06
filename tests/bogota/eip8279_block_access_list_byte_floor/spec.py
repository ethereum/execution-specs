"""Reference spec for [EIP-8279: Block Access List Byte Floor](https://eips.ethereum.org/EIPS/eip-8279)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8279 = ReferenceSpec(
    git_path="EIPS/eip-8279.md",
    version="744eafd69f87ba1cc5754671d8bf1fda8acec5f8",
)
