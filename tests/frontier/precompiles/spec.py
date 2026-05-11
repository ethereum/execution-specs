"""Defines spec constants and input types for the ECRECOVER precompile."""

from dataclasses import dataclass

from execution_testing import Address, BytesConcatenation


@dataclass(frozen=True)
class EcrecoverInput(BytesConcatenation):
    """
    ECRECOVER precompile input: 32-byte message hash, 32-byte v, 32-byte r,
    32-byte s — concatenated big-endian (128 bytes total).
    """

    msg_hash: int
    v: int
    r: int
    s: int

    def __bytes__(self) -> bytes:
        """Convert input to bytes."""
        return b"".join(
            x.to_bytes(32, byteorder="big")
            for x in (self.msg_hash, self.v, self.r, self.s)
        )


@dataclass(frozen=True)
class Spec:
    """Parameters for the frontier precompiles."""

    ECRECOVER = Address(0x01)
    SHA256 = Address(0x02)
    RIPEMD160 = Address(0x03)
