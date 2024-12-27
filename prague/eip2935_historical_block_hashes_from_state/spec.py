"""Defines EIP-2935 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_2935 = ReferenceSpec("EIPS/eip-2935.md", "68d54a80a4f5b9c0cf4ae3a10586d63ef221de36")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-2935 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-2935.
    """

    FORK_TIMESTAMP = 15_000
    HISTORY_STORAGE_ADDRESS = 0x0AAE40965E6800CD9B1F4B05FF21581047E3F91E
    HISTORY_SERVE_WINDOW = 8192
    BLOCKHASH_OLD_WINDOW = 256
