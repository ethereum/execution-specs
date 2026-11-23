"""Defines EIP-8288 specification constants and types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8288 = ReferenceSpec(
    "EIPS/eip-8288.md", "81b896b4584f2360d5ca038ea2b29d295898945e"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8288 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8288.
    """

    MODE_DEP_VERIFY = 4
    """The dependency verification frame mode value."""

    DEPENDENCY_LENGTH = 96
    """Length of one `(scheme, data_hash, verification_key_hash)` triple."""

    MAX_DEPENDENCIES_PER_FRAME = 256

    LEANSPHINCS_SCHEME = 0x10
    LEANSTARK_SCHEME = 0x11

    MAX_DEPENDENCY_PROOF_BYTES = 1048576

    EMPTY_PROOF_HASH = bytes.fromhex(
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    )
    """`keccak256(b"")`, both commitments of a block without claims."""
