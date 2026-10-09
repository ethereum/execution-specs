"""Defines EIP-8272 specification constants and types."""

from dataclasses import dataclass

from execution_testing import Address, keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8272 = ReferenceSpec(
    "EIPS/eip-8272.md", "0acc21ad8359be83c0929c7cc70e45326be8acff"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8272 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8272.
    """

    RECENT_ROOT_ADDRESS = Address(0x8272D9679689EA2F307140CDF9002D27DC00FFFF)
    RECENT_ROOT_DEPLOYER = Address(0x14BF16D4C9842BF1EBF396E553477C66EB0A8A82)
    RECENT_ROOT_CODE = bytes.fromhex(
        "346100ba57366040146100c05736604836066100ba5780156100ba57610480"
        "81116100ba574b60005b602081013560c01c828110156100ba578083036120"
        "0011156100ba577f8f42481679c8e6fefa040974b3c905e0ce3f2e464ba93a"
        "cdb074a41181617efc60005260488260203760686000207fbdc897da2177d2"
        "60ff5f4be5d4b2aad43f89c3347a305b584fa5a2546d053daa60005290611f"
        "ff1660c01b60405260486000205414156100ba5760480182811061002857005b"
        "60006000fd5b33600052602060006020376034600c20807f8f42481679c8e6"
        "fefa040974b3c905e0ce3f2e464ba93acdb074a41181617efc6040524b6068"
        "52606052602060206088376068604020817fbdc897da2177d260ff5f4be5d4"
        "b2aad43f89c3347a305b584fa5a2546d053daa60a852611fff4b1660d05260"
        "c852604860a8205500"
    )
    RECENT_ROOT_NONCE = 1
    RECENT_ROOT_LENGTH = 8192
    RECENT_ROOT_USABLE_WINDOW = 8191
    MAX_RECENT_ROOT_REFERENCES = 16
    RECENT_ROOT_TUPLE_BYTES = 72
    RECENT_ROOT_WRITE_BYTES = 64
    RECENT_ROOT_ENTRY_DOMAIN = keccak256(b"RECENT_ROOT_ENTRY")
    RECENT_ROOT_STORAGE_DOMAIN = keccak256(b"RECENT_ROOT_STORAGE")

    # Reference vector from the EIP, valid at `current_slot = 2`.
    VECTOR_SOURCE_ADDRESS = Address(0x01)
    VECTOR_SALT = bytes(32)
    VECTOR_SLOT = 1
    VECTOR_ROOT = (2).to_bytes(32, "big")
    VECTOR_CURRENT_SLOT = 2
    VECTOR_SOURCE_ID = bytes.fromhex(
        "b9382d35273c75a50631a3e84d3c75ec9266e2b18c35a627e16cdbf26a18ca85"
    )
    VECTOR_ENTRY_HASH = bytes.fromhex(
        "0a0d1254c851be5a133b4c9a9e300f5602fc0f43dbe65aa6a66930d4ca0a51b8"
    )
    VECTOR_STORAGE_KEY = bytes.fromhex(
        "5f027aa1cbe2df279bf6518edd4b44ea5409fd800189ec35224e10ab05e574c3"
    )


def source_id(source_address: Address, salt: bytes) -> bytes:
    """
    Return the root source identifier: the keccak256 of the 20-byte source
    address followed by the 32-byte salt.
    """
    return bytes(keccak256(bytes(source_address) + bytes(salt)))


def entry_hash(source: bytes, slot: int, root: bytes) -> bytes:
    """
    Return the committed entry for `(source_id, slot, root)`: the keccak256
    of the entry domain, the source identifier, the slot as an eight-byte
    big-endian integer, and the root.
    """
    return bytes(
        keccak256(
            bytes(Spec.RECENT_ROOT_ENTRY_DOMAIN)
            + bytes(source)
            + slot.to_bytes(8, "big")
            + bytes(root)
        )
    )


def storage_key(source: bytes, slot: int) -> int:
    """
    Return the recent root storage key holding the entry of `slot` for a
    source: the keccak256 of the storage domain, the source identifier,
    and the ring buffer index `slot mod RECENT_ROOT_LENGTH` as an
    eight-byte big-endian integer.
    """
    index = slot % Spec.RECENT_ROOT_LENGTH
    return int.from_bytes(
        keccak256(
            bytes(Spec.RECENT_ROOT_STORAGE_DOMAIN)
            + bytes(source)
            + index.to_bytes(8, "big")
        ),
        "big",
    )


def validation_tuple(source: bytes, slot: int, root: bytes) -> bytes:
    """Return the 72-byte validation encoding of `(source_id, slot, root)`."""
    return bytes(source) + slot.to_bytes(8, "big") + bytes(root)


def write_calldata(salt: bytes, root: bytes) -> bytes:
    """Return the 64-byte write encoding of `(salt, root)`."""
    return bytes(salt) + bytes(root)
