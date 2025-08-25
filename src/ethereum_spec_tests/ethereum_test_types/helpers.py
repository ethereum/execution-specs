"""Helper functions/classes used to generate Ethereum tests."""

from typing import List, SupportsBytes

import ethereum_rlp as eth_rlp
from pydantic import BaseModel, ConfigDict

from ethereum_test_base_types.base_types import Address, Bytes, Hash
from ethereum_test_base_types.conversions import BytesConvertible, FixedSizeBytesConvertible
from ethereum_test_vm import Opcodes as Op

from .account_types import EOA
from .utils import int_to_bytes

"""
Helper functions
"""


def ceiling_division(a: int, b: int) -> int:
    """
    Calculate ceil without using floating point.
    Used by many of the EVM's formulas.
    """
    return -(a // -b)


def compute_create_address(
    *,
    address: FixedSizeBytesConvertible | EOA,
    nonce: int | None = None,
    salt: int = 0,
    initcode: BytesConvertible = b"",
    opcode: Op = Op.CREATE,
) -> Address:
    """
    Compute address of the resulting contract created using a transaction
    or the `CREATE` opcode.
    """
    if opcode == Op.CREATE:
        if isinstance(address, EOA):
            if nonce is None:
                nonce = address.nonce
        else:
            address = Address(address)
        if nonce is None:
            nonce = 0
        hash_bytes = Bytes(eth_rlp.encode([address, int_to_bytes(nonce)])).keccak256()
        return Address(hash_bytes[-20:])
    if opcode == Op.CREATE2:
        return compute_create2_address(address, salt, initcode)
    raise ValueError("Unsupported opcode")


def compute_create2_address(
    address: FixedSizeBytesConvertible, salt: FixedSizeBytesConvertible, initcode: BytesConvertible
) -> Address:
    """
    Compute address of the resulting contract created using the `CREATE2`
    opcode.
    """
    hash_bytes = Bytes(
        b"\xff" + Address(address) + Hash(salt) + Bytes(initcode).keccak256()
    ).keccak256()
    return Address(hash_bytes[-20:])


def compute_eofcreate_address(
    address: FixedSizeBytesConvertible, salt: FixedSizeBytesConvertible
) -> Address:
    """Compute address of the resulting contract created using the `EOFCREATE` opcode."""
    hash_bytes = Bytes(b"\xff" + b"\x00" * 12 + Address(address) + Hash(salt)).keccak256()
    return Address(hash_bytes[-20:])


def add_kzg_version(
    b_hashes: List[bytes | SupportsBytes | int | str], kzg_version: int
) -> List[Hash]:
    """Add  Kzg Version to each blob hash."""
    kzg_version_hex = bytes([kzg_version])
    kzg_versioned_hashes = []

    for b_hash in b_hashes:
        b_hash = bytes(Hash(b_hash))
        if isinstance(b_hash, int) or isinstance(b_hash, str):
            kzg_versioned_hashes.append(Hash(kzg_version_hex + b_hash[1:]))
        elif isinstance(b_hash, bytes) or isinstance(b_hash, SupportsBytes):
            if isinstance(b_hash, SupportsBytes):
                b_hash = bytes(b_hash)
            kzg_versioned_hashes.append(Hash(kzg_version_hex + b_hash[1:]))
        else:
            raise TypeError("Blob hash must be either an integer, string or bytes")
    return kzg_versioned_hashes


class TestParameterGroup(BaseModel):
    """
    Base class for grouping test parameters in a dataclass. Provides a generic
    __repr__ method to generate clean test ids, including only non-default
    optional fields.
    """

    __test__ = False  # explicitly prevent pytest collecting this class

    model_config = ConfigDict(frozen=True, validate_default=True)

    def __repr__(self):
        """
        Generate repr string, intended to be used as a test id, based on the class
        name and the values of the non-default optional fields.
        """
        class_name = self.__class__.__name__
        field_strings = [
            f"{field}_{value}"
            # Include the field only if it is not optional or not set to its default value
            for field, value in self.model_dump(exclude_defaults=True, exclude_unset=True).items()
        ]

        return f"{class_name}_{'-'.join(field_strings)}"
