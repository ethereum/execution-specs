"""Defines EIP-197 specification constants and functions."""

from dataclasses import dataclass

from execution_testing import Address, BytesConcatenation

from ...constantinople.eip145_bitwise_shift.spec import ReferenceSpec
from ..eip196_ec_add_mul.spec import FP, PointG1
from ..eip196_ec_add_mul.spec import Spec as Spec196

ref_spec_197 = ReferenceSpec(
    "EIPS/eip-197.md", "9f9b3d33440e7c122b6c9192facfc380bc009422"
)


@dataclass(frozen=True)
class PointG2(BytesConcatenation):
    """Affine point in the BN254 E'(Fp2) twist group (G2)."""

    x: tuple[int, int] = (0, 0)
    y: tuple[int, int] = (0, 0)

    def __bytes__(self) -> bytes:
        """Convert point to bytes."""
        return FP(self.x[0]) + FP(self.x[1]) + FP(self.y[0]) + FP(self.y[1])


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-197 specification
    (https://eips.ethereum.org/EIPS/eip-197).
    """

    # The prime modulus of the BN254 prime field Fp (from EIP-196)
    P = Spec196.P

    # The order of the BN254 G1 group
    N = Spec196.N

    # Precompile address
    ECPAIRING = Address(0x08)

    # G1 points (from EIP-196)
    G1 = Spec196.G1
    INF_G1 = Spec196.INF_G1
    NEG_G1 = PointG1(Spec196.G1.x, Spec196.P - Spec196.G1.y)

    # G2 generator
    G2 = PointG2(
        (
            0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
            0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
        ),
        (
            0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
            0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
        ),
    )

    # Point at infinity in G2
    INF_G2 = PointG2()

    # Pairing precompile results
    PAIRING_TRUE = int.to_bytes(1, length=32, byteorder="big")
    PAIRING_FALSE = int.to_bytes(0, length=32, byteorder="big")

    # Returned on precompile failure
    INVALID = b""
