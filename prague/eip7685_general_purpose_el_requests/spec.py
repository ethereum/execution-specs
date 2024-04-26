"""
Common procedures to test
[EIP-7685: General purpose execution layer requests](https://eips.ethereum.org/EIPS/eip-7685)
"""  # noqa: E501

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_7685 = ReferenceSpec("EIPS/eip-7685.md", "52a260582376476e658b1dda60864bcac3cf5e1a")
