"""Reference spec for [EIP-7805: Fork-choice Enforced Inclusion Lists](https://eips.ethereum.org/EIPS/eip-7805)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7805 = ReferenceSpec(
    git_path="EIPS/eip-7805.md",
    version="c492bd79366ebb10d07374379031daff4aa9e39a",
)


@dataclass(frozen=True)
class Spec:
    """Constants and parameters from EIP-7805."""

    # EIP-7805 Inclusion List parameters
    MAX_BYTES_PER_INCLUSION_LIST: int = 8192  # Maximum size per inclusion list
    IL_COMMITTEE_SIZE: int = 16  # Number of validators in the IL committee
