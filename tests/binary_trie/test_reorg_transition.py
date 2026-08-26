"""
Reorg coverage for the EIP-8297 MPT -> PBT state-tree flip.

The activation block is the first block whose post-state is committed by the
PBT; its parent is still MPT-committed. EIP-8347 therefore requires both trees
to remain available through the transition window so an unfinalized reorg can
cross the boundary safely.

These tests pin the reference-state invariant directly: advancing a PBT branch
must not consume or mutate the retained MPT parent, and post-flip branches must
be discardable back to a common PBT parent rather than "undone" in place.
"""

from ethereum_types.bytes import Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.state import EMPTY_CODE_HASH, Account, BlockDiff
from ethereum.state_mpt import State as MptState
from ethereum.state_mpt import set_account as mpt_set_account
from ethereum.state_mpt import set_storage as mpt_set_storage
from ethereum.state_mpt import state_root as mpt_state_root
from ethereum.state_pbt import State as PbtState
from ethereum.state_pbt import apply_changes_to_state as pbt_apply_changes
from ethereum.state_pbt import state_root as pbt_state_root

from .transition import pbt_from_mpt_snapshot

ADDRESS = Bytes20(b"\xaa" * 20)
SLOT = Bytes32((1).to_bytes(32, "big"))


def _account() -> Account:
    """Return a small live account used on both sides of the flip."""
    return Account(
        nonce=Uint(0),
        balance=U256(1_000),
        code_hash=EMPTY_CODE_HASH,
    )


def _mpt_parent() -> MptState:
    """Build the last MPT-committed state before PBT activation."""
    state = MptState()
    mpt_set_account(state, ADDRESS, _account())
    mpt_set_storage(state, ADDRESS, SLOT, U256(1))
    return state


def _copy_pbt_state(state: PbtState) -> PbtState:
    """Copy a PBT layer so sibling branches share no mutable mappings."""
    return PbtState(
        _accounts=dict(state._accounts),
        _storage={
            address: dict(slots) for address, slots in state._storage.items()
        },
        _code_store=dict(state._code_store),
    )


def _storage_write(value: int) -> BlockDiff:
    """Return a block diff that writes the test slot."""
    return BlockDiff(storage_changes={ADDRESS: {SLOT: U256(value)}})


def test_reorg_across_activation_retains_mpt_parent() -> None:
    """
    Discard a PBT activation branch and rebuild from the MPT parent.

    Branch A crosses the activation boundary and advances the new tree. A
    reorg then selects a competing activation block. The safe operation is to
    discard A and construct branch B from the still-retained MPT parent; no
    reverse write against the PBT is required and the MPT commitment remains
    byte-identical throughout.
    """
    mpt_parent = _mpt_parent()
    parent_root = mpt_state_root(mpt_parent)

    branch_a = pbt_from_mpt_snapshot(mpt_parent)
    activation_root = pbt_state_root(branch_a)
    pbt_apply_changes(branch_a, _storage_write(2))
    branch_a_root = pbt_state_root(branch_a)

    # Crossing into PBT and advancing it must not consume the MPT parent.
    assert mpt_state_root(mpt_parent) == parent_root
    assert mpt_parent.get_storage(ADDRESS, SLOT) == U256(1)

    # Reorg across the flip: throw away branch A and re-cross activation from
    # the retained MPT parent with a competing block.
    branch_b = pbt_from_mpt_snapshot(mpt_parent)
    assert pbt_state_root(branch_b) == activation_root
    pbt_apply_changes(branch_b, _storage_write(3))
    branch_b_root = pbt_state_root(branch_b)

    assert branch_a_root != branch_b_root
    assert branch_a.get_storage(ADDRESS, SLOT) == U256(2)
    assert branch_b.get_storage(ADDRESS, SLOT) == U256(3)
    assert mpt_state_root(mpt_parent) == parent_root


def test_post_flip_reorg_discards_pbt_branch_layers() -> None:
    """
    Reorg between two PBT branches without mutating their common parent.

    EIP-8347 records post-values rather than reversible writes, so rollback is
    modeled by discarding branch layers to the common ancestor and replaying
    the replacement branch. Both siblings start from an identical copied PBT
    parent and diverge independently.
    """
    common_parent = pbt_from_mpt_snapshot(_mpt_parent())
    pbt_apply_changes(common_parent, _storage_write(4))
    common_root = pbt_state_root(common_parent)

    branch_a = _copy_pbt_state(common_parent)
    branch_b = _copy_pbt_state(common_parent)

    pbt_apply_changes(branch_a, _storage_write(5))
    pbt_apply_changes(branch_b, _storage_write(6))

    assert pbt_state_root(common_parent) == common_root
    assert common_parent.get_storage(ADDRESS, SLOT) == U256(4)
    assert pbt_state_root(branch_a) != pbt_state_root(branch_b)
    assert branch_a.get_storage(ADDRESS, SLOT) == U256(5)
    assert branch_b.get_storage(ADDRESS, SLOT) == U256(6)
