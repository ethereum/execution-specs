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
from typing import NewType, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes256
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U8, U32, U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.state import Account, Address

BlockAccessIndex = U32
"""
Position within the set of all changes in a [`Block`].

[`Block`]: ref:ethereum.forks.bogota.blocks.Block
"""

VersionedHash = Hash32

Bloom = Bytes256


ExecutionGas = NewType("ExecutionGas", Uint)

StateGas = NewType("StateGas", Uint)


@final
@slotted_freezable
@dataclass
class StateGasPerByte:
    """
    State gas charged per byte of state growth, per [EIP-8037].

    A rate, not an amount: deliberately not a `Uint`, since adding a rate to
    a gas amount is meaningless. Multiplying it by a byte count, in either
    operand order, yields a `StateGas`.

    [EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
    """

    rate: Uint

    def __mul__(self, num_bytes: Uint) -> StateGas:
        """Return the state gas for `num_bytes` charged at this rate."""
        return StateGas(self.rate * num_bytes)

    def __rmul__(self, num_bytes: Uint) -> StateGas:
        """Return the state gas for `num_bytes` charged at this rate."""
        return StateGas(self.rate * num_bytes)


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


@final
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
