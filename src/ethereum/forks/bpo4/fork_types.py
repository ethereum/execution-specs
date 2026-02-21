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

from ethereum_types.bytes import Bytes20, Bytes256
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U8, U64, U256

from ethereum.crypto.hash import Hash32

Address = Bytes20
Root = Hash32
VersionedHash = Hash32

Bloom = Bytes256


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
