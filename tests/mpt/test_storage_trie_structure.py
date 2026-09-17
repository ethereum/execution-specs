"""
Exercise the Merkle Patricia Trie as a data structure via storage slots.

Storage trie keys are `keccak256(slot)`: fixed 64 nibbles, so no key is a
prefix of another and a branch never carries a value. Within that
constraint, mined slot indices (`constants.py`) force the shapes an
unconstrained slot choice essentially never produces: branch arity,
extension length, and the branch/extension collapse that only happens on
delete. Each test asserts the shape it claims against the reference
`patricialize` (`trie_shape.py`) at fill time; the state root each block
commits is the cross-client oracle.

Pinned to the latest deployed fork so every client consumes one identical
fixture set; MPT rules are fork-invariant.
"""

from typing import List, Sequence, Tuple

import pytest
from ethereum_rlp import rlp
from ethereum_types.numeric import U256
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.base_types import StorageRootType

from ethereum.merkle_patricia_trie import nibble_list_to_compact

from .constants import (
    BRANCH_SURVIVOR_TRIO,
    EMBEDDED_LEAF_PAIR,
    EXT_MERGE_TRIO,
    HASHED_LEAF_PAIR,
    ROOT_PAIR,
    SINGLE_SLOT,
    SINGLE_SLOT_SIBLING_DEPTH1,
    SINGLE_SLOT_SIBLING_DEPTH2,
    SIXTEEN_SLOTS_BRANCH4,
    TWO_SLOTS_EXT4,
    TWO_SLOTS_EXT4_SIBLING_DEPTH1,
)
from .trie_shape import Shape, path_shape, slot_key

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")

# Writes `calldata[0:32]` -> `calldata[32:64]`; one transaction per slot
# lets multi-block tests commit each mutation separately.
SLOT_WRITER = Op.SSTORE(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)) + Op.STOP


def _writer_code(pairs: List[Tuple[int, int]]) -> Bytecode:
    """Return code that `SSTORE`s each `(slot, value)` pair, in order."""
    code = Bytecode()
    for slot, value in pairs:
        code += Op.SSTORE(slot, value)
    return code + Op.STOP


def _write(
    sender: EOA, contract: Address, slot: int, value: int
) -> Transaction:
    """One `SLOT_WRITER` call setting `slot` to `value`."""
    return Transaction(
        sender=sender,
        to=contract,
        data=slot.to_bytes(32, "big") + value.to_bytes(32, "big"),
    )


def _shape(slots: Sequence[int], target: int) -> Shape:
    return path_shape([slot_key(s) for s in slots], slot_key(target))


def _leaf_rlp_size(rest_nibbles: int, value: int) -> int:
    """RLP size of a storage leaf with `rest_nibbles` left and `value`."""
    compact = nibble_list_to_compact(bytes([0] * rest_nibbles), True)
    return len(rlp.encode((compact, rlp.encode(U256(value)))))


# --- inserts -----------------------------------------------------------


def test_insert_leaf_into_empty_trie(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """A single `SSTORE` into an empty storage trie creates one leaf."""
    assert _shape([SINGLE_SLOT], SINGLE_SLOT) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(code=_writer_code([(SINGLE_SLOT, 1)]))

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={SINGLE_SLOT: 1})},
    )


def test_update_existing_leaf(state_test: StateTestFiller, pre: Alloc) -> None:
    """Overwriting an existing slot changes its value, not the trie shape."""
    contract = pre.deploy_contract(
        code=_writer_code([(SINGLE_SLOT, 2)]),
        storage={SINGLE_SLOT: 1},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={SINGLE_SLOT: 2})},
    )


def test_insert_splits_into_extension_and_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """Two slots sharing 4 nibbles build ext(4) -> branch -> 2 leaves."""
    a, b = TWO_SLOTS_EXT4
    assert _shape([a, b], a) == [
        (0, "ext", 4),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    contract = pre.deploy_contract(code=_writer_code([(a, 1), (b, 2)]))

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, b: 2})},
    )


def test_insert_pair_sharing_one_nibble(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Pre: empty storage trie.
    Op: write two slots whose hashed keys share exactly one nibble.
    Post: ext(1) -> branch@1 -> two 62-nibble leaves; the shortest
    extension a leaf split can create.
    Exercises: leaf split with a one-nibble common prefix (geth
    `Trie.insert`, shortNode case with `matchlen == 1`), as opposed to
    the four-nibble split of `test_insert_splits_into_extension_and_branch`
    and the prefix-free split of `ROOT_PAIR`.
    """
    a, b = SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1
    assert _shape([a, b], a) == [
        (0, "ext", 1),
        (1, "branch", 2),
        (2, "leaf", 62),
    ]
    contract = pre.deploy_contract(code=_writer_code([(a, 1), (b, 2)]))

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, b: 2})},
    )


def test_insert_into_committed_extension(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Inserting a key that diverges inside a committed 5-nibble extension
    splits it: ext(2) -> branch -> {new leaf, ext(2) -> branch -> 2 leaves}.
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    assert _shape([l1, l2], l1) == [
        (0, "ext", 5),
        (5, "branch", 2),
        (6, "leaf", 58),
    ]
    assert _shape([l1, l2, l3], l1) == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "ext", 2),
        (5, "branch", 2),
        (6, "leaf", 58),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(l3, 3)]), storage={l1: 1, l2: 2}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={l1: 1, l2: 2, l3: 3})},
    )


@pytest.mark.parametrize(
    "new_slot,post_shape",
    [
        pytest.param(
            SINGLE_SLOT_SIBLING_DEPTH2,
            [
                (0, "branch", 2),
                (1, "ext", 1),
                (2, "branch", 2),
                (3, "leaf", 61),
            ],
            id="ext_then_branch",
        ),
        pytest.param(
            SINGLE_SLOT_SIBLING_DEPTH1,
            [(0, "branch", 2), (1, "branch", 2), (2, "leaf", 62)],
            id="branch_direct",
        ),
    ],
)
def test_insert_splits_below_root_branch(
    state_test: StateTestFiller,
    pre: Alloc,
    new_slot: int,
    post_shape: Shape,
) -> None:
    """
    Pre: ROOT_PAIR committed as a root branch with two direct leaves.
    Op: write a slot that shares the first nibble with ROOT_PAIR[0].
    Post: the root branch keeps both slots; the leaf in the shared slot is
    split in place, into ext(1) -> branch@2 when the new key shares two
    nibbles, or into a branch@1 directly when it shares only the first.
    Exercises: a split whose result is re-parented into an existing branch
    slot instead of becoming the root (geth `Trie.insert` fullNode case
    recursing into a shortNode).
    """
    a, b = ROOT_PAIR
    assert _shape([a, b], a) == [(0, "branch", 2), (1, "leaf", 63)]
    assert _shape([a, b, new_slot], a) == post_shape
    assert _shape([a, b, new_slot], b) == [(0, "branch", 2), (1, "leaf", 63)]
    contract = pre.deploy_contract(
        code=_writer_code([(new_slot, 3)]), storage={a: 1, b: 2}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, b: 2, new_slot: 3})},
    )


@pytest.mark.parametrize(
    "committed,new_slot,pre_shape,post_shape",
    [
        pytest.param(
            TWO_SLOTS_EXT4,
            SINGLE_SLOT,
            [(0, "ext", 4), (4, "branch", 2), (5, "leaf", 59)],
            [
                (0, "branch", 2),
                (1, "ext", 3),
                (4, "branch", 2),
                (5, "leaf", 59),
            ],
            id="ext4_shortened_to_ext3",
        ),
        pytest.param(
            (SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1),
            ROOT_PAIR[1],
            [(0, "ext", 1), (1, "branch", 2), (2, "leaf", 62)],
            [(0, "branch", 2), (1, "branch", 2), (2, "leaf", 62)],
            id="ext1_vanishes",
        ),
    ],
)
def test_insert_diverges_at_extension_first_nibble(
    state_test: StateTestFiller,
    pre: Alloc,
    committed: Sequence[int],
    new_slot: int,
    pre_shape: Shape,
    post_shape: Shape,
) -> None:
    """
    Pre: a pair whose root is an extension (4 nibbles, or a single one).
    Op: write a slot whose hashed key differs from the pair in nibble 0.
    Post: the root becomes a branch. A 4-nibble extension survives one
    nibble shorter as the branch child; a 1-nibble extension disappears
    and its branch becomes the child directly, no ext(0) is created.
    Exercises: extension split at offset 0 (geth `Trie.insert` shortNode
    case with `matchlen == 0`), including the zero-length remainder path
    that returns the child node instead of building a shortNode.
    """
    target = committed[0]
    assert _shape(committed, target) == pre_shape
    assert _shape([*committed, new_slot], target) == post_shape
    assert _shape([*committed, new_slot], new_slot) == [
        (0, "branch", 2),
        (1, "leaf", 63),
    ]
    storage: StorageRootType = {s: i + 1 for i, s in enumerate(committed)}
    contract = pre.deploy_contract(
        code=_writer_code([(new_slot, 3)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={**storage, new_slot: 3})},
    )


def test_insert_full_branch_arity_sixteen(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """Sixteen slots sharing 4 nibbles fill every child of one branch."""
    slots = SIXTEEN_SLOTS_BRANCH4
    assert _shape(slots, slots[0]) == [
        (0, "ext", 4),
        (4, "branch", 16),
        (5, "leaf", 59),
    ]
    pairs = [(slot, i + 1) for i, slot in enumerate(slots)]
    contract = pre.deploy_contract(code=_writer_code(pairs))

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage=dict(pairs))},
    )


@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reversed"])
def test_insert_full_branch_across_blocks(
    blockchain_test: BlockchainTestFiller, pre: Alloc, reverse: bool
) -> None:
    """
    Build the 16-way branch across two blocks, one slot per transaction,
    so the second half is inserted into an already-committed branch. The
    two orderings must reach the same root; only across a block boundary
    is insertion order observable by an incremental trie.
    """
    slots = list(SIXTEEN_SLOTS_BRANCH4)
    if reverse:
        slots.reverse()
    values = {slot: i + 1 for i, slot in enumerate(SIXTEEN_SLOTS_BRANCH4)}
    contract = pre.deploy_contract(code=SLOT_WRITER)
    sender = pre.fund_eoa()
    first, second = slots[:8], slots[8:]

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=values)},
        blocks=[
            Block(
                txs=[_write(sender, contract, s, values[s]) for s in first],
                expected_post_state={
                    contract: Account(storage={s: values[s] for s in first})
                },
            ),
            Block(
                txs=[_write(sender, contract, s, values[s]) for s in second]
            ),
        ],
    )


# --- deletes against a genesis-committed trie -------------------------


def test_delete_via_zero_value(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """`SSTORE(slot, 0)` removes the slot: the trie is empty afterwards."""
    contract = pre.deploy_contract(
        code=_writer_code([(SINGLE_SLOT, 0)]),
        storage={SINGLE_SLOT: 1},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={})},
    )


def test_delete_missing_through_extension(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Zeroing a key that diverges inside a committed extension is a no-op:
    the walk must reject the extension mismatch without touching nodes.
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    assert _shape([l1, l2], l1)[0] == (0, "ext", 5)
    contract = pre.deploy_contract(
        code=_writer_code([(l3, 0)]), storage={l1: 1, l2: 2}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={l1: 1, l2: 2})},
    )


def test_delete_missing_into_empty_branch_slot(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """Zeroing a key whose branch child slot is empty is a no-op."""
    present, absent = SIXTEEN_SLOTS_BRANCH4[:15], SIXTEEN_SLOTS_BRANCH4[15]
    assert _shape(present, present[0])[1] == (4, "branch", 15)
    storage: StorageRootType = {slot: i + 1 for i, slot in enumerate(present)}
    contract = pre.deploy_contract(
        code=_writer_code([(absent, 0)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage=storage)},
    )


def test_delete_absent_key_ending_at_other_leaf(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Pre: a single committed leaf for SINGLE_SLOT (the root itself).
    Op: zero ROOT_PAIR[1], whose hashed key diverges from the leaf's path
    at nibble 0.
    Post: unchanged; the root is still the same 64-nibble leaf.
    Exercises: delete-missing whose walk ends at a leaf with a different
    path, the third no-op shape after the extension mismatch and the empty
    branch slot. geth and Nethermind take the shared shortNode mismatch
    path; Besu's `RemoveVisitor` has a leaf-specific visit.
    """
    present, absent = SINGLE_SLOT, ROOT_PAIR[1]
    assert _shape([present], present) == [(0, "leaf", 64)]
    assert _shape([present, absent], present)[0] == (0, "branch", 2)
    contract = pre.deploy_contract(
        code=_writer_code([(absent, 0)]), storage={present: 1}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={present: 1})},
    )


def test_delete_collapses_branch_into_leaf(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Deleting one of two siblings under ext(4) -> branch collapses the
    branch and extension into a single leaf.
    """
    a, b = TWO_SLOTS_EXT4
    assert _shape([b], b) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(
        code=_writer_code([(a, 0)]), storage={a: 1, b: 2}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={b: 2})},
    )


def test_delete_merges_adjacent_extensions(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Deleting the shallow sibling of ext(2) -> branch -> {leaf, ext(2) ->
    branch} leaves the outer branch with one child; it collapses and the
    two extensions merge into ext(5).
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    assert _shape([l1, l2, l3], l1)[:3] == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "ext", 2),
    ]
    assert _shape([l1, l2], l1)[0] == (0, "ext", 5)
    contract = pre.deploy_contract(
        code=_writer_code([(l3, 0)]), storage={l1: 1, l2: 2, l3: 3}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={l1: 1, l2: 2})},
    )


def test_delete_collapses_branch_onto_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Deleting the shallow sibling of ext(2) -> branch -> {leaf, branch}
    collapses the outer branch onto a *branch* survivor: the extension
    absorbs the surviving nibble and points straight at the inner branch.
    """
    a, b, c = BRANCH_SURVIVOR_TRIO
    assert _shape([a, b, c], a) == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "branch", 2),
        (4, "leaf", 60),
    ]
    assert _shape([a, b], a) == [
        (0, "ext", 3),
        (3, "branch", 2),
        (4, "leaf", 60),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(c, 0)]), storage={a: 1, b: 2, c: 3}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, b: 2})},
    )


def test_delete_collapses_root_branch_into_leaf(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Two leaves diverging at nibble 0 sit under a root branch; deleting
    one turns the root itself into a leaf (no extension anywhere).
    """
    a, b = ROOT_PAIR
    assert _shape([a, b], a) == [(0, "branch", 2), (1, "leaf", 63)]
    contract = pre.deploy_contract(
        code=_writer_code([(a, 0)]), storage={a: 1, b: 2}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={b: 2})},
    )


def test_collapse_under_branch_parent_leaf_survivor(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Pre: root branch -> {branch@1 -> {SINGLE_SLOT, its depth-1 sibling},
    leaf ROOT_PAIR[1]}.
    Op: zero the depth-1 sibling.
    Post: branch@1 collapses; the surviving leaf gains the branch's nibble
    (62 -> 63 remaining) and stays in the root branch's slot. Nothing
    merges: the parent is a branch, not an extension.
    Exercises: geth `Trie.delete` fullNode reduction with a shortNode
    survivor whose parent frame is itself a fullNode. Every other collapse
    in the suite either becomes the root or merges into an extension.
    """
    a, sibling, other = SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]
    assert _shape([a, sibling, other], a) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "leaf", 62),
    ]
    assert _shape([a, other], a) == [(0, "branch", 2), (1, "leaf", 63)]
    contract = pre.deploy_contract(
        code=_writer_code([(sibling, 0)]),
        storage={a: 1, sibling: 2, other: 3},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, other: 3})},
    )


def test_collapse_under_branch_parent_branch_survivor(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Pre: root branch -> {branch@1 -> {depth-1 sibling, branch@2 ->
    {SINGLE_SLOT, its depth-2 sibling}}, leaf ROOT_PAIR[1]}.
    Op: zero the depth-1 sibling.
    Post: branch@1 collapses onto a branch survivor, so a fresh 1-nibble
    extension appears between the root branch and branch@2; the root
    branch keeps its slot.
    Exercises: geth `Trie.delete` fullNode reduction where the survivor is
    a fullNode and the parent is a fullNode (a new shortNode is created,
    not merged). `test_delete_collapses_branch_onto_branch` covers the
    extension-parent variant where the nibble merges into ext(k+1).
    """
    a, d1, d2, other = (
        SINGLE_SLOT,
        SINGLE_SLOT_SIBLING_DEPTH1,
        SINGLE_SLOT_SIBLING_DEPTH2,
        ROOT_PAIR[1],
    )
    assert _shape([a, d1, d2, other], a) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "branch", 2),
        (3, "leaf", 61),
    ]
    assert _shape([a, d2, other], a) == [
        (0, "branch", 2),
        (1, "ext", 1),
        (2, "branch", 2),
        (3, "leaf", 61),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(d1, 0)]),
        storage={a: 1, d1: 2, d2: 3, other: 4},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, d2: 3, other: 4})},
    )


def test_root_branch_collapses_onto_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Pre: root branch -> {branch@1 -> {SINGLE_SLOT, its depth-1 sibling},
    leaf ROOT_PAIR[1]}.
    Op: zero ROOT_PAIR[1].
    Post: the root branch collapses onto branch@1; the root becomes a
    1-nibble extension pointing at that branch. Root kind changes from
    branch to extension, the one root transition the suite lacked.
    Exercises: geth `Trie.delete` fullNode reduction at the root with a
    fullNode survivor. `test_delete_collapses_root_branch_into_leaf` is
    the leaf-survivor counterpart.
    """
    a, sibling, other = SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]
    assert _shape([a, sibling, other], a) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "leaf", 62),
    ]
    assert _shape([a, sibling], a) == [
        (0, "ext", 1),
        (1, "branch", 2),
        (2, "leaf", 62),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(other, 0)]),
        storage={a: 1, sibling: 2, other: 3},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, sibling: 2})},
    )


def test_collapse_under_branch_parent_extension_survivor(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Pre: root branch -> {branch@1 -> {depth-1 sibling of TWO_SLOTS_EXT4,
    ext(2) -> branch@4 -> TWO_SLOTS_EXT4}, leaf SINGLE_SLOT}.
    Op: zero the depth-1 sibling.
    Post: branch@1 collapses onto an extension survivor, which absorbs the
    branch's nibble: ext(2) becomes ext(3) under the root branch, which
    keeps its slot. No merge with a parent extension is involved.
    Exercises: geth `Trie.delete` fullNode reduction with a shortNode
    (extension) survivor under a fullNode parent, the extension-lengthens
    path that `test_delete_merges_adjacent_extensions` only reaches with
    an extension parent.
    """
    p, q = TWO_SLOTS_EXT4
    sibling, other = TWO_SLOTS_EXT4_SIBLING_DEPTH1, SINGLE_SLOT
    assert _shape([p, q, sibling, other], p) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "ext", 2),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    assert _shape([p, q, other], p) == [
        (0, "branch", 2),
        (1, "ext", 3),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(sibling, 0)]),
        storage={p: 1, q: 2, sibling: 3, other: 4},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={p: 1, q: 2, other: 4})},
    )


def test_delete_from_full_branch_keeps_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """Deleting one of 16 children leaves a 15-child branch: no collapse."""
    slots = SIXTEEN_SLOTS_BRANCH4
    storage: StorageRootType = {slot: i + 1 for i, slot in enumerate(slots)}
    remaining = {s: v for s, v in storage.items() if s != slots[0]}
    assert _shape(slots[1:], slots[1])[1] == (4, "branch", 15)
    contract = pre.deploy_contract(
        code=_writer_code([(slots[0], 0)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage=remaining)},
    )


def test_delete_from_three_child_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Pre: ext(4) -> branch@4 with exactly three children (the first three
    of SIXTEEN_SLOTS_BRANCH4).
    Op: zero the first child.
    Post: branch@4 keeps two children; no collapse, no extension change.
    Exercises: the smallest non-collapsing delete. A client that reduces a
    branch when two or fewer children remain, instead of exactly one,
    passes the 16 -> 15 case and fails here.
    """
    slots = SIXTEEN_SLOTS_BRANCH4[:3]
    assert _shape(slots, slots[1]) == [
        (0, "ext", 4),
        (4, "branch", 3),
        (5, "leaf", 59),
    ]
    assert _shape(slots[1:], slots[1]) == [
        (0, "ext", 4),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    storage: StorageRootType = {s: i + 1 for i, s in enumerate(slots)}
    contract = pre.deploy_contract(
        code=_writer_code([(slots[0], 0)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={slots[1]: 2, slots[2]: 3})},
    )


def test_delete_all_slots_empties_trie(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """Deleting all 16 children of a branch yields the empty trie root."""
    slots = SIXTEEN_SLOTS_BRANCH4
    contract = pre.deploy_contract(
        code=_writer_code([(s, 0) for s in slots]),
        storage={slot: i + 1 for i, slot in enumerate(slots)},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={})},
    )


# --- deletes against a trie committed by an earlier block -------------


@pytest.mark.parametrize(
    "group,target",
    [
        pytest.param(TWO_SLOTS_EXT4, TWO_SLOTS_EXT4[0], id="collapse_to_leaf"),
        pytest.param(EXT_MERGE_TRIO, EXT_MERGE_TRIO[2], id="merge_extensions"),
        pytest.param(
            BRANCH_SURVIVOR_TRIO,
            BRANCH_SURVIVOR_TRIO[2],
            id="collapse_onto_branch",
        ),
        pytest.param(ROOT_PAIR, ROOT_PAIR[0], id="root_to_leaf"),
        pytest.param(
            SIXTEEN_SLOTS_BRANCH4,
            SIXTEEN_SLOTS_BRANCH4[0],
            id="full_branch_minus_one",
        ),
    ],
)
def test_delete_against_committed_trie(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    group: Sequence[int],
    target: int,
) -> None:
    """
    Insert the group in block 1, delete `target` in block 2, re-insert it
    in block 3. Each block commits, so the delete and the re-insert run
    against hashed, persisted nodes rather than the same block's journal.
    """
    values = {slot: i + 1 for i, slot in enumerate(group)}
    without = {s: v for s, v in values.items() if s != target}
    contract = pre.deploy_contract(code=SLOT_WRITER)
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=values)},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, s, v) for s, v in values.items()
                ],
                expected_post_state={contract: Account(storage=values)},
            ),
            Block(
                txs=[_write(sender, contract, target, 0)],
                expected_post_state={contract: Account(storage=without)},
            ),
            Block(txs=[_write(sender, contract, target, values[target])]),
        ],
    )


# --- several mutations inside one block --------------------------------


@pytest.mark.parametrize("per_tx", [False, True], ids=["single_tx", "per_tx"])
def test_mass_delete_sixteen_to_one(
    blockchain_test: BlockchainTestFiller, pre: Alloc, per_tx: bool
) -> None:
    """
    Pre: ext(4) -> branch@4 with all 16 children committed at genesis.
    Op: zero 15 of the 16 slots inside one block, either from one
    transaction or one transaction per slot.
    Post: the branch collapses onto its last child and merges with the
    extension: the root is a single 64-nibble leaf.
    Exercises: a branch losing 15 children in one block diff. Flat-diff
    clients see the child mask go from 0xffff to a single bit in one pass
    instead of 15 separate reductions; the existing cases only cover
    16 -> 15 and 16 -> 0.
    """
    slots = SIXTEEN_SLOTS_BRANCH4
    survivor, doomed = slots[0], slots[1:]
    assert _shape(slots, survivor)[1] == (4, "branch", 16)
    assert _shape([survivor], survivor) == [(0, "leaf", 64)]
    storage: StorageRootType = {s: i + 1 for i, s in enumerate(slots)}
    sender = pre.fund_eoa()
    if per_tx:
        contract = pre.deploy_contract(code=SLOT_WRITER, storage=storage)
        txs = [_write(sender, contract, s, 0) for s in doomed]
    else:
        contract = pre.deploy_contract(
            code=_writer_code([(s, 0) for s in doomed]), storage=storage
        )
        txs = [Transaction(sender=sender, to=contract)]

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={survivor: 1})},
        blocks=[Block(txs=txs)],
    )


def test_one_to_sixteen_into_committed_leaf(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Pre: one slot of SIXTEEN_SLOTS_BRANCH4 committed at genesis as the
    root leaf.
    Op: write the other 15 slots in one block, one transaction each.
    Post: ext(4) -> branch@4 with all 16 children.
    Exercises: one split of a committed leaf into ext+branch followed by
    14 slot fills of the branch it just created, all inside one block
    diff. `test_insert_full_branch_across_blocks` grows a committed
    branch from 8 to 16 but never starts from a leaf.
    """
    slots = SIXTEEN_SLOTS_BRANCH4
    first, rest = slots[0], slots[1:]
    assert _shape([first], first) == [(0, "leaf", 64)]
    assert _shape(slots, first) == [
        (0, "ext", 4),
        (4, "branch", 16),
        (5, "leaf", 59),
    ]
    values = {s: i + 1 for i, s in enumerate(slots)}
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={first: 1})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=values)},
        blocks=[
            Block(txs=[_write(sender, contract, s, values[s]) for s in rest])
        ],
    )


def test_insert_then_delete_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Pre: TWO_SLOTS_EXT4[0] committed at genesis as the root leaf.
    Op: in one block, tx1 writes TWO_SLOTS_EXT4[1] (which would split the
    leaf into ext(4) -> branch@4), tx2 zeroes it again.
    Post: storage identical to the pre-state, so the contract's storage
    root must be byte-identical to its genesis value: no residual
    extension or one-child branch may survive the round trip.
    Exercises: a key whose final value equals its original inside one
    block diff. Object-diff clients must skip it; touched-key clients
    (erigon, reth) process it and must arrive at the same node set.
    """
    a, b = TWO_SLOTS_EXT4
    assert _shape([a], a) == [(0, "leaf", 64)]
    assert _shape([a, b], a)[:2] == [(0, "ext", 4), (4, "branch", 2)]
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={a: 1})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={a: 1})},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, b, 2),
                    _write(sender, contract, b, 0),
                ]
            )
        ],
    )


@pytest.mark.parametrize("new_value", [2, 5], ids=["same_value", "new_value"])
def test_delete_then_reinsert_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc, new_value: int
) -> None:
    """
    Pre: TWO_SLOTS_EXT4 committed at genesis as ext(4) -> branch@4.
    Op: in one block, tx1 zeroes TWO_SLOTS_EXT4[1] (which would collapse
    the branch into a root leaf), tx2 writes it back with the same value
    or a new one.
    Post: the pre shape; the same-value case leaves the storage root
    byte-identical to genesis, the new-value case changes one leaf value.
    Exercises: a per-key delete marker followed by a write inside one
    block diff. The delete must not shadow the re-insert, and the
    same-value case must fold to a no-op rather than delete+insert.
    """
    a, b = TWO_SLOTS_EXT4
    assert _shape([a, b], a) == [
        (0, "ext", 4),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    assert _shape([a], a) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={a: 1, b: 2})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={a: 1, b: new_value})},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, b, 0),
                    _write(sender, contract, b, new_value),
                ]
            )
        ],
    )


def test_delete_sibling_and_update_survivor_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Pre: TWO_SLOTS_EXT4 committed at genesis as ext(4) -> branch@4.
    Op: in one block, tx1 zeroes TWO_SLOTS_EXT4[0], tx2 overwrites
    TWO_SLOTS_EXT4[1] with a new value.
    Post: the branch collapses and merges with the extension into a root
    leaf that must carry the survivor's new value, not its committed one.
    Exercises: a collapse whose survivor is itself dirty in the same block
    diff; the reduction must read the updated leaf, and flat-diff clients
    must order the delete and the update correctly.
    """
    a, b = TWO_SLOTS_EXT4
    assert _shape([a, b], b)[:2] == [(0, "ext", 4), (4, "branch", 2)]
    assert _shape([b], b) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={a: 1, b: 2})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={b: 7})},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, a, 0),
                    _write(sender, contract, b, 7),
                ]
            )
        ],
    )


def test_replace_child_within_branch_slot(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Pre: ROOT_PAIR committed at genesis as a root branch with two leaves.
    Op: in one block, tx1 zeroes SINGLE_SLOT (= ROOT_PAIR[0]), tx2 writes
    its depth-1 sibling, whose hashed key lands in the same root-branch
    slot.
    Post: the root branch still has two children; the slot that held
    SINGLE_SLOT's leaf now holds the sibling's leaf, a different key with
    a different 63-nibble remaining path.
    Exercises: a branch whose child count is unchanged while one child's
    content is swapped inside one block diff. Clients that key cached
    nodes by path must not reuse the old leaf; child-mask based
    appliers see no mask change at all.
    """
    old, other = ROOT_PAIR
    new = SINGLE_SLOT_SIBLING_DEPTH1
    assert _shape([old, other], other) == [(0, "branch", 2), (1, "leaf", 63)]
    assert _shape([new, other], other) == [(0, "branch", 2), (1, "leaf", 63)]
    assert _shape([new, other], new) == [(0, "branch", 2), (1, "leaf", 63)]
    contract = pre.deploy_contract(
        code=SLOT_WRITER, storage={old: 1, other: 2}
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={other: 2, new: 3})},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, old, 0),
                    _write(sender, contract, new, 3),
                ]
            )
        ],
    )


# --- node embedding ----------------------------------------------------


@pytest.mark.parametrize(
    "pair,value,leaf_size",
    [
        pytest.param(
            EMBEDDED_LEAF_PAIR, 1, 31, id="depth8_value1_embedded_31"
        ),
        pytest.param(HASHED_LEAF_PAIR, 1, 32, id="depth7_value1_hashed_32"),
        pytest.param(
            EMBEDDED_LEAF_PAIR, 128, 33, id="depth8_value128_hashed_33"
        ),
    ],
)
def test_embedded_leaf_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    pair: Sequence[int],
    value: int,
    leaf_size: int,
) -> None:
    """
    Leaf RLP size straddles the 32-byte embedding threshold: 55 remaining
    nibbles with a single-byte value encode to 31 bytes (inlined into the
    parent branch); one more path nibble (56) or a two-byte value pushes
    it to 32 or 33 (hashed child).
    """
    a, b = pair
    depth, kind, rest = _shape([a, b], a)[-1]
    assert kind == "leaf"
    assert _leaf_rlp_size(rest, value) == leaf_size
    contract = pre.deploy_contract(code=_writer_code([(a, value), (b, value)]))

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: value, b: value})},
    )


def test_embedded_leaf_becomes_hashed_and_back(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Growing one embedded leaf's value past the threshold turns it into a
    hashed child; shrinking it back re-embeds it. Each step commits.
    """
    a, b = EMBEDDED_LEAF_PAIR
    assert _leaf_rlp_size(55, 1) < 32 <= _leaf_rlp_size(55, 128)
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={a: 1, b: 1})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={a: 1, b: 1})},
        blocks=[
            Block(
                txs=[_write(sender, contract, a, 128)],
                expected_post_state={
                    contract: Account(storage={a: 128, b: 1})
                },
            ),
            Block(txs=[_write(sender, contract, a, 1)]),
        ],
    )
