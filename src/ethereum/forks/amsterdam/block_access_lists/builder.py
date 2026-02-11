"""
Implements the Block Access List builder that tracks all account
and storage accesses during block execution and constructs the final
[`BlockAccessList`].

The builder follows a two-phase approach:

1. **Collection Phase**: During transaction execution, all state accesses are
   recorded via the tracking functions.
2. **Build Phase**: After block execution, the accumulated data is sorted
   and encoded into the final deterministic format.

[`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
"""  # noqa: E501

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.state import Account, Address, PreState

from ..state_tracker import BlockState, TransactionState
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


@dataclass
class AccountData:
    """
    Account data stored in the builder during block execution.

    This dataclass tracks all changes made to a single account throughout
    the execution of a block, organized by the type of change and the
    transaction index where it occurred.
    """

    storage_changes: Dict[U256, List[StorageChange]] = field(
        default_factory=dict
    )
    """
    Mapping from storage slot to list of changes made to that slot.
    Each change includes the transaction index and new value.
    """

    storage_reads: Set[U256] = field(default_factory=set)
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

    [`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
    """  # noqa: E501

    block_access_index: BlockAccessIndex = BlockAccessIndex(0)
    """
    Current block access index.  Set by the caller before each
    [`incorporate_tx_into_block`] call (0 for system txs, i+1 for the
    i-th user tx, N+1 for post-execution operations).

    [`incorporate_tx_into_block`]: ref:ethereum.forks.amsterdam.state_tracker.incorporate_tx_into_block
    """  # noqa: E501

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

    [`AccountData`]: ref:ethereum.forks.amsterdam.block_access_lists.builder.AccountData
    """  # noqa: E501
    if address not in builder.accounts:
        builder.accounts[address] = AccountData()


def add_storage_write(
    builder: BlockAccessListBuilder,
    address: Address,
    slot: U256,
    block_access_index: BlockAccessIndex,
    new_value: U256,
) -> None:
    """
    Add a storage write operation to the block access list.

    Records a storage slot modification for a given address at a specific
    transaction index. If multiple writes occur to the same slot within the
    same transaction (same `block_access_index`), only the final value is kept.
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
    builder: BlockAccessListBuilder, address: Address, slot: U256
) -> None:
    """
    Add a storage read operation to the block access list.

    Records that a storage slot was read during execution. Storage slots
    that are both read and written will only appear in the storage changes
    list, not in the storage reads list, as per [EIP-7928].
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
    during contract creation via [`CREATE`], [`CREATE2`], or
    [`SetCodeTransaction`][sct] operations.

    [`CREATE`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.forks.amsterdam.vm.instructions.system.create2
    [sct]: ref:ethereum.forks.amsterdam.transactions.SetCodeTransaction
    """
    ensure_account(builder, address)

    # Check if we already have a code change for this block_access_index
    # This handles the case of in-transaction selfdestructs where code is
    # first deployed and then cleared in the same transaction
    existing_changes = builder.accounts[address].code_changes
    for i, existing in enumerate(existing_changes):
        if existing.block_access_index == block_access_index:
            # Replace the existing code change with the new one
            # For selfdestructs, this ensures we only record the final
            # state (empty code)
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

    [`EXTCODEHASH`]: ref:ethereum.forks.amsterdam.vm.instructions.environment.extcodehash
    [`BALANCE`]: ref:ethereum.forks.amsterdam.vm.instructions.environment.balance
    [`EXTCODESIZE`]: ref:ethereum.forks.amsterdam.vm.instructions.environment.extcodesize
    [`EXTCODECOPY`]: ref:ethereum.forks.amsterdam.vm.instructions.environment.extcodecopy
    """  # noqa: E501
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

    [`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
    """  # noqa: E501
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


def _get_pre_tx_account(
    pre_tx_accounts: Dict[Address, Optional[Account]],
    pre_state: PreState,
    address: Address,
) -> Optional[Account]:
    """
    Look up an account in cumulative state, falling back to `pre_state`.

    The cumulative account state (`pre_tx_accounts`) should contain state up
    to (but not including) the current transaction.

    Returns `None` if the `address` does not exist.
    """
    if address in pre_tx_accounts:
        return pre_tx_accounts[address]
    return pre_state.get_account_optional(address)


def _get_pre_tx_storage(
    pre_tx_storage: Dict[Address, Dict[Bytes32, U256]],
    pre_state: PreState,
    address: Address,
    key: Bytes32,
) -> U256:
    """
    Look up a storage value in cumulative state, falling back to `pre_state`.

    Returns `0` if not set.
    """
    if address in pre_tx_storage and key in pre_tx_storage[address]:
        return pre_tx_storage[address][key]
    return pre_state.get_storage(address, key)


def update_builder_from_tx(
    builder: BlockAccessListBuilder,
    tx_state: TransactionState,
) -> None:
    """
    Update the BAL builder with changes from a single transaction.

    Compare the transaction's writes against the block's cumulative
    state (falling back to `pre_state`) to extract balance, nonce, code, and
    storage changes.  Net-zero filtering is automatic: if the pre-tx value
    equals the post-tx value, no change is recorded.

    Must be called **before** the transaction's writes are merged into
    the block state.
    """
    block_state = tx_state.parent
    pre_state = block_state.pre_state
    idx = builder.block_access_index

    # Compare account writes against block cumulative state
    for address, post_account in tx_state.account_writes.items():
        pre_account = _get_pre_tx_account(
            block_state.account_writes, pre_state, address
        )

        pre_balance = pre_account.balance if pre_account else U256(0)
        post_balance = post_account.balance if post_account else U256(0)
        if pre_balance != post_balance:
            add_balance_change(builder, address, idx, post_balance)

        pre_nonce = pre_account.nonce if pre_account else Uint(0)
        post_nonce = post_account.nonce if post_account else Uint(0)
        if pre_nonce != post_nonce:
            add_nonce_change(builder, address, idx, U64(post_nonce))

        pre_code = pre_account.code if pre_account else b""
        post_code = post_account.code if post_account else b""
        if pre_code != post_code:
            add_code_change(builder, address, idx, post_code)

    # Compare storage writes against block cumulative state
    for address, slots in tx_state.storage_writes.items():
        for key, post_value in slots.items():
            pre_value = _get_pre_tx_storage(
                block_state.storage_writes, pre_state, address, key
            )
            if pre_value != post_value:
                # Convert slot from internal Bytes32 format to U256 for BAL.
                # EIP-7928 uses U256 as it's more space-efficient in RLP.
                u256_slot = U256.from_be_bytes(key)
                add_storage_write(builder, address, u256_slot, idx, post_value)


def build_block_access_list(
    builder: BlockAccessListBuilder,
    block_state: BlockState,
) -> BlockAccessList:
    """
    Build a [`BlockAccessList`] from the builder and block state.

    Feed accumulated reads from the block state into the builder, then produce
    the final sorted and encoded block access list.

    [`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
    """  # noqa: E501
    # Add storage reads (convert Bytes32 to U256 for BAL encoding)
    for address, slot in block_state.storage_reads:
        add_storage_read(builder, address, U256.from_be_bytes(slot))

    # Add touched addresses
    for address in block_state.account_reads:
        add_touched_account(builder, address)

    return _build_from_builder(builder)
