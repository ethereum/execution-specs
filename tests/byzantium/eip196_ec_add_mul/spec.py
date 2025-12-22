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

    # The prime modulus of the BN254 prime field Fp
    P = 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD47

    # G1 generator point
    G1 = PointG1(1, 2)

    # The point at infinity in G1
    INF_G1 = PointG1()

    # G1 generator point doubled: [2]G1
    G1x2 = PointG1(
        0x030644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,
        0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4,
    )

    # Example point P
    P1 = PointG1(
        0x17C139DF0EFEE0F766BC0204762B774362E4DED88953A39CE849A8A7FA163FA9,
        0x01E0559BACB160664764A357AF8A9FE70BAA9258E0B959273FFC5718C6D4CC7C,
    )

    # Example point Q
    Q1 = PointG1(
        0x039730EA8DFF1254C0FEE9C0EA777D29A9C710B7E616683F194F18C43B43B869,
        0x073A5FFCC6FC7A28C30723D6E58CE577356982D65B833A5A5C15BF9024B43D98,
    )

    # Example point R = P + Q
    R1 = PointG1(
        0x15BF2BB17880144B5D1CD2B1F46EFF9D617BFFD1CA57C37FB5A49BD84E53CF66,
        0x049C797F9CE0D17083DEB32B5E36F2EA2A212EE036598DD7624C168993D1355F,
    )
