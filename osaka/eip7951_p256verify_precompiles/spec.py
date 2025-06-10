"""Defines EIP-7951 specification constants and functions."""

from dataclasses import dataclass
from typing import Sized, SupportsBytes

from ethereum_test_tools import Address, Bytes


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7951 = ReferenceSpec("EIPS/eip-7951.md", "06aadd458ee04ede80498db55927b052eb5bef38")


class BytesConcatenation(SupportsBytes, Sized):
    """A class that can be concatenated with bytes."""

    def __len__(self) -> int:
        """Return length of the object when converted to bytes."""
        return len(bytes(self))

    def __add__(self, other: bytes | SupportsBytes) -> bytes:
        """Concatenates the object with another bytes object."""
        return bytes(self) + bytes(other)

    def __radd__(self, other: bytes | SupportsBytes) -> bytes:
        """Concatenates the object with another bytes object."""
        return bytes(other) + bytes(self)


@dataclass(frozen=True)
class FieldElement(BytesConcatenation):
    """Dataclass that defines a single field element."""

    value: int = 0

    def __bytes__(self) -> bytes:
        """Convert field element to bytes."""
        return self.value.to_bytes(32, byteorder="big")


# Specific field element classes
@dataclass(frozen=True)
class R(FieldElement):
    """Dataclass that defines a R component of the signature."""

    pass


@dataclass(frozen=True)
class S(FieldElement):
    """Dataclass that defines a S component of the signature."""

    pass


@dataclass(frozen=True)
class X(FieldElement):
    """Dataclass that defines a X coordinate value."""

    pass


@dataclass(frozen=True)
class Y(FieldElement):
    """Dataclass that defines a Y coordinate value."""

    pass


@dataclass(frozen=True)
class H(FieldElement):
    """Dataclass that defines a Message Hash value."""

    pass


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7951 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7951.
    """

    # Address
    P256VERIFY = 0x100

    # Gas constants
    P256VERIFY_GAS = 3450

    # Curve Parameters
    P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF  ## Base field modulus
    A = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC  ## Curve Coefficient
    B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B  ## Curve Coefficient
    N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551  ## Subgroup Order

    # Other constants
    SUCCESS_RETURN_VALUE = b"\x01".rjust(32, b"\x00")
    INVALID_RETURN_VALUE = b""
    DELEGATION_DESIGNATION = Bytes("ef0100")

    # Test constants (from https://github.com/C2SP/wycheproof/blob/4a6c2bf5dc4c0b67c770233ad33961ee653996a0/testvectors/ecdsa_secp256r1_sha256_test.json#L35)
    H0 = H(0xBB5A52F42F9C9261ED4361F59422A1E30036E7C32B270C8807A419FECA605023)
    R0 = R(0x2BA3A8BE6B94D5EC80A6D9D1190A436EFFE50D85A1EEE859B8CC6AF9BD5C2E18)
    S0 = S(0x4CD60B855D442F5B3C7B11EB6C4E0AE7525FE710FAB9AA7C77A67F79E6FADD76)
    X0 = X(0x2927B10512BAE3EDDCFE467828128BAD2903269919F7086069C8C4DF6C732838)
    Y0 = Y(0xC7787964EAAC00E5921FB1498A60F4606766B3D9685001558D1A974E7341513E)

    @staticmethod
    def delegation_designation(address: Address) -> Bytes:
        """Return delegation designation for the given address."""
        return Bytes(Spec.DELEGATION_DESIGNATION + bytes(address))
