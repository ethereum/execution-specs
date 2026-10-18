"""
Defines EIP-7709 specification constants and reference spec version.
"""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7709 = ReferenceSpec(
    git_path="EIPS/eip-7709.md",
    version="0c7c4c625efdd4e0a8932f38d005c39463284cf1",
)


class Spec:
    """
    Parameters from the EIP-7709 and EIP-2935 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7709.
    """

    FORK_TIMESTAMP = 15_000
    HISTORY_STORAGE_ADDRESS = Address(
        0x0000F90827F1C53A10CB7A02335B175320002935
    )
    HISTORY_SERVE_WINDOW = 8191
    BLOCKHASH_SERVE_WINDOW = 256
