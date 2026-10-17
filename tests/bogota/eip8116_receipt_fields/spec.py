"""Reference spec for EIP-8116."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8116 = ReferenceSpec(
    git_path="EIPS/eip-8116.md",
    version="c1f453382a4fef890e5a097bace777299fa16343",
)
