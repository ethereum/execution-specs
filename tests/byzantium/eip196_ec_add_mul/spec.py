"""Defines EIP-196 specification constants and functions."""

from dataclasses import dataclass

from execution_testing import Address, BytesConcatenation

from ...constantinople.eip145_bitwise_shift.spec import ReferenceSpec

ref_spec_196 = ReferenceSpec(
    "EIPS/eip-196.md", "6538d198b1db10784ddccd6931888d7ae718de75"
)


@dataclass(frozen=True)
class FP(BytesConcatenation):
    """Dataclass that defines an element of the BN254 Prime Field (Fp)."""

    x: int = 0

    def __bytes__(self) -> bytes:
        """Convert field element to bytes."""
        return self.x.to_bytes(32, byteorder="big")


@dataclass(frozen=True)
class PointG1(BytesConcatenation):
    """Dataclass that defines an affine point in the BN254 E(Fp) group (G1)."""

    x: int = 0
    y: int = 0

    def __bytes__(self) -> bytes:
        """Convert point to bytes."""
        return FP(self.x) + FP(self.y)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-196 specification (https://eips.ethereum.org/EIPS/eip-196)
    with some modifications for readability.
    """

    # Addresses
    ECADD = Address(0x06)
    ECMUL = Address(0x07)

    # G1 generator point
    G1 = PointG1(1, 2)

    # The point at infinity in G1
    INF_G1 = PointG1()
