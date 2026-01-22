"""
State Tracker.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import modify
from ethereum_types.numeric import U256, Uint

from . import state as state_
from .fork_types import EMPTY_ACCOUNT, Account, Address
from .state import State

BlockAccessIndex = Uint


@dataclass
class BlockStateTracking:
    """
    Tracking of state changes at the block level.
    """

    parent: State
    current_index: BlockAccessIndex

    account_reads: Set[Address]
    storage_reads: Set[Tuple[Address, Bytes32]]

    account_writes: Dict[
        Address, List[Tuple[BlockAccessIndex, Optional[Account]]]
    ]
    storage_writes: Dict[
        Address, Dict[Bytes32, List[Tuple[BlockAccessIndex, U256]]]
    ]


@dataclass
class TxStateTracking:
    """
    Tracking of state changes within a transaction.
    """

    parent: BlockStateTracking

    account_reads: Set[Address]
    storage_reads: Set[Tuple[Address, Bytes32]]

    account_writes: Dict[Address, Optional[Account]]
    storage_writes: Dict[Address, Dict[Bytes32, U256]]

    created_accounts: Set[Address]


# get_account_optional
# set_account
# get_storage
# set_storage
# mark_account_created
# destroy_storage


def get_account_optional(
    state: TxStateTracking | BlockStateTracking, address: Address
) -> Optional[Account]:
    """FIXME."""
    if isinstance(state, TxStateTracking):
        if address in state.account_writes:
            return state.account_writes[address]
        else:
            return get_account_optional(state.parent, address)
    elif isinstance(state, BlockStateTracking):
        if address in state.account_writes:
            return state.account_writes[address][-1][1]
        else:
            return state_.get_account_optional(state.parent, address)


def set_account(
    state: TxStateTracking | BlockStateTracking,
    address: Address,
    account: Optional[Account],
) -> None:
    """FIXME."""
    if isinstance(state, TxStateTracking):
        state.account_writes[address] = account
    elif isinstance(state, BlockStateTracking):
        writes = state.account_writes.get(address, [])
        if writes == [] or writes[-1][0] < state.current_index:
            writes.append((state.current_index, account))
        else:
            writes[-1] = (state.current_index, account)
        state.account_writes[address] = writes


def get_storage(
    state: TxStateTracking | BlockStateTracking, address: Address, key: Bytes32
) -> U256:
    """FIXME."""
    if isinstance(state, TxStateTracking):
        if key in state.storage_writes.get(address, {}):
            return state.storage_writes[address][key]
        else:
            return get_storage(state.parent, address, key)
    elif isinstance(state, BlockStateTracking):
        writes = state.storage_writes.get(address, {}).get(key, [])
        if writes == []:
            return state_.get_storage(state.parent, address, key)
        else:
            return writes[-1][1]


def set_storage(
    state: TxStateTracking | BlockStateTracking,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """FIXME."""
    if isinstance(state, TxStateTracking):
        if address not in state.storage_writes:
            state.storage_writes[address] = {}
        state.storage_writes[address][key] = value
    elif isinstance(state, BlockStateTracking):
        writes = state.storage_writes.get(address, {}).get(key, [])
        if writes == [] or writes[-1][0] < state.current_index:
            writes.append((state.current_index, value))
        else:
            writes[-1] = (state.current_index, value)
        if address not in state.storage_writes:
            state.storage_writes[address] = {}
        state.storage_writes[address][key] = writes


def destroy_storage(state: TxStateTracking, address: Address) -> None:
    """FIXME."""
    if address in state.storage_writes:
        del state.storage_writes[address]


def bump_index(state: BlockStateTracking) -> None:
    """FIXME."""
    state.current_index += Uint(1)


def mark_account_created(state: TxStateTracking, address: Address) -> None:
    """FIXME."""
    state.created_accounts.add(address)


def incorporate_tx_state_into_parent(tx_state: TxStateTracking) -> None:
    """
    After a transaction has finished, write the final state changes to the
    parent.
    """
    parent = tx_state.parent
    parent.account_reads |= tx_state.account_reads
    parent.storage_reads |= tx_state.storage_reads
    for address, account in tx_state.account_writes.items():
        set_account(parent, address, account)
    for address, items in tx_state.storage_writes.items():
        for key, value in items.items():
            set_storage(parent, address, key, value)


def write_block_state_changes(block_state: BlockStateTracking) -> None:
    """
    At the end of the block. Write the final state changes to the state object.

    This is a temporary arrangement, until a future refactor abolishes the
    state.
    """
    parent = block_state.parent
    for address, writes in block_state.account_writes.items():
        state_.set_account(parent, address, writes[-1][1])
    for address, items in block_state.storage_writes.items():
        for key, writes_ in items.items():
            state_.set_storage(parent, address, key, writes_[-1][1])


def copy_tx_state_tracking(tx_state: TxStateTracking) -> TxStateTracking:
    """
    Copy a `TxStateTracking`.
    """
    new_storage_writes = {}
    for key, value in tx_state.storage_writes.items():
        new_storage_writes[key] = value.copy()
    return TxStateTracking(
        parent=tx_state.parent,
        account_reads=tx_state.account_reads.copy(),
        storage_reads=tx_state.storage_reads.copy(),
        account_writes=tx_state.account_writes.copy(),
        storage_writes=new_storage_writes,
        created_accounts=tx_state.created_accounts.copy(),
    )


####


def get_account(
    state: TxStateTracking | BlockStateTracking, address: Address
) -> Account:
    """
    Get the `Account` object at an address. Returns `EMPTY_ACCOUNT` if there
    is no account at the address.

    Use `get_account_optional()` if you care about the difference between a
    non-existent account and `EMPTY_ACCOUNT`.

    Parameters
    ----------
    state: `TxStateTracking | BlockStateTracking`
        The state
    address : `Address`
        Address to lookup.

    Returns
    -------
    account : `Account`
        Account at address.

    """
    account = get_account_optional(state, address)
    if isinstance(account, Account):
        return account
    else:
        return EMPTY_ACCOUNT


def destroy_account(state: TxStateTracking, address: Address) -> None:
    """
    Completely remove the account at `address` and all of its storage.

    This function is made available exclusively for the `SELFDESTRUCT`
    opcode. It is expected that `SELFDESTRUCT` will be disabled in a future
    hardfork and this function will be removed.

    Parameters
    ----------
    state: `TxStateTracking | BlockStateTracking`
        The state
    address : `Address`
        Address of account to destroy.

    """
    destroy_storage(state, address)
    set_account(state, address, None)


def account_exists(
    state: TxStateTracking | BlockStateTracking, address: Address
) -> bool:
    """
    Checks if an account exists in the state trie.

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    account_exists : `bool`
        True if account exists in the state trie, False otherwise

    """
    return get_account_optional(state, address) is not None


def account_has_code_or_nonce(
    state: TxStateTracking | BlockStateTracking, address: Address
) -> bool:
    """
    Checks if an account has non zero nonce or non empty code.

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    has_code_or_nonce : `bool`
        True if the account has non zero nonce or non empty code,
        False otherwise.

    """
    account = get_account(state, address)
    return account.nonce != Uint(0) or account.code != b""


def account_exists_and_is_empty(
    state: TxStateTracking | BlockStateTracking, address: Address
) -> bool:
    """
    Checks if an account exists and has zero nonce, empty code and zero
    balance.

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    exists_and_is_empty : `bool`
        True if an account exists and has zero nonce, empty code and zero
        balance, False otherwise.

    """
    account = get_account_optional(state, address)
    return (
        account is not None
        and account.nonce == Uint(0)
        and account.code == b""
        and account.balance == 0
    )


def is_account_alive(
    state: TxStateTracking | BlockStateTracking, address: Address
) -> bool:
    """
    Check whether an account is both in the state and non-empty.

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    is_alive : `bool`
        True if the account is alive.

    """
    account = get_account_optional(state, address)
    return account is not None and account != EMPTY_ACCOUNT


def modify_state(
    state: TxStateTracking | BlockStateTracking,
    address: Address,
    f: Callable[[Account], None],
) -> None:
    """
    Modify an `Account` in the `State`. If, after modification, the account
    exists and has zero nonce, empty code, and zero balance, it is destroyed.
    """
    new_account = modify(get_account(state, address), f)

    account_exists_and_is_empty = (
        new_account is not None
        and new_account.nonce == Uint(0)
        and new_account.code == b""
        and new_account.balance == 0
    )

    if account_exists_and_is_empty:
        set_account(state, address, None)
    else:
        set_account(state, address, new_account)


def move_ether(
    state: TxStateTracking | BlockStateTracking,
    sender_address: Address,
    recipient_address: Address,
    amount: U256,
) -> None:
    """
    Move funds between accounts.
    """

    def reduce_sender_balance(sender: Account) -> None:
        if sender.balance < amount:
            raise AssertionError
        sender.balance -= amount

    def increase_recipient_balance(recipient: Account) -> None:
        recipient.balance += amount

    modify_state(state, sender_address, reduce_sender_balance)
    modify_state(state, recipient_address, increase_recipient_balance)


def set_account_balance(
    state: TxStateTracking | BlockStateTracking, address: Address, amount: U256
) -> None:
    """
    Sets the balance of an account.

    Parameters
    ----------
    state:
        The current state.

    address:
        Address of the account whose nonce needs to be incremented.

    amount:
        The amount that needs to set in balance.

    """

    def set_balance(account: Account) -> None:
        account.balance = amount

    modify_state(state, address, set_balance)


def increment_nonce(
    state: TxStateTracking | BlockStateTracking, address: Address
) -> None:
    """
    Increments the nonce of an account.

    Parameters
    ----------
    state:
        The current state.

    address:
        Address of the account whose nonce needs to be incremented.

    """

    def increase_nonce(sender: Account) -> None:
        sender.nonce += Uint(1)

    modify_state(state, address, increase_nonce)


def set_code(
    state: TxStateTracking | BlockStateTracking, address: Address, code: Bytes
) -> None:
    """
    Sets Account code.

    Parameters
    ----------
    state:
        The current state.

    address:
        Address of the account whose code needs to be update.

    code:
        The bytecode that needs to be set.

    """

    def write_code(sender: Account) -> None:
        sender.code = code

    modify_state(state, address, write_code)


def set_authority_code(
    state: TxStateTracking | BlockStateTracking, address: Address, code: Bytes
) -> None:
    """
    Sets authority account code for EIP-7702 delegation.

    This function is used specifically for setting authority code within
    EIP-7702 Set Code Transactions.

    Parameters
    ----------
    state:
        The current state.

    address:
        Address of the authority account whose code needs to be set.

    code:
        The delegation designation bytecode to set.

    """

    def write_code(sender: Account) -> None:
        sender.code = code

    modify_state(state, address, write_code)


def get_storage_original(
    state: TxStateTracking, address: Address, key: Bytes32
) -> U256:
    """
    Get the original value in a storage slot i.e. the value before the current
    transaction began. This function reads the value from the snapshots taken
    before executing the transaction.

    Parameters
    ----------
    state:
        The current state.
    address:
        Address of the account to read the value from.
    key:
        Key of the storage slot.

    """
    # In the transaction where an account is created, its preexisting storage
    # is ignored.
    if address in state.created_accounts:
        return U256(0)

    return get_storage(state.parent, address, key)
