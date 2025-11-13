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
Stored in root frame, accessed by walking parent chain.

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

    Frames form a hierarchy and merge changes upward on completion.
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

    def get_block_access_index(self) -> BlockAccessIndex:
        """Get current block access index by walking to root."""
        current = self
        while current.parent is not None:
            current = current.parent
        return current._block_access_index

    def capture_pre_balance(self, address: Address, balance: U256) -> None:
        """Capture pre-balance (first-write-wins for net-zero filtering)."""
        if address not in self.pre_balances:
            self.pre_balances[address] = balance

    def capture_pre_nonce(self, address: Address, nonce: U64) -> None:
        """Capture pre-nonce (first-write-wins)."""
        if address not in self.pre_nonces:
            self.pre_nonces[address] = nonce

    def capture_pre_storage(
        self, address: Address, key: Bytes32, value: U256
    ) -> None:
        """Capture pre-storage (first-write-wins for noop filtering)."""
        slot = (address, key)
        if slot not in self.pre_storage:
            self.pre_storage[slot] = value

    def capture_pre_code(self, address: Address, code: Bytes) -> None:
        """Capture pre-code (first-write-wins)."""
        if address not in self.pre_code:
            self.pre_code[address] = code

    def track_address(self, address: Address) -> None:
        """Track that an address was accessed."""
        self.touched_addresses.add(address)

    def track_storage_read(self, address: Address, key: Bytes32) -> None:
        """Track a storage read operation."""
        self.storage_reads.add((address, key))

    def track_storage_write(
        self, address: Address, key: Bytes32, value: U256
    ) -> None:
        """Track a storage write operation with block access index."""
        self.storage_writes[(address, key, self.get_block_access_index())] = (
            value
        )

    def track_balance_change(
        self, address: Address, new_balance: U256
    ) -> None:
        """Track balance change keyed by (address, index)."""
        self.balance_changes[(address, self.get_block_access_index())] = (
            new_balance
        )

    def track_nonce_change(self, address: Address, new_nonce: U64) -> None:
        """Track a nonce change."""
        self.nonce_changes.add(
            (address, self.get_block_access_index(), new_nonce)
        )

    def track_code_change(self, address: Address, new_code: Bytes) -> None:
        """Track a code change."""
        self.code_changes[(address, self.get_block_access_index())] = new_code

    def increment_index(self) -> None:
        """Increment block access index by walking to root."""
        root = self
        while root.parent is not None:
            root = root.parent
        root._block_access_index = BlockAccessIndex(
            root._block_access_index + Uint(1)
        )

    def merge_on_success(self) -> None:
        """
        Merge this frame's changes into parent on successful completion.

        Merges all tracked changes (reads and writes) from this frame
        into the parent frame. Filters out net-zero changes based on
        captured pre-state values by comparing initial vs final values.
        """
        if self.parent is None:
            return

        # Merge address accesses
        self.parent.touched_addresses.update(self.touched_addresses)

        # Merge pre-state captures for transaction-level normalization
        # Only if parent doesn't have value (first capture wins)
        for addr, balance in self.pre_balances.items():
            if addr not in self.parent.pre_balances:
                self.parent.pre_balances[addr] = balance
        for addr, nonce in self.pre_nonces.items():
            if addr not in self.parent.pre_nonces:
                self.parent.pre_nonces[addr] = nonce
        for slot, value in self.pre_storage.items():
            if slot not in self.parent.pre_storage:
                self.parent.pre_storage[slot] = value
        for addr, code in self.pre_code.items():
            if addr not in self.parent.pre_code:
                self.parent.pre_code[addr] = code

        # Merge storage operations, filtering noop writes
        self.parent.storage_reads.update(self.storage_reads)
        for (addr, key, idx), value in self.storage_writes.items():
            # Only merge if value actually changed from pre-state
            if (addr, key) in self.pre_storage:
                if self.pre_storage[(addr, key)] != value:
                    self.parent.storage_writes[(addr, key, idx)] = value
                # If equal, it's a noop write - convert to read only
                else:
                    self.parent.storage_reads.add((addr, key))
            else:
                # No pre-state captured, merge as-is
                self.parent.storage_writes[(addr, key, idx)] = value

        # Merge balance changes - filter net-zero changes
        # balance_changes keyed by (address, index)
        for (addr, idx), final_balance in self.balance_changes.items():
            if addr in self.pre_balances:
                if self.pre_balances[addr] != final_balance:
                    # Net change occurred - merge the final balance
                    self.parent.balance_changes[(addr, idx)] = final_balance
                # else: Net-zero change - skip entirely
            else:
                # No pre-balance captured, merge as-is
                self.parent.balance_changes[(addr, idx)] = final_balance

        # Merge nonce changes - keep only highest nonce per address
        # Nonces are monotonically increasing, so just keep the max
        address_final_nonces: Dict[Address, Tuple[BlockAccessIndex, U64]] = {}
        for addr, idx, nonce in self.nonce_changes:
            # Keep the highest nonce value for each address
            if (
                addr not in address_final_nonces
                or nonce > address_final_nonces[addr][1]
            ):
                address_final_nonces[addr] = (idx, nonce)

        # Merge final nonces (no net-zero filtering - nonces never decrease)
        for addr, (idx, final_nonce) in address_final_nonces.items():
            self.parent.nonce_changes.add((addr, idx, final_nonce))

        # Merge code changes - filter net-zero changes
        # code_changes keyed by (address, index)
        for (addr, idx), final_code in self.code_changes.items():
            if addr in self.pre_code:
                if self.pre_code[addr] != final_code:
                    # Net change occurred - merge the final code
                    self.parent.code_changes[(addr, idx)] = final_code
                # else: Net-zero change - skip entirely
            else:
                # No pre-code captured, merge as-is
                self.parent.code_changes[(addr, idx)] = final_code

    def merge_on_failure(self) -> None:
        """
        Merge this frame's changes into parent on failed completion.

        Merges only read operations from this frame into the parent.
        Write operations are discarded since the frame reverted.
        This is called when a call frame fails/reverts.
        """
        if self.parent is None:
            return

        # Only merge reads and address accesses on failure
        self.parent.touched_addresses.update(self.touched_addresses)
        self.parent.storage_reads.update(self.storage_reads)

        # Convert writes to reads (failed writes still accessed the slots)
        for address, key, _idx in self.storage_writes.keys():
            self.parent.storage_reads.add((address, key))

        # Note: balance_changes, nonce_changes, and code_changes are NOT
        # merged on failure - they are discarded


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


def create_child_frame(parent: StateChanges) -> StateChanges:
    """
    Create a child frame for nested execution.

    The child frame will dynamically read the block_access_index from
    the root (block) frame, ensuring all frames see the same current index.

    Parameters
    ----------
    parent : StateChanges
        The parent frame.

    Returns
    -------
    child : StateChanges
        A new child frame with parent link.

    """
    return StateChanges(parent=parent)
