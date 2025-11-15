"""
Hierarchical state change tracking for EIP-7928 Block Access Lists.

Implements a frame-based hierarchy: Block → Transaction → Call frames.
Each frame tracks state changes and merges upward on completion:
- Success: merge all changes (reads + writes)
- Failure: merge only reads (writes discarded)

Frame Hierarchy:
  Block Frame: Root, lifetime = entire block, index 0..N+1
  Transaction Frame: Child of block, lifetime = single transaction
  Call Frame: Child of transaction/call, lifetime = single message

Block Access Index: 0=pre-exec, 1..N=transactions, N+1=post-exec
Stored in root frame, passed explicitly to operations.

Pre-State Tracking: Values captured before modifications to enable
net-zero filtering.

[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from .block_access_lists.rlp_types import BlockAccessIndex
from .fork_types import Address

if TYPE_CHECKING:
    from .state import State


@dataclass
class StateChanges:
    """
    Tracks state changes within a single execution frame.

    Frames form a hierarchy: Block → Transaction → Call frames.
    Each frame holds a reference to its parent for upward traversal.
    """

    parent: Optional["StateChanges"] = None
    _block_access_index: BlockAccessIndex = BlockAccessIndex(0)

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

    # Pre-state captures for net-zero filtering
    pre_balances: Dict[Address, U256] = field(default_factory=dict)
    pre_nonces: Dict[Address, U64] = field(default_factory=dict)
    pre_storage: Dict[Tuple[Address, Bytes32], U256] = field(
        default_factory=dict
    )
    pre_code: Dict[Address, Bytes] = field(default_factory=dict)


def get_block_frame(state_changes: StateChanges) -> StateChanges:
    """
    Walk to block-level frame.

    Parameters
    ----------
    state_changes :
        Any state changes frame.

    Returns
    -------
    block_frame : StateChanges
        The block-level frame.

    """
    block_frame = state_changes
    while block_frame.parent is not None:
        block_frame = block_frame.parent
    return block_frame


def get_block_access_index(root_frame: StateChanges) -> BlockAccessIndex:
    """
    Get current block access index from root frame.

    Parameters
    ----------
    root_frame :
        The root (block-level) state changes frame.

    Returns
    -------
    index : BlockAccessIndex
        The current block access index.

    """
    return root_frame._block_access_index


def increment_block_access_index(root_frame: StateChanges) -> None:
    """
    Increment block access index in root frame.

    Parameters
    ----------
    root_frame :
        The root (block-level) state changes frame to increment.

    """
    root_frame._block_access_index = BlockAccessIndex(
        root_frame._block_access_index + Uint(1)
    )


def capture_pre_balance(
    state_changes: StateChanges, address: Address, balance: U256
) -> None:
    """
    Capture pre-balance (first-write-wins for net-zero filtering).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose balance is being captured.
    balance :
        The balance value before modification.

    """
    if address not in state_changes.pre_balances:
        state_changes.pre_balances[address] = balance


def capture_pre_nonce(
    state_changes: StateChanges, address: Address, nonce: U64
) -> None:
    """
    Capture pre-nonce (first-write-wins).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose nonce is being captured.
    nonce :
        The nonce value before modification.

    """
    if address not in state_changes.pre_nonces:
        state_changes.pre_nonces[address] = nonce


def capture_pre_storage(
    state_changes: StateChanges, address: Address, key: Bytes32, value: U256
) -> None:
    """
    Capture pre-storage (first-write-wins for noop filtering).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose storage is being captured.
    key :
        The storage key.
    value :
        The storage value before modification.

    """
    slot = (address, key)
    if slot not in state_changes.pre_storage:
        state_changes.pre_storage[slot] = value


def capture_pre_code(
    state_changes: StateChanges, address: Address, code: Bytes
) -> None:
    """
    Capture pre-code (first-write-wins).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose code is being captured.
    code :
        The code value before modification.

    """
    if address not in state_changes.pre_code:
        state_changes.pre_code[address] = code


def track_address(state_changes: StateChanges, address: Address) -> None:
    """
    Track that an address was accessed.

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
    Track a storage read operation.

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
    Track a storage write operation with block access index.

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
    block_frame = get_block_frame(state_changes)
    state_changes.storage_writes[
        (address, key, get_block_access_index(block_frame))
    ] = value


def track_balance_change(
    state_changes: StateChanges,
    address: Address,
    new_balance: U256,
) -> None:
    """
    Track balance change keyed by (address, index).

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose balance changed.
    new_balance :
        The new balance value.

    """
    block_frame = get_block_frame(state_changes)
    state_changes.balance_changes[
        (address, get_block_access_index(block_frame))
    ] = new_balance


def track_nonce_change(
    state_changes: StateChanges,
    address: Address,
    new_nonce: U64,
) -> None:
    """
    Track a nonce change.

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose nonce changed.
    new_nonce :
        The new nonce value.

    """
    block_frame = get_block_frame(state_changes)
    state_changes.nonce_changes.add(
        (address, get_block_access_index(block_frame), new_nonce)
    )


def track_code_change(
    state_changes: StateChanges,
    address: Address,
    new_code: Bytes,
) -> None:
    """
    Track a code change.

    Parameters
    ----------
    state_changes :
        The state changes frame.
    address :
        The address whose code changed.
    new_code :
        The new code value.

    """
    block_frame = get_block_frame(state_changes)
    state_changes.code_changes[
        (address, get_block_access_index(block_frame))
    ] = new_code


def merge_on_success(child_frame: StateChanges) -> None:
    """
    Merge child frame's changes into parent on successful completion.

    Merges all tracked changes (reads and writes) from the child frame
    into the parent frame. Filters out net-zero changes based on
    captured pre-state values by comparing initial vs final values.

    Parameters
    ----------
    child_frame :
        The child frame being merged.

    """
    assert child_frame.parent is not None
    parent_frame = child_frame.parent
    # Merge address accesses
    parent_frame.touched_addresses.update(child_frame.touched_addresses)

    # Merge pre-state captures for transaction-level normalization
    # Only if parent doesn't have value (first capture wins)
    for addr, balance in child_frame.pre_balances.items():
        if addr not in parent_frame.pre_balances:
            parent_frame.pre_balances[addr] = balance
    for addr, nonce in child_frame.pre_nonces.items():
        if addr not in parent_frame.pre_nonces:
            parent_frame.pre_nonces[addr] = nonce
    for slot, value in child_frame.pre_storage.items():
        if slot not in parent_frame.pre_storage:
            parent_frame.pre_storage[slot] = value
    for addr, code in child_frame.pre_code.items():
        if addr not in parent_frame.pre_code:
            capture_pre_code(parent_frame, addr, code)

    # Merge storage operations, filtering noop writes
    parent_frame.storage_reads.update(child_frame.storage_reads)
    for (addr, key, idx), value in child_frame.storage_writes.items():
        # Only merge if value actually changed from pre-state
        if (addr, key) in child_frame.pre_storage:
            if child_frame.pre_storage[(addr, key)] != value:
                parent_frame.storage_writes[(addr, key, idx)] = value
            # If equal, it's a noop write - convert to read only
            else:
                parent_frame.storage_reads.add((addr, key))
        else:
            # No pre-state captured, merge as-is
            parent_frame.storage_writes[(addr, key, idx)] = value

    # Merge balance changes - filter net-zero changes
    # balance_changes keyed by (address, index)
    for (addr, idx), final_balance in child_frame.balance_changes.items():
        if addr in child_frame.pre_balances:
            if child_frame.pre_balances[addr] != final_balance:
                parent_frame.balance_changes[(addr, idx)] = final_balance
            # else: Net-zero change - skip entirely
        else:
            # No pre-balance captured, merge as-is
            parent_frame.balance_changes[(addr, idx)] = final_balance

    # Merge nonce changes - keep only highest nonce per address
    address_final_nonces: Dict[Address, Tuple[BlockAccessIndex, U64]] = {}
    for addr, idx, nonce in child_frame.nonce_changes:
        if (
            addr not in address_final_nonces
            or nonce > address_final_nonces[addr][1]
        ):
            address_final_nonces[addr] = (idx, nonce)

    # Merge final nonces (no net-zero filtering - nonces never decrease)
    for addr, (idx, final_nonce) in address_final_nonces.items():
        parent_frame.nonce_changes.add((addr, idx, final_nonce))

    # Merge code changes - filter net-zero changes
    # code_changes keyed by (address, index)
    for (addr, idx), final_code in child_frame.code_changes.items():
        pre_code = child_frame.pre_code.get(addr, b"")
        if pre_code != final_code:
            parent_frame.code_changes[(addr, idx)] = final_code
        # else: Net-zero change - skip entirely


def commit_transaction_frame(tx_frame: StateChanges) -> None:
    """
    Commit a transaction frame's changes to the block frame.

    Merges ALL changes from the transaction frame into the block frame
    without net-zero filtering. Each transaction's changes are recorded
    at their respective transaction index, even if a later transaction
    reverts a change back to its original value.

    This is different from merge_on_success() which filters net-zero
    changes within a single transaction's execution.

    Parameters
    ----------
    tx_frame :
        The transaction frame to commit.

    """
    assert tx_frame.parent is not None
    block_frame = tx_frame.parent

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

    # Merge code changes - filter net-zero changes within the transaction
    # Compare final code against transaction's pre-code
    for (addr, idx), final_code in tx_frame.code_changes.items():
        pre_code = tx_frame.pre_code.get(addr, b"")
        if pre_code != final_code:
            block_frame.code_changes[(addr, idx)] = final_code
        # else: Net-zero change within this transaction - skip


def merge_on_failure(child_frame: StateChanges) -> None:
    """
    Merge child frame's changes into parent on failed completion.

    Merges only read operations from the child frame into the parent.
    Write operations are discarded since the frame reverted.
    This is called when a call frame fails/reverts.

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


def create_child_frame(parent: StateChanges) -> StateChanges:
    """
    Create a child frame for nested execution.

    Parameters
    ----------
    parent :
        The parent frame.

    Returns
    -------
    child : StateChanges
        A new child frame with parent reference set.

    """
    return StateChanges(parent=parent)


def handle_in_transaction_selfdestruct(
    state_changes: StateChanges,
    address: Address,
    current_block_access_index: BlockAccessIndex,
) -> None:
    """
    Handle account self-destructed in same transaction as creation.

    Per EIP-7928 and EIP-6780, accounts destroyed within their creation
    transaction must have:
    - Nonce changes from current transaction removed
    - Code changes from current transaction removed
    - Storage writes from current transaction converted to reads
    - Balance changes handled by net-zero filtering

    Parameters
    ----------
    state_changes : StateChanges
        The state changes tracker (typically the block-level frame).
    address : Address
        The address that self-destructed.
    current_block_access_index : BlockAccessIndex
        The current block access index (transaction index).

    """
    # Remove nonce changes from current transaction
    state_changes.nonce_changes = {
        (addr, idx, nonce)
        for addr, idx, nonce in state_changes.nonce_changes
        if not (addr == address and idx == current_block_access_index)
    }

    # Remove code changes from current transaction
    if (address, current_block_access_index) in state_changes.code_changes:
        del state_changes.code_changes[(address, current_block_access_index)]

    # Convert storage writes from current transaction to reads
    for addr, key, idx in list(state_changes.storage_writes.keys()):
        if addr == address and idx == current_block_access_index:
            del state_changes.storage_writes[(addr, key, idx)]
            state_changes.storage_reads.add((addr, key))


def normalize_balance_changes_for_transaction(
    block_frame: StateChanges,
    current_block_access_index: BlockAccessIndex,
    state: "State",
) -> None:
    """
    Normalize balance changes for the current transaction.

    Removes balance changes where post-transaction balance equals
    pre-transaction balance. This handles net-zero transfers across
    the entire transaction.

    This function should be called after merging transaction frames
    into the block frame to filter out addresses where balance didn't
    actually change from transaction start to transaction end.

    Parameters
    ----------
    block_frame : StateChanges
        The block-level state changes frame.
    current_block_access_index : BlockAccessIndex
        The current transaction's block access index.
    state : State
        The current state to read final balances from.

    """
    # Import locally to avoid circular import
    from .state import get_account

    # Collect addresses that have balance changes in this transaction
    addresses_to_check = [
        addr
        for (addr, idx) in block_frame.balance_changes.keys()
        if idx == current_block_access_index
    ]

    # For each address, compare pre vs post balance
    for addr in addresses_to_check:
        if addr in block_frame.pre_balances:
            pre_balance = block_frame.pre_balances[addr]
            post_balance = get_account(state, addr).balance

            if pre_balance == post_balance:
                # Remove balance change for this address - net-zero transfer
                del block_frame.balance_changes[
                    (addr, current_block_access_index)
                ]
