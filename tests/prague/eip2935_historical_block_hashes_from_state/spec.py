"""Defines EIP-2935 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_2935 = ReferenceSpec("EIPS/eip-2935.md", "06aadd458ee04ede80498db55927b052eb5bef38")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-2935 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-2935.
    """

    FORK_TIMESTAMP = 15_000
    HISTORY_STORAGE_ADDRESS = 0x0000F90827F1C53A10CB7A02335B175320002935
    HISTORY_SERVE_WINDOW = 8191
    BLOCKHASH_OLD_WINDOW = 256
