"""
Exercise the Merkle Patricia Trie via storage slots.

Every test writes slots whose keccak256 hashes (see `constants.py`) force
one node operation: a leaf split, an extension split, a branch collapse,
an extension merge, or a leaf crossing the 32-byte inlining threshold.

Tests with several transactions write through `SLOT_WRITER`, so
successive transactions or blocks can write different slots of one
contract; single-transaction tests use fixed code.
"""

from typing import Dict, List, Sequence, Tuple

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.base_types import StorageRootType

from .constants import (
    BRANCH_SURVIVOR_TRIO,
    EMBEDDED_LEAF_PAIR,
    EMBEDDED_LEAF_PAIR_SIBLING_DEPTH4,
    EXT_MERGE_TRIO,
    EXT_MERGE_TRIO_SIBLING_DEPTH3,
    HASHED_LEAF_PAIR,
    INLINE_TRIO,
    ROOT_PAIR,
    ROOT_SIXTEEN,
    SINGLE_SLOT,
    SINGLE_SLOT_SIBLING_DEPTH1,
    SINGLE_SLOT_SIBLING_DEPTH2,
    SIXTEEN_SLOTS_BRANCH4,
    SLOT_WRITER,
    TWO_SLOTS_EXT4,
    TWO_SLOTS_EXT4_SIBLING_DEPTH1,
    TWO_SLOTS_EXT4_SIBLING_DEPTH2,
    TWO_SLOTS_EXT4_SIBLING_DEPTH3,
    VALUE_BOUNDARY_PAIR,
)
from .trie_shape import Shape, storage_leaf_size, storage_shape

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")


def _writer_code(pairs: List[Tuple[int, int]]) -> Bytecode:
    """Return code that `SSTORE`s each `(slot, value)` pair, in order."""
    code = Bytecode()
    for slot, value in pairs:
        code += Op.SSTORE(slot, value)
    return code + Op.STOP


def _write(
    sender: EOA, contract: Address, slot: int, value: int
) -> Transaction:
    """Return a `SLOT_WRITER` call setting `slot` to `value`."""
    return Transaction(
        sender=sender, to=contract, data=Hash(slot) + Hash(value)
    )


def _storage(slots: Sequence[int]) -> Storage:
    """Return storage mapping each slot in `slots` to its position + 1."""
    assert len(set(slots)) == len(slots)
    storage = Storage()
    for i, slot in enumerate(slots):
        storage[slot] = i + 1
    return storage


# --- inserts -----------------------------------------------------------


def test_insert_leaf_into_empty_trie(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    First write into an empty storage trie.

    pre:  empty
    post: leaf(64)
    """
    assert storage_shape([SINGLE_SLOT], SINGLE_SLOT) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(code=_writer_code([(SINGLE_SLOT, 1)]))

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={SINGLE_SLOT: 1})},
    )


def test_update_existing_leaf(state_test: StateTestFiller, pre: Alloc) -> None:
    """
    Overwrite the only leaf; the value changes, the shape does not.

    pre:  leaf(64) = 1
    post: leaf(64) = 2
    """
    assert storage_shape([SINGLE_SLOT], SINGLE_SLOT) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(
        code=_writer_code([(SINGLE_SLOT, 2)]), storage={SINGLE_SLOT: 1}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={SINGLE_SLOT: 2})},
    )


def test_insert_splits_into_extension_and_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Two slots sharing four nibbles, written into an empty trie.

    pre:  empty
    post: ext(4) -> branch@4 -> {leaf(59), leaf(59)}
    """
    a, b = TWO_SLOTS_EXT4
    assert storage_shape([a, b], a) == [
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
    Two slots sharing one nibble: the shortest extension a split creates.

    pre:  empty
    post: ext(1) -> branch@1 -> {leaf(62), leaf(62)}
    """
    a, b = SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1
    assert storage_shape([a, b], a) == [
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
    Insert a key that diverges in the middle of a committed extension.

    pre:  ext(5) -> branch@5 -> {l1, l2}
    post: ext(2) -> branch@2 -> {l3, ext(2) -> branch@5 -> {l1, l2}}
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    assert storage_shape([l1, l2], l1) == [
        (0, "ext", 5),
        (5, "branch", 2),
        (6, "leaf", 58),
    ]
    assert storage_shape([l1, l2, l3], l1) == [
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
    Split a leaf that hangs off a committed root branch.

    pre:  branch@0 -> {leaf(63), leaf(63)}
    post: branch@0 -> {ext(1) -> branch@2 -> {..}, leaf(63)}, or
          branch@0 -> {branch@1 -> {..}, leaf(63)} when the new key shares
          only the first nibble
    The split result takes the leaf's slot in the root branch.
    """
    a, b = ROOT_PAIR
    assert storage_shape([a, b], a) == [(0, "branch", 2), (1, "leaf", 63)]
    assert storage_shape([a, b, new_slot], a) == post_shape
    assert storage_shape([a, b, new_slot], b) == [
        (0, "branch", 2),
        (1, "leaf", 63),
    ]
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
    Insert a key that differs from a root extension in its first nibble.

    pre:  ext(n) -> branch@n -> {..}, for n = 4 and n = 1
    post: branch@0 -> {ext(n-1) -> branch@n -> {..}, leaf(63)}
    For n = 1 no zero-length extension is left: the branch hangs off the
    root directly.
    """
    target = committed[0]
    assert storage_shape(committed, target) == pre_shape
    assert storage_shape([*committed, new_slot], target) == post_shape
    assert storage_shape([*committed, new_slot], new_slot) == [
        (0, "branch", 2),
        (1, "leaf", 63),
    ]
    storage = _storage(committed)
    contract = pre.deploy_contract(
        code=_writer_code([(new_slot, 3)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={**storage, new_slot: 3})},
    )


@pytest.mark.parametrize(
    "committed,new_slot,post_shape",
    [
        pytest.param(
            (*TWO_SLOTS_EXT4, SINGLE_SLOT),
            TWO_SLOTS_EXT4_SIBLING_DEPTH1,
            [
                (0, "branch", 2),
                (1, "branch", 2),
                (2, "ext", 2),
                (4, "branch", 2),
                (5, "leaf", 59),
            ],
            id="offset0",
        ),
        pytest.param(
            (SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH2, ROOT_PAIR[1]),
            SINGLE_SLOT_SIBLING_DEPTH1,
            [
                (0, "branch", 2),
                (1, "branch", 2),
                (2, "branch", 2),
                (3, "leaf", 61),
            ],
            id="offset0_vanishes",
        ),
        pytest.param(
            (*TWO_SLOTS_EXT4, SINGLE_SLOT),
            TWO_SLOTS_EXT4_SIBLING_DEPTH2,
            [
                (0, "branch", 2),
                (1, "ext", 1),
                (2, "branch", 2),
                (3, "ext", 1),
                (4, "branch", 2),
                (5, "leaf", 59),
            ],
            id="middle",
        ),
        pytest.param(
            (*TWO_SLOTS_EXT4, SINGLE_SLOT),
            TWO_SLOTS_EXT4_SIBLING_DEPTH3,
            [
                (0, "branch", 2),
                (1, "ext", 2),
                (3, "branch", 2),
                (4, "branch", 2),
                (5, "leaf", 59),
            ],
            id="last_nibble",
        ),
    ],
)
def test_insert_splits_extension_under_branch(
    state_test: StateTestFiller,
    pre: Alloc,
    committed: Sequence[int],
    new_slot: int,
    post_shape: Shape,
) -> None:
    """
    Split an extension that hangs off a root branch, at each offset.

    pre:  branch@0 -> {ext(n) -> branch -> {..}, leaf(63)}
    post: branch@0 -> {.. -> branch -> {new, .. -> branch -> {..}}, ..}
    The new branch sits at the split offset and an extension part left
    with no nibbles disappears; the result takes the extension's slot in
    the root branch.
    """
    target = committed[0]
    assert storage_shape(committed, target)[0] == (0, "branch", 2)
    assert storage_shape(committed, target)[1][1] == "ext"
    assert storage_shape([*committed, new_slot], target) == post_shape
    storage = _storage(committed)
    contract = pre.deploy_contract(
        code=_writer_code([(new_slot, 9)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={**storage, new_slot: 9})},
    )


def test_insert_splits_nested_extension_first_nibble(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Insert a key that differs from a nested extension in its first nibble.

    pre:  ext(2) -> branch@2 -> {l3, ext(2) -> branch@5 -> {l1, l2}}
    post: ext(2) -> branch@2 -> {l3, branch@3 -> {new, ext(1) -> branch@5}}
    A branch replaces the inner extension's first nibble and the extension
    shrinks by one, below both a root extension and a branch.
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    new = EXT_MERGE_TRIO_SIBLING_DEPTH3
    assert storage_shape([l1, l2, l3], l1)[2] == (3, "ext", 2)
    assert storage_shape([l1, l2, l3, new], l1) == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "branch", 2),
        (4, "ext", 1),
        (5, "branch", 2),
        (6, "leaf", 58),
    ]
    assert storage_shape([l1, l2, l3, new], new)[-1] == (4, "leaf", 60)
    contract = pre.deploy_contract(
        code=_writer_code([(new, 4)]), storage={l1: 1, l2: 2, l3: 3}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={l1: 1, l2: 2, l3: 3, new: 4})},
    )


@pytest.mark.parametrize(
    "committed,writes,present,post_shape",
    [
        pytest.param(
            ROOT_SIXTEEN,
            [(s, 0) for s in ROOT_SIXTEEN[1:]],
            ROOT_SIXTEEN[:1],
            [(0, "leaf", 64)],
            id="sixteen_to_one",
        ),
        pytest.param(
            ROOT_SIXTEEN,
            [(ROOT_SIXTEEN[0], 0)],
            ROOT_SIXTEEN[1:],
            [(0, "branch", 15), (1, "leaf", 63)],
            id="sixteen_to_fifteen",
        ),
        pytest.param(
            (),
            [(s, i + 1) for i, s in enumerate(ROOT_SIXTEEN)],
            ROOT_SIXTEEN,
            [(0, "branch", 16), (1, "leaf", 63)],
            id="fill",
        ),
    ],
)
def test_root_branch_arity_sixteen(
    state_test: StateTestFiller,
    pre: Alloc,
    committed: Sequence[int],
    writes: List[Tuple[int, int]],
    present: Sequence[int],
    post_shape: Shape,
) -> None:
    """
    Fill a 16-way root branch from empty, or reduce one to 15 or 1 child.

    pre:  empty, or branch@0 -> {16 x leaf(63)}
    post: branch@0 -> {16 x leaf(63)}, branch@0 -> {15 x leaf(63)}, or
          leaf(64)
    """
    assert storage_shape(ROOT_SIXTEEN, ROOT_SIXTEEN[0]) == [
        (0, "branch", 16),
        (1, "leaf", 63),
    ]
    assert storage_shape(present, present[0]) == post_shape
    contract = pre.deploy_contract(
        code=_writer_code(writes), storage=_storage(committed)
    )
    expected = {
        s: v for s, v in _storage(ROOT_SIXTEEN).items() if s in present
    }

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage=expected)},
    )


def test_insert_full_branch_arity_sixteen(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Sixteen slots sharing four nibbles fill every child of one branch.

    pre:  empty
    post: ext(4) -> branch@4 -> {16 x leaf(59)}
    """
    slots = SIXTEEN_SLOTS_BRANCH4
    assert storage_shape(slots, slots[0]) == [
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
    Fill a 16-way branch over two blocks, in two orders.

    pre:  empty
    post: ext(4) -> branch@4 -> {16 x leaf(59)}   after block 2
    Block 2 inserts into a committed 8-child branch; both orders must
    reach the same root.
    """
    slots = list(SIXTEEN_SLOTS_BRANCH4)
    if reverse:
        slots.reverse()
    values = _storage(SIXTEEN_SLOTS_BRANCH4)
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
    """
    Zero the only slot.

    pre:  leaf(64)
    post: empty
    """
    assert storage_shape([SINGLE_SLOT], SINGLE_SLOT) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(
        code=_writer_code([(SINGLE_SLOT, 0)]), storage={SINGLE_SLOT: 1}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={})},
    )


@pytest.mark.parametrize(
    "committed,absent,pre_shape",
    [
        pytest.param(
            [SINGLE_SLOT],
            ROOT_PAIR[1],
            [(0, "leaf", 64)],
            id="leaf_mismatch",
        ),
        pytest.param(
            EXT_MERGE_TRIO[:2],
            EXT_MERGE_TRIO[2],
            [(0, "ext", 5), (5, "branch", 2), (6, "leaf", 58)],
            id="ext_mismatch",
        ),
        pytest.param(
            SIXTEEN_SLOTS_BRANCH4[:15],
            SIXTEEN_SLOTS_BRANCH4[15],
            [(0, "ext", 4), (4, "branch", 15), (5, "leaf", 59)],
            id="empty_slot",
        ),
    ],
)
def test_delete_missing_is_noop(
    state_test: StateTestFiller,
    pre: Alloc,
    committed: Sequence[int],
    absent: int,
    pre_shape: Shape,
) -> None:
    """
    Zero a slot that is not in the trie; the root does not change.

    pre:  leaf(64), ext(5) -> branch@5 -> {..}, or
          ext(4) -> branch@4 -> {15 x leaf(59)}
    post: identical
    The slot's path ends at another leaf, inside an extension or at an
    empty branch slot.
    """
    storage = _storage(committed)
    assert storage_shape(committed, committed[0]) == pre_shape
    assert absent not in storage
    contract = pre.deploy_contract(
        code=_writer_code([(absent, 0)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage=storage)},
    )


# One slot deleted from a group: (group, target, along, pre, post), where
# pre and post are the path along the slot `along` before and after the
# delete.
DELETE_CASES = [
    # The leaf absorbs the branch nibble and the root extension.
    pytest.param(
        TWO_SLOTS_EXT4,
        TWO_SLOTS_EXT4[0],
        TWO_SLOTS_EXT4[1],
        [(0, "ext", 4), (4, "branch", 2), (5, "leaf", 59)],
        [(0, "leaf", 64)],
        id="collapse_to_leaf",
    ),
    # Both extensions and the branch nibble merge into one.
    pytest.param(
        EXT_MERGE_TRIO,
        EXT_MERGE_TRIO[2],
        EXT_MERGE_TRIO[0],
        [
            (0, "ext", 2),
            (2, "branch", 2),
            (3, "ext", 2),
            (5, "branch", 2),
            (6, "leaf", 58),
        ],
        [(0, "ext", 5), (5, "branch", 2), (6, "leaf", 58)],
        id="merge_extensions",
    ),
    # The root extension grows onto the surviving branch.
    pytest.param(
        BRANCH_SURVIVOR_TRIO,
        BRANCH_SURVIVOR_TRIO[2],
        BRANCH_SURVIVOR_TRIO[0],
        [(0, "ext", 2), (2, "branch", 2), (3, "branch", 2), (4, "leaf", 60)],
        [(0, "ext", 3), (3, "branch", 2), (4, "leaf", 60)],
        id="collapse_onto_branch",
    ),
    # The root branch collapses into a leaf.
    pytest.param(
        ROOT_PAIR,
        ROOT_PAIR[0],
        ROOT_PAIR[1],
        [(0, "branch", 2), (1, "leaf", 63)],
        [(0, "leaf", 64)],
        id="root_to_leaf",
    ),
    # A full branch loses one child and stays a branch.
    pytest.param(
        SIXTEEN_SLOTS_BRANCH4,
        SIXTEEN_SLOTS_BRANCH4[0],
        SIXTEEN_SLOTS_BRANCH4[1],
        [(0, "ext", 4), (4, "branch", 16), (5, "leaf", 59)],
        [(0, "ext", 4), (4, "branch", 15), (5, "leaf", 59)],
        id="full_branch_minus_one",
    ),
    # With two children left the branch stays.
    pytest.param(
        SIXTEEN_SLOTS_BRANCH4[:3],
        SIXTEEN_SLOTS_BRANCH4[0],
        SIXTEEN_SLOTS_BRANCH4[1],
        [(0, "ext", 4), (4, "branch", 3), (5, "leaf", 59)],
        [(0, "ext", 4), (4, "branch", 2), (5, "leaf", 59)],
        id="three_to_two",
    ),
    # Below a branch the leaf only gains the branch nibble.
    pytest.param(
        (SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]),
        SINGLE_SLOT_SIBLING_DEPTH1,
        SINGLE_SLOT,
        [(0, "branch", 2), (1, "branch", 2), (2, "leaf", 62)],
        [(0, "branch", 2), (1, "leaf", 63)],
        id="leaf_under_branch",
    ),
    # Below a branch the extension only gains the branch nibble.
    pytest.param(
        (*TWO_SLOTS_EXT4, TWO_SLOTS_EXT4_SIBLING_DEPTH1, SINGLE_SLOT),
        TWO_SLOTS_EXT4_SIBLING_DEPTH1,
        TWO_SLOTS_EXT4[0],
        [
            (0, "branch", 2),
            (1, "branch", 2),
            (2, "ext", 2),
            (4, "branch", 2),
            (5, "leaf", 59),
        ],
        [(0, "branch", 2), (1, "ext", 3), (4, "branch", 2), (5, "leaf", 59)],
        id="ext_under_branch",
    ),
    # Below a branch a 1-nibble extension appears above the survivor.
    pytest.param(
        (
            SINGLE_SLOT,
            SINGLE_SLOT_SIBLING_DEPTH1,
            SINGLE_SLOT_SIBLING_DEPTH2,
            ROOT_PAIR[1],
        ),
        SINGLE_SLOT_SIBLING_DEPTH1,
        SINGLE_SLOT,
        [
            (0, "branch", 2),
            (1, "branch", 2),
            (2, "branch", 2),
            (3, "leaf", 61),
        ],
        [(0, "branch", 2), (1, "ext", 1), (2, "branch", 2), (3, "leaf", 61)],
        id="branch_under_branch",
    ),
    # The root branch becomes a 1-nibble extension.
    pytest.param(
        (SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]),
        ROOT_PAIR[1],
        SINGLE_SLOT,
        [(0, "branch", 2), (1, "branch", 2), (2, "leaf", 62)],
        [(0, "ext", 1), (1, "branch", 2), (2, "leaf", 62)],
        id="root_onto_branch",
    ),
    # The root branch merges into the extension below it.
    pytest.param(
        (*TWO_SLOTS_EXT4, SINGLE_SLOT),
        SINGLE_SLOT,
        TWO_SLOTS_EXT4[0],
        [(0, "branch", 2), (1, "ext", 3), (4, "branch", 2), (5, "leaf", 59)],
        [(0, "ext", 4), (4, "branch", 2), (5, "leaf", 59)],
        id="root_onto_ext",
    ),
    # The merged leaf stays below branch@2 instead of becoming the root.
    pytest.param(
        EXT_MERGE_TRIO,
        EXT_MERGE_TRIO[0],
        EXT_MERGE_TRIO[1],
        [
            (0, "ext", 2),
            (2, "branch", 2),
            (3, "ext", 2),
            (5, "branch", 2),
            (6, "leaf", 58),
        ],
        [(0, "ext", 2), (2, "branch", 2), (3, "leaf", 61)],
        id="nested_ext_leaf",
    ),
    # Two extensions merge below the root branch.
    pytest.param(
        (*TWO_SLOTS_EXT4, TWO_SLOTS_EXT4_SIBLING_DEPTH2, SINGLE_SLOT),
        TWO_SLOTS_EXT4_SIBLING_DEPTH2,
        TWO_SLOTS_EXT4[0],
        [
            (0, "branch", 2),
            (1, "ext", 1),
            (2, "branch", 2),
            (3, "ext", 1),
            (4, "branch", 2),
            (5, "leaf", 59),
        ],
        [(0, "branch", 2), (1, "ext", 3), (4, "branch", 2), (5, "leaf", 59)],
        id="nested_ext_ext",
    ),
    # The extension parent grows onto the surviving branch.
    pytest.param(
        (*TWO_SLOTS_EXT4, TWO_SLOTS_EXT4_SIBLING_DEPTH3, SINGLE_SLOT),
        TWO_SLOTS_EXT4_SIBLING_DEPTH3,
        TWO_SLOTS_EXT4[0],
        [
            (0, "branch", 2),
            (1, "ext", 2),
            (3, "branch", 2),
            (4, "branch", 2),
            (5, "leaf", 59),
        ],
        [(0, "branch", 2), (1, "ext", 3), (4, "branch", 2), (5, "leaf", 59)],
        id="nested_ext_branch",
    ),
]


def _delete_case(
    group: Sequence[int],
    target: int,
    along: int,
    pre_shape: Shape,
    post_shape: Shape,
) -> Tuple[Storage, Dict[int, int]]:
    """
    Return the storage of `group` and what remains once `target` is zero.

    Assert the path along `along` before and after the delete.
    """
    storage = _storage(group)
    remaining: Dict[int, int] = {
        s: v for s, v in storage.items() if s != target
    }
    assert storage_shape(group, along) == pre_shape
    assert storage_shape(list(remaining), along) == post_shape
    return storage, remaining


@pytest.mark.parametrize(
    "group,target,along,pre_shape,post_shape", DELETE_CASES
)
def test_delete_from_genesis_trie(
    state_test: StateTestFiller,
    pre: Alloc,
    group: Sequence[int],
    target: int,
    along: int,
    pre_shape: Shape,
    post_shape: Shape,
) -> None:
    """
    Zero one slot of a storage trie committed at genesis.

    Each `DELETE_CASES` row gives the path before and after the delete;
    the rows cover every survivor kind under every parent kind.
    """
    storage, remaining = _delete_case(
        group, target, along, pre_shape, post_shape
    )
    contract = pre.deploy_contract(
        code=_writer_code([(target, 0)]), storage=storage
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage=remaining)},
    )


@pytest.mark.parametrize(
    "slots,root_kind",
    [
        pytest.param(SIXTEEN_SLOTS_BRANCH4, "ext", id="root_extension"),
        pytest.param(ROOT_PAIR, "branch", id="root_branch"),
        pytest.param([SINGLE_SLOT], "leaf", id="root_leaf"),
    ],
)
def test_delete_all_slots_empties_trie(
    state_test: StateTestFiller,
    pre: Alloc,
    slots: Sequence[int],
    root_kind: str,
) -> None:
    """
    Delete every slot in one transaction.

    pre:  ext(4) -> branch@4 -> {16 x leaf(59)},
          branch@0 -> {leaf(63), leaf(63)}, or leaf(64)
    post: empty
    """
    assert storage_shape(slots, slots[0])[0][1] == root_kind
    contract = pre.deploy_contract(
        code=_writer_code([(s, 0) for s in slots]),
        storage=_storage(slots),
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={})},
    )


# --- deletes against nodes built by an earlier block --------------------


@pytest.mark.parametrize(
    "group,target,along,pre_shape,post_shape", DELETE_CASES
)
def test_delete_from_block_built_trie(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    group: Sequence[int],
    target: int,
    along: int,
    pre_shape: Shape,
    post_shape: Shape,
) -> None:
    """
    Zero one slot of a trie built in an earlier block, then restore it.

    pre:  empty; block 1 writes the group
    post: block 2 zeroes the slot, block 3 writes it back
    The `DELETE_CASES` deletes, run on nodes built in block 1 instead of
    loaded at genesis, each followed by the insert that undoes it.
    """
    values, without = _delete_case(group, target, along, pre_shape, post_shape)
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


def test_mass_delete_sixteen_to_one(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Zero fifteen of sixteen children in one transaction.

    pre:  ext(4) -> branch@4 -> {16 x leaf(59)}
    post: leaf(64)
    """
    slots = SIXTEEN_SLOTS_BRANCH4
    survivor, doomed = slots[0], slots[1:]
    assert storage_shape(slots, survivor)[1] == (4, "branch", 16)
    assert storage_shape([survivor], survivor) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(
        code=_writer_code([(s, 0) for s in doomed]),
        storage=_storage(slots),
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={survivor: 1})},
    )


def test_one_to_sixteen_into_committed_leaf(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Grow a committed single leaf into a full branch in one block.

    pre:  leaf(64)
    post: ext(4) -> branch@4 -> {16 x leaf(59)}
    One split followed by fourteen slot fills of the branch it created.
    """
    slots = SIXTEEN_SLOTS_BRANCH4
    first, rest = slots[0], slots[1:]
    assert storage_shape([first], first) == [(0, "leaf", 64)]
    assert storage_shape(slots, first)[1] == (4, "branch", 16)
    values = _storage(slots)
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={first: 1})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=values)},
        blocks=[
            Block(txs=[_write(sender, contract, s, values[s]) for s in rest])
        ],
    )


@pytest.mark.parametrize(
    "committed,slot",
    [
        pytest.param(TWO_SLOTS_EXT4[:1], TWO_SLOTS_EXT4[1], id="leaf_split"),
        pytest.param(EXT_MERGE_TRIO[:2], EXT_MERGE_TRIO[2], id="ext_split"),
        pytest.param(
            SIXTEEN_SLOTS_BRANCH4[:15],
            SIXTEEN_SLOTS_BRANCH4[15],
            id="branch_slot",
        ),
    ],
)
def test_insert_then_delete_same_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    committed: Sequence[int],
    slot: int,
) -> None:
    """
    Write a slot and zero it again in one block; the root does not change.

    pre:  leaf(64), ext(5) -> branch@5 -> {..}, or
          ext(4) -> branch@4 -> {15 x leaf(59)}
    post: identical
    The transient write would split a leaf, split an extension or fill a
    branch slot.
    """
    storage = _storage(committed)
    assert storage_shape([*committed, slot], slot) != storage_shape(
        committed, committed[0]
    )
    contract = pre.deploy_contract(code=SLOT_WRITER, storage=storage)
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, slot, 9),
                    _write(sender, contract, slot, 0),
                ]
            )
        ],
    )


def test_insert_then_delete_beside_real_change(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Round-trip one leaf's value while its sibling really changes.

    pre:  ext(4) -> branch@4 -> {p = 1, q = 2}
    post: the same shape with p = 9 and q = 2
    q returns to its original value inside a subtree that changed.
    """
    p, q = TWO_SLOTS_EXT4
    assert storage_shape([p, q], p)[:2] == [(0, "ext", 4), (4, "branch", 2)]
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={p: 1, q: 2})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={p: 9, q: 2})},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, q, 5),
                    _write(sender, contract, q, 2),
                    _write(sender, contract, p, 9),
                ]
            )
        ],
    )


@pytest.mark.parametrize("new_value", [2, 5], ids=["same_value", "new_value"])
def test_delete_then_reinsert_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc, new_value: int
) -> None:
    """
    Zero a slot and write it back within one block.

    pre:  ext(4) -> branch@4 -> {leaf(59), leaf(59)}
    post: the same shape, the slot back at its old value or a new one
    The later write wins over the deletion in the same block.
    """
    a, b = TWO_SLOTS_EXT4
    assert storage_shape([a, b], a)[:2] == [(0, "ext", 4), (4, "branch", 2)]
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
    Zero one sibling and overwrite the other within one block.

    pre:  ext(4) -> branch@4 -> {leaf(59) = 1, leaf(59) = 2}
    post: leaf(64) = 7
    The collapsed leaf carries the survivor's new value.
    """
    a, b = TWO_SLOTS_EXT4
    assert storage_shape([a, b], b)[:2] == [(0, "ext", 4), (4, "branch", 2)]
    assert storage_shape([b], b) == [(0, "leaf", 64)]
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
    Zero a leaf and write another key into the same branch slot.

    pre:  branch@0 -> {leaf(63) old, leaf(63) other}
    post: branch@0 -> {leaf(63) new, leaf(63) other}
    The child count stays the same while the slot's content changes; had
    both keys stayed, the slot would hold ext(1) -> branch@2.
    """
    old, other = ROOT_PAIR
    new = SINGLE_SLOT_SIBLING_DEPTH1
    assert storage_shape([old, other], other) == [
        (0, "branch", 2),
        (1, "leaf", 63),
    ]
    assert storage_shape([new, other], new) == [
        (0, "branch", 2),
        (1, "leaf", 63),
    ]
    assert storage_shape([old, new], old)[:2] == [
        (0, "ext", 1),
        (1, "branch", 2),
    ]
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


def test_two_shape_changes_at_different_depths(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Collapse at depth 2 and split at depth 3 within one block.

    pre:  ext(2) -> branch@2 -> {l3, ext(2) -> branch@5 -> {l1, l2}}
    post: ext(3) -> branch@3 -> {new, ext(1) -> branch@5 -> {l1, l2}}
    The result is neither single change applied alone, whichever runs
    first.
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    new = EXT_MERGE_TRIO_SIBLING_DEPTH3
    assert storage_shape([l1, l2, l3], l1) == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "ext", 2),
        (5, "branch", 2),
        (6, "leaf", 58),
    ]
    assert storage_shape([l1, l2, new], l1) == [
        (0, "ext", 3),
        (3, "branch", 2),
        (4, "ext", 1),
        (5, "branch", 2),
        (6, "leaf", 58),
    ]
    contract = pre.deploy_contract(
        code=SLOT_WRITER, storage={l1: 1, l2: 2, l3: 3}
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={l1: 1, l2: 2, new: 4})},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, l3, 0),
                    _write(sender, contract, new, 4),
                ]
            )
        ],
    )


@pytest.mark.parametrize(
    "second_write,post_second",
    [
        pytest.param(
            (SINGLE_SLOT_SIBLING_DEPTH1, 0),
            [(0, "branch", 2), (1, "leaf", 63)],
            id="two_collapses",
        ),
        pytest.param(
            (SINGLE_SLOT_SIBLING_DEPTH2, 9),
            [
                (0, "branch", 2),
                (1, "branch", 2),
                (2, "branch", 2),
                (3, "leaf", 61),
            ],
            id="collapse_and_split",
        ),
    ],
)
def test_restructure_two_disjoint_paths_same_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    second_write: Tuple[int, int],
    post_second: Shape,
) -> None:
    """
    Restructure two sibling subtrees of the root branch in one block.

    pre:  branch@0 -> {ext(3) -> branch@4 -> {p, q}, branch@1 -> {a, sibling}}
    post: branch@0 -> {leaf(63) p, leaf(63) a}, or
          branch@0 -> {leaf(63) p, branch@1 -> {sibling, branch@2 -> {..}}}
    Two subtrees under one root change in one block; the root keeps its
    two children.
    """
    p, q = TWO_SLOTS_EXT4
    a, sibling = SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1
    slot, value = second_write
    assert storage_shape([p, q, a, sibling], p) == [
        (0, "branch", 2),
        (1, "ext", 3),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    assert storage_shape([p, q, a, sibling], a)[:2] == [
        (0, "branch", 2),
        (1, "branch", 2),
    ]
    after = {p: 1, a: 3, sibling: 4}
    after.pop(slot, None)
    if value:
        after[slot] = value
    assert storage_shape(list(after), p) == [(0, "branch", 2), (1, "leaf", 63)]
    assert storage_shape(list(after), a) == post_second
    contract = pre.deploy_contract(
        code=SLOT_WRITER, storage={p: 1, q: 2, a: 3, sibling: 4}
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=after)},
        blocks=[
            Block(
                txs=[
                    _write(sender, contract, q, 0),
                    _write(sender, contract, slot, value),
                ]
            )
        ],
    )


def test_two_storage_tries_reshaped_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Collapse one contract's trie and split another's in one block.

    pre:  A: ext(4) -> branch@4 -> {p, q}    B: ext(5) -> branch@5 -> {l1, l2}
    post: A: leaf(64)                        B: ext(2) -> branch@2 -> {l3, ..}
    Two storage roots change in one diff; both feed the account trie.
    """
    p, q = TWO_SLOTS_EXT4
    l1, l2, l3 = EXT_MERGE_TRIO
    assert storage_shape([p], p) == [(0, "leaf", 64)]
    assert storage_shape([l1, l2, l3], l1)[:2] == [
        (0, "ext", 2),
        (2, "branch", 2),
    ]
    contract_a = pre.deploy_contract(code=SLOT_WRITER, storage={p: 1, q: 2})
    contract_b = pre.deploy_contract(code=SLOT_WRITER, storage={l1: 1, l2: 2})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={
            contract_a: Account(storage={p: 1}),
            contract_b: Account(storage={l1: 1, l2: 2, l3: 3}),
        },
        blocks=[
            Block(
                txs=[
                    _write(sender, contract_a, q, 0),
                    _write(sender, contract_b, l3, 3),
                ]
            )
        ],
    )


def test_shared_node_deleted_in_one_trie(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Two contracts hold byte-identical storage tries; one is emptied.

    pre:  A: leaf(64)   B: leaf(64)   (the same node, one hash)
    post: block 1: A empty, B unchanged; block 2: B grows to ext(4) -> ..
    A store keyed by node hash must keep the shared node for B after A
    deletes it.
    """
    a, b = TWO_SLOTS_EXT4
    assert storage_shape([a], a) == [(0, "leaf", 64)]
    assert storage_shape([a, b], a)[0] == (0, "ext", 4)
    contract_a = pre.deploy_contract(code=SLOT_WRITER, storage={a: 1})
    contract_b = pre.deploy_contract(code=SLOT_WRITER, storage={a: 1})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={
            contract_a: Account(storage={}),
            contract_b: Account(storage={a: 1, b: 2}),
        },
        blocks=[
            Block(
                txs=[_write(sender, contract_a, a, 0)],
                expected_post_state={
                    contract_a: Account(storage={}),
                    contract_b: Account(storage={a: 1}),
                },
            ),
            Block(txs=[_write(sender, contract_b, b, 2)]),
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
        pytest.param(
            VALUE_BOUNDARY_PAIR, 1, 30, id="depth10_value1_embedded_30"
        ),
        pytest.param(
            VALUE_BOUNDARY_PAIR, 128, 32, id="depth10_value128_hashed_32"
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
    Leaf RLP of exactly 30, 31, 32 and 33 bytes.

    pre:  empty
    post: ext(n) -> branch@n -> {leaf(63-n), leaf(63-n)}, each 30 to 33 B
    Under 32 B the leaves are inlined in the branch, from 32 B on hashed.
    32 B is reached from the key side (one more nibble at a 1-byte value)
    and from the value side (a 2-byte value at 53 nibbles).
    """
    a, b = pair
    depth, kind, rest = storage_shape([a, b], a)[-1]
    assert kind == "leaf"
    assert storage_leaf_size(rest, value) == leaf_size
    contract = pre.deploy_contract(code=_writer_code([(a, value), (b, value)]))

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: value, b: value})},
    )


@pytest.mark.parametrize(
    "new_value,new_size",
    [
        pytest.param(128, 33, id="flips_to_hashed"),
        pytest.param(2, 31, id="stays_inline"),
    ],
)
def test_update_inline_leaf(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    new_value: int,
    new_size: int,
) -> None:
    """
    Overwrite an inline leaf's value, then restore it.

    pre:  ext(8) -> branch@8 -> {leaf(55) 31 B, leaf(55) 31 B}
    post: block 1: one leaf rewritten at 33 B (hashed) or 31 B (inline);
          block 2: the pre state
    An inline leaf is rewritten inside its parent's RLP, never under a
    hash of its own.
    """
    a, b = EMBEDDED_LEAF_PAIR
    assert storage_shape([a, b], a)[-1] == (9, "leaf", 55)
    assert storage_leaf_size(55, 1) == 31
    assert storage_leaf_size(55, new_value) == new_size
    contract = pre.deploy_contract(code=SLOT_WRITER, storage={a: 1, b: 1})
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={a: 1, b: 1})},
        blocks=[
            Block(
                txs=[_write(sender, contract, a, new_value)],
                expected_post_state={
                    contract: Account(storage={a: new_value, b: 1})
                },
            ),
            Block(txs=[_write(sender, contract, a, 1)]),
        ],
    )


@pytest.mark.parametrize(
    "values,doomed,survivor_sizes",
    [
        pytest.param(
            {0: 1, 1: 1, 2: 1}, 1, (31, 33), id="deleted_inline_survivor_flips"
        ),
        pytest.param(
            {0: 1, 1: 128, 2: 1},
            0,
            (33, 35),
            id="deleted_inline_survivor_hashed",
        ),
        pytest.param(
            {0: 128, 1: 1, 2: 1},
            0,
            (31, 33),
            id="deleted_hashed_survivor_flips",
        ),
        pytest.param(
            {0: 1, 1: 1, 2: 1},
            2,
            (31, 31),
            id="deleted_hashed_siblings_inline",
        ),
    ],
)
def test_delete_around_inline_leaves(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    values: Dict[int, int],
    doomed: int,
    survivor_sizes: Tuple[int, int],
) -> None:
    """
    Delete next to inline leaves; re-insert in the next block.

    pre:  ext(4) -> branch@4 -> {c, ext(3) -> branch@8 -> {a, b}}
          a, b = leaf(55), 31 B with a 1-byte value, 33 B with 2 bytes
    post: block 1: deleting a or b collapses branch@8 and the survivor
          becomes leaf(59), 2 B larger; deleting c leaves
          ext(8) -> branch@8 -> {a, b}; block 2: the pre shape
    Two more bytes move a 31 B leaf past the hash threshold.
    """
    trio = (*EMBEDDED_LEAF_PAIR, EMBEDDED_LEAF_PAIR_SIBLING_DEPTH4)
    storage: StorageRootType = {trio[i]: v for i, v in values.items()}
    doomed_slot = trio[doomed]
    survivor = trio[0] if doomed else trio[1]
    before, after = survivor_sizes
    assert storage_shape(trio, survivor)[-1] == (9, "leaf", 55)
    assert storage_leaf_size(55, values[trio.index(survivor)]) == before
    remaining = [s for s in trio if s != doomed_slot]
    depth, kind, rest = storage_shape(remaining, survivor)[-1]
    assert storage_leaf_size(rest, values[trio.index(survivor)]) == after
    if doomed == 2:
        assert storage_shape(remaining, survivor)[0] == (0, "ext", 8)
    else:
        assert storage_shape(remaining, survivor)[-1] == (5, "leaf", 59)
    contract = pre.deploy_contract(code=SLOT_WRITER, storage=storage)
    sender = pre.fund_eoa()
    without = {s: v for s, v in storage.items() if s != doomed_slot}

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        blocks=[
            Block(
                txs=[_write(sender, contract, doomed_slot, 0)],
                expected_post_state={contract: Account(storage=without)},
            ),
            Block(txs=[_write(sender, contract, doomed_slot, values[doomed])]),
        ],
    )


@pytest.mark.parametrize(
    "doomed_value,doomed_size",
    [
        pytest.param(1, 31, id="deleted_inline"),
        pytest.param(128, 33, id="deleted_hashed"),
    ],
)
def test_delete_inline_leaf_survivor_stays_inline(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    doomed_value: int,
    doomed_size: int,
) -> None:
    """
    Collapse a branch of inline leaves; the survivor stays inline.

    pre:  ext(8) -> branch@8 -> {s, branch@9 -> {x, y}}
          x, y = leaf(54) and s = leaf(55), 31 B each with a 1-byte value;
          y is 33 B with a 2-byte value
    post: ext(8) -> branch@8 -> {s, x = leaf(55) 31 B}
    Block 2 writes y back, splitting the inline survivor again.
    """
    x, y, s = INLINE_TRIO
    assert storage_shape([x, y, s], x) == [
        (0, "ext", 8),
        (8, "branch", 2),
        (9, "branch", 2),
        (10, "leaf", 54),
    ]
    assert storage_shape([x, s], x) == [
        (0, "ext", 8),
        (8, "branch", 2),
        (9, "leaf", 55),
    ]
    assert storage_leaf_size(54, 1) == 31 and storage_leaf_size(55, 1) == 31
    assert storage_leaf_size(54, doomed_value) == doomed_size
    storage: StorageRootType = {x: 1, y: doomed_value, s: 1}
    contract = pre.deploy_contract(code=SLOT_WRITER, storage=storage)
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        blocks=[
            Block(
                txs=[_write(sender, contract, y, 0)],
                expected_post_state={contract: Account(storage={x: 1, s: 1})},
            ),
            Block(txs=[_write(sender, contract, y, doomed_value)]),
        ],
    )
