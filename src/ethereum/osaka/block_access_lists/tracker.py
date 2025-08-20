"""
Block Access List State Change Tracker for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module provides state change tracking functionality for building Block
Access Lists during transaction execution.

The tracker integrates with the EVM execution to capture all state accesses
and modifications, distinguishing between actual changes and no-op operations.
It maintains a cache of pre-state values to enable accurate change detection
throughout block execution.

See [EIP-7928] for the full specification.

[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
"""

from dataclasses import dataclass, field
from typing import Dict, TYPE_CHECKING

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, U256, Uint

from ..rlp_types import BlockAccessIndex

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

if TYPE_CHECKING:
    from ..state import State  # noqa: F401


@dataclass
class StateChangeTracker:
    """
    Tracks state changes during transaction execution for Block Access List
    construction.

    This tracker maintains a cache of pre-state values and coordinates with
    the [`BlockAccessListBuilder`] to record all state changes made during
    block execution. It ensures that only actual changes (not no-op writes)
    are recorded in the access list.

    [`BlockAccessListBuilder`]: ref:ethereum.osaka.block_access_lists.builder.BlockAccessListBuilder
    """

    block_access_list_builder: BlockAccessListBuilder
    """
    The builder instance that accumulates all tracked changes.
    """

    pre_storage_cache: Dict[tuple, U256] = field(default_factory=dict)
    """
    Cache of pre-state storage values, keyed by (address, slot) tuples.
    This cache persists across transactions within a block to track the
    original state before any modifications.
    """

    current_block_access_index: int = 0
    """
    The current block access index (0 for pre-execution, 1..n for transactions, n+1 for post-execution).
    """


def set_transaction_index(tracker: StateChangeTracker, block_access_index: int) -> None:
    """
    Set the current block access index for tracking changes.

    Must be called before processing each transaction/system contract to ensure changes
    are associated with the correct block access index.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    block_access_index :
        The block access index (0 for pre-execution, 1..n for transactions, n+1 for post-execution).
    """
    tracker.current_block_access_index = block_access_index


def capture_pre_state(
    tracker: StateChangeTracker, address: Address, key: Bytes, state: "State"
) -> U256:
    """
    Capture and cache the pre-state value for a storage location.

    Retrieves the storage value from before any transactions in the current
    block modified it. The value is cached to avoid repeated lookups and
    to maintain consistency across multiple accesses.

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
        The original storage value before any block modifications.
    """
    cache_key = (address, key)
    if cache_key not in tracker.pre_storage_cache:
        # Import locally to avoid circular import
        from ..state import get_storage

        tracker.pre_storage_cache[cache_key] = get_storage(state, address, key)
    return tracker.pre_storage_cache[cache_key]


def track_address_access(tracker: StateChangeTracker, address: Address) -> None:
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
    tracker: StateChangeTracker, address: Address, key: Bytes, state: "State"
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
    key: Bytes,
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
    else:
        add_storage_read(tracker.block_access_list_builder, address, key)


def track_balance_change(
    tracker: StateChangeTracker,
    address: Address,
    new_balance: U256,
) -> None:
    """
    Track a balance change for an account.

    Records the new balance after any balance-affecting operation, including
    transfers, gas payments, block rewards, and withdrawals. The balance is
    encoded as a 16-byte value (uint128) which is sufficient for the total
    ETH supply.

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

    add_balance_change(
        tracker.block_access_list_builder,
        address,
        BlockAccessIndex(tracker.current_block_access_index),
        new_balance,
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

    [`CREATE`]: ref:ethereum.osaka.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.osaka.vm.instructions.system.create2
    """
    track_address_access(tracker, address)
    add_nonce_change(
        tracker.block_access_list_builder,
        address,
        BlockAccessIndex(tracker.current_block_access_index),
        U64(new_nonce),
    )


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

    [`CREATE`]: ref:ethereum.osaka.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.osaka.vm.instructions.system.create2
    [`SETCODE`]: ref:ethereum.osaka.vm.instructions.system.setcode
    """
    track_address_access(tracker, address)
    add_code_change(
        tracker.block_access_list_builder,
        address,
        BlockAccessIndex(tracker.current_block_access_index),
        new_code,
    )


def finalize_transaction_changes(tracker: StateChangeTracker, state: "State") -> None:
    """
    Finalize changes for the current transaction.

    This method is called at the end of each transaction execution. Currently
    a no-op as all tracking is done incrementally during execution, but
    provided for future extensibility.

    Parameters
    ----------
    tracker :
        The state change tracker instance.
    state :
        The current execution state.
    """
    pass
