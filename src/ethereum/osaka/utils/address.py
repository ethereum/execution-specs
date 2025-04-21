"""
Hardfork Utility Functions For Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Address specific functions used in this osaka version of
specification.
"""
from typing import Union

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import keccak256
from ethereum.utils.byte import left_pad_zero_bytes

from ..fork_types import Address

MAX_ADDRESS_U256 = U256.from_be_bytes(b"\xff" * 20)


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
    return Address(data.to_be_bytes32()[-20:])


def to_address_without_mask(data: U256) -> Address:
    """
    Convert a Uint or U256 value to a valid address (20 bytes).
    Raises a `ValueError` if the data is larger than `MAX_ADDRESS_U256

    Parameters
    ----------
    data :
        The string to be converted to bytes.

    Raises
    ------
    ValueError
        If `data` is larger than `MAX_ADDRESS_U256`.

    Returns
    -------
    address : `Address`
        The obtained address.
    """
    if data > MAX_ADDRESS_U256:
        raise ValueError("Address is too large")
    return Address(data.to_be_bytes32()[-20:])


def compute_contract_address(address: Address, nonce: Uint) -> Address:
    """
    Computes address of the new account that needs to be created based
    on the account nonce.

    Parameters
    ----------
    address :
        The address of the account that wants to create the new account.
    nonce :
        The transaction count of the account that wants to create the new
        account.

    Returns
    -------
    address: `Address`
        The computed address of the new account.
    """
    computed_address = keccak256(rlp.encode([address, nonce]))
    canonical_address = computed_address[-20:]
    padded_address = left_pad_zero_bytes(canonical_address, 20)
    return Address(padded_address)


def compute_create2_contract_address(
    address: Address, salt: Bytes32, call_data: bytearray
) -> Address:
    """
    Computes address of the new account that needs to be created, which is
    based on the sender address, salt and the call data as well.

    Parameters
    ----------
    address :
        The address of the account that wants to create the new account.
    salt :
        Address generation salt.
    call_data :
        The code of the new account which is to be created.

    Returns
    -------
    address: `ethereum.osaka.fork_types.Address`
        The computed address of the new account.
    """
    preimage = b"\xff" + address + salt + keccak256(call_data)
    computed_address = keccak256(preimage)
    canonical_address = computed_address[-20:]
    padded_address = left_pad_zero_bytes(canonical_address, 20)

    return Address(padded_address)


def compute_eof_tx_create_contract_address(
    address: Address, salt: Bytes32
) -> Address:
    """
    Computes address of the new account that needs to be created, in the
    EOF1 TXCREATE Opcode.

    Parameters
    ----------
    address :
        The address of the account that wants to create the new account.
    salt :
        Address generation salt.

    Returns
    -------
    address: `ethereum.osaka.fork_types.Address`
        The computed address of the new account.
    """
    preimage = b"\xff" + left_pad_zero_bytes(address, 32) + salt
    computed_address = keccak256(preimage)
    canonical_address = computed_address[-20:]
    padded_address = left_pad_zero_bytes(canonical_address, 20)

    return Address(padded_address)
