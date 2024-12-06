"""
Hardfork Utility Functions For Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Address specific functions used in this spurious dragon version of
specification.
"""
from typing import Union

from ethereum_rlp import rlp
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import keccak256
from ethereum.utils.byte import left_pad_zero_bytes

from ..fork_types import Address


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


def compute_contract_address(address: Address, nonce: Uint) -> Address:
    """
    Computes address of the new account that needs to be created.

    Parameters
    ----------
    address :
        The address of the account that wants to create the new account.
    nonce :
        The transaction count of the account that wants to create the new
        account.

    Returns
    -------
    address: `ethereum.spurious_dragon.fork_types.Address`
        The computed address of the new account.
    """
    computed_address = keccak256(rlp.encode([address, nonce]))
    canonical_address = computed_address[-20:]
    padded_address = left_pad_zero_bytes(canonical_address, 20)
    return Address(padded_address)
