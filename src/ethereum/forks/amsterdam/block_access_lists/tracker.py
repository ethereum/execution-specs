"""
Provides state change tracking functionality for building Block
Access Lists during transaction execution.

The tracker integrates with the EVM execution to capture all state accesses
and modifications, distinguishing between actual changes and no-op operations.
It maintains a cache of pre-state values to enable accurate change detection
throughout block execution.

See [EIP-7928] for the full specification
[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ..fork_types import Address
from .builder import (
    BlockAccessListBuilder,
    add_balance_change,
    add_code_change,
    add_nonce_change,
    add_storage_read,
    add_storage_write,
    add_touched_account,
)
from .rlp_types import BlockAccessIndex

if TYPE_CHECKING:
    from ..state import State  # noqa: F401


@dataclass
class CallFrameSnapshot:
    """
    Snapshot of block access list state for a single call frame.

    Used to track changes within a call frame to enable proper handling
    of reverts as specified in EIP-7928.
    """

    touched_addresses: Set[Address] = field(default_factory=set)
    """Addresses touched during this call frame."""

    storage_writes: Dict[Tuple[Address, Bytes32], U256] = field(
        default_factory=dict
    )
    """Storage writes made during this call frame."""

    balance_changes: Set[Tuple[Address, BlockAccessIndex, U256]] = field(
        default_factory=set
    )
    """Balance changes made during this call frame."""

    nonce_changes: Set[Tuple[Address, BlockAccessIndex, U64]] = field(
        default_factory=set
    )
    """Nonce changes made during this call frame."""

    code_changes: Set[Tuple[Address, BlockAccessIndex, Bytes]] = field(
        default_factory=set
    )
    """Code changes made during this call frame."""


@dataclass
class StateChangeTracker:
    """
    Tracks state changes during transaction execution for Block Access List
    construction.

    This tracker maintains a cache of pre-state values and coordinates with
    the [`BlockAccessListBuilder`] to record all state changes made during
    block execution. It ensures that only actual changes (not no-op writes)
    are recorded in the access list.

    [`BlockAccessListBuilder`]:
    ref:ethereum.forks.amsterdam.block_access_lists.builder.BlockAccessListBuilder
    """

    block_access_list_builder: BlockAccessListBuilder
    """
    The builder instance that accumulates all tracked changes.
    """

    pre_storage_cache: Dict[tuple, U256] = field(default_factory=dict)
    """
    Cache of pre-transaction storage values, keyed by (address, slot) tuples.
    This cache is cleared at the start of each transaction to track values
    from the beginning of the current transaction.
    """

    pre_balance_cache: Dict[Address, U256] = field(default_factory=dict)
    """
    Cache of pre-transaction balance values, keyed by address.
    This cache is cleared at the start of each transaction and used by
    normalize_balance_changes to filter out balance changes where
    the final balance equals the initial balance.
    """

    current_block_access_index: Uint = Uint(0)
    """
    The current block access index (0 for pre-execution,
    1..n for transactions, n+1 for post-execution).
    """

    call_frame_snapshots: List[CallFrameSnapshot] = field(default_factory=list)
    """
    Stack of snapshots for nested call frames to handle reverts properly.
    """


def set_block_access_index(
    tracker: StateChangeTracker, block_access_index: Uint
) -> None:
    """
    Set the current block access index for tracking changes.

    Must be called before processing each transaction/system contract
    to ensure changes are associated with the correct block access index.

    Note: Block access indices differ from transaction indices:
    - 0: Pre-execution (system contracts like beacon roots, block hashes)
    - 1..n: Transactions (tx at index i gets block_access_index i+1)
    - n+1: Post-execution (withdrawals, requests)

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    block_access_index :
        The block access index (0 for pre-execution,
        1..n for transactions, n+1 for post-execution).

    """
    tracker.current_block_access_index = block_access_index
    # Clear the pre-storage cache for each new transaction to ensure
    # no-op writes are detected relative to the transaction start
    tracker.pre_storage_cache.clear()
    # Clear the pre-balance cache for each new transaction
    tracker.pre_balance_cache.clear()


def capture_pre_state(
    tracker: StateChangeTracker, address: Address, key: Bytes32, state: "State"
) -> U256:
    """
    Capture and cache the pre-transaction value for a storage location.

    Retrieves the storage value from the beginning of the current transaction.
    The value is cached within the transaction to avoid repeated lookups and
    to maintain consistency across multiple accesses within the same
    transaction.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The account address containing the storage.
    key :
        The storage slot to read.
    state :
        The current execution state.

    Returns
    -------
    value :
        The storage value at the beginning of the current transaction.

    """
    cache_key = (address, key)
    if cache_key not in tracker.pre_storage_cache:
        # Import locally to avoid circular import
        from ..state import get_storage

        tracker.pre_storage_cache[cache_key] = get_storage(state, address, key)
    return tracker.pre_storage_cache[cache_key]


def track_address_access(
    tracker: StateChangeTracker, address: Address
) -> None:
    """
    Track that an address was accessed.

    Records account access even when no state changes occur. This is
    important for operations that read account data without modifying it.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The account address that was accessed.

    """
    add_touched_account(tracker.block_access_list_builder, address)


def track_storage_read(
    tracker: StateChangeTracker, address: Address, key: Bytes32, state: "State"
) -> None:
    """
    Track a storage read operation.

    Records that a storage slot was read and captures its pre-state value.
    The slot will only appear in the final access list if it wasn't also
    written to during block execution.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The account address whose storage is being read.
    key :
        The storage slot being read.
    state :
        The current execution state.

    """
    track_address_access(tracker, address)

    capture_pre_state(tracker, address, key, state)

    add_storage_read(tracker.block_access_list_builder, address, key)


def track_storage_write(
    tracker: StateChangeTracker,
    address: Address,
    key: Bytes32,
    new_value: U256,
    state: "State",
) -> None:
    """
    Track a storage write operation.

    Records storage modifications, but only if the new value differs from
    the pre-state value. No-op writes (where the value doesn't change) are
    tracked as reads instead, as specified in [EIP-7928].

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The account address whose storage is being modified.
    key :
        The storage slot being written to.
    new_value :
        The new value to write.
    state :
        The current execution state.

    [EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928

    """
    track_address_access(tracker, address)

    pre_value = capture_pre_state(tracker, address, key, state)

    value_bytes = new_value.to_be_bytes32()

    if pre_value != new_value:
        add_storage_write(
            tracker.block_access_list_builder,
            address,
            key,
            BlockAccessIndex(tracker.current_block_access_index),
            value_bytes,
        )
        # Record in current call frame snapshot if exists
        if tracker.call_frame_snapshots:
            snapshot = tracker.call_frame_snapshots[-1]
            snapshot.storage_writes[(address, key)] = new_value
    else:
        add_storage_read(tracker.block_access_list_builder, address, key)


def capture_pre_balance(
    tracker: StateChangeTracker, address: Address, state: "State"
) -> U256:
    """
    Capture and cache the pre-transaction balance for an account.

    This function caches the balance on first access for each address during
    a transaction. It must be called before any balance modifications are made
    to ensure we capture the pre-transaction balance correctly. The cache is
    cleared at the beginning of each transaction.

    This is used by normalize_balance_changes to determine which balance
    changes should be filtered out.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The account address.
    state :
        The current execution state.

    Returns
    -------
    value :
        The balance at the beginning of the current transaction.

    """
    if address not in tracker.pre_balance_cache:
        # Import locally to avoid circular import
        from ..state import get_account

        # Cache the current balance on first access
        # This should be called before any balance modifications
        account = get_account(state, address)
        tracker.pre_balance_cache[address] = account.balance
    return tracker.pre_balance_cache[address]


def track_balance_change(
    tracker: StateChangeTracker,
    address: Address,
    new_balance: U256,
) -> None:
    """
    Track a balance change for an account.

    Records the new balance after any balance-affecting operation, including
    transfers, gas payments, block rewards, and withdrawals.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The account address whose balance changed.
    new_balance :
        The new balance value.

    """
    track_address_access(tracker, address)

    block_access_index = BlockAccessIndex(tracker.current_block_access_index)
    add_balance_change(
        tracker.block_access_list_builder,
        address,
        block_access_index,
        new_balance,
    )

    # Record in current call frame snapshot if exists
    if tracker.call_frame_snapshots:
        snapshot = tracker.call_frame_snapshots[-1]
        snapshot.balance_changes.add(
            (address, block_access_index, new_balance)
        )


def track_nonce_change(
    tracker: StateChangeTracker, address: Address, new_nonce: Uint
) -> None:
    """
    Track a nonce change for an account.

    Records nonce increments for both EOAs (when sending transactions) and
    contracts (when performing [`CREATE`] or [`CREATE2`] operations). Deployed
    contracts also have their initial nonce tracked.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The account address whose nonce changed.
    new_nonce :
        The new nonce value.
    state :
        The current execution state.

    [`CREATE`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create2

    """
    track_address_access(tracker, address)
    block_access_index = BlockAccessIndex(tracker.current_block_access_index)
    nonce_u64 = U64(new_nonce)
    add_nonce_change(
        tracker.block_access_list_builder,
        address,
        block_access_index,
        nonce_u64,
    )

    # Record in current call frame snapshot if exists
    if tracker.call_frame_snapshots:
        snapshot = tracker.call_frame_snapshots[-1]
        snapshot.nonce_changes.add((address, block_access_index, nonce_u64))


def track_code_change(
    tracker: StateChangeTracker, address: Address, new_code: Bytes
) -> None:
    """
    Track a code change for contract deployment.

    Records new contract code deployments via [`CREATE`], [`CREATE2`], or
    [`SETCODE`] operations. This function is called when contract bytecode
    is deployed to an address.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The address receiving the contract code.
    new_code :
        The deployed contract bytecode.

    [`CREATE`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create2

    """
    track_address_access(tracker, address)
    block_access_index = BlockAccessIndex(tracker.current_block_access_index)
    add_code_change(
        tracker.block_access_list_builder,
        address,
        block_access_index,
        new_code,
    )

    # Record in current call frame snapshot if exists
    if tracker.call_frame_snapshots:
        snapshot = tracker.call_frame_snapshots[-1]
        snapshot.code_changes.add((address, block_access_index, new_code))


def handle_in_transaction_selfdestruct(
    tracker: StateChangeTracker, address: Address
) -> None:
    """
    Handle an account that self-destructed in the same transaction it was
    created.

    Per EIP-7928, accounts destroyed within their creation transaction must be
    included as read-only with storage writes converted to reads. Nonce and
    code changes from the current transaction are also removed.

    Note: Balance changes are handled separately by
          normalize_balance_changes.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    address :
        The address that self-destructed.

    """
    builder = tracker.block_access_list_builder
    if address not in builder.accounts:
        return

    account_data = builder.accounts[address]
    current_index = tracker.current_block_access_index

    # Convert storage writes from current tx to reads
    for slot in list(account_data.storage_changes.keys()):
        account_data.storage_changes[slot] = [
            c
            for c in account_data.storage_changes[slot]
            if c.block_access_index != current_index
        ]
        if not account_data.storage_changes[slot]:
            del account_data.storage_changes[slot]
            account_data.storage_reads.add(slot)

    # Remove nonce and code changes from current transaction
    account_data.nonce_changes = [
        c
        for c in account_data.nonce_changes
        if c.block_access_index != current_index
    ]
    account_data.code_changes = [
        c
        for c in account_data.code_changes
        if c.block_access_index != current_index
    ]


def normalize_balance_changes(
    tracker: StateChangeTracker, state: "State"
) -> None:
    """
    Normalize balance changes for the current block access index.

    This method filters out spurious balance changes by removing all balance
    changes for addresses where the post-execution balance equals the
    pre-execution balance.

    This is crucial for handling cases like:
    - In-transaction self-destructs where an account with 0 balance is created
      and destroyed, resulting in no net balance change
    - Round-trip transfers where an account receives and sends equal amounts
    - Zero-amount withdrawals where the balance doesn't actually change

    This should be called at the end of any operation that tracks balance
    changes (transactions, withdrawals, etc.). Only actual state changes are
    recorded in the Block Access List.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    state :
        The current execution state.

    """
    # Import locally to avoid circular import
    from ..state import get_account

    builder = tracker.block_access_list_builder
    current_index = tracker.current_block_access_index

    # Check each address that had balance changes in this transaction
    for address in list(builder.accounts.keys()):
        account_data = builder.accounts[address]

        # Get the pre-transaction balance
        pre_balance = capture_pre_balance(tracker, address, state)

        # Get the current (post-transaction) balance
        post_balance = get_account(state, address).balance

        # If pre-tx balance equals post-tx balance, remove all balance changes
        # for this address in the current transaction
        if pre_balance == post_balance:
            # Filter out balance changes from the current transaction
            account_data.balance_changes = [
                change
                for change in account_data.balance_changes
                if change.block_access_index != current_index
            ]


def begin_call_frame(tracker: StateChangeTracker) -> None:
    """
    Begin a new call frame for tracking reverts.

    Creates a new snapshot to track changes within this call frame.
    This allows proper handling of reverts as specified in EIP-7928.

    Parameters
    ----------
    tracker :
        The state change tracker instance.

    """
    tracker.call_frame_snapshots.append(CallFrameSnapshot())


def rollback_call_frame(tracker: StateChangeTracker) -> None:
    """
    Rollback changes from the current call frame.

    When a call reverts, this function:
    - Converts storage writes to reads
    - Removes balance, nonce, and code changes
    - Preserves touched addresses

    This implements EIP-7928 revert handling where reverted writes
    become reads and addresses remain in the access list.

    Parameters
    ----------
    tracker :
        The state change tracker instance.

    """
    if not tracker.call_frame_snapshots:
        return

    snapshot = tracker.call_frame_snapshots.pop()
    builder = tracker.block_access_list_builder

    # Convert storage writes to reads
    for (address, slot), _ in snapshot.storage_writes.items():
        # Remove the write from storage_changes
        if address in builder.accounts:
            account_data = builder.accounts[address]
            if slot in account_data.storage_changes:
                # Filter out changes from this call frame
                account_data.storage_changes[slot] = [
                    change
                    for change in account_data.storage_changes[slot]
                    if change.block_access_index
                    != tracker.current_block_access_index
                ]
                if not account_data.storage_changes[slot]:
                    del account_data.storage_changes[slot]
            # Add as a read instead
            account_data.storage_reads.add(slot)

    # Remove balance changes from this call frame
    for address, block_access_index, new_balance in snapshot.balance_changes:
        if address in builder.accounts:
            account_data = builder.accounts[address]
            # Filter out balance changes from this call frame
            account_data.balance_changes = [
                change
                for change in account_data.balance_changes
                if not (
                    change.block_access_index == block_access_index
                    and change.post_balance == new_balance
                )
            ]

    # Remove nonce changes from this call frame
    for address, block_access_index, new_nonce in snapshot.nonce_changes:
        if address in builder.accounts:
            account_data = builder.accounts[address]
            # Filter out nonce changes from this call frame
            account_data.nonce_changes = [
                change
                for change in account_data.nonce_changes
                if not (
                    change.block_access_index == block_access_index
                    and change.new_nonce == new_nonce
                )
            ]

    # Remove code changes from this call frame
    for address, block_access_index, new_code in snapshot.code_changes:
        if address in builder.accounts:
            account_data = builder.accounts[address]
            # Filter out code changes from this call frame
            account_data.code_changes = [
                change
                for change in account_data.code_changes
                if not (
                    change.block_access_index == block_access_index
                    and change.new_code == new_code
                )
            ]

    # All touched addresses remain in the access list (already tracked)


def commit_call_frame(tracker: StateChangeTracker) -> None:
    """
    Commit changes from the current call frame.

    Removes the current call frame snapshot without rolling back changes.
    Called when a call completes successfully.

    Parameters
    ----------
    tracker :
        The state change tracker instance.

    """
    if tracker.call_frame_snapshots:
        tracker.call_frame_snapshots.pop()
