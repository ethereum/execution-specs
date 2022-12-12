"""
Helper functions/classes used to generate Ethereum tests.
"""

from ethereum.crypto.hash import keccak256
from ethereum.rlp import encode

"""
Helper functions
"""


def ceiling_division(a: int, b: int) -> int:
    """
    Calculates the ceil without using floating point.
    Used by many of the EVM's formulas
    """
    return -(a // -b)


def compute_create_address(address: str | int, nonce: int) -> str:
    """
    Compute address of the resulting contract created using a transaction
    or the `CREATE` opcode.
    """
    if type(address) is str:
        if address.startswith("0x"):
            address = address[2:]
        address_bytes = bytes.fromhex(address)
    elif type(address) is int:
        address_bytes = address.to_bytes(length=20, byteorder="big")
    if nonce == 0:
        nonce_bytes = bytes()
    else:
        nonce_bytes = nonce.to_bytes(length=1, byteorder="big")
    hash = keccak256(encode([address_bytes, nonce_bytes]))
    return "0x" + hash[-20:].hex()


def compute_create2_address(
    address: str | int, salt: int, initcode: bytes
) -> str:
    """
    Compute address of the resulting contract created using the `CREATE2`
    opcode.
    """
    ff = bytes([0xFF])
    if type(address) is str:
        if address.startswith("0x"):
            address = address[2:]
        address_bytes = bytes.fromhex(address)
    elif type(address) is int:
        address_bytes = address.to_bytes(length=20, byteorder="big")
    salt_bytes = salt.to_bytes(length=32, byteorder="big")
    initcode_hash = keccak256(initcode)
    hash = keccak256(ff + address_bytes + salt_bytes + initcode_hash)
    return "0x" + hash[-20:].hex()


def eip_2028_transaction_data_cost(data: bytes | str) -> int:
    """
    Calculates the cost of a given data as part of a transaction, based on the
    costs specified in EIP-2028: https://eips.ethereum.org/EIPS/eip-2028
    """
    if type(data) is str:
        if data.startswith("0x"):
            data = data[2:]
        data = bytes.fromhex(data)
    cost = 0
    for b in data:
        if b == 0:
            cost += 4
        else:
            cost += 16
    return cost


def to_address(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(20, "big").hex()
    raise Exception("invalid type to convert to account address")


def to_hash(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(32, "big").hex()
    raise Exception("invalid type to convert to hash")
