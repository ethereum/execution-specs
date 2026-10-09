"""
Keyed nonces for frame transactions, introduced in [EIP-8250].

A frame transaction selects a set of nonce keys sharing one sequence
number. The legacy key set aliases the sender's account nonce; every
other key selects an independent sequence held in the storage of the
nonce manager contract, so transactions whose key sets are disjoint do
not order each other.

Keyed nonce reads and writes are protocol bookkeeping: they bypass the
access lists and `SSTORE` pricing of ordinary storage access, and warm
nothing for later user-level access.

[EIP-8250]: https://eips.ethereum.org/EIPS/eip-8250
"""

from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import NonceMismatchError
from ethereum.state import Address
from ethereum.utils.byte import left_pad_zero_bytes

from .state_tracker import (
    TransactionState,
    get_account,
    get_storage,
    increment_nonce,
    set_storage,
)
from .transactions.frame_transaction import (
    LEGACY_NONCE_KEYS,
    NONCE_MANAGER,
    FrameTransaction,
)


def nonce_slot(sender: Address, nonce_key: U256) -> Bytes32:
    """
    Return the nonce manager storage slot holding `sender`'s sequence
    for `nonce_key`: the hash of the left-padded sender address followed
    by the big-endian key.
    """
    return Bytes32(
        keccak256(left_pad_zero_bytes(sender, 32) + nonce_key.to_be_bytes32())
    )


def current_nonce_seq(
    tx_state: TransactionState, sender: Address, nonce_key: U256
) -> Uint:
    """
    Return the current sequence of `sender`'s nonce domain `nonce_key`.

    The zero key reads the account nonce. Any other key reads the nonce
    manager, where an absent slot is sequence zero: the protocol never
    writes zero, so a zero read identifies a key's first use.
    """
    if nonce_key == U256(0):
        return get_account(tx_state, sender).nonce
    return Uint(
        get_storage(tx_state, NONCE_MANAGER, nonce_slot(sender, nonce_key))
    )


def check_nonce_set(tx_state: TransactionState, tx: FrameTransaction) -> None:
    """
    Check that every nonce key the transaction selects currently holds
    the transaction's sequence.
    """
    for nonce_key in tx.nonce_keys:
        current = current_nonce_seq(tx_state, tx.sender, nonce_key)
        if current > Uint(tx.nonce_seq):
            raise NonceMismatchError("nonce too low")
        elif current < Uint(tx.nonce_seq):
            raise NonceMismatchError("nonce too high")


def count_first_uses(tx_state: TransactionState, tx: FrameTransaction) -> Uint:
    """
    Return how many of the transaction's keyed nonce slots are still
    unused, each of which consuming the nonce set creates.
    """
    count = Uint(0)
    for nonce_key in tx.nonce_keys:
        if current_nonce_seq(tx_state, tx.sender, nonce_key) == Uint(0):
            count += Uint(1)
    return count


def consume_nonce_set(
    tx_state: TransactionState, tx: FrameTransaction
) -> None:
    """
    Consume the transaction's nonce set, once, on payment approval.

    The legacy key set increments the sender's account nonce, whatever
    it currently is, rather than setting it to the transaction's
    sequence plus one: an earlier frame may already have changed it.
    Any other key set advances each selected keyed sequence past the
    transaction's sequence.
    """
    if tx.nonce_keys == LEGACY_NONCE_KEYS:
        increment_nonce(tx_state, tx.sender)
        return
    for nonce_key in tx.nonce_keys:
        set_storage(
            tx_state,
            NONCE_MANAGER,
            nonce_slot(tx.sender, nonce_key),
            U256(tx.nonce_seq) + U256(1),
        )
