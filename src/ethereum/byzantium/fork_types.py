"""
Ethereum Types
^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Types re-used throughout the specification, which are specific to Ethereum.
"""

from dataclasses import dataclass

from .. import rlp
from ..base_types import (
    U256,
    Bytes,
    Bytes20,
    Bytes256,
    Uint,
    slotted_freezable,
)
from ..crypto.hash import Hash32, keccak256

Address = Bytes20
Root = Hash32
Bloom = Bytes256


@slotted_freezable
@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: Uint
    balance: U256
    code: bytes


EMPTY_ACCOUNT = Account(
    nonce=Uint(0),
    balance=U256(0),
    code=bytearray(),
)


def encode_account(raw_account_data: Account, storage_root: Bytes) -> Bytes:
    """
    Encode `Account` dataclass.

    Storage is not stored in the `Account` dataclass, so `Accounts` cannot be
    encoded with providing a storage root.
    """
    return rlp.encode(
        (
            raw_account_data.nonce,
            raw_account_data.balance,
            storage_root,
            keccak256(raw_account_data.code),
        )
    )
