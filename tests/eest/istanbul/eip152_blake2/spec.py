"""Defines EIP-152 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_152 = ReferenceSpec("EIPS/eip-152.md", "2762bfcff3e549ef263342e5239ef03ac2b07400")


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-152 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-152#specification.

    If the parameter is not currently used within the tests, it is commented
    out.
    """

    BLAKE2_PRECOMPILE_ADDRESS = 0x09

    # The following constants are used to define the bytes length of the
    # parameters passed to the BLAKE2 precompile.
    BLAKE2_PRECOMPILE_ROUNDS_LENGTH = 4
    # BLAKE2_PRECOMPILE_M_LENGTH = 128
    BLAKE2_PRECOMPILE_T_0_LENGTH = 8
    BLAKE2_PRECOMPILE_T_1_LENGTH = 8
    BLAKE2_PRECOMPILE_F_LENGTH = 1

    # Constants for BLAKE2b and BLAKE2s spec defined at https://datatracker.ietf.org/doc/html/rfc7693#section-3.2
    BLAKE2B_PRECOMPILE_ROUNDS = 12
    BLAKE2B_PRECOMPILE_H_LENGTH = 64

    # BLAKE2S_PRECOMPILE_ROUNDS = 10
    # BLAKE2S_PRECOMPILE_H_LENGTH = 32


class SpecTestVectors:
    """Defines common test parameters for the BLAKE2b precompile."""

    # The following constants are used to define common test parameters
    # Origin of vectors defined at https://datatracker.ietf.org/doc/html/rfc7693.html#appendix-A
    BLAKE2_STATE_VECTOR = "48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b"  # noqa:E501
    BLAKE2_MESSAGE_BLOCK_VECTOR = "6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa:E501
    BLAKE2_OFFSET_COUNTER_0 = 3
    BLAKE2_OFFSET_COUNTER_1 = 0
