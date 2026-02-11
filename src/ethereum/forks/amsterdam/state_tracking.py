"""
State Tracking for Block Execution.

Track state changes on top of a read-only ``PreState``.  At block end,
accumulated diffs feed into
``PreState.compute_state_root_and_trie_changes()``.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Replace the mutable ``State`` class with lightweight state trackers that
record diffs.  ``BlockStateTracker`` accumulates committed transaction
changes across a block.  ``TxStateTracker`` tracks in-flight changes
within a single transaction and supports copy-on-write rollback.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import modify
from ethereum_types.numeric import U256, Uint

from ethereum.state import PreState

from .block_access_lists.rlp_types import BlockAccessIndex
from .fork_types import EMPTY_ACCOUNT, Account, Address


@dataclass
class BlockStateTracker:
    """
    Accumulate committed transaction-level changes across a block.

    Read chain: block writes -> pre_state.

    BAL tracking: ``tx_write_history`` saves per-tx raw writes at
    incorporate time.  ``account_reads`` and ``storage_reads``
    accumulate across all transactions.  At block end, the builder
    processes the write history sequentially to produce the Block
    Access List.
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

    # BAL tracking
    block_access_index: BlockAccessIndex = BlockAccessIndex(0)
    tx_write_history: List[
        Tuple[
            BlockAccessIndex,
            Dict[Address, Optional[Account]],
            Dict[Address, Dict[Bytes32, U256]],
        ]
    ] = field(default_factory=list)


@dataclass
class TxStateTracker:
    """
    Track in-flight state changes within a single transaction.

    Read chain: tx writes -> block writes -> pre_state.

    ``storage_reads`` and ``account_reads`` are shared references
    that survive rollback (reads from failed calls still appear in the
    Block Access List).
    """

    parent: BlockStateTracker
    account_reads: Set[Address] = field(default_factory=set)
    account_writes: Dict[Address, Optional[Account]] = field(
        default_factory=dict
    )
    storage_reads: Set[Tuple[Address, Bytes32]] = field(default_factory=set)
    storage_writes: Dict[Address, Dict[Bytes32, U256]] = field(
        default_factory=dict
    )
    created_accounts: Set[Address] = field(default_factory=set)
    transient_storage: Dict[Tuple[Address, Bytes32], U256] = field(
        default_factory=dict
    )


def get_account_optional(
    tracker: TxStateTracker, address: Address
) -> Optional[Account]:
    """
    Get the ``Account`` object at an address. Return ``None`` (rather than
    ``EMPTY_ACCOUNT``) if there is no account at the address.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address to look up.

    Returns
    -------
    account : ``Optional[Account]``
        Account at address.

    """
    if address in tracker.account_writes:
        return tracker.account_writes[address]
    if address in tracker.parent.account_writes:
        return tracker.parent.account_writes[address]
    return tracker.parent.pre_state.get_account_optional(address)


def get_account(tracker: TxStateTracker, address: Address) -> Account:
    """
    Get the ``Account`` object at an address. Return ``EMPTY_ACCOUNT``
    if there is no account at the address.

    Use ``get_account_optional()`` if you care about the difference
    between a non-existent account and ``EMPTY_ACCOUNT``.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address to look up.

    Returns
    -------
    account : ``Account``
        Account at address.

    """
    account = get_account_optional(tracker, address)
    if isinstance(account, Account):
        return account
    else:
        return EMPTY_ACCOUNT


def get_storage(
    tracker: TxStateTracker, address: Address, key: Bytes32
) -> U256:
    """
    Get a value at a storage key on an account. Return ``U256(0)`` if
    the storage key has not been set previously.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account.
    key :
        Key to look up.

    Returns
    -------
    value : ``U256``
        Value at the key.

    """
    if address in tracker.storage_writes:
        if key in tracker.storage_writes[address]:
            return tracker.storage_writes[address][key]
    if address in tracker.parent.storage_writes:
        if key in tracker.parent.storage_writes[address]:
            return tracker.parent.storage_writes[address][key]
    return tracker.parent.pre_state.get_storage(address, key)


def get_storage_original(
    tracker: TxStateTracker, address: Address, key: Bytes32
) -> U256:
    """
    Get the original value in a storage slot i.e. the value before the
    current transaction began. Read from block-level writes, then
    pre_state. Return ``U256(0)`` for accounts created in the current
    transaction.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account to read the value from.
    key :
        Key of the storage slot.

    """
    if address in tracker.created_accounts:
        return U256(0)
    if address in tracker.parent.storage_writes:
        if key in tracker.parent.storage_writes[address]:
            return tracker.parent.storage_writes[address][key]
    return tracker.parent.pre_state.get_storage(address, key)


def get_transient_storage(
    tracker: TxStateTracker, address: Address, key: Bytes32
) -> U256:
    """
    Get a value at a storage key on an account from transient storage.
    Return ``U256(0)`` if the storage key has not been set previously.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account.
    key :
        Key to look up.

    Returns
    -------
    value : ``U256``
        Value at the key.

    """
    return tracker.transient_storage.get((address, key), U256(0))


def account_exists(tracker: TxStateTracker, address: Address) -> bool:
    """
    Check if an account exists in the state trie.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    account_exists : ``bool``
        True if account exists in the state trie, False otherwise.

    """
    return get_account_optional(tracker, address) is not None


def account_has_code_or_nonce(
    tracker: TxStateTracker, address: Address
) -> bool:
    """
    Check if an account has non-zero nonce or non-empty code.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    has_code_or_nonce : ``bool``
        True if the account has non-zero nonce or non-empty code,
        False otherwise.

    """
    account = get_account(tracker, address)
    return account.nonce != Uint(0) or account.code != b""


def account_has_storage(tracker: TxStateTracker, address: Address) -> bool:
    """
    Check if an account has storage.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    has_storage : ``bool``
        True if the account has storage, False otherwise.

    """
    if tracker.storage_writes.get(address):
        return True
    if tracker.parent.storage_writes.get(address):
        return True
    return tracker.parent.pre_state.account_has_storage(address)


def account_exists_and_is_empty(
    tracker: TxStateTracker, address: Address
) -> bool:
    """
    Check if an account exists and has zero nonce, empty code and zero
    balance.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    exists_and_is_empty : ``bool``
        True if an account exists and has zero nonce, empty code and
        zero balance, False otherwise.

    """
    account = get_account_optional(tracker, address)
    return (
        account is not None
        and account.nonce == Uint(0)
        and account.code == b""
        and account.balance == 0
    )


def is_account_alive(tracker: TxStateTracker, address: Address) -> bool:
    """
    Check whether an account is both in the state and non-empty.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account that needs to be checked.

    Returns
    -------
    is_alive : ``bool``
        True if the account is alive.

    """
    account = get_account_optional(tracker, address)
    return account is not None and account != EMPTY_ACCOUNT


def set_account(
    tracker: TxStateTracker,
    address: Address,
    account: Optional[Account],
) -> None:
    """
    Set the ``Account`` object at an address. Setting to ``None``
    deletes the account (but not its storage, see
    ``destroy_account()``).

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address to set.
    account :
        Account to set at address.

    """
    tracker.account_writes[address] = account


def set_storage(
    tracker: TxStateTracker,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """
    Set a value at a storage key on an account.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account.
    key :
        Key to set.
    value :
        Value to set at the key.

    """
    assert get_account_optional(tracker, address) is not None
    if address not in tracker.storage_writes:
        tracker.storage_writes[address] = {}
    tracker.storage_writes[address][key] = value


def destroy_account(tracker: TxStateTracker, address: Address) -> None:
    """
    Completely remove the account at ``address`` and all of its storage.

    This function is made available exclusively for the ``SELFDESTRUCT``
    opcode. It is expected that ``SELFDESTRUCT`` will be disabled in a
    future hardfork and this function will be removed.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of account to destroy.

    """
    destroy_storage(tracker, address)
    set_account(tracker, address, None)


def destroy_storage(tracker: TxStateTracker, address: Address) -> None:
    """
    Completely remove the storage at ``address``.

    Convert storage writes to reads before deleting so that accesses
    from created-then-destroyed accounts appear in the Block Access
    List.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of account whose storage is to be deleted.

    """
    if address in tracker.storage_writes:
        for key in tracker.storage_writes[address]:
            tracker.storage_reads.add((address, key))
        del tracker.storage_writes[address]


def mark_account_created(tracker: TxStateTracker, address: Address) -> None:
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
    tracker :
        The transaction state tracker.
    address :
        Address of the account that has been created.

    """
    tracker.created_accounts.add(address)


def set_transient_storage(
    tracker: TxStateTracker,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """
    Set a value at a storage key on an account in transient storage.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account.
    key :
        Key to set.
    value :
        Value to set at the key.

    """
    if value == U256(0):
        tracker.transient_storage.pop((address, key), None)
    else:
        tracker.transient_storage[(address, key)] = value


def modify_state(
    tracker: TxStateTracker,
    address: Address,
    f: Callable[[Account], None],
) -> None:
    """
    Modify an ``Account`` in the state. If, after modification, the
    account exists and has zero nonce, empty code, and zero balance, it
    is destroyed.
    """
    set_account(tracker, address, modify(get_account(tracker, address), f))
    if account_exists_and_is_empty(tracker, address):
        destroy_account(tracker, address)


def move_ether(
    tracker: TxStateTracker,
    sender_address: Address,
    recipient_address: Address,
    amount: U256,
) -> None:
    """
    Move funds between accounts.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
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

    modify_state(tracker, sender_address, reduce_sender_balance)
    modify_state(tracker, recipient_address, increase_recipient_balance)


def set_account_balance(
    tracker: TxStateTracker, address: Address, amount: U256
) -> None:
    """
    Set the balance of an account.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account whose balance needs to be set.
    amount :
        The amount that needs to be set in the balance.

    """

    def set_balance(account: Account) -> None:
        account.balance = amount

    modify_state(tracker, address, set_balance)


def increment_nonce(tracker: TxStateTracker, address: Address) -> None:
    """
    Increment the nonce of an account.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account whose nonce needs to be incremented.

    """

    def increase_nonce(sender: Account) -> None:
        sender.nonce += Uint(1)

    modify_state(tracker, address, increase_nonce)


def set_code(tracker: TxStateTracker, address: Address, code: Bytes) -> None:
    """
    Set Account code.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the account whose code needs to be updated.
    code :
        The bytecode that needs to be set.

    """

    def write_code(sender: Account) -> None:
        sender.code = code

    modify_state(tracker, address, write_code)


def set_authority_code(
    tracker: TxStateTracker, address: Address, code: Bytes
) -> None:
    """
    Set authority account code for EIP-7702 delegation.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        Address of the authority account whose code needs to be set.
    code :
        The delegation designation bytecode to set.

    """

    def write_code(sender: Account) -> None:
        sender.code = code

    modify_state(tracker, address, write_code)


# -- Snapshot / Rollback ---------------------------------------------------


def copy_tx_state_tracker(tracker: TxStateTracker) -> TxStateTracker:
    """
    Create a snapshot of the transaction state tracker for rollback.

    Deep-copy writes and transient storage.  The parent reference,
    ``created_accounts``, ``storage_reads``, and ``account_reads``
    are shared (not rolled back).

    Parameters
    ----------
    tracker :
        The transaction state tracker to snapshot.

    Returns
    -------
    snapshot : ``TxStateTracker``
        A copy of the tracker state.

    """
    return TxStateTracker(
        parent=tracker.parent,
        account_writes=dict(tracker.account_writes),
        storage_writes={
            addr: dict(slots) for addr, slots in tracker.storage_writes.items()
        },
        created_accounts=tracker.created_accounts,
        transient_storage=dict(tracker.transient_storage),
        storage_reads=tracker.storage_reads,
        account_reads=tracker.account_reads,
    )


def restore_tx_state_tracker(
    tracker: TxStateTracker, snapshot: TxStateTracker
) -> None:
    """
    Restore tracker state from a snapshot (rollback on failure).

    Parameters
    ----------
    tracker :
        The transaction state tracker to restore.
    snapshot :
        The snapshot to restore from.

    """
    tracker.account_writes = snapshot.account_writes
    tracker.storage_writes = snapshot.storage_writes
    tracker.transient_storage = snapshot.transient_storage


# -- Lifecycle --------------------------------------------------------------


def incorporate_tx_into_block(tracker: TxStateTracker) -> None:
    """
    Merge transaction writes into the block tracker and clear for reuse.

    Save per-tx write snapshots into ``tx_write_history`` for BAL
    generation at block end.  Merge reads and touches into block-level
    sets.

    Parameters
    ----------
    tracker :
        The transaction state tracker to commit.

    """
    block = tracker.parent

    # Save per-tx write snapshot for BAL generation
    block.tx_write_history.append(
        (
            block.block_access_index,
            dict(tracker.account_writes),
            {
                addr: dict(slots)
                for addr, slots in tracker.storage_writes.items()
            },
        )
    )

    # Merge reads and touches into block-level sets
    block.storage_reads.update(tracker.storage_reads)
    block.account_reads.update(tracker.account_reads)

    # Merge cumulative writes
    for address, account in tracker.account_writes.items():
        block.account_writes[address] = account

    for address, slots in tracker.storage_writes.items():
        if address not in block.storage_writes:
            block.storage_writes[address] = {}
        block.storage_writes[address].update(slots)

    tracker.account_writes.clear()
    tracker.storage_writes.clear()
    tracker.created_accounts.clear()
    tracker.transient_storage.clear()
    tracker.storage_reads = set()
    tracker.account_reads = set()


def extract_block_diffs(
    block_tracker: BlockStateTracker,
) -> Tuple[
    Dict[Address, Optional[Account]],
    Dict[Address, Dict[Bytes32, U256]],
]:
    """
    Extract account and storage diffs from the block tracker.

    Parameters
    ----------
    block_tracker :
        The block state tracker.

    Returns
    -------
    account_diffs :
        Account changes to apply.
    storage_diffs :
        Storage changes to apply.

    """
    return block_tracker.account_writes, block_tracker.storage_writes


# -- BAL Tracking -----------------------------------------------------------


def track_address(tracker: TxStateTracker, address: Address) -> None:
    """
    Record that an address was accessed.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        The address that was accessed.

    """
    tracker.account_reads.add(address)


def track_storage_read(
    tracker: TxStateTracker, address: Address, key: Bytes32
) -> None:
    """
    Record a storage read operation.

    Parameters
    ----------
    tracker :
        The transaction state tracker.
    address :
        The address whose storage was read.
    key :
        The storage key that was read.

    """
    tracker.storage_reads.add((address, key))


def increment_block_access_index(
    block_tracker: BlockStateTracker,
) -> None:
    """
    Increment the block access index.

    Parameters
    ----------
    block_tracker :
        The block state tracker.

    """
    block_tracker.block_access_index = BlockAccessIndex(
        block_tracker.block_access_index + Uint(1)
    )
