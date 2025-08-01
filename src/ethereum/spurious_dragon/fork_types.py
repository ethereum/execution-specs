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

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes20, Bytes256
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

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
    code: Bytes


EMPTY_ACCOUNT = Account(
    nonce=Uint(0),
    balance=U256(0),
    code=b"",
)


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
