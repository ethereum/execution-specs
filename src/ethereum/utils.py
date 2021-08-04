"""
Utility Functions
^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Utility functions used in this application.
"""
from typing import Any, Dict, Tuple, Union

from ethereum import crypto
from ethereum.base_types import Uint
from ethereum.frontier import rlp
from ethereum.frontier.eth_types import (
    U256,
    Address,
    Block,
    Bloom,
    Bytes,
    Bytes8,
    Bytes32,
    Hash32,
    Header,
    Root,
    Transaction,
)


def get_sign(value: int) -> int:
    """
    Determines the sign of a number.

    Parameters
    ----------
    value :
        The value whose sign is to be determined.

    Returns
    -------
    sign : `int`
        The sign of the number (-1 or 0 or 1).
        The return value is based on math signum function.
    """
    if value < 0:
        return -1
    elif value == 0:
        return 0
    else:
        return 1


def ceil32(value: Uint) -> Uint:
    """
    Converts a unsigned integer to the next closest multiple of 32.

    Parameters
    ----------
    value :
        The value whose ceil32 is to be calculated.

    Returns
    -------
    ceil32 : `ethereum.base_types.U256`
        The same value if it's a perfect multiple of 32
        else it returns the smallest multiple of 32
        that is greater than `value`.
    """
    ceiling = Uint(32)
    remainder = value % ceiling
    if remainder == Uint(0):
        return value
    else:
        return value + ceiling - remainder


def to_address(data: Union[Uint, U256]) -> Address:
    """
    Convert a Uint or U256 value to a valid address (20 bytes).

    Parameters
    ----------
    data :
        The string to be converted to bytes.

    Returns
    -------
    address : `Address`
        The obtained address.
    """
    return data.to_be_bytes32()[-20:]


def has_hex_prefix(hex_string: str) -> bool:
    """
    Check if a hex string starts with hex prefix (0x).

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be checked for presence of prefix.

    Returns
    -------
    has_prefix : `bool`
        Boolean indicating whether the hex string has 0x prefix.
    """
    return hex_string.startswith("0x")


def remove_hex_prefix(hex_string: str) -> str:
    """
    Remove 0x prefix from a hex string if present. This function returns the
    passed hex string if it isn't prefixed with 0x.

    Parameters
    ----------
    hex_string :
        The hexadecimal string whose prefix is to be removed.

    Returns
    -------
    modified_hex_string : `str`
        The hexadecimal string with the 0x prefix removed if present.
    """
    if has_hex_prefix(hex_string):
        return hex_string[len("0x") :]

    return hex_string


def hex_to_bytes(hex_string: str) -> Bytes:
    """
    Convert hex string to bytes.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to bytes.

    Returns
    -------
    byte_stream : `bytes`
        Byte stream corresponding to the given hexadecimal string.
    """
    return bytes.fromhex(remove_hex_prefix(hex_string))


def hex_to_bytes8(hex_string: str) -> Bytes8:
    """
    Convert hex string to 8 bytes.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to 8 bytes.

    Returns
    -------
    8_byte_stream : `bytes`
        8-byte stream corresponding to the given hexadecimal string.
    """
    return Bytes8(bytes.fromhex(remove_hex_prefix(hex_string).rjust(16, "0")))


def hex_to_bytes32(hex_string: str) -> Bytes32:
    """
    Convert hex string to 32 bytes.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to 32 bytes.

    Returns
    -------
    32_byte_stream : `bytes`
        32-byte stream corresponding to the given hexadecimal string.
    """
    return Bytes32(bytes.fromhex(remove_hex_prefix(hex_string).rjust(64, "0")))


def hex_to_hash(hex_string: str) -> Hash32:
    """
    Convert hex string to hash32 (32 bytes).

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to hash32.

    Returns
    -------
    hash : `Hash32`
        32-byte stream obtained from the given hexadecimal string.
    """
    return Hash32(bytes.fromhex(remove_hex_prefix(hex_string)))


def hex_to_root(hex_string: str) -> Root:
    """
    Convert hex string to trie root.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to trie root.

    Returns
    -------
    root : `Root`
        Trie root obtained from the given hexadecimal string.
    """
    return Root(bytes.fromhex(remove_hex_prefix(hex_string)))


def hex_to_bloom(hex_string: str) -> Bloom:
    """
    Convert hex string to bloom.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to bloom.

    Returns
    -------
    bloom : `Bloom`
        Bloom obtained from the given hexadecimal string.
    """
    return Bloom(bytes.fromhex(remove_hex_prefix(hex_string)))


def hex_to_address(hex_string: str) -> Address:
    """
    Convert hex string to Address (20 bytes).

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to Address.

    Returns
    -------
    address : `Address`
        The address obtained from the given hexadecimal string.
    """
    return Address(bytes.fromhex(remove_hex_prefix(hex_string).rjust(40, "0")))


def hex_to_uint(hex_string: str) -> Uint:
    """
    Convert hex string to Uint.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to Uint.

    Returns
    -------
    converted : `Uint`
        The unsigned integer obtained from the given hexadecimal string.
    """
    return Uint(int(remove_hex_prefix(hex_string), 16))


def hex_to_u256(hex_string: str) -> U256:
    """
    Convert hex string to U256.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to U256.

    Returns
    -------
    converted : `U256`
        The U256 integer obtained from the given hexadecimal string.
    """
    return U256(int(remove_hex_prefix(hex_string), 16))


def rlp_hash(data: rlp.RLP) -> Hash32:
    """
    Obtain the keccak-256 hash of the rlp encoding of the passed in data.

    Parameters
    ----------
    data :
        The data for which we need the rlp hash.

    Returns
    -------
    hash : `Hash32`
        The rlp hash of the passed in data.
    """
    return crypto.keccak256(rlp.encode(data))


def json_to_header(json_data: Dict[Any, Any]) -> Header:
    """
    Convert json data to block header.

    Parameters
    ----------
    json_data :
        The header data where the values are hexadecimals.

    Returns
    -------
    header : `Header`
        The header object obtained from the json data.
    """
    return Header(
        parent_hash=hex_to_hash(json_data["parentHash"]),
        ommers_hash=hex_to_hash(json_data["sha3Uncles"]),
        coinbase=hex_to_address(json_data["miner"]),
        state_root=hex_to_root(json_data["stateRoot"]),
        transactions_root=hex_to_root(json_data["transactionsRoot"]),
        receipt_root=hex_to_root(json_data["receiptsRoot"]),
        bloom=hex_to_bloom(json_data["logsBloom"]),
        difficulty=hex_to_uint(json_data["difficulty"]),
        number=hex_to_uint(json_data["number"]),
        gas_limit=hex_to_uint(json_data["gasLimit"]),
        gas_used=hex_to_uint(json_data["gasUsed"]),
        timestamp=hex_to_u256(json_data["timestamp"]),
        extra_data=hex_to_bytes(json_data["extraData"]),
        mix_digest=hex_to_bytes32(json_data["mixHash"]),
        nonce=hex_to_bytes8(json_data["nonce"]),
    )


def json_to_transactions(json_data: Dict[Any, Any]) -> Tuple[Transaction, ...]:
    """
    Convert json data to tuple of transaction objects.

    Parameters
    ----------
    json_data :
        The transactions data where the values are hexadecimals.

    Returns
    -------
    transactions : `Tuple[Transaction, ...]`
        The transaction objects obtained from the json data.
    """
    transactions = []
    for transaction in json_data["transactions"]:
        tx = Transaction(
            nonce=hex_to_u256(transaction["nonce"]),
            gas_price=hex_to_u256(transaction["gasPrice"]),
            gas=hex_to_u256(transaction["gas"]),
            to=(
                None
                if transaction["to"] == ""
                else hex_to_address(transaction["to"])
            ),
            value=hex_to_u256(transaction["value"]),
            data=hex_to_bytes(transaction["input"]),
            v=hex_to_u256(transaction["v"]),
            r=hex_to_u256(transaction["r"]),
            s=hex_to_u256(transaction["s"]),
        )
        transactions.append(tx)

    return tuple(transactions)


def json_to_block(
    block_json_data: Dict[Any, Any], ommers: Tuple[Header, ...]
) -> Block:
    """
    Convert json data to a block object with the help of ommer objects.

    Parameters
    ----------
    block_json_data :
        The block json data where the values are hexadecimals, which is used
        to derive the header and the transactions.
    ommers:
        The ommer headers required to form the current block object.

    Returns
    -------
    header : `Header`
        The header object obtained from the json data.
    """
    header = json_to_header(block_json_data)
    transactions = json_to_transactions(block_json_data)

    return Block(
        header=header,
        transactions=transactions,
        ommers=ommers,
    )
