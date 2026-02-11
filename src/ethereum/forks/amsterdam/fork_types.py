"""
Ethereum Types.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Types reused throughout the specification, which are specific to Ethereum.
"""

from dataclasses import dataclass

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes256
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U8, U64, U256

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import Account, Address

VersionedHash = Hash32

Bloom = Bytes256


def encode_account(raw_account_data: Account, storage_root: Bytes) -> Bytes:
    """
    Encode `Account` dataclass.

    Storage is not stored in the `Account` dataclass, so `Accounts` cannot be
    encoded without providing a storage root.
    """
    return rlp.encode(
        (
            raw_account_data.nonce,
            raw_account_data.balance,
            storage_root,
            keccak256(raw_account_data.code),
        )
    )


@slotted_freezable
@dataclass
class Authorization:
    """
    The authorization for a set code transaction.
    """

    chain_id: U256
    address: Address
    nonce: U64
    y_parity: U8
    r: U256
    s: U256
