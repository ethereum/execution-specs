"""
Implements the Block Access List builder that tracks all account
and storage accesses during block execution and constructs the final
[`BlockAccessList`].

The builder follows a two-phase approach:

1. **Collection Phase**: During transaction execution, all state accesses are
   recorded via the tracking functions.
2. **Build Phase**: After block execution, the accumulated data is sorted
   and encoded into the final deterministic format.

[`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList  # noqa: E501
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Set

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256

from ..fork_types import Address
from .rlp_types import (
    AccountChanges,
    BalanceChange,
    BlockAccessIndex,
    BlockAccessList,
    CodeChange,
    NonceChange,
    SlotChanges,
    StorageChange,
)

if TYPE_CHECKING:
    from ..state_tracker import StateChanges


@dataclass
class AccountData:
    """
    Account data stored in the builder during block execution.

    This dataclass tracks all changes made to a single account throughout
    the execution of a block, organized by the type of change and the
    transaction index where it occurred.
    """

    storage_changes: Dict[Bytes32, List[StorageChange]] = field(
        default_factory=dict
    )
    """
    Mapping from storage slot to list of changes made to that slot.
    Each change includes the transaction index and new value.
    """

    storage_reads: Set[Bytes32] = field(default_factory=set)
    """
    Set of storage slots that were read but not modified.
    """

    balance_changes: List[BalanceChange] = field(default_factory=list)
    """
    List of balance changes for this account, ordered by transaction index.
    """

    nonce_changes: List[NonceChange] = field(default_factory=list)
    """
    List of nonce changes for this account, ordered by transaction index.
    """

    code_changes: List[CodeChange] = field(default_factory=list)
    """
    List of code changes (contract deployments) for this account,
    ordered by transaction index.
    """


@dataclass
class BlockAccessListBuilder:
    """
    Builder for constructing [`BlockAccessList`] efficiently during transaction
    execution.

    The builder accumulates all account and storage accesses during block
    execution and constructs a deterministic access list. Changes are tracked
    by address, field type, and transaction index to enable efficient
    reconstruction of state changes.

    [`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList  # noqa: E501
    """

    accounts: Dict[Address, AccountData] = field(default_factory=dict)
    """
    Mapping from account address to its tracked changes during block execution.
    """


def ensure_account(builder: BlockAccessListBuilder, address: Address) -> None:
    """
    Ensure an account exists in the builder's tracking structure.

    Creates an empty [`AccountData`] entry for the given address if it
    doesn't already exist. This function is idempotent and safe to call
    multiple times for the same address.

    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address to ensure exists.

    [`AccountData`] :
        ref:ethereum.forks.amsterdam.block_access_lists.builder.AccountData

    """
    if address not in builder.accounts:
        builder.accounts[address] = AccountData()


def add_storage_write(
    builder: BlockAccessListBuilder,
    address: Address,
    slot: Bytes32,
    block_access_index: BlockAccessIndex,
    new_value: Bytes32,
) -> None:
    """
    Add a storage write operation to the block access list.

    Records a storage slot modification for a given address at a specific
    transaction index. If multiple writes occur to the same slot within the
    same transaction (same block_access_index), only the final value is kept.

    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address whose storage is being modified.
    slot :
        The storage slot being written to.
    block_access_index :
        The block access index for this change (0 for pre-execution,
        1..n for transactions, n+1 for post-execution).
    new_value :
        The new value being written to the storage slot.

    """
    ensure_account(builder, address)

    if slot not in builder.accounts[address].storage_changes:
        builder.accounts[address].storage_changes[slot] = []

    # Check if there's already an entry with the same block_access_index
    # If so, update it with the new value, keeping only the final write
    changes = builder.accounts[address].storage_changes[slot]
    for i, existing_change in enumerate(changes):
        if existing_change.block_access_index == block_access_index:
            # Update the existing entry with the new value
            changes[i] = StorageChange(
                block_access_index=block_access_index, new_value=new_value
            )
            return

    # No existing entry found, append new change
    change = StorageChange(
        block_access_index=block_access_index, new_value=new_value
    )
    builder.accounts[address].storage_changes[slot].append(change)


def add_storage_read(
    builder: BlockAccessListBuilder, address: Address, slot: Bytes32
) -> None:
    """
    Add a storage read operation to the block access list.

    Records that a storage slot was read during execution. Storage slots
    that are both read and written will only appear in the storage changes
    list, not in the storage reads list, as per [EIP-7928].

    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address whose storage is being read.
    slot :
        The storage slot being read.

    [EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928

    """
    ensure_account(builder, address)
    builder.accounts[address].storage_reads.add(slot)


def add_balance_change(
    builder: BlockAccessListBuilder,
    address: Address,
    block_access_index: BlockAccessIndex,
    post_balance: U256,
) -> None:
    """
    Add a balance change to the block access list.

    Records the post-transaction balance for an account after it has been
    modified. This includes changes from transfers, gas fees, block rewards,
    and any other balance-affecting operations.

    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address whose balance changed.
    block_access_index :
        The block access index for this change (0 for pre-execution,
        1..n for transactions, n+1 for post-execution).
    post_balance :
        The account balance after the change as U256.

    """
    ensure_account(builder, address)

    # Balance value is already U256
    balance_value = post_balance

    # Check if we already have a balance change for this tx_index and update it
    # This ensures we only track the final balance per transaction
    existing_changes = builder.accounts[address].balance_changes
    for i, existing in enumerate(existing_changes):
        if existing.block_access_index == block_access_index:
            # Update the existing balance change with the new balance
            existing_changes[i] = BalanceChange(
                block_access_index=block_access_index,
                post_balance=balance_value,
            )
            return

    # No existing change for this tx_index, add a new one
    change = BalanceChange(
        block_access_index=block_access_index, post_balance=balance_value
    )
    builder.accounts[address].balance_changes.append(change)


def add_nonce_change(
    builder: BlockAccessListBuilder,
    address: Address,
    block_access_index: BlockAccessIndex,
    new_nonce: U64,
) -> None:
    """
    Add a nonce change to the block access list.

    Records a nonce increment for an account. This occurs when an EOA sends
    a transaction or when a contract performs [`CREATE`] or [`CREATE2`]
    operations.

    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address whose nonce changed.
    block_access_index :
        The block access index for this change (0 for pre-execution,
        1..n for transactions, n+1 for post-execution).
    new_nonce :
        The new nonce value after the change.

    [`CREATE`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create2

    """
    ensure_account(builder, address)

    # Check if we already have a nonce change for this tx_index and update it
    # This ensures we only track the final (highest) nonce per transaction
    existing_changes = builder.accounts[address].nonce_changes
    for i, existing in enumerate(existing_changes):
        if existing.block_access_index == block_access_index:
            # Keep the highest nonce value
            if new_nonce > existing.new_nonce:
                existing_changes[i] = NonceChange(
                    block_access_index=block_access_index, new_nonce=new_nonce
                )
            return

    # No existing change for this tx_index, add a new one
    change = NonceChange(
        block_access_index=block_access_index, new_nonce=new_nonce
    )
    builder.accounts[address].nonce_changes.append(change)


def add_code_change(
    builder: BlockAccessListBuilder,
    address: Address,
    block_access_index: BlockAccessIndex,
    new_code: Bytes,
) -> None:
    """
    Add a code change to the block access list.

    Records contract code deployment or modification. This typically occurs
    during contract creation via [`CREATE`], [`CREATE2`], or [`SETCODE`]
    operations.

    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address receiving new code.
    block_access_index :
        The block access index for this change (0 for pre-execution,
        1..n for transactions, n+1 for post-execution).
    new_code :
        The deployed contract bytecode.

    [`CREATE`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create2

    """
    ensure_account(builder, address)

    # Check if we already have a code change for this block_access_index
    # This handles the case of in-transaction selfdestructs where code is
    # first deployed and then cleared in the same transaction
    existing_changes = builder.accounts[address].code_changes
    for i, existing in enumerate(existing_changes):
        if existing.block_access_index == block_access_index:
            # Replace the existing code change with the new one
            # For selfdestructs, this ensures we only record the final state (empty code)
            existing_changes[i] = CodeChange(
                block_access_index=block_access_index, new_code=new_code
            )
            return

    # No existing change for this block_access_index, add a new one
    change = CodeChange(
        block_access_index=block_access_index, new_code=new_code
    )
    builder.accounts[address].code_changes.append(change)


def add_touched_account(
    builder: BlockAccessListBuilder, address: Address
) -> None:
    """
    Add an account that was accessed but not modified.

    Records that an account was accessed during execution without any state
    changes. This is used for operations like [`EXTCODEHASH`], [`BALANCE`],
    [`EXTCODESIZE`], and [`EXTCODECOPY`] that read account data without
    modifying it.

    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address that was accessed.

    [`EXTCODEHASH`] :
        ref:ethereum.forks.amsterdam.vm.instructions.environment.extcodehash
    [`BALANCE`] :
        ref:ethereum.forks.amsterdam.vm.instructions.environment.balance
    [`EXTCODESIZE`] :
        ref:ethereum.forks.amsterdam.vm.instructions.environment.extcodesize
    [`EXTCODECOPY`] :
        ref:ethereum.forks.amsterdam.vm.instructions.environment.extcodecopy

    """
    ensure_account(builder, address)


def _build_from_builder(
    builder: BlockAccessListBuilder,
) -> BlockAccessList:
    """
    Build the final [`BlockAccessList`] from a builder (internal helper).

    Constructs a deterministic block access list by sorting all accumulated
    changes. The resulting list is ordered by:

    1. Account addresses (lexicographically)
    2. Within each account:
       - Storage slots (lexicographically)
       - Transaction indices (numerically) for each change type

    Parameters
    ----------
    builder :
        The block access list builder containing all tracked changes.

    Returns
    -------
    block_access_list :
        The final sorted and encoded block access list.

    [`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList  # noqa: E501

    """
    block_access_list: BlockAccessList = []

    for address, changes in builder.accounts.items():
        storage_changes = []
        for slot, slot_changes in changes.storage_changes.items():
            sorted_changes = tuple(
                sorted(slot_changes, key=lambda x: x.block_access_index)
            )
            storage_changes.append(
                SlotChanges(slot=slot, changes=sorted_changes)
            )

        storage_reads = []
        for slot in changes.storage_reads:
            if slot not in changes.storage_changes:
                storage_reads.append(slot)

        balance_changes = tuple(
            sorted(changes.balance_changes, key=lambda x: x.block_access_index)
        )
        nonce_changes = tuple(
            sorted(changes.nonce_changes, key=lambda x: x.block_access_index)
        )
        code_changes = tuple(
            sorted(changes.code_changes, key=lambda x: x.block_access_index)
        )

        storage_changes.sort(key=lambda x: x.slot)
        storage_reads.sort()

        account_change = AccountChanges(
            address=address,
            storage_changes=tuple(storage_changes),
            storage_reads=tuple(storage_reads),
            balance_changes=balance_changes,
            nonce_changes=nonce_changes,
            code_changes=code_changes,
        )

        block_access_list.append(account_change)

    block_access_list.sort(key=lambda x: x.address)

    return block_access_list


def build_block_access_list(
    state_changes: "StateChanges",
) -> BlockAccessList:
    """
    Build a [`BlockAccessList`] from a StateChanges frame.

    Converts the accumulated state changes from the frame-based architecture
    into the final deterministic BlockAccessList format.

    Parameters
    ----------
    state_changes :
        The block-level StateChanges frame containing all changes from the block.

    Returns
    -------
    block_access_list :
        The final sorted and encoded block access list.

    [`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList  # noqa: E501
    [`StateChanges`]: ref:ethereum.forks.amsterdam.state_tracker.StateChanges

    """
    builder = BlockAccessListBuilder()

    # Add all touched addresses
    for address in state_changes.touched_addresses:
        add_touched_account(builder, address)

    # Add all storage reads
    for address, slot in state_changes.storage_reads:
        add_storage_read(builder, address, slot)

    # Add all storage writes
    # Net-zero filtering happens at transaction commit time, not here.
    # At block level, we track ALL writes at their respective indices.
    for (
        address,
        slot,
        block_access_index,
    ), value in state_changes.storage_writes.items():
        # Convert U256 to Bytes32 for storage
        value_bytes = Bytes32(value.to_bytes(U256(32), "big"))
        add_storage_write(
            builder, address, slot, block_access_index, value_bytes
        )

    # Add all balance changes (balance_changes is keyed by (address, index))
    for (
        address,
        block_access_index,
    ), new_balance in state_changes.balance_changes.items():
        add_balance_change(builder, address, block_access_index, new_balance)

    # Add all nonce changes
    for address, block_access_index, new_nonce in state_changes.nonce_changes:
        add_nonce_change(builder, address, block_access_index, new_nonce)

    # Add all code changes
    # Filtering happens at transaction level in eoa_delegation.py
    for (
        address,
        block_access_index,
    ), new_code in state_changes.code_changes.items():
        add_code_change(builder, address, block_access_index, new_code)

    return _build_from_builder(builder)
