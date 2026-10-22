"""Reference spec for [EIP-4758](https://eips.ethereum.org/EIPS/eip-4758)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_4758 = ReferenceSpec(
    git_path="EIPS/eip-4758.md",
    version="df7433a9a0f56d5629e9ec2219623540590487ef",
)
