"""
Helper functions/classes used to generate Ethereum tests.
"""

from dataclasses import MISSING, dataclass, fields
from typing import List, SupportsBytes

from ethereum.rlp import encode

from ethereum_test_base_types.base_types import Address, Bytes, Hash
from ethereum_test_base_types.conversions import BytesConvertible, FixedSizeBytesConvertible
from ethereum_test_vm import Opcodes as Op

from .types import EOA

"""
Helper functions
"""


def ceiling_division(a: int, b: int) -> int:
    """
    Calculates the ceil without using floating point.
    Used by many of the EVM's formulas
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
        nonce_bytes = bytes() if nonce == 0 else nonce.to_bytes(length=1, byteorder="big")
        hash = Bytes(encode([address, nonce_bytes])).keccak256()
        return Address(hash[-20:])
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
    hash = Bytes(b"\xff" + Address(address) + Hash(salt) + Bytes(initcode).keccak256()).keccak256()
    return Address(hash[-20:])


def cost_memory_bytes(new_bytes: int, previous_bytes: int) -> int:
    """
    Calculates the cost of memory expansion, based on the costs specified in
    the yellow paper: https://ethereum.github.io/yellowpaper/paper.pdf
    """
    if new_bytes <= previous_bytes:
        return 0
    new_words = ceiling_division(new_bytes, 32)
    previous_words = ceiling_division(previous_bytes, 32)

    def c(w: int) -> int:
        g_memory = 3
        return (g_memory * w) + ((w * w) // 512)

    return c(new_words) - c(previous_words)


def copy_opcode_cost(length: int) -> int:
    """
    Calculates the cost of the COPY opcodes, assuming memory expansion from
    empty memory, based on the costs specified in the yellow paper:
    https://ethereum.github.io/yellowpaper/paper.pdf
    """
    return 3 + (ceiling_division(length, 32) * 3) + cost_memory_bytes(length, 0)


def compute_eofcreate_address(
    address: FixedSizeBytesConvertible,
    salt: FixedSizeBytesConvertible,
    init_container: BytesConvertible,
) -> Address:
    """
    Compute address of the resulting contract created using the `EOFCREATE` opcode.
    """
    hash = Bytes(
        b"\xff" + Address(address) + Hash(salt) + Bytes(init_container).keccak256()
    ).keccak256()
    return Address(hash[-20:])


def eip_2028_transaction_data_cost(data: BytesConvertible) -> int:
    """
    Calculates the cost of a given data as part of a transaction, based on the
    costs specified in EIP-2028: https://eips.ethereum.org/EIPS/eip-2028
    """
    cost = 0
    for b in Bytes(data):
        if b == 0:
            cost += 4
        else:
            cost += 16
    return cost


def add_kzg_version(
    b_hashes: List[bytes | SupportsBytes | int | str], kzg_version: int
) -> List[bytes]:
    """
    Adds the Kzg Version to each blob hash.
    """
    kzg_version_hex = bytes([kzg_version])
    kzg_versioned_hashes = []

    for hash in b_hashes:
        hash = bytes(Hash(hash))
        if isinstance(hash, int) or isinstance(hash, str):
            kzg_versioned_hashes.append(kzg_version_hex + hash[1:])
        elif isinstance(hash, bytes) or isinstance(hash, SupportsBytes):
            if isinstance(hash, SupportsBytes):
                hash = bytes(hash)
            kzg_versioned_hashes.append(kzg_version_hex + hash[1:])
        else:
            raise TypeError("Blob hash must be either an integer, string or bytes")
    return kzg_versioned_hashes


@dataclass(kw_only=True, frozen=True, repr=False)
class TestParameterGroup:
    """
    Base class for grouping test parameters in a dataclass. Provides a generic
    __repr__ method to generate clean test ids, including only non-default
    optional fields.
    """

    __test__ = False  # explicitly prevent pytest collecting this class

    def __repr__(self):
        """
        Generates a repr string, intended to be used as a test id, based on the class
        name and the values of the non-default optional fields.
        """
        class_name = self.__class__.__name__
        field_strings = []

        for field in fields(self):
            value = getattr(self, field.name)
            # Include the field only if it is not optional or not set to its default value
            if field.default is MISSING or field.default != value:
                field_strings.append(f"{field.name}_{value}")

        return f"{class_name}_{'-'.join(field_strings)}"
