"""
Exercise the Merkle Patricia Trie as a data structure via storage slots.

Every test writes storage slots whose keccak256 hashes were chosen (see
`constants.py`) to force one specific node operation: a leaf split, an
extension split, a branch collapse, an extension merge, or a change of a
leaf's RLP size across the 32-byte inlining threshold. The committed
`stateRoot` is the oracle: a client that reshapes or encodes a node
differently from the reference `patricialize` disagrees on the root.

Each docstring gives the node path along the slot of interest as
`pre:`/`post:` lines in the notation `ext(n) -> branch@d -> {children}`,
where `n` counts extension nibbles, `d` is the branch's depth in nibbles
and `leaf(r)` a leaf with `r` remaining nibbles; the same shapes are
asserted at fill time against `patricialize`.

Writes go through `SLOT_WRITER`, which stores `calldata[32:64]` at slot
`calldata[0:32]`, so successive transactions or blocks can write different
slots to one contract; single-transaction tests use fixed code instead.
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
    Op,
    StateTestFiller,
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
    SINGLE_SLOT,
    SINGLE_SLOT_SIBLING_DEPTH1,
    SINGLE_SLOT_SIBLING_DEPTH2,
    SIXTEEN_SLOTS_BRANCH4,
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


def _storage(slots: Sequence[int]) -> Dict[int, int]:
    """Storage mapping `slot -> position + 1` for `slots`."""
    assert len(set(slots)) == len(slots)
    return {slot: i + 1 for i, slot in enumerate(slots)}


def _alloc(values: Dict[int, int]) -> StorageRootType:
    """`values` typed for `deploy_contract(storage=...)`."""
    storage: StorageRootType = {}
    for slot, value in values.items():
        storage[slot] = value
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

    pre:  branch@0 -> {leaf(63) SINGLE_SLOT, leaf(63)}
    post: branch@0 -> {ext(1) -> branch@2 -> {..}, leaf(63)}   two shared
          branch@0 -> {branch@1 -> {..}, leaf(63)}             one shared
    The split result is re-parented into the existing slot, not the root.
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

    pre:  ext(4) -> branch@4 -> {..}
    post: branch@0 -> {ext(3) -> branch@4 -> {..}, leaf(63)}
    pre:  ext(1) -> branch@1 -> {..}
    post: branch@0 -> {branch@1 -> {..}, leaf(63)}
    A 1-nibble extension vanishes; no zero-length extension is created.
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
        code=_writer_code([(new_slot, 3)]), storage=_alloc(storage)
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
    Split an extension that hangs off a root branch, at every offset.

    pre:  branch@0 -> {ext(3) -> branch@4 -> {p, q}, leaf(63)}
    post: branch@0 -> {branch@1 -> {new, ext(2) -> ..}, ..}     offset 0
          branch@0 -> {ext(1) -> branch@2 -> {new, ext(1) ..}}  middle
          branch@0 -> {ext(2) -> branch@3 -> {new, branch@4}}   last
    pre:  branch@0 -> {ext(1) -> branch@2 -> {..}, leaf(63)}
    post: branch@0 -> {branch@1 -> {new, branch@2 -> {..}}}     vanishes
    The split result is re-parented into the root branch's slot.
    """
    target = committed[0]
    assert storage_shape(committed, target)[0] == (0, "branch", 2)
    assert storage_shape(committed, target)[1][1] == "ext"
    assert storage_shape([*committed, new_slot], target) == post_shape
    storage = _storage(committed)
    contract = pre.deploy_contract(
        code=_writer_code([(new_slot, 9)]), storage=_alloc(storage)
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={**storage, new_slot: 9})},
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
    Zero a slot that is not in the trie.

    pre:  leaf(64) / ext(5) -> branch@5 / ext(4) -> branch@4 (15 children)
    post: identical
    Control: the walk ends at a different leaf, inside an extension, or in
    an empty branch slot; clients skip the write in their state layer and
    the root must equal the pre-state root.
    """
    storage = _storage(committed)
    assert storage_shape(committed, committed[0]) == pre_shape
    assert absent not in storage
    contract = pre.deploy_contract(
        code=_writer_code([(absent, 0)]), storage=_alloc(storage)
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage=storage)},
    )


def test_delete_collapses_branch_into_leaf(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Delete one of two siblings under a root extension.

    pre:  ext(4) -> branch@4 -> {leaf(59), leaf(59)}
    post: leaf(64)
    The survivor absorbs the branch nibble and the extension.
    """
    a, b = TWO_SLOTS_EXT4
    assert storage_shape([a, b], b)[:2] == [(0, "ext", 4), (4, "branch", 2)]
    assert storage_shape([b], b) == [(0, "leaf", 64)]
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
    Delete the shallow sibling of a nested extension.

    pre:  ext(2) -> branch@2 -> {l3, ext(2) -> branch@5 -> {l1, l2}}
    post: ext(5) -> branch@5 -> {l1, l2}
    Two extensions and the collapsed branch's nibble merge into one.
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    assert storage_shape([l1, l2, l3], l1)[:3] == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "ext", 2),
    ]
    assert storage_shape([l1, l2], l1)[0] == (0, "ext", 5)
    contract = pre.deploy_contract(
        code=_writer_code([(l3, 0)]), storage={l1: 1, l2: 2, l3: 3}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={l1: 1, l2: 2})},
    )


def test_delete_collapses_into_nested_extension(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Delete a deep sibling; the survivor merges into a non-root extension.

    pre:  ext(2) -> branch@2 -> {l3, ext(2) -> branch@5 -> {l1, l2}}
    post: ext(2) -> branch@2 -> {l3, leaf(61)}
    The merged leaf sits under branch@2 rather than becoming the root, so
    the merge and the parent branch's slot update happen together.
    """
    l1, l2, l3 = EXT_MERGE_TRIO
    assert storage_shape([l1, l2, l3], l2)[2:] == [
        (3, "ext", 2),
        (5, "branch", 2),
        (6, "leaf", 58),
    ]
    assert storage_shape([l2, l3], l2) == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "leaf", 61),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(l1, 0)]), storage={l1: 1, l2: 2, l3: 3}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={l2: 2, l3: 3})},
    )


def test_delete_collapses_branch_onto_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Delete the leaf sibling of a branch under a root extension.

    pre:  ext(2) -> branch@2 -> {c, branch@3 -> {a, b}}
    post: ext(3) -> branch@3 -> {a, b}
    The survivor is a branch; the extension grows by one nibble.
    """
    a, b, c = BRANCH_SURVIVOR_TRIO
    assert storage_shape([a, b, c], a) == [
        (0, "ext", 2),
        (2, "branch", 2),
        (3, "branch", 2),
        (4, "leaf", 60),
    ]
    assert storage_shape([a, b], a) == [
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
    Delete one of two leaves under a root branch.

    pre:  branch@0 -> {leaf(63), leaf(63)}
    post: leaf(64)
    """
    a, b = ROOT_PAIR
    assert storage_shape([a, b], a) == [(0, "branch", 2), (1, "leaf", 63)]
    assert storage_shape([b], b) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(
        code=_writer_code([(a, 0)]), storage={a: 1, b: 2}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={b: 2})},
    )


def test_delete_under_branch_parent_leaf_survivor(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Collapse a branch whose parent is a branch, onto a leaf.

    pre:  branch@0 -> {branch@1 -> {leaf(62), leaf(62)}, leaf(63)}
    post: branch@0 -> {leaf(63), leaf(63)}
    Nothing merges: the survivor only gains the branch nibble.
    """
    a, sibling, other = SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]
    assert storage_shape([a, sibling, other], a) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "leaf", 62),
    ]
    assert storage_shape([a, other], a) == [(0, "branch", 2), (1, "leaf", 63)]
    contract = pre.deploy_contract(
        code=_writer_code([(sibling, 0)]),
        storage={a: 1, sibling: 2, other: 3},
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={a: 1, other: 3})},
    )


def test_delete_under_branch_parent_branch_survivor(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Collapse a branch whose parent is a branch, onto a branch.

    pre:  branch@0 -> {branch@1 -> {leaf, branch@2 -> {..}}, leaf(63)}
    post: branch@0 -> {ext(1) -> branch@2 -> {..}, leaf(63)}
    A fresh 1-nibble extension appears between two branches.
    """
    a, d1, d2, other = (
        SINGLE_SLOT,
        SINGLE_SLOT_SIBLING_DEPTH1,
        SINGLE_SLOT_SIBLING_DEPTH2,
        ROOT_PAIR[1],
    )
    assert storage_shape([a, d1, d2, other], a) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "branch", 2),
        (3, "leaf", 61),
    ]
    assert storage_shape([a, d2, other], a) == [
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


def test_delete_root_branch_onto_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Collapse the root branch onto a branch.

    pre:  branch@0 -> {branch@1 -> {leaf(62), leaf(62)}, leaf(63)}
    post: ext(1) -> branch@1 -> {leaf(62), leaf(62)}
    The root changes kind from branch to extension.
    """
    a, sibling, other = SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]
    assert storage_shape([a, sibling, other], a) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "leaf", 62),
    ]
    assert storage_shape([a, sibling], a) == [
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


def test_delete_root_branch_onto_extension(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Collapse the root branch onto an extension.

    pre:  branch@0 -> {ext(3) -> branch@4 -> {p, q}, leaf(63)}
    post: ext(4) -> branch@4 -> {p, q}
    The root changes kind from branch to extension and the extension
    grows by the branch nibble; the last survivor-parent cell.
    """
    p, q = TWO_SLOTS_EXT4
    other = SINGLE_SLOT
    assert storage_shape([p, q, other], p) == [
        (0, "branch", 2),
        (1, "ext", 3),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    assert storage_shape([p, q], p) == [
        (0, "ext", 4),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(other, 0)]), storage={p: 1, q: 2, other: 3}
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={p: 1, q: 2})},
    )


def test_delete_under_branch_parent_extension_survivor(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Collapse a branch whose parent is a branch, onto an extension.

    pre:  branch@0 -> {branch@1 -> {leaf, ext(2) -> branch@4 -> {..}}, ..}
    post: branch@0 -> {ext(3) -> branch@4 -> {..}, ..}
    The extension grows by the branch nibble; nothing above it merges.
    """
    p, q = TWO_SLOTS_EXT4
    sibling, other = TWO_SLOTS_EXT4_SIBLING_DEPTH1, SINGLE_SLOT
    assert storage_shape([p, q, sibling, other], p) == [
        (0, "branch", 2),
        (1, "branch", 2),
        (2, "ext", 2),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    assert storage_shape([p, q, other], p) == [
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
    """
    Delete one of sixteen children.

    pre:  ext(4) -> branch@4 -> {16 x leaf(59)}
    post: ext(4) -> branch@4 -> {15 x leaf(59)}
    """
    slots = SIXTEEN_SLOTS_BRANCH4
    storage = _storage(slots)
    remaining = {s: v for s, v in storage.items() if s != slots[0]}
    assert storage_shape(slots, slots[1])[1] == (4, "branch", 16)
    assert storage_shape(slots[1:], slots[1])[1] == (4, "branch", 15)
    contract = pre.deploy_contract(
        code=_writer_code([(slots[0], 0)]), storage=_alloc(storage)
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
    Delete one of three children: the smallest non-collapsing delete.

    pre:  ext(4) -> branch@4 -> {leaf, leaf, leaf}
    post: ext(4) -> branch@4 -> {leaf, leaf}
    A client that collapses at two remaining children fails here and
    passes the 16-to-15 case.
    """
    slots = SIXTEEN_SLOTS_BRANCH4[:3]
    assert storage_shape(slots, slots[1]) == [
        (0, "ext", 4),
        (4, "branch", 3),
        (5, "leaf", 59),
    ]
    assert storage_shape(slots[1:], slots[1]) == [
        (0, "ext", 4),
        (4, "branch", 2),
        (5, "leaf", 59),
    ]
    contract = pre.deploy_contract(
        code=_writer_code([(slots[0], 0)]), storage=_alloc(_storage(slots))
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={slots[1]: 2, slots[2]: 3})},
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

    pre:  ext(4) -> branch@4 -> {16 x leaf}  /  branch@0 -> {..}  /  leaf
    post: empty
    Every root kind reaches the empty trie root.
    """
    assert storage_shape(slots, slots[0])[0][1] == root_kind
    contract = pre.deploy_contract(
        code=_writer_code([(s, 0) for s in slots]),
        storage=_alloc(_storage(slots)),
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=contract),
        post={contract: Account(storage={})},
    )


# --- deletes against nodes built by an earlier block --------------------


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
        pytest.param(
            SIXTEEN_SLOTS_BRANCH4[:3],
            SIXTEEN_SLOTS_BRANCH4[0],
            id="three_to_two",
        ),
        pytest.param(
            (SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]),
            SINGLE_SLOT_SIBLING_DEPTH1,
            id="leaf_under_branch",
        ),
        pytest.param(
            (*TWO_SLOTS_EXT4, TWO_SLOTS_EXT4_SIBLING_DEPTH1, SINGLE_SLOT),
            TWO_SLOTS_EXT4_SIBLING_DEPTH1,
            id="ext_under_branch",
        ),
        pytest.param(
            (
                SINGLE_SLOT,
                SINGLE_SLOT_SIBLING_DEPTH1,
                SINGLE_SLOT_SIBLING_DEPTH2,
                ROOT_PAIR[1],
            ),
            SINGLE_SLOT_SIBLING_DEPTH1,
            id="branch_under_branch",
        ),
        pytest.param(
            (SINGLE_SLOT, SINGLE_SLOT_SIBLING_DEPTH1, ROOT_PAIR[1]),
            ROOT_PAIR[1],
            id="root_onto_branch",
        ),
        pytest.param(
            (*TWO_SLOTS_EXT4, SINGLE_SLOT),
            SINGLE_SLOT,
            id="root_onto_ext",
        ),
        pytest.param(EXT_MERGE_TRIO, EXT_MERGE_TRIO[0], id="nested_ext_leaf"),
    ],
)
def test_delete_against_committed_trie(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    group: Sequence[int],
    target: int,
) -> None:
    """
    Insert a group in block 1, delete `target` in block 2, re-insert it in
    block 3.

    pre:  empty
    post: the group's shape, after a round trip through the reduced shape
    Every collapse cell of the genesis-committed tests, replayed on nodes
    the client itself built in block 1 (its diff layer or dirty cache)
    rather than imported at genesis; block 3 splits the reduced shape
    back open the same way.
    """
    values = _storage(group)
    without = {s: v for s, v in values.items() if s != target}
    survivor = next(s for s in group if s != target)
    assert storage_shape(group, survivor) != storage_shape(
        list(without), survivor
    )
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
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Zero fifteen of sixteen children in one block.

    pre:  ext(4) -> branch@4 -> {16 x leaf(59)}
    post: leaf(64)
    One block diff takes the branch from 16 children to a collapsed leaf.
    """
    slots = SIXTEEN_SLOTS_BRANCH4
    survivor, doomed = slots[0], slots[1:]
    assert storage_shape(slots, survivor)[1] == (4, "branch", 16)
    assert storage_shape([survivor], survivor) == [(0, "leaf", 64)]
    contract = pre.deploy_contract(
        code=_writer_code([(s, 0) for s in doomed]),
        storage=_alloc(_storage(slots)),
    )

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={survivor: 1})},
        blocks=[Block(txs=[Transaction(sender=pre.fund_eoa(), to=contract)])],
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
    Write a slot and zero it again within one block.

    pre:  leaf(64) / ext(5) -> branch@5 / ext(4) -> branch@4 (15 children)
    post: identical, storage root byte-identical to genesis
    Control: the transient write would split a leaf, split an extension or
    fill a branch slot; the block diff must leave no residue of it.
    """
    storage = _storage(committed)
    assert storage_shape([*committed, slot], slot) != storage_shape(
        committed, committed[0]
    )
    contract = pre.deploy_contract(code=SLOT_WRITER, storage=_alloc(storage))
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


@pytest.mark.parametrize("new_value", [2, 5], ids=["same_value", "new_value"])
def test_delete_then_reinsert_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc, new_value: int
) -> None:
    """
    Zero a slot and write it back within one block.

    pre:  ext(4) -> branch@4 -> {leaf(59), leaf(59)}
    post: identical shape; same_value leaves the root byte-identical
    Control: a delete marker must not shadow the later write.
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
    The collapsed leaf must carry the survivor's new value.
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

    pre:  branch@0 -> {leaf(63) SINGLE_SLOT, leaf(63)}
    post: branch@0 -> {leaf(63) sibling, leaf(63)}
    The child count is unchanged while the slot's content is swapped; had
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
    Neither the pre shape nor either single-step result; sorted appliers
    apply the insert first, node walkers the delete first.
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
    post: ext(8) -> branch@8 -> {leaf(55), leaf(55)}   31 B inline, 33 B
          ext(7) -> branch@7 -> {leaf(56), leaf(56)}   32 B hashed
          ext(10) -> branch@10 -> {leaf(53), leaf(53)} 30 B inline, 32 B
    Exactly 32 bytes is reached from the key side (one more nibble at a
    1-byte value) and from the value side (a 2-byte value at 53 nibbles).
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
    post: block 1: the leaf is 33 B hashed, or still 31 B inline with a
          different 1-byte value; block 2: the pre state
    Each step commits. The inline case rewrites the leaf inside its
    parent's RLP without ever giving it a hash of its own.
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
          a, b = leaf(55): 31 B inline with a 1-byte value, 33 B hashed
          with a 2-byte value; c = leaf(59), always hashed
    post: deleting a or b: branch@8 collapses, the survivor becomes a
          leaf(59) under branch@4 (31 -> 33 B flips inline to hashed,
          33 -> 35 B stays hashed); deleting c: ext(8) -> branch@8 with
          both leaves still inline
    Block 2 restores the pre shape, re-inlining what block 1 hashed.
    """
    trio = (*EMBEDDED_LEAF_PAIR, EMBEDDED_LEAF_PAIR_SIBLING_DEPTH4)
    storage = {trio[i]: v for i, v in values.items()}
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
    contract = pre.deploy_contract(code=SLOT_WRITER, storage=_alloc(storage))
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
            Block(
                txs=[
                    _write(sender, contract, doomed_slot, storage[doomed_slot])
                ]
            ),
        ],
    )


@pytest.mark.parametrize(
    "doomed_value", [1, 128], ids=["deleted_inline", "deleted_hashed"]
)
def test_delete_inline_leaf_survivor_stays_inline(
    blockchain_test: BlockchainTestFiller, pre: Alloc, doomed_value: int
) -> None:
    """
    Collapse a branch of inline leaves; the survivor stays inline.

    pre:  ext(8) -> branch@8 -> {s, branch@9 -> {x, y}}
          x, y = leaf(54) 31 B, s = leaf(55) 31 B, all inline with 1-byte
          values; y is 33 B hashed when its value has 2 bytes
    post: ext(8) -> branch@8 -> {s, x = leaf(55) 31 B}   still inline
    Block 2 re-inserts y, splitting an inline leaf into two inline ones.
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
    assert storage_leaf_size(54, doomed_value) in (31, 33)
    storage = {x: 1, y: doomed_value, s: 1}
    contract = pre.deploy_contract(code=SLOT_WRITER, storage=_alloc(storage))
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
