"""
State diff of the executing frame transaction, as exposed to its
`POST_TX` assertion frames by the [EIP-7906] instructions.

The diff is the net difference between the transaction prestate, the
state before any write made in relation to the transaction with the gas
payment included, and the state as of the reading instruction. Writes
that later restore the prestate value leave no entry. `POST_TX` frames
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
from ethereum_types.numeric import U256

from ethereum.crypto.hash import Hash32
from ethereum.state import EMPTY_ACCOUNT, EMPTY_CODE_HASH, Account, Address

from ..blocks import Log
from ..state_tracker import (
    TransactionState,
    get_code,
    get_pre_state_account_optional,
)
from . import FrameContext
from .eoa_delegation import is_valid_delegation

CHANGE_FLAG_NONCE = U256(0b0001)
"""
`account_change_flags` bit set when the account's nonce differs from
its transaction prestate value.
"""

CHANGE_FLAG_BALANCE = U256(0b0010)
"""
`account_change_flags` bit set when the account's balance differs from
its transaction prestate value.
"""

CHANGE_FLAG_STORAGE = U256(0b0100)
"""
`account_change_flags` bit set when any storage slot of the account
differs from its transaction prestate value.
"""

CHANGE_FLAG_CODE = U256(0b1000)
"""
`account_change_flags` bit set when the account's code hash differs
from its transaction prestate value.
"""


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
class DeployedContract:
    """
    Entry of the `contracts_deployed` table: an address whose code hash
    changed from the empty-code hash to the hash of code that is not an
    [EIP-7702] delegation designator.

    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """

    address: Address
    """
    The address of the newly deployed contract.
    """

    code_hash: Hash32
    """
    The code hash as of the reading instruction.
    """


@final
@slotted_freezable
@dataclass
class TransactionDiff:
    """
    The transaction's state diff, in the canonical enumeration order:
    balance and slot changes ascending by address, slots of one address
    ascending by key, and events in emission order.
    """

    balances: Tuple[BalanceChange, ...]
    """
    The `balances_changed` table.
    """

    slots: Tuple[SlotChange, ...]
    """
    The `slots_changed` table.
    """

    deployed: Tuple[DeployedContract, ...]
    """
    The `contracts_deployed` table.
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


def code_hash_after(tx_state: TransactionState, account: Account) -> Hash32:
    """
    Return the code hash `contracts_deployed` reports for an account
    the transaction wrote, treating an [EIP-7702] delegation designator
    as no deployed code.

    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """
    if account.code_hash == EMPTY_CODE_HASH:
        return EMPTY_CODE_HASH
    if is_valid_delegation(get_code(tx_state, account.code_hash)):
        return EMPTY_CODE_HASH
    return account.code_hash


def transaction_diff(
    tx_state: TransactionState, frame_context: FrameContext
) -> TransactionDiff:
    """
    Compute the executing frame transaction's state diff.

    Balance changes and deployments are read off the accounts the
    transaction wrote, slot changes off the slots it wrote, each
    compared with its transaction prestate value. Entries the
    transaction restored are omitted. Events are the logs of the
    completed frames' receipts, in the order the transaction receipt
    reports them. A frame that failed, or whose atomic batch was
    unrolled, contributes none.
    """
    balances = []
    deployed = []
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
        deployed_code_hash = code_hash_after(tx_state, after)
        if (
            before.code_hash == EMPTY_CODE_HASH
            and deployed_code_hash != EMPTY_CODE_HASH
        ):
            deployed.append(
                DeployedContract(address=address, code_hash=deployed_code_hash)
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
        deployed=tuple(deployed),
        events=events,
    )


def account_change_flags(
    tx_state: TransactionState, diff: TransactionDiff, address: Address
) -> U256:
    """
    Return the `account_change_flags` bitmask of an account: one bit per
    field of the account tuple, following its `(nonce, balance,
    storage_root, code_hash)` order, set when the field's net value
    differs from the transaction prestate.

    An account with neither an account write nor a changed slot has no
    set bit, and no live state is read to establish that.
    """
    flags = U256(0)
    after = written_account(tx_state, address)
    if after is not None:
        before = pre_state_account(tx_state, address)
        if before.nonce != after.nonce:
            flags |= CHANGE_FLAG_NONCE
        if before.balance != after.balance:
            flags |= CHANGE_FLAG_BALANCE
        if before.code_hash != after.code_hash:
            flags |= CHANGE_FLAG_CODE
    if any(change.address == address for change in diff.slots):
        flags |= CHANGE_FLAG_STORAGE
    return flags


def slot_indices_of(
    diff: TransactionDiff, address: Address
) -> Tuple[int, ...]:
    """
    Return the `slots_changed` indices of the entries of one account,
    the per-address view `TXDIFF` exposes, in enumeration order.
    """
    return tuple(
        index
        for index, change in enumerate(diff.slots)
        if change.address == address
    )


def event_indices_of(
    diff: TransactionDiff, address: Address
) -> Tuple[int, ...]:
    """
    Return the `events_count` indices of the events one account
    emitted, the per-address view `TXDIFF` exposes, in emission order.
    """
    return tuple(
        index
        for index, event in enumerate(diff.events)
        if event.address == address
    )


def event_indices_with_topic(
    diff: TransactionDiff, topic: Hash32
) -> Tuple[int, ...]:
    """
    Return the `events_count` indices of the events carrying `topic` in
    any indexed position (`topic1` to `topic3`), the per-topic view
    `TXDIFF` exposes, in emission order. The signature topic `topic0`
    identifies the event type and is excluded.
    """
    return tuple(
        index
        for index, event in enumerate(diff.events)
        if topic in event.topics[1:]
    )
