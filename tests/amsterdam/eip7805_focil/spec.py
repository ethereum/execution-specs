"""Reference spec for [EIP-7805: FOCIL](https://eips.ethereum.org/EIPS/eip-7805)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7805 = ReferenceSpec(
    git_path="EIPS/eip-7805.md",
    version="0a3955d9e8772b7666f560402b2d81ae032a3d06",
)


@dataclass(frozen=True)
class Spec:
    """Constants and parameters from EIP-7805."""

    INCLUSION_LIST_UNSATISFIED_STATUS = "INCLUSION_LIST_UNSATISFIED"
