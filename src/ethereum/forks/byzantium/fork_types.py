"""
Ethereum Types.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Types reused throughout the specification, which are specific to Ethereum.
"""

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes256

from ethereum.crypto.hash import Hash32
from ethereum.state import EMPTY_ACCOUNT, EMPTY_CODE_HASH, Account, Address

Root = Hash32

Bloom = Bytes256

__all__ = (
    "Account",
    "Address",
    "Bloom",
    "EMPTY_ACCOUNT",
    "EMPTY_CODE_HASH",
    "Root",
    "encode_account",
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
            raw_account_data.code_hash,
        )
    )
