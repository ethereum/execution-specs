"""
Block Access List Builder for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module implements the Block Access List builder that tracks all account
and storage accesses during block execution and constructs the final
[`BlockAccessList`].

The builder follows a two-phase approach:

1. **Collection Phase**: During transaction execution, all state accesses are
   recorded via the tracking functions.
2. **Build Phase**: After block execution, the accumulated data is sorted
   and encoded into the final deterministic format.

[`BlockAccessList`]: ref:ethereum.osaka.ssz_types.BlockAccessList
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U32, U64, U256, Uint

from ..fork_types import Address
from ..rlp_types import (
    AccountChanges,
    BalanceChange,
    BlockAccessList,
    BlockAccessIndex,
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
    storage_changes: Dict[Bytes, List[StorageChange]] = field(default_factory=dict)
    """
    Mapping from storage slot to list of changes made to that slot.
    Each change includes the transaction index and new value.
    """
    
    storage_reads: Set[Bytes] = field(default_factory=set)
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
    
    [`BlockAccessList`]: ref:ethereum.osaka.ssz_types.BlockAccessList
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
    
    [`AccountData`]: ref:ethereum.osaka.block_access_lists.builder.AccountData
    """
    if address not in builder.accounts:
        builder.accounts[address] = AccountData()


def add_storage_write(
    builder: BlockAccessListBuilder,
    address: Address, 
    slot: Bytes, 
    block_access_index: BlockAccessIndex, 
    new_value: Bytes
) -> None:
    """
    Add a storage write operation to the block access list.
    
    Records a storage slot modification for a given address at a specific
    transaction index. Multiple writes to the same slot are tracked
    separately, maintaining the order and transaction index of each change.
    
    Parameters
    ----------
    builder :
        The block access list builder instance.
    address :
        The account address whose storage is being modified.
    slot :
        The storage slot being written to.
    block_access_index :
        The block access index for this change (0 for pre-execution, 1..n for transactions, n+1 for post-execution).
    new_value :
        The new value being written to the storage slot.
    """
    ensure_account(builder, address)
    
    if slot not in builder.accounts[address].storage_changes:
        builder.accounts[address].storage_changes[slot] = []
        
    change = StorageChange(block_access_index=block_access_index, new_value=new_value)
    builder.accounts[address].storage_changes[slot].append(change)


def add_storage_read(
    builder: BlockAccessListBuilder,
    address: Address,
    slot: Bytes
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
    post_balance: U256
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
        The block access index for this change (0 for pre-execution, 1..n for transactions, n+1 for post-execution).
    post_balance :
        The account balance after the change as U256.
    """
    ensure_account(builder, address)
    
    change = BalanceChange(block_access_index=block_access_index, post_balance=post_balance)
    builder.accounts[address].balance_changes.append(change)


def add_nonce_change(
    builder: BlockAccessListBuilder,
    address: Address, 
    block_access_index: BlockAccessIndex, 
    new_nonce: U64
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
        The block access index for this change (0 for pre-execution, 1..n for transactions, n+1 for post-execution).
    new_nonce :
        The new nonce value after the change.
    
    [`CREATE`]: ref:ethereum.osaka.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.osaka.vm.instructions.system.create2
    """
    ensure_account(builder, address)
    
    change = NonceChange(block_access_index=block_access_index, new_nonce=new_nonce)
    builder.accounts[address].nonce_changes.append(change)


def add_code_change(
    builder: BlockAccessListBuilder,
    address: Address, 
    block_access_index: BlockAccessIndex, 
    new_code: Bytes
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
        The block access index for this change (0 for pre-execution, 1..n for transactions, n+1 for post-execution).
    new_code :
        The deployed contract bytecode.
    
    [`CREATE`]: ref:ethereum.osaka.vm.instructions.system.create
    [`CREATE2`]: ref:ethereum.osaka.vm.instructions.system.create2
    [`SETCODE`]: ref:ethereum.osaka.vm.instructions.system.setcode
    """
    ensure_account(builder, address)
    
    change = CodeChange(block_access_index=block_access_index, new_code=new_code)
    builder.accounts[address].code_changes.append(change)


def add_touched_account(builder: BlockAccessListBuilder, address: Address) -> None:
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
    
    [`EXTCODEHASH`]: ref:ethereum.osaka.vm.instructions.environment.extcodehash
    [`BALANCE`]: ref:ethereum.osaka.vm.instructions.environment.balance
    [`EXTCODESIZE`]: ref:ethereum.osaka.vm.instructions.environment.extcodesize
    [`EXTCODECOPY`]: ref:ethereum.osaka.vm.instructions.environment.extcodecopy
    """
    ensure_account(builder, address)


def build(builder: BlockAccessListBuilder) -> BlockAccessList:
    """
    Build the final [`BlockAccessList`] from accumulated changes.
    
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
    
    [`BlockAccessList`]: ref:ethereum.osaka.ssz_types.BlockAccessList
    """
    account_changes_list = []
    
    for address, changes in builder.accounts.items():
        storage_changes = []
        for slot, slot_changes in changes.storage_changes.items():
            sorted_changes = tuple(sorted(slot_changes, key=lambda x: x.block_access_index))
            storage_changes.append(SlotChanges(slot=slot, changes=sorted_changes))
        
        storage_reads = []
        for slot in changes.storage_reads:
            if slot not in changes.storage_changes:
                storage_reads.append(slot)
        
        balance_changes = tuple(sorted(changes.balance_changes, key=lambda x: x.block_access_index))
        nonce_changes = tuple(sorted(changes.nonce_changes, key=lambda x: x.block_access_index))
        code_changes = tuple(sorted(changes.code_changes, key=lambda x: x.block_access_index))
        
        storage_changes.sort(key=lambda x: x.slot)
        storage_reads.sort()
        
        account_change = AccountChanges(
            address=address,
            storage_changes=tuple(storage_changes),
            storage_reads=tuple(storage_reads),
            balance_changes=balance_changes,
            nonce_changes=nonce_changes,
            code_changes=code_changes
        )
        
        account_changes_list.append(account_change)
    
    account_changes_list.sort(key=lambda x: x.address)
    
    return BlockAccessList(account_changes=tuple(account_changes_list))