"""
Defines EIP-2935 specification constants and functions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_2935 = ReferenceSpec("EIPS/eip-2935.md", "3ab311ccd6029c080fb2a8b9615d493dfc093377")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-2935 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-2935
    """

    HISTORY_STORAGE_ADDRESS = 0x25A219378DAD9B3503C8268C9CA836A52427A4FB
    HISTORY_SERVE_WINDOW = 8192
    BLOCKHASH_OLD_WINDOW = 256
