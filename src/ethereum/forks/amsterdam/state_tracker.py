"""
EIP-7928 Block Access Lists: Hierarchical State Change Tracking.

Frame hierarchy mirrors EVM execution: Block -> Transaction -> Call frames.
Each frame tracks state accesses and merges to parent on completion.

On success, changes merge upward with net-zero filtering (pre-state vs final).
On failure, only reads merge (writes discarded). Pre-state captures use
first-write-wins semantics and are stored at the transaction frame level.

[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from .block_access_lists.rlp_types import BlockAccessIndex
from .fork_types import Address


@dataclass
class StateChanges:
    """
    Tracks state changes within a single execution frame.

    Frames form a hierarchy (Block -> Transaction -> Call) linked by parent
    references. The block_access_index is stored at the root frame. Pre-state
    captures (pre_balances, etc.) are only populated at the transaction level.
    """

    parent: Optional["StateChanges"] = None
    block_access_index: BlockAccessIndex = BlockAccessIndex(0)

    touched_addresses: Set[Address] = field(default_factory=set)
    storage_reads: Set[Tuple[Address, Bytes32]] = field(default_factory=set)
    storage_writes: Dict[Tuple[Address, Bytes32, BlockAccessIndex], U256] = (
        field(default_factory=dict)
    )

    balance_changes: Dict[Tuple[Address, BlockAccessIndex], U256] = field(
        default_factory=dict
    )
    nonce_changes: Set[Tuple[Address, BlockAccessIndex, U64]] = field(
        default_factory=set
    )
    code_changes: Dict[Tuple[Address, BlockAccessIndex], Bytes] = field(
        default_factory=dict
    )

    # Pre-state captures (transaction-scoped, only populated at tx frame)
    pre_balances: Dict[Address, U256] = field(default_factory=dict)
    pre_nonces: Dict[Address, U64] = field(default_factory=dict)
    pre_storage: Dict[Tuple[Address, Bytes32], U256] = field(
        default_factory=dict
    )
    pre_code: Dict[Address, Bytes] = field(default_factory=dict)


def get_block_frame(state_changes: StateChanges) -> StateChanges:
    """
    Walk to the root (block-level) frame.

    Parameters
    ----------
    state_changes :
        Any frame in the hierarchy.

    Returns
    -------
    block_frame : StateChanges
        The root block-level frame.

    """
    block_frame = state_changes
    while block_frame.parent is not None:
        block_frame = block_frame.parent
    return block_frame


def increment_block_access_index(root_frame: StateChanges) -> None:
    """
    Increment the block access index in the root frame.

    Parameters
    ----------
    root_frame :
        The root block-level frame.

    """
    root_frame.block_access_index = BlockAccessIndex(
        root_frame.block_access_index + Uint(1)
    )


def get_transaction_frame(state_changes: StateChanges) -> StateChanges:
    """
    Walk to the transaction-level frame (child of block frame).

    Parameters
    ----------
    state_changes :
        Any frame in the hierarchy.

    Returns
    -------
    tx_frame : StateChanges
        The transaction-level frame.

    """
    tx_frame = state_changes
    while tx_frame.parent is not None and tx_frame.parent.parent is not None:
        tx_frame = tx_frame.parent
    return tx_frame


def capture_pre_balance(
    tx_frame: StateChanges, address: Address, balance: U256
) -> None:
    """
    Capture pre-balance if not already captured (first-write-wins).

    Parameters
    ----------
    tx_frame :
        The transaction-level frame.
    address :
        The address whose balance to capture.
    balance :
        The current balance value.

    """
    # Only capture pre-values in a transaction level
    # or block level frame
    assert tx_frame.parent is None or tx_frame.parent.parent is None
    if address not in tx_frame.pre_balances:
        tx_frame.pre_balances[address] = balance


def capture_pre_storage(
    tx_frame: StateChanges, address: Address, key: Bytes32, value: U256
) -> None:
    """
    Capture pre-storage value if not already captured (first-write-wins).

    Parameters
    ----------
    tx_frame :
        The transaction-level frame.
    address :
        The address whose storage to capture.
    key :
        The storage key.
    value :
        The current storage value.

    """
    # Only capture pre-values in a transaction level
    # or block level frame
    assert tx_frame.parent is None or tx_frame.parent.parent is None
    slot = (address, key)
    if slot not in tx_frame.pre_storage:
        tx_frame.pre_storage[slot] = value


def capture_pre_code(
    tx_frame: StateChanges, address: Address, code: Bytes
) -> None:
    """
    Capture pre-code if not already captured (first-write-wins).

    Parameters
    ----------
    tx_frame :
        The transaction-level frame.
    address :
        The address whose code to capture.
    code :
        The current code value.

    """
    # Only capture pre-values in a transaction level
    # or block level frame
    assert tx_frame.parent is None or tx_frame.parent.parent is None
    if address not in tx_frame.pre_code:
        tx_frame.pre_code[address] = code


def track_address(state_changes: StateChanges, address: Address) -> None:
    """
    Record that an address was accessed.

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address that was accessed.

    """
    state_changes.touched_addresses.add(address)


def track_storage_read(
    state_changes: StateChanges, address: Address, key: Bytes32
) -> None:
    """
    Record a storage read operation.

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose storage was read.
    key :
        The storage key that was read.

    """
    state_changes.storage_reads.add((address, key))


def track_storage_write(
    state_changes: StateChanges,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """
    Record a storage write keyed by (address, key, block_access_index).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose storage was written.
    key :
        The storage key that was written.
    value :
        The new storage value.

    """
    idx = state_changes.block_access_index
    state_changes.storage_writes[(address, key, idx)] = value


def track_balance_change(
    state_changes: StateChanges,
    address: Address,
    new_balance: U256,
) -> None:
    """
    Record a balance change keyed by (address, block_access_index).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose balance changed.
    new_balance :
        The new balance value.

    """
    idx = state_changes.block_access_index
    state_changes.balance_changes[(address, idx)] = new_balance


def track_nonce_change(
    state_changes: StateChanges,
    address: Address,
    new_nonce: U64,
) -> None:
    """
    Record a nonce change as (address, block_access_index, new_nonce).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose nonce changed.
    new_nonce :
        The new nonce value.

    """
    idx = state_changes.block_access_index
    state_changes.nonce_changes.add((address, idx, new_nonce))


def track_code_change(
    state_changes: StateChanges,
    address: Address,
    new_code: Bytes,
) -> None:
    """
    Record a code change keyed by (address, block_access_index).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose code changed.
    new_code :
        The new code value.

    """
    idx = state_changes.block_access_index
    state_changes.code_changes[(address, idx)] = new_code


def track_selfdestruct(
    tx_frame: StateChanges,
    address: Address,
) -> None:
    """
    Handle selfdestruct of account created in same transaction.

    Per EIP-7928/EIP-6780: removes nonce/code changes, converts storage
    writes to reads. Balance changes handled by net-zero filtering.

    Parameters
    ----------
    tx_frame :
        The state changes tracker. Should be a transaction frame.
    address :
        The address that self-destructed.

    """
    # Has to be a transaction frame
    assert tx_frame.parent is not None and tx_frame.parent.parent is None

    idx = tx_frame.block_access_index

    # Remove nonce changes from current transaction
    tx_frame.nonce_changes = {
        (addr, i, nonce)
        for addr, i, nonce in tx_frame.nonce_changes
        if not (addr == address and i == idx)
    }

    # Remove balance changes from current transaction
    if (address, idx) in tx_frame.balance_changes:
        pre_balance = tx_frame.pre_balances[address]
        if pre_balance == U256(0):
            # Post balance will be U256(0) after deletion.
            # So no change and hence bal does not need to
            # capture anything.
            del tx_frame.balance_changes[(address, idx)]

    # Remove code changes from current transaction
    if (address, idx) in tx_frame.code_changes:
        del tx_frame.code_changes[(address, idx)]

    # Convert storage writes from current transaction to reads
    for addr, key, i in list(tx_frame.storage_writes.keys()):
        if addr == address and i == idx:
            del tx_frame.storage_writes[(addr, key, i)]
            tx_frame.storage_reads.add((addr, key))


def merge_on_success(child_frame: StateChanges) -> None:
    """
    Merge child frame into parent on success.

    Child values overwrite parent values (most recent wins). No net-zero
    filtering here - that happens once at transaction commit via
    normalize_transaction().

    Parameters
    ----------
    child_frame :
        The child frame being merged.

    """
    assert child_frame.parent is not None
    parent_frame = child_frame.parent

    # Merge address accesses
    parent_frame.touched_addresses.update(child_frame.touched_addresses)

    # Merge storage: reads union, writes overwrite (child supersedes parent)
    parent_frame.storage_reads.update(child_frame.storage_reads)
    for storage_key, storage_value in child_frame.storage_writes.items():
        parent_frame.storage_writes[storage_key] = storage_value

    # Merge balance changes: child overwrites parent for same key
    for balance_key, balance_value in child_frame.balance_changes.items():
        parent_frame.balance_changes[balance_key] = balance_value

    # Merge nonce changes: keep highest nonce per address
    address_final_nonces: Dict[Address, Tuple[BlockAccessIndex, U64]] = {}
    for addr, idx, nonce in child_frame.nonce_changes:
        if (
            addr not in address_final_nonces
            or nonce > address_final_nonces[addr][1]
        ):
            address_final_nonces[addr] = (idx, nonce)
    for addr, (idx, final_nonce) in address_final_nonces.items():
        parent_frame.nonce_changes.add((addr, idx, final_nonce))

    # Merge code changes: child overwrites parent for same key
    for code_key, code_value in child_frame.code_changes.items():
        parent_frame.code_changes[code_key] = code_value


def merge_on_failure(child_frame: StateChanges) -> None:
    """
    Merge child frame into parent on failure/revert.

    Only reads merge; writes are discarded (converted to reads).

    Parameters
    ----------
    child_frame :
        The failed child frame.

    """
    assert child_frame.parent is not None
    parent_frame = child_frame.parent
    # Only merge reads and address accesses on failure
    parent_frame.touched_addresses.update(child_frame.touched_addresses)
    parent_frame.storage_reads.update(child_frame.storage_reads)

    # Convert writes to reads (failed writes still accessed the slots)
    for address, key, _idx in child_frame.storage_writes.keys():
        parent_frame.storage_reads.add((address, key))

    # Note: balance_changes, nonce_changes, and code_changes are NOT
    # merged on failure - they are discarded


def commit_transaction_frame(tx_frame: StateChanges) -> None:
    """
    Commit transaction frame to block frame.

    Filters net-zero changes before merging to ensure only actual state
    modifications are recorded in the block access list.

    Parameters
    ----------
    tx_frame :
        The transaction frame to commit.

    """
    assert tx_frame.parent is not None
    block_frame = tx_frame.parent

    # Filter net-zero changes before committing
    filter_net_zero_frame_changes(tx_frame)

    # Merge address accesses
    block_frame.touched_addresses.update(tx_frame.touched_addresses)

    # Merge storage operations
    block_frame.storage_reads.update(tx_frame.storage_reads)
    for (addr, key, idx), value in tx_frame.storage_writes.items():
        block_frame.storage_writes[(addr, key, idx)] = value

    # Merge balance changes
    for (addr, idx), final_balance in tx_frame.balance_changes.items():
        block_frame.balance_changes[(addr, idx)] = final_balance

    # Merge nonce changes
    for addr, idx, nonce in tx_frame.nonce_changes:
        block_frame.nonce_changes.add((addr, idx, nonce))

    # Merge code changes
    for (addr, idx), final_code in tx_frame.code_changes.items():
        block_frame.code_changes[(addr, idx)] = final_code


def create_child_frame(parent: StateChanges) -> StateChanges:
    """
    Create a child frame linked to the given parent.

    Inherits block_access_index from parent so track functions can
    access it directly without walking up the frame hierarchy.

    Parameters
    ----------
    parent :
        The parent frame.

    Returns
    -------
    child : StateChanges
        A new child frame with parent reference and inherited
        block_access_index.

    """
    return StateChanges(
        parent=parent,
        block_access_index=parent.block_access_index,
    )


def filter_net_zero_frame_changes(tx_frame: StateChanges) -> None:
    """
    Filter net-zero changes from transaction frame before commit.

    Compares final values against pre-tx state for storage, balance, and code.
    Net-zero storage writes are converted to reads. Net-zero balance/code
    changes are removed entirely. Nonces are not filtered (only increment).

    Parameters
    ----------
    tx_frame :
        The transaction-level state changes frame.

    """
    idx = tx_frame.block_access_index

    # Filter storage: compare against pre_storage, convert net-zero to reads
    addresses_to_check_storage = [
        (addr, key)
        for (addr, key, i) in tx_frame.storage_writes.keys()
        if i == idx
    ]
    for addr, key in addresses_to_check_storage:
        # For any (address, key) whose balance has changed, its
        # pre-value should have been captured
        assert (addr, key) in tx_frame.pre_storage
        pre_value = tx_frame.pre_storage[(addr, key)]
        post_value = tx_frame.storage_writes[(addr, key, idx)]
        if (addr, key) in tx_frame.pre_storage:
            if pre_value == post_value:
                # Net-zero write - convert to read
                del tx_frame.storage_writes[(addr, key, idx)]
                tx_frame.storage_reads.add((addr, key))

    # Filter balance: compare pre vs post, remove if equal
    addresses_to_check_balance = [
        addr for (addr, i) in tx_frame.balance_changes.keys() if i == idx
    ]
    for addr in addresses_to_check_balance:
        # For any account whose balance has changed, its
        # pre-balance should have been captured
        assert addr in tx_frame.pre_balances
        pre_balance = tx_frame.pre_balances[addr]
        post_balance = tx_frame.balance_changes[(addr, idx)]
        if pre_balance == post_balance:
            del tx_frame.balance_changes[(addr, idx)]

    # Filter code: compare pre vs post, remove if equal
    addresses_to_check_code = [
        addr for (addr, i) in tx_frame.code_changes.keys() if i == idx
    ]
    for addr in addresses_to_check_code:
        assert addr in tx_frame.pre_code
        pre_code = tx_frame.pre_code[addr]
        post_code = tx_frame.code_changes[(addr, idx)]
        if pre_code == post_code:
            del tx_frame.code_changes[(addr, idx)]

    # Nonces: no filtering needed (nonces only increment, never net-zero)
