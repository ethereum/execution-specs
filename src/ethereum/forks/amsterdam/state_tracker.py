"""
State Tracking for Block Execution.

Track state changes on top of a read-only ``PreState``.  At block end,
accumulated diffs feed into
``PreState.compute_state_root()``.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Replace the mutable ``State`` class with lightweight state trackers that
record diffs.  ``BlockState`` accumulates committed transaction
changes across a block.  ``TransactionState`` tracks in-flight changes
within a single transaction and supports copy-on-write rollback.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, Optional, Set, Tuple, final

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import modify
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import (
    EMPTY_ACCOUNT,
    EMPTY_CODE_HASH,
    Account,
    Address,
    BlockDiff,
    PreState,
)

if TYPE_CHECKING:
    from .block_access_lists import BlockAccessListBuilder


@final
@dataclass
class BlockState:
    """
    Accumulate committed transaction-level changes across a block.

    Read chain: block writes -> pre_state.

    ``account_reads`` and ``storage_reads`` accumulate across all
    transactions for BAL generation.
    """

    pre_state: PreState
    account_reads: Set[Address] = field(default_factory=set)
    account_writes: Dict[Address, Optional[Account]] = field(
        default_factory=dict
    )
    storage_reads: Set[Tuple[Address, Bytes32]] = field(default_factory=set)
    storage_writes: Dict[Address, Dict[Bytes32, U256]] = field(
        default_factory=dict
    )
    code_writes: Dict[Hash32, Bytes] = field(default_factory=dict)


@final
@dataclass
class TransactionState:
    """
    Track in-flight state changes within a single transaction.

    Read chain: tx writes -> block writes -> pre_state.

    ``storage_reads`` and ``account_reads`` are shared references
    that survive rollback (reads from failed calls still appear in the
    Block Access List).
    """

    parent: BlockState
    account_reads: Set[Address] = field(default_factory=set)
    account_writes: Dict[Address, Optional[Account]] = field(
        default_factory=dict
    )
    storage_reads: Set[Tuple[Address, Bytes32]] = field(default_factory=set)
    storage_writes: Dict[Address, Dict[Bytes32, U256]] = field(
        default_factory=dict
    )
    code_writes: Dict[Hash32, Bytes] = field(default_factory=dict)
    created_accounts: Set[Address] = field(default_factory=set)
    transient_storage: Dict[Tuple[Address, Bytes32], U256] = field(
        default_factory=dict
    )


def get_pre_state_account_optional(
    tx_state: TransactionState, address: Address
) -> Optional[Account]:
    """
    Get the `Account` object at an address that existed before the current
    transaction, or `None` (rather than [`EMPTY_ACCOUNT`]) if there was no
    account at the address at that point.

    Use [`get_pre_state_account()`][pre] if the difference between a
    non-existent account and [`EMPTY_ACCOUNT`] isn't important.

    [`EMPTY_ACCOUNT`]: ref:ethereum.state.EMPTY_ACCOUNT
    [pre]: ref:ethereum.forks.amsterdam.state_tracker.get_pre_state_account

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address to look up.

    Returns
    -------
    account : ``Optional[Account]``
        Account at address before the current transaction.

    """
    tx_state.account_reads.add(address)
    if address in tx_state.parent.account_writes:
        return tx_state.parent.account_writes[address]
    return tx_state.parent.pre_state.get_account_optional(address)


def get_pre_state_account(
    tx_state: TransactionState, address: Address
) -> Account:
    """
    Get the `Account` object at an address that existed before the current
    transaction, or [`EMPTY_ACCOUNT`]) if there was no account at the address
    at that point.

    Use [`get_pre_state_account_optional()`][opt] if the difference between a
    non-existent account and [`EMPTY_ACCOUNT`] is material.

    [`EMPTY_ACCOUNT`]: ref:ethereum.state.EMPTY_ACCOUNT
    [opt]: ref:ethereum.forks.amsterdam.state_tracker.get_pre_state_account_optional

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address to look up.

    Returns
    -------
    account : ``Account``
        Account at address before the current transaction.

    """  # noqa: E501
    account = get_pre_state_account_optional(tx_state, address)
    if account is None:
        return EMPTY_ACCOUNT
    else:
        return account


def get_account_optional(
    tx_state: TransactionState, address: Address
) -> Optional[Account]:
    """
    Get the ``Account`` object at an address. Return ``None`` (rather than
    ``EMPTY_ACCOUNT``) if there is no account at the address.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address to look up.

    Returns
    -------
    account : ``Optional[Account]``
        Account at address.

    """
    tx_state.account_reads.add(address)
    if address in tx_state.account_writes:
        return tx_state.account_writes[address]
    return get_pre_state_account_optional(tx_state, address)


def get_account(tx_state: TransactionState, address: Address) -> Account:
    """
    Get the ``Account`` object at an address. Return ``EMPTY_ACCOUNT``
    if there is no account at the address.

    Use ``get_account_optional()`` if you care about the difference
    between a non-existent account and ``EMPTY_ACCOUNT``.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address to look up.

    Returns
    -------
    account : ``Account``
        Account at address.

    """
    account = get_account_optional(tx_state, address)
    if account is None:
        return EMPTY_ACCOUNT
    else:
        return account


def get_code(tx_state: TransactionState, code_hash: Hash32) -> Bytes:
    """
    Get the bytecode for a given code hash.

    Read chain: tx code_writes -> block code_writes -> pre_state.

    Parameters
    ----------
    tx_state :
        The transaction state.
    code_hash :
        Hash of the code to look up.

    Returns
    -------
    code : ``Bytes``
        The bytecode.

    """
    if code_hash == EMPTY_CODE_HASH:
        return b""
    if code_hash in tx_state.code_writes:
        return tx_state.code_writes[code_hash]
    if code_hash in tx_state.parent.code_writes:
        return tx_state.parent.code_writes[code_hash]
    return tx_state.parent.pre_state.get_code(code_hash)


def get_storage(
    tx_state: TransactionState, address: Address, key: Bytes32
) -> U256:
    """
    Get a value at a storage key on an account. Return ``U256(0)`` if
    the storage key has not been set previously.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account.
    key :
        Key to look up.

    Returns
    -------
    value : ``U256``
        Value at the key.

    """
    tx_state.storage_reads.add((address, key))
    if address in tx_state.storage_writes:
        if key in tx_state.storage_writes[address]:
            return tx_state.storage_writes[address][key]
    if address in tx_state.parent.storage_writes:
        if key in tx_state.parent.storage_writes[address]:
            return tx_state.parent.storage_writes[address][key]
    return tx_state.parent.pre_state.get_storage(address, key)


def get_storage_original(
    tx_state: TransactionState, address: Address, key: Bytes32
) -> U256:
    """
    Get the original value in a storage slot i.e. the value before the
    current transaction began. Read from block-level writes, then
    pre_state. Return ``U256(0)`` for accounts created in the current
    transaction.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account to read the value from.
    key :
        Key of the storage slot.

    """
    if address in tx_state.created_accounts:
        return U256(0)
    if address in tx_state.parent.storage_writes:
        if key in tx_state.parent.storage_writes[address]:
            return tx_state.parent.storage_writes[address][key]
    return tx_state.parent.pre_state.get_storage(address, key)


def get_transient_storage(
    tx_state: TransactionState, address: Address, key: Bytes32
) -> U256:
    """
    Get a value at a storage key on an account from transient storage.
    Return ``U256(0)`` if the storage key has not been set previously.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account.
    key :
        Key to look up.

    Returns
    -------
    value : ``U256``
        Value at the key.

    """
    return tx_state.transient_storage.get((address, key), U256(0))


def account_exists(tx_state: TransactionState, address: Address) -> bool:
    """
    Check if an account exists in the state trie.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    account_exists : ``bool``
        True if account exists in the state trie, False otherwise.

    """
    return get_account_optional(tx_state, address) is not None


def account_deployable(tx_state: TransactionState, address: Address) -> bool:
    """
    Check if an account's code can be written to.
    """
    account = get_account(tx_state, address)
    if account.nonce != Uint(0) or account.code_hash != EMPTY_CODE_HASH:
        return False

    return True


def account_exists_and_is_empty(
    tx_state: TransactionState, address: Address
) -> bool:
    """
    Check if an account exists and has zero nonce, empty code and zero
    balance.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    exists_and_is_empty : ``bool``
        True if an account exists and has zero nonce, empty code and
        zero balance, False otherwise.

    """
    account = get_account_optional(tx_state, address)
    return (
        account is not None
        and account.nonce == Uint(0)
        and account.code_hash == EMPTY_CODE_HASH
        and account.balance == 0
    )


def is_account_alive(tx_state: TransactionState, address: Address) -> bool:
    """
    Check whether an account is both in the state and non-empty.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    is_alive : ``bool``
        True if the account is alive.

    """
    account = get_account_optional(tx_state, address)
    return account is not None and account != EMPTY_ACCOUNT


def set_account(
    tx_state: TransactionState,
    address: Address,
    account: Optional[Account],
) -> None:
    """
    Set the ``Account`` object at an address. Setting to ``None``
    deletes the account (but not its storage, see
    ``destroy_account()``).

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address to set.
    account :
        Account to set at address.

    """
    tx_state.account_writes[address] = account


def set_storage(
    tx_state: TransactionState,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """
    Set a value at a storage key on an account.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account.
    key :
        Key to set.
    value :
        Value to set at the key.

    """
    assert get_account_optional(tx_state, address) is not None
    if address not in tx_state.storage_writes:
        tx_state.storage_writes[address] = {}
    tx_state.storage_writes[address][key] = value


def destroy_account(tx_state: TransactionState, address: Address) -> None:
    """
    Completely remove the account at ``address`` and all of its storage.

    Invoked by ``modify_state`` (and the coinbase fee-credit path) to
    clean up an account that has become empty (zero nonce, empty
    code, and zero balance) so it does not appear in the post-state.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of account to destroy.

    """
    destroy_storage(tx_state, address)
    set_account(tx_state, address, None)


def clear_account_preserving_balance(
    tx_state: TransactionState, address: Address
) -> None:
    """
    Clear an account's nonce, code, and storage while preserving its
    balance.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account to modify.

    """

    def clear_account(account: Account) -> None:
        account.nonce = Uint(0)
        account.code_hash = EMPTY_CODE_HASH

    destroy_storage(tx_state, address)
    modify_state(tx_state, address, clear_account)


def destroy_storage(tx_state: TransactionState, address: Address) -> None:
    """
    Completely remove the storage at ``address``.

    Convert storage writes to reads before deleting so that accesses
    from created-then-destroyed accounts appear in the Block Access
    List. Only supports same transaction destruction.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of account whose storage is to be deleted.

    """
    if address in tx_state.storage_writes:
        for key in tx_state.storage_writes[address]:
            tx_state.storage_reads.add((address, key))
        del tx_state.storage_writes[address]


def mark_account_created(tx_state: TransactionState, address: Address) -> None:
    """
    Mark an account as having been created in the current transaction.
    This information is used by ``get_storage_original()`` to handle an
    obscure edgecase, and to respect the constraints added to
    SELFDESTRUCT by EIP-6780.

    The marker is not removed even if the account creation reverts.
    Since the account cannot have had code prior to its creation and
    can't call ``get_storage_original()``, this is harmless.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account that has been created.

    """
    tx_state.created_accounts.add(address)


def set_transient_storage(
    tx_state: TransactionState,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """
    Set a value at a storage key on an account in transient storage.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account.
    key :
        Key to set.
    value :
        Value to set at the key.

    """
    if value == U256(0):
        tx_state.transient_storage.pop((address, key), None)
    else:
        tx_state.transient_storage[(address, key)] = value


def modify_state(
    tx_state: TransactionState,
    address: Address,
    f: Callable[[Account], None],
) -> None:
    """
    Modify an ``Account`` in the state. If, after modification, the
    account exists and has zero nonce, empty code, and zero balance, it
    is destroyed.
    """
    set_account(tx_state, address, modify(get_account(tx_state, address), f))
    if account_exists_and_is_empty(tx_state, address):
        destroy_account(tx_state, address)


def move_ether(
    tx_state: TransactionState,
    sender_address: Address,
    recipient_address: Address,
    amount: U256,
) -> None:
    """
    Move funds between accounts.

    Parameters
    ----------
    tx_state :
        The transaction state.
    sender_address :
        Address of the sender.
    recipient_address :
        Address of the recipient.
    amount :
        The amount to transfer.

    """

    def reduce_sender_balance(sender: Account) -> None:
        if sender.balance < amount:
            raise AssertionError
        sender.balance -= amount

    def increase_recipient_balance(recipient: Account) -> None:
        recipient.balance += amount

    modify_state(tx_state, sender_address, reduce_sender_balance)
    modify_state(tx_state, recipient_address, increase_recipient_balance)


def create_ether(
    tx_state: TransactionState, address: Address, amount: U256
) -> None:
    """
    Add newly created ether to an account.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account to which ether is added.
    amount :
        The amount of ether to be added to the account of interest.

    """

    def increase_balance(account: Account) -> None:
        account.balance += amount

    modify_state(tx_state, address, increase_balance)


def set_account_balance(
    tx_state: TransactionState, address: Address, amount: U256
) -> None:
    """
    Set the balance of an account.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account whose balance needs to be set.
    amount :
        The amount that needs to be set in the balance.

    """

    def set_balance(account: Account) -> None:
        account.balance = amount

    modify_state(tx_state, address, set_balance)


def increment_nonce(tx_state: TransactionState, address: Address) -> None:
    """
    Increment the nonce of an account.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account whose nonce needs to be incremented.

    """

    def increase_nonce(sender: Account) -> None:
        sender.nonce += Uint(1)

    modify_state(tx_state, address, increase_nonce)


def set_account_nonce(
    tx_state: TransactionState, address: Address, nonce: Uint
) -> None:
    """Set the nonce of an account."""

    def set_nonce(account: Account) -> None:
        account.nonce = nonce

    modify_state(tx_state, address, set_nonce)


def set_code(
    tx_state: TransactionState, address: Address, code: Bytes
) -> None:
    """
    Set Account code.

    Parameters
    ----------
    tx_state :
        The transaction state.
    address :
        Address of the account whose code needs to be updated.
    code :
        The bytecode that needs to be set.

    """
    code_hash = keccak256(code)
    if code_hash != EMPTY_CODE_HASH:
        tx_state.code_writes[code_hash] = code

    def write_code_hash(sender: Account) -> None:
        sender.code_hash = code_hash

    modify_state(tx_state, address, write_code_hash)


# -- Snapshot / Rollback ---------------------------------------------------


def copy_tx_state(tx_state: TransactionState) -> TransactionState:
    """
    Create a snapshot of the transaction state for rollback.

    Deep-copy writes and transient storage.  The parent reference,
    ``created_accounts``, ``storage_reads``, and ``account_reads``
    are shared (not rolled back).

    Parameters
    ----------
    tx_state :
        The transaction state to snapshot.

    Returns
    -------
    snapshot : ``TransactionState``
        A copy of the transaction state.

    """
    return TransactionState(
        parent=tx_state.parent,
        account_writes=dict(tx_state.account_writes),
        storage_writes={
            addr: dict(slots)
            for addr, slots in tx_state.storage_writes.items()
        },
        code_writes=dict(tx_state.code_writes),
        created_accounts=tx_state.created_accounts,
        transient_storage=dict(tx_state.transient_storage),
        storage_reads=tx_state.storage_reads,
        account_reads=tx_state.account_reads,
    )


def restore_tx_state(
    tx_state: TransactionState, snapshot: TransactionState
) -> None:
    """
    Restore transaction state from a snapshot (rollback on failure).

    Parameters
    ----------
    tx_state :
        The transaction state to restore.
    snapshot :
        The snapshot to restore from.

    """
    tx_state.account_writes = snapshot.account_writes
    tx_state.storage_writes = snapshot.storage_writes
    tx_state.code_writes = snapshot.code_writes
    tx_state.transient_storage = snapshot.transient_storage


# -- Lifecycle --------------------------------------------------------------


def incorporate_tx_into_block(
    tx_state: TransactionState,
    builder: "BlockAccessListBuilder",
) -> None:
    """
    Merge transaction writes into the block state and clear for reuse.

    Update the BAL builder incrementally by diffing this transaction's
    writes against the block's cumulative state.  Merge reads and
    touches into block-level sets.

    Parameters
    ----------
    tx_state :
        The transaction state to commit.
    builder :
        The BAL builder for incremental updates.

    """
    from .block_access_lists import update_builder_from_tx

    block = tx_state.parent

    # Update BAL builder before merging writes into block state
    update_builder_from_tx(builder, tx_state)

    # Merge reads and touches into block-level sets
    block.storage_reads.update(tx_state.storage_reads)
    block.account_reads.update(tx_state.account_reads)

    # Merge cumulative writes
    for address, account in tx_state.account_writes.items():
        block.account_writes[address] = account

    for address, slots in tx_state.storage_writes.items():
        if address not in block.storage_writes:
            block.storage_writes[address] = {}
        block.storage_writes[address].update(slots)

    block.code_writes.update(tx_state.code_writes)

    tx_state.account_writes.clear()
    tx_state.storage_writes.clear()
    tx_state.code_writes.clear()
    tx_state.created_accounts.clear()
    tx_state.transient_storage.clear()
    tx_state.storage_reads = set()
    tx_state.account_reads = set()


def extract_block_diff(block_state: BlockState) -> BlockDiff:
    """
    Extract account, storage, and code diff from the block state.

    Parameters
    ----------
    block_state :
        The block state.

    Returns
    -------
    diff : `BlockDiff`
        Account, storage, and code changes accumulated during block execution.

    """
    return BlockDiff(
        account_changes=block_state.account_writes,
        storage_changes=block_state.storage_writes,
        code_changes=block_state.code_writes,
    )
