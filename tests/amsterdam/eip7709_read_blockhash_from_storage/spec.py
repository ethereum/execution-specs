"""Defines EIP-7709 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7709 = ReferenceSpec(
    "EIPS/eip-7709.md",
    "b94046519523b2041f975e7227c1e7dfa2bfc782",
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7709 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7709.
    """

    HISTORY_STORAGE_ADDRESS = 0x0000F90827F1C53A10CB7A02335B175320002935
    HISTORY_SERVE_WINDOW = 8191
    BLOCKHASH_SERVE_WINDOW = 256
    GAS_COLD_STORAGE_ACCESS = 2100
    GAS_WARM_ACCESS = 100
