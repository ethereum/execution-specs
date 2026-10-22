"""
State diff of the executing frame transaction, as exposed to its
`ASSERT` assertion frames by the [EIP-7906] instructions.

The diff is the net difference between the transaction prestate, the
state before any write made in relation to the transaction with the gas
payment included, and the state as of the reading instruction. Writes
that later restore the prestate value leave no entry. `ASSERT` frames
run read-only after the execution body. Gas settlement and deferred
account deletion still follow them: the diff is the state at the read,
not the final committed state after that cleanup.

The tables are derived from the transaction-local write sets. A
storage wipe can also clear pre-existing slots absent from those sets,
and those slots are not enumerated: listing them would mean iterating
the account's prestate storage.

[EIP-7906]: https://eips.ethereum.org/EIPS/eip-7906
"""

from dataclasses import dataclass
from typing import Optional, Tuple, final

from ethereum_types.bytes import Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.state import EMPTY_ACCOUNT, Account, Address

from ..blocks import Log
from ..state_tracker import TransactionState, get_pre_state_account_optional
from . import FrameContext


@final
@slotted_freezable
@dataclass
class BalanceChange:
    """
    Entry of the `balances_changed` table: an address whose balance
    differs from its transaction prestate value.
    """

    address: Address
    """
    The account whose balance changed.
    """

    before: U256
    """
    The balance at the start of the transaction.
    """

    after: U256
    """
    The balance as of the reading instruction.
    """


@final
@slotted_freezable
@dataclass
class SlotChange:
    """
    Entry of the `slots_changed` table: a storage slot whose value
    differs from its transaction prestate value.
    """

    address: Address
    """
    The account whose storage changed.
    """

    key: Bytes32
    """
    The storage slot key.
    """

    before: U256
    """
    The slot value at the start of the transaction.
    """

    after: U256
    """
    The slot value as of the reading instruction.
    """


@final
@slotted_freezable
@dataclass
class CodeChange:
    """
    Entry of the `codes_changed` table: an address whose code hash
    differs from its transaction prestate value.
    """

    address: Address
    """
    The account whose code changed.
    """

    before: Hash32
    """
    The code hash at the start of the transaction.
    """

    after: Hash32
    """
    The code hash as of the reading instruction.
    """


@final
@slotted_freezable
@dataclass
class NonceChange:
    """
    Entry of the `nonces_changed` table: an address whose nonce differs
    from its transaction prestate value.
    """

    address: Address
    """
    The account whose nonce changed.
    """

    before: Uint
    """
    The nonce at the start of the transaction.
    """

    after: Uint
    """
    The nonce as of the reading instruction.
    """


@final
@slotted_freezable
@dataclass
class TransactionDiff:
    """
    The transaction's state diff, in the canonical enumeration order:
    balance, slot, code and nonce changes ascending by address, slots
    of one address ascending by key, and events in emission order.
    """

    balances: Tuple[BalanceChange, ...]
    """
    The `balances_changed` table.
    """

    slots: Tuple[SlotChange, ...]
    """
    The `slots_changed` table.
    """

    codes: Tuple[CodeChange, ...]
    """
    The `codes_changed` table.
    """

    nonces: Tuple[NonceChange, ...]
    """
    The `nonces_changed` table.
    """

    events: Tuple[Log, ...]
    """
    The `events_count` table: every event the transaction's completed
    frames emitted, in their global log order.
    """


def address_order(address: Address) -> int:
    """
    Return the sort key of an address in the canonical enumeration
    order: its numerical `uint160` value.
    """
    return int.from_bytes(address, "big")


def storage_key_order(key: Bytes32) -> int:
    """
    Return the sort key of a storage slot key in the canonical
    enumeration order: its numerical `uint256` value.
    """
    return int.from_bytes(key, "big")


def pre_state_account(tx_state: TransactionState, address: Address) -> Account:
    """
    Return the account as it was at the start of the transaction, or
    the empty account when none existed.
    """
    account = get_pre_state_account_optional(tx_state, address)
    if account is None:
        return EMPTY_ACCOUNT
    return account


def pre_state_storage(
    tx_state: TransactionState, address: Address, key: Bytes32
) -> U256:
    """
    Return a slot's transaction prestate value, including at an address
    recreated during the transaction.

    The storage gas-accounting helper treats created accounts as having
    zero original storage. Assertions instead observe the actual
    transaction prestate, including storage erased by the creation.
    """
    if address in tx_state.parent.storage_writes:
        if key in tx_state.parent.storage_writes[address]:
            return tx_state.parent.storage_writes[address][key]
    if address in tx_state.parent.storage_clears:
        return U256(0)
    return tx_state.parent.pre_state.get_storage(address, key)


def written_account(
    tx_state: TransactionState, address: Address
) -> Optional[Account]:
    """
    Return the account as the transaction last wrote it, the empty
    account when the transaction destroyed it, or `None` when the
    transaction never wrote the account.

    Reading the transaction's own write set records no access.
    """
    if address not in tx_state.account_writes:
        return None
    account = tx_state.account_writes[address]
    if account is None:
        return EMPTY_ACCOUNT
    return account


def transaction_diff(
    tx_state: TransactionState, frame_context: FrameContext
) -> TransactionDiff:
    """
    Compute the executing frame transaction's state diff.

    Balance, code and nonce changes are read off the accounts the
    transaction wrote, slot changes off the slots it wrote, each
    compared with its transaction prestate value. Entries the
    transaction restored are omitted. Events are the logs of the
    completed frames' receipts, in the order the transaction receipt
    reports them. A frame that failed, or whose atomic batch was
    unrolled, contributes none.
    """
    balances = []
    codes = []
    nonces = []
    for address in sorted(tx_state.account_writes, key=address_order):
        before = pre_state_account(tx_state, address)
        after = written_account(tx_state, address)
        assert after is not None
        if before.balance != after.balance:
            balances.append(
                BalanceChange(
                    address=address, before=before.balance, after=after.balance
                )
            )
        if before.code_hash != after.code_hash:
            codes.append(
                CodeChange(
                    address=address,
                    before=before.code_hash,
                    after=after.code_hash,
                )
            )
        if before.nonce != after.nonce:
            nonces.append(
                NonceChange(
                    address=address, before=before.nonce, after=after.nonce
                )
            )

    slots = []
    for address in sorted(tx_state.storage_writes, key=address_order):
        written_slots = tx_state.storage_writes[address]
        for key in sorted(written_slots, key=storage_key_order):
            value_before = pre_state_storage(tx_state, address, key)
            value_after = written_slots[key]
            if value_before != value_after:
                slots.append(
                    SlotChange(
                        address=address,
                        key=key,
                        before=value_before,
                        after=value_after,
                    )
                )

    events: Tuple[Log, ...] = ()
    for receipt in frame_context.frame_receipts:
        events += receipt.logs

    return TransactionDiff(
        balances=tuple(balances),
        slots=tuple(slots),
        codes=tuple(codes),
        nonces=tuple(nonces),
        events=events,
    )
