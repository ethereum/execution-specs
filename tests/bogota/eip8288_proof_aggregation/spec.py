"""Defines EIP-8288 specification constants and types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8288 = ReferenceSpec(
    "EIPS/eip-8288.md", "6e055031bf086a618840bd234348be3f0f6ba283"
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
    """Reserved: invalid until the EIP defines its `get_deps_hash`."""
