"""Tests for the Merkle-Patricia-Trie-backed state."""

from ethereum_types.numeric import U256

from ethereum.state import EMPTY_ACCOUNT, Address
from ethereum.state_mpt import (
    State,
    destroy_storage,
    set_account,
    set_storage,
    state_root,
)

ADDRESS = Address(b"\xaa" * 20)
OTHER_ADDRESS = Address(b"\xbb" * 20)
FIRST_SLOT = U256(1).to_be_bytes32()
SECOND_SLOT = U256(2).to_be_bytes32()


def account_with_storage() -> State:
    """
    Build a state holding one account with two storage slots set.
    """
    state = State()
    set_account(state, ADDRESS, EMPTY_ACCOUNT)
    set_storage(state, ADDRESS, FIRST_SLOT, U256(11))
    set_storage(state, ADDRESS, SECOND_SLOT, U256(22))
    return state


def test_destroy_storage_clears_every_slot() -> None:
    """
    Destroying storage drops all of an account's slots at once, where
    ``set_storage`` could only zero them one by one.
    """
    state = account_with_storage()
    assert state.account_has_storage(ADDRESS)

    destroy_storage(state, ADDRESS)

    assert not state.account_has_storage(ADDRESS)
    assert state.get_storage(ADDRESS, FIRST_SLOT) == U256(0)
    assert state.get_storage(ADDRESS, SECOND_SLOT) == U256(0)


def test_destroy_storage_keeps_the_account() -> None:
    """
    Only the storage trie is dropped; the account it hangs off survives.
    """
    state = account_with_storage()

    destroy_storage(state, ADDRESS)

    assert state.get_account_optional(ADDRESS) == EMPTY_ACCOUNT


def test_destroy_storage_matches_an_account_that_never_had_storage() -> None:
    """
    A destroyed account commits to the empty storage root, so its state
    root is indistinguishable from one that was never written to.
    """
    destroyed = account_with_storage()
    destroy_storage(destroyed, ADDRESS)

    untouched = State()
    set_account(untouched, ADDRESS, EMPTY_ACCOUNT)

    assert state_root(destroyed) == state_root(untouched)


def test_destroy_storage_leaves_other_accounts_alone() -> None:
    """
    Clearing one account's storage does not reach its neighbours.
    """
    state = account_with_storage()
    set_account(state, OTHER_ADDRESS, EMPTY_ACCOUNT)
    set_storage(state, OTHER_ADDRESS, FIRST_SLOT, U256(33))

    destroy_storage(state, ADDRESS)

    assert state.get_storage(OTHER_ADDRESS, FIRST_SLOT) == U256(33)


def test_destroy_storage_of_an_unknown_address_is_a_no_op() -> None:
    """
    Destroying storage that was never there is permitted and changes
    nothing, unlike ``set_storage``, which insists the account exists.
    """
    state = account_with_storage()
    root_before = state_root(state)

    destroy_storage(state, OTHER_ADDRESS)

    assert state_root(state) == root_before
