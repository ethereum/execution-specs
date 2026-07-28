"""
Tests for the raw binary tree structure.
"""

import random
import sys
from typing import Dict, Set

import pytest
from blake3 import blake3
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import Uint

from ethereum.binary_trie.trie import (
    BRANCH_NODE_TAG,
    EMPTY_TRIE_ROOT,
    LEAF_NODE_TAG,
    BinaryNode,
    BinaryTrie,
    BranchNode,
    LeafNode,
    binarize,
    bytes_to_bit_list,
    copy_trie,
    encode_bit_prefix,
    root,
    trie_get,
    trie_set,
)

from .incremental_trie import (
    IncrementalRadixTree,
    _bits,
    _branch_hash,
    _leaf_hash,
)


def test_bytes_to_bit_list_is_msb_first() -> None:
    """
    Bytes expand to bits most significant bit first.
    """
    assert bytes_to_bit_list(Bytes(b"\x80")) == Bytes(
        bytes([1, 0, 0, 0, 0, 0, 0, 0])
    )
    assert bytes_to_bit_list(Bytes(b"\x01")) == Bytes(
        bytes([0, 0, 0, 0, 0, 0, 0, 1])
    )
    assert bytes_to_bit_list(Bytes(b"\xa5")) == Bytes(
        bytes([1, 0, 1, 0, 0, 1, 0, 1])
    )


def test_encode_bit_prefix_layout() -> None:
    """
    A prefix encodes as a two-byte big-endian bit count followed by
    the bits packed most significant bit first, zero padded to a byte
    boundary.
    """
    assert encode_bit_prefix(Bytes(b"")) == b"\x00\x00"
    assert encode_bit_prefix(Bytes(bytes([1, 0, 1]))) == b"\x00\x03\xa0"
    # Nine bits cross a byte boundary into a zero-padded second byte.
    assert encode_bit_prefix(Bytes(bytes([1] * 9))) == b"\x00\x09\xff\x80"


def test_encode_bit_prefix_rejects_unrepresentable_counts() -> None:
    """
    A prefix whose bit count does not fit the two-byte field is
    rejected.
    """
    with pytest.raises(AssertionError):
        encode_bit_prefix(Bytes(bytes(2**16)))


def test_encode_bit_prefix_counts_trailing_zero_bits() -> None:
    """
    Prefixes differing only by trailing zero bits pack to the same
    bytes; the explicit count is what keeps their encodings and
    subsequently their commitments distinct.
    """
    shorter = Bytes(bytes([0, 1, 1, 0]))
    longer = Bytes(bytes([0, 1, 1, 0, 0]))

    assert encode_bit_prefix(shorter)[2:] == encode_bit_prefix(longer)[2:]
    assert encode_bit_prefix(shorter) != encode_bit_prefix(longer)


def test_empty_trie_root_is_all_zeros() -> None:
    """
    An empty trie commits to 32 zero bytes.
    """
    trie: BinaryTrie = BinaryTrie(_data={})
    assert root(trie) == b"\x00" * 32
    assert EMPTY_TRIE_ROOT == b"\x00" * 32


def test_trie_set_and_get() -> None:
    """
    Values can be stored, retrieved, and overwritten.
    """
    trie = BinaryTrie()
    key = Bytes32(b"\x01" * 32)
    value = Bytes32(b"\x02" * 32)

    assert trie_get(trie, key) is None
    trie_set(trie, key, value)
    assert trie_get(trie, key) == value

    replacement = Bytes32(b"\x03" * 32)
    trie_set(trie, key, replacement)
    assert trie_get(trie, key) == replacement


def test_trie_set_rejects_malformed_inputs() -> None:
    """
    Empty keys, keys past the maximum length, and values that are not
    32 bytes are rejected.
    """
    trie = BinaryTrie()
    with pytest.raises(AssertionError):
        trie_set(trie, Bytes(b""), Bytes32(b"\x01" * 32))
    with pytest.raises(AssertionError):
        trie_set(trie, Bytes(b"\x01" * 8193), Bytes32(b"\x01" * 32))
    with pytest.raises(AssertionError):
        trie_set(
            trie,
            Bytes(b"\x01"),
            Bytes(b"\x02" * 31),  # type: ignore[arg-type]
        )


def test_copy_trie_is_independent() -> None:
    """
    Mutating a copy leaves the original untouched, and vice versa.
    """
    key = Bytes32(b"\x01" * 32)
    other_key = Bytes32(b"\x02" * 32)
    value = Bytes32(b"\x03" * 32)

    original = BinaryTrie()
    trie_set(original, key, value)

    duplicate = copy_trie(original)
    assert trie_get(duplicate, key) == value

    trie_set(duplicate, other_key, value)
    assert trie_get(original, other_key) is None
    assert root(duplicate) != root(original)


def test_single_key_is_a_leaf_at_the_root() -> None:
    """
    A trie with one key commits to a single leaf carrying its full
    key.
    """
    key = Bytes(b"\x00" + b"\x42" * 32 + b"\x07")
    value = Bytes32(b"\x11" * 32)

    trie = BinaryTrie()
    trie_set(trie, key, value)

    assert root(trie) == _leaf_hash(key, value)


def test_keys_sharing_a_stem_split_under_one_branch() -> None:
    """
    Two keys sharing a 33-byte stem diverge in their final byte's
    first bit: a single branch carrying the whole stem as its prefix,
    over two leaves.
    """
    stem = b"\x00" + b"\x42" * 32
    low_key = Bytes(stem + b"\x00")
    high_key = Bytes(stem + b"\xff")
    low_value = Bytes32(b"\x01" * 32)
    high_value = Bytes32(b"\x02" * 32)

    trie = BinaryTrie()
    trie_set(trie, low_key, low_value)
    trie_set(trie, high_key, high_value)

    assert root(trie) == _branch_hash(
        _bits(stem),
        _leaf_hash(low_key, low_value),
        _leaf_hash(high_key, high_value),
    )


def test_first_bit_divergence_has_empty_prefix() -> None:
    """
    Keys differing in their first bit branch at the root with an
    empty prefix.
    """
    zero_key = Bytes(b"\x00" * 34)
    one_key = Bytes(b"\xff" * 66)
    value = Bytes32(b"\x33" * 32)

    trie = BinaryTrie()
    trie_set(trie, zero_key, value)
    trie_set(trie, one_key, value)

    assert root(trie) == _branch_hash(
        [], _leaf_hash(zero_key, value), _leaf_hash(one_key, value)
    )


def test_canonical_form_example() -> None:
    """
    Three keys sharing a stem, with sub-indices 0, 1, and 128: a
    branch carrying the stem as its prefix, splitting on the first
    sub-index bit; below it, a branch carrying the next six shared
    bits over the two low leaves, and the high leaf directly on the
    other side.
    """
    stem = b"\xff" + b"\xab" * 32
    key_0 = Bytes(stem + b"\x00")
    key_1 = Bytes(stem + b"\x01")
    key_128 = Bytes(stem + b"\x80")
    value = Bytes32(b"\x44" * 32)

    trie = BinaryTrie()
    for key in (key_0, key_1, key_128):
        trie_set(trie, key, value)

    low_side = _branch_hash(
        [0] * 6,
        _leaf_hash(key_0, value),
        _leaf_hash(key_1, value),
    )
    assert root(trie) == _branch_hash(
        _bits(stem), low_side, _leaf_hash(key_128, value)
    )


def test_binarize_builds_relative_prefixes_and_full_key_leaves() -> None:
    """
    Branch prefixes are relative (only the bits shared beyond the
    parent's split point), while leaves commit their complete keys
    wherever they sit in the tree.
    """
    stem = b"\xff" + b"\xab" * 32
    key_0 = Bytes(stem + b"\x00")
    key_1 = Bytes(stem + b"\x01")
    key_128 = Bytes(stem + b"\x80")
    value = Bytes32(b"\x44" * 32)

    top = binarize({key_0: value, key_1: value, key_128: value}, Uint(0))

    assert isinstance(top, BranchNode)
    assert top.prefix == bytes_to_bit_list(Bytes(stem))

    low = top.left
    assert isinstance(low, BranchNode)
    # Relative to the split above it, not 271 bits from the root.
    assert low.prefix == Bytes(bytes([0] * 6))
    assert isinstance(low.left, LeafNode)
    assert isinstance(low.right, LeafNode)
    assert low.left.key == key_0
    assert low.right.key == key_1

    high = top.right
    assert isinstance(high, LeafNode)
    assert high.key == key_128


def test_zero_value_is_not_absence() -> None:
    """
    Storing 32 zero bytes commits differently from storing nothing.
    """
    key = Bytes32(b"\x07" * 31 + b"\x00")

    trie = BinaryTrie()
    trie_set(trie, key, Bytes32(b"\x00" * 32))

    assert root(trie) != EMPTY_TRIE_ROOT


def test_prefix_key_violation_is_rejected() -> None:
    """
    A key that is a prefix of another key makes the tree ill-defined,
    and computing the root fails the prefix-freeness assertion.
    """
    trie = BinaryTrie()
    trie_set(trie, Bytes(b"\xaa" * 34), Bytes32(b"\x01" * 32))
    trie_set(trie, Bytes(b"\xaa" * 34 + b"\xbb" * 32), Bytes32(b"\x02" * 32))

    with pytest.raises(AssertionError):
        root(trie)


def test_prefix_key_violation_in_mid_byte_group_is_rejected() -> None:
    """
    A prefix-violating pair is rejected even when it is isolated only
    by a split inside a byte, so the scan that runs the shorter key
    out of bits starts at a bit position that is not byte-aligned.

    All three keys share bit 0 and diverge at bit 1, splitting
    `0x00` off and leaving the offending pair grouped at depth 2.
    """
    trie = BinaryTrie()
    trie_set(trie, Bytes(b"\x50"), Bytes32(b"\x01" * 32))
    trie_set(trie, Bytes(b"\x50\xff"), Bytes32(b"\x02" * 32))
    trie_set(trie, Bytes(b"\x00"), Bytes32(b"\x03" * 32))

    with pytest.raises(AssertionError):
        root(trie)


def random_entries(rng: random.Random) -> Dict[bytes, bytes]:
    """
    Generate a random key/value set mixing three key shapes: fully
    random keys, keys sharing an existing 31-byte prefix, and keys
    sharing a shorter prefix (forcing splits at every depth).
    """
    entries: Dict[bytes, bytes] = {}
    for _ in range(rng.randrange(1, 40)):
        key = rng.randbytes(32)
        entries[key] = rng.randbytes(32)

        # Same first 31 bytes, different final byte: long shared
        # prefixes carried by one branch.
        for _ in range(rng.randrange(0, 3)):
            entries[key[:31] + rng.randbytes(1)] = rng.randbytes(32)

        # Same first 1, 7, or 30 bytes: splits 8, 56, or 240 bits
        # deep.
        for prefix_length in (1, 7, 30):
            if rng.random() < 0.2:
                cousin = (
                    key[:prefix_length]
                    + rng.randbytes(31 - prefix_length)
                    + rng.randbytes(1)
                )
                entries[cousin] = rng.randbytes(32)
    return entries


def test_root_matches_reference_implementation() -> None:
    """
    Randomized key/value sets produce the same root in the spec-style
    rebuild and the insertion-based reference.
    """
    rng = random.Random(8297)

    for trial in range(20):
        entries = random_entries(rng)

        reference = IncrementalRadixTree()
        trie = BinaryTrie()
        for key, value in entries.items():
            reference.insert(key, value)
            trie_set(trie, Bytes(key), Bytes32(value))

        assert root(trie) == reference.merkelize(), f"trial {trial}"


def test_root_matches_reference_with_variable_length_keys() -> None:
    """
    Keys shaped like the embedding's (34-byte account and code keys,
    66-byte storage keys) produce the same root in both
    implementations when mixed in one tree.
    """
    rng = random.Random(11832)

    for trial in range(10):
        entries: Dict[bytes, bytes] = {}
        for _ in range(rng.randrange(1, 30)):
            if rng.random() < 0.5:
                # Account or code zone: 34-byte keys.
                prefix = bytes([rng.choice((0, 1))]) + rng.randbytes(32)
            else:
                # Storage zone: 66-byte keys.
                prefix = b"\xff" + rng.randbytes(64)
            for _ in range(rng.randrange(1, 4)):
                entries[prefix + rng.randbytes(1)] = rng.randbytes(32)

        reference = IncrementalRadixTree()
        trie = BinaryTrie()
        for key, value in entries.items():
            reference.insert(key, value)
            trie_set(trie, Bytes(key), Bytes32(value))

        assert root(trie) == reference.merkelize(), f"trial {trial}"


def test_root_is_insertion_order_independent() -> None:
    """
    The root depends only on the contents, not insertion order.
    """
    rng = random.Random(1234)
    entries = [
        (Bytes32(rng.randbytes(32)), Bytes32(rng.randbytes(32)))
        for _ in range(16)
    ]

    forward = BinaryTrie()
    for key, value in entries:
        trie_set(forward, key, value)

    backward = BinaryTrie()
    for key, value in reversed(entries):
        trie_set(backward, key, value)

    assert root(forward) == root(backward)


def test_reference_roots_are_insertion_order_independent() -> None:
    """
    The insertion-based reference converges to the same canonical
    structure whatever order keys arrive in.

    The rebuild-based spec is order-independent trivially; for the
    incremental reference it is the canonicity property that splits
    happening in different sequences must produce one structure.
    """
    rng = random.Random(3102)

    for trial in range(10):
        entries = list(random_entries(rng).items())

        trie = BinaryTrie()
        for key, value in entries:
            trie_set(trie, Bytes(key), Bytes32(value))
        expected = root(trie)

        for _ in range(3):
            rng.shuffle(entries)
            reference = IncrementalRadixTree()
            for key, value in entries:
                reference.insert(key, value)
            assert reference.merkelize() == expected, f"trial {trial}"


def test_overwriting_a_value_recommits_to_the_final_value() -> None:
    """
    Overwriting a key's value changes the root and matches a trie
    that only ever held the final value; the insertion-based
    reference reaches the same root through its equal-key path.
    """
    stem = b"\x00" + b"\x42" * 32
    key = Bytes(stem + b"\x07")
    neighbour = Bytes(stem + b"\x08")
    first = Bytes32(b"\x01" * 32)
    second = Bytes32(b"\x02" * 32)

    overwritten = BinaryTrie()
    trie_set(overwritten, key, first)
    trie_set(overwritten, neighbour, first)
    old_root = root(overwritten)
    trie_set(overwritten, key, second)

    fresh = BinaryTrie()
    trie_set(fresh, key, second)
    trie_set(fresh, neighbour, first)

    reference = IncrementalRadixTree()
    reference.insert(key, first)
    reference.insert(neighbour, first)
    reference.insert(key, second)

    assert root(overwritten) != old_root
    assert root(overwritten) == root(fresh)
    assert reference.merkelize() == root(fresh)


def test_leaf_preimage_golden_vector() -> None:
    """
    A single-leaf trie's root is the direct BLAKE3 hash of the leaf
    tag, key, and value.

    Reconstructed here by calling `blake3` directly, independent of
    `merkleize`, `blake3_hash`, and the incremental reference, to pin
    the documented leaf preimage layout on its own.
    """
    key = Bytes(b"\x00" + b"\xab" * 33)
    value = Bytes32(b"\x99" * 32)

    trie = BinaryTrie()
    trie_set(trie, key, value)

    assert root(trie) == blake3(b"\x00" + key + value).digest()


def test_branch_preimage_golden_vector() -> None:
    """
    A two-leaf branch's root is the direct BLAKE3 hash of the branch
    tag, a hand-packed prefix encoding, and the two leaf hashes.

    The 33-byte shared stem is exactly 264 bits, a byte boundary, so
    its most-significant-bit-first packing is the stem's own bytes;
    only the 2-byte big-endian bit count (0x0108) is prepended by
    hand, without calling `encode_bit_prefix`.
    """
    stem = b"\x11" * 33
    low_key = Bytes(stem + b"\x00")
    high_key = Bytes(stem + b"\x80")
    low_value = Bytes32(b"\x22" * 32)
    high_value = Bytes32(b"\x33" * 32)

    trie = BinaryTrie()
    trie_set(trie, low_key, low_value)
    trie_set(trie, high_key, high_value)

    prefix_encoding = b"\x01\x08" + stem
    leaf_lo = blake3(b"\x00" + low_key + low_value).digest()
    leaf_hi = blake3(b"\x00" + high_key + high_value).digest()
    expected = blake3(b"\x01" + prefix_encoding + leaf_lo + leaf_hi).digest()

    assert root(trie) == expected


def test_fixed_trie_root_is_pinned() -> None:
    """
    A small fixed trie spanning the embedding's three key shapes
    commits to a hardcoded root hash.

    This is a deliberate change-detector for the hash function, node
    tags, and prefix encoding: the EIP still debates the hash choice,
    and this test is meant to fail loudly the moment any of them
    change. To regenerate the constant after a deliberate, reviewed
    change: print `root(trie).hex()` for this same trie and paste the
    new value below.
    """
    key_a = Bytes(b"\x00" + b"\x11" * 33)  # 34-byte key, 0x00 zone
    key_b = Bytes(b"\x01" + b"\x22" * 33)  # 34-byte key, 0x01 zone
    key_c = Bytes(b"\xff" + b"\x33" * 65)  # 66-byte key, 0xff zone

    trie = BinaryTrie()
    trie_set(trie, key_a, Bytes32(b"\xaa" * 32))
    trie_set(trie, key_b, Bytes32(b"\xbb" * 32))
    trie_set(trie, key_c, Bytes32(b"\xcc" * 32))

    assert root(trie) == bytes.fromhex(
        "580244b78611bbadd6b4b743bb973a6e4d7bcce6458a39450fc51d552437ec5a"
    )


def test_leaf_and_branch_tags_are_domain_separated() -> None:
    """
    Leaf and branch nodes hash under different, fixed tag bytes, so
    the same payload can never collide between the two node types.
    """
    assert LEAF_NODE_TAG == b"\x00"
    assert BRANCH_NODE_TAG == b"\x01"

    payload = b"\x99" * 40
    assert (
        blake3(LEAF_NODE_TAG + payload).digest()
        != blake3(BRANCH_NODE_TAG + payload).digest()
    )


def test_max_length_keys_diverging_at_last_bit() -> None:
    """
    Two maximum-length (8192-byte) keys differing only in their final
    bit are accepted and pin the branch preimage at the deepest
    prefix the encoding can represent.
    """
    low_key = Bytes(b"\xab" * 8191 + b"\xfe")
    high_key = Bytes(b"\xab" * 8191 + b"\xff")
    low_value = Bytes32(b"\x01" * 32)
    high_value = Bytes32(b"\x02" * 32)

    trie = BinaryTrie()
    trie_set(trie, low_key, low_value)
    trie_set(trie, high_key, high_value)

    shared_bits = bytes_to_bit_list(low_key)[:-1]
    assert len(shared_bits) == 65535

    expected = blake3(
        b"\x01"
        + encode_bit_prefix(Bytes(shared_bits))
        + _leaf_hash(low_key, low_value)
        + _leaf_hash(high_key, high_value)
    ).digest()
    assert root(trie) == expected

    # Exact-boundary accept side of the two-byte count field; the
    # 65536 reject already exists in
    # test_encode_bit_prefix_rejects_unrepresentable_counts.
    assert encode_bit_prefix(Bytes(bytes(2**16 - 1)))[:2] == b"\xff\xff"


def test_trie_set_rejects_zero_and_thirty_three_byte_values() -> None:
    """
    Values shorter or longer than 32 bytes are rejected.
    """
    trie = BinaryTrie()
    with pytest.raises(AssertionError):
        trie_set(
            trie,
            Bytes(b"\x01"),
            Bytes(b""),  # type: ignore[arg-type]
        )
    with pytest.raises(AssertionError):
        trie_set(
            trie,
            Bytes(b"\x02"),
            Bytes(b"\x03" * 33),  # type: ignore[arg-type]
        )


def test_root_is_idempotent_and_does_not_mutate() -> None:
    """
    Computing the root does not mutate the trie's stored entries, and
    repeated calls return the same value.
    """
    rng = random.Random(42)
    trie = BinaryTrie()
    for _ in range(5):
        trie_set(trie, Bytes(rng.randbytes(32)), Bytes32(rng.randbytes(32)))

    snapshot = dict(trie._data)
    first = root(trie)
    second = root(trie)

    assert first == second
    assert trie._data == snapshot


def test_prefix_violation_only_fails_at_root_time() -> None:
    """
    A prefix-violating pair of keys is accepted and stays readable
    through ordinary `trie_set`/`trie_get` calls; prefix-freeness is
    only enforced lazily, when `root` walks the tree.

    EIP-8297's "Tree structure" section places this rejection in
    `insert` itself ("`insert` rejects keys that violate either
    constraint"); this reference implementation's `trie_set` instead
    defers that enforcement to `root()`, the same disclosure
    treatment the zero-value/absence divergence already receives
    elsewhere in this tree. The practical consequence is nil for a
    rebuild-based reference that always calls `root()` before
    trusting a commitment, which is exactly why it is disclosed
    rather than fixed.
    """
    prefix_key = Bytes(b"\x50" * 34)
    extended_key = Bytes(b"\x50" * 34 + b"\x60")
    prefix_value = Bytes32(b"\x01" * 32)
    extended_value = Bytes32(b"\x02" * 32)

    trie = BinaryTrie()
    trie_set(trie, prefix_key, prefix_value)
    trie_set(trie, extended_key, extended_value)

    assert trie_get(trie, prefix_key) == prefix_value
    assert trie_get(trie, extended_key) == extended_value

    with pytest.raises(AssertionError):
        root(trie)


def assert_canonical_structure(
    node: BinaryNode, keys: Set[Bytes], depth: Uint
) -> None:
    """
    Check that `node` is the canonical `binarize` encoding of `keys`,
    whose members all share their first `depth` bits.

    Recomputes each branch's split independently from `keys` (rather
    than trusting the node's own claimed prefix) to confirm: both of
    a branch's subtrees are non-empty; its prefix is exactly the run
    all of `keys` share from `depth`; at the split bit, the keys
    partition into the left (0) and right (1) subtrees with both
    sides non-empty, which is what makes the prefix maximal; and
    every leaf's key is one of `keys`, placing it on the path its own
    bits take.
    """
    if len(keys) == 1:
        assert isinstance(node, LeafNode)
        assert node.key in keys
        return

    assert isinstance(node, BranchNode)
    bit_lists = {key: bytes_to_bit_list(key) for key in keys}

    for offset, prefix_bit in enumerate(node.prefix):
        position = depth + Uint(offset)
        for bits in bit_lists.values():
            assert bits[position] == prefix_bit

    split = depth + Uint(len(node.prefix))
    left_keys = {key for key in keys if bit_lists[key][split] == 0}
    right_keys = {key for key in keys if bit_lists[key][split] == 1}

    assert len(left_keys) > 0
    assert len(right_keys) > 0
    assert isinstance(node.left, (BranchNode, LeafNode))
    assert isinstance(node.right, (BranchNode, LeafNode))

    assert_canonical_structure(node.left, left_keys, split + Uint(1))
    assert_canonical_structure(node.right, right_keys, split + Uint(1))


def test_canonical_structure_holds_for_fixed_trie() -> None:
    """
    The fixed trie from `test_fixed_trie_root_is_pinned` binarizes
    into a canonical structure.
    """
    entries = {
        Bytes(b"\x00" + b"\x11" * 33): Bytes32(b"\xaa" * 32),
        Bytes(b"\x01" + b"\x22" * 33): Bytes32(b"\xbb" * 32),
        Bytes(b"\xff" + b"\x33" * 65): Bytes32(b"\xcc" * 32),
    }

    top = binarize(entries, Uint(0))

    assert_canonical_structure(top, set(entries.keys()), Uint(0))


def test_canonical_structure_holds_for_random_corpora() -> None:
    """
    `binarize` produces a canonical structure over many random
    key/value corpora, not merely the same root as the reference.
    """
    rng = random.Random(90210)

    for trial in range(10):
        entries = {
            Bytes(key): Bytes32(value)
            for key, value in random_entries(rng).items()
        }

        top = binarize(entries, Uint(0))
        try:
            assert_canonical_structure(top, set(entries.keys()), Uint(0))
        except AssertionError as exc:
            raise AssertionError(f"trial {trial}") from exc


def _thermometer_key(ones: int, total_bits: int) -> bytes:
    """
    Build the `total_bits`-bit key whose first `ones` bits are one
    and the remainder are zero, most significant bit first.
    """
    value = (2**ones - 1) << (total_bits - ones)
    return value.to_bytes(total_bits // 8, "big")


def test_deep_thermometer_chain_matches_reference() -> None:
    """
    A "thermometer" key set, one 66-byte key per possible run length
    of leading one-bits, forces the deepest branch chain equal-length
    keys can produce.

    All 529 keys share the same length, so they are trivially
    prefix-free; each differs from its neighbours only in where its
    run of one-bits ends, splitting off its own branch one level
    below the last, 528 levels deep in total. The rebuild-based spec
    and the insertion-based reference agree on its root.
    """
    total_bits = 8 * 66
    entries = {
        Bytes(_thermometer_key(ones, total_bits)): Bytes32(
            bytes([ones % 256]) * 32
        )
        for ones in range(total_bits + 1)
    }

    reference = IncrementalRadixTree()
    trie = BinaryTrie()
    for key, value in entries.items():
        reference.insert(key, value)
        trie_set(trie, key, value)

    assert root(trie) == reference.merkelize()


def test_deep_chain_past_recursion_limit_is_an_implementation_limit() -> None:
    """
    A branch chain deeper than Python's recursion limit overflows
    `root`'s recursive walk with `RecursionError`, even though
    nothing about the chain violates the tree's rules.

    The limit is lowered here only to make the failure cheap to
    trigger. At the interpreter's default limit (raised to 12288 by
    `ethereum/__init__.py`), the same failure is reachable with legal
    maximum-length (8192-byte) keys, whose shared-prefix chains can
    run up to 65535 branches deep; this is therefore a limit of this
    reference implementation, not a rule the specification imposes.
    """
    total_bits = 8 * 34
    entries = {
        Bytes(_thermometer_key(ones, total_bits)): Bytes32(b"\x01" * 32)
        for ones in range(260)
    }

    trie = BinaryTrie()
    for key, value in entries.items():
        trie_set(trie, key, value)

    old_limit = sys.getrecursionlimit()
    # 260 branches is already deep enough at this lowered limit; see
    # the docstring for why the same failure applies to legal inputs
    # at the default limit.
    sys.setrecursionlimit(200)
    try:
        with pytest.raises(RecursionError):
            root(trie)
    finally:
        sys.setrecursionlimit(old_limit)


def _large_variable_length_entries(
    rng: random.Random, count: int
) -> Dict[bytes, bytes]:
    """
    Generate `count` entries mixing 34-byte account/code-zone keys
    and 66-byte storage-zone keys, plus a handful of 200-byte keys in
    a fourth zone.

    Every zone uses a fixed, disjoint leading byte, so no key can
    ever be a prefix of one from another zone regardless of the
    random bytes that follow.
    """
    entries: Dict[bytes, bytes] = {}
    long_key_count = min(8, count // 20)
    for _ in range(long_key_count):
        entries[b"\x02" + rng.randbytes(199)] = rng.randbytes(32)
    while len(entries) < count:
        if rng.random() < 0.5:
            key = bytes([rng.choice((0, 1))]) + rng.randbytes(33)
        else:
            key = b"\xff" + rng.randbytes(65)
        entries[key] = rng.randbytes(32)
    return entries


@pytest.mark.parametrize("seed", [20260727, 5551212, 918273645])
def test_larger_random_corpora_match_reference(seed: int) -> None:
    """
    Larger, more varied corpora of 300-800 entries spanning three key
    lengths still agree between the rebuild-based spec and the
    insertion-based reference.
    """
    rng = random.Random(seed)
    count = rng.randrange(300, 801)
    entries = _large_variable_length_entries(rng, count)

    reference = IncrementalRadixTree()
    trie = BinaryTrie()
    for key, value in entries.items():
        reference.insert(key, value)
        trie_set(trie, Bytes(key), Bytes32(value))

    assert root(trie) == reference.merkelize()
