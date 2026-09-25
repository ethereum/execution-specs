"""Tests for the incremental MPT witness decoding and HashedNode."""

from typing import Any

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes

from ethereum.crypto.hash import keccak256
from ethereum.forks.amsterdam.incremental_mpt import (
    HashedNode,
    IncrementalMPT,
    MutableBranchNode,
    MutableLeafNode,
    build_mpt,
    compact_to_nibbles,
    decode_witness_to_mpt,
    mpt_get,
    mpt_root,
    mpt_set,
)
from ethereum.merkle_patricia_trie import (
    EMPTY_TRIE_ROOT,
    Trie,
    nibble_list_to_compact,
    root,
    trie_set,
)
from ethereum.state import Root


class TestCompactToNibbles:
    """Test compact_to_nibbles."""

    def test_even_leaf(self) -> None:
        """Even-length leaf: flag nibble = 0x20."""
        nibbles = Bytes(b"\x01\x02\x03\x04")
        compact = nibble_list_to_compact(nibbles, True)
        result, is_leaf = compact_to_nibbles(compact)
        assert result == nibbles
        assert is_leaf is True

    def test_odd_leaf(self) -> None:
        """Odd-length leaf: flag nibble = 0x3X."""
        nibbles = Bytes(b"\x01\x02\x03")
        compact = nibble_list_to_compact(nibbles, True)
        result, is_leaf = compact_to_nibbles(compact)
        assert result == nibbles
        assert is_leaf is True

    def test_even_extension(self) -> None:
        """Even-length extension: flag nibble = 0x00."""
        nibbles = Bytes(b"\x0a\x0b")
        compact = nibble_list_to_compact(nibbles, False)
        result, is_leaf = compact_to_nibbles(compact)
        assert result == nibbles
        assert is_leaf is False

    def test_odd_extension(self) -> None:
        """Odd-length extension: flag nibble = 0x1X."""
        nibbles = Bytes(b"\x0f")
        compact = nibble_list_to_compact(nibbles, False)
        result, is_leaf = compact_to_nibbles(compact)
        assert result == nibbles
        assert is_leaf is False

    def test_empty_even_leaf(self) -> None:
        """Empty nibble list as even leaf."""
        nibbles = Bytes(b"")
        compact = nibble_list_to_compact(nibbles, True)
        result, is_leaf = compact_to_nibbles(compact)
        assert result == nibbles
        assert is_leaf is True

    @pytest.mark.parametrize(
        "nibbles,is_leaf",
        [
            pytest.param(Bytes(bytes(range(16))), True, id="all-nibbles-leaf"),
            pytest.param(
                Bytes(bytes(range(16))),
                False,
                id="all-nibbles-ext",
            ),
            pytest.param(Bytes(b"\x00"), True, id="zero-leaf"),
            pytest.param(Bytes(b"\x0f" * 20), True, id="long-leaf"),
        ],
    )
    def test_roundtrip(self, nibbles: Bytes, is_leaf: bool) -> None:
        """Roundtrip compact -> nibbles -> compact."""
        compact = nibble_list_to_compact(nibbles, is_leaf)
        result, result_leaf = compact_to_nibbles(compact)
        assert result == nibbles
        assert result_leaf == is_leaf


class TestHashedNode:
    """Test HashedNode behavior in the MutableNode functions."""

    def test_hashed_node_as_child_in_root_computation(self) -> None:
        """A hashed node child contributes its stored hash to the root."""
        fake_hash = keccak256(b"some subtree data")
        hashed_node = HashedNode(_hash=fake_hash)

        branch = MutableBranchNode(
            children=[None] * 16,
            value=b"",
            _dirty=True,
        )
        branch.children[0] = MutableLeafNode(
            rest_of_key=Bytes(b"\x01\x02"),
            value=b"hello",
            _dirty=True,
        )
        branch.children[1] = hashed_node

        mpt: IncrementalMPT[Bytes, Bytes] = IncrementalMPT(
            secured=False,
            default=b"",
            root_node=branch,
            _data={},
        )
        # Should not raise — hashed node's hash is used directly
        result = mpt_root(mpt)
        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_insert_into_hashed_node_raises(self) -> None:
        """Inserting into a HashedNode raises AssertionError."""
        hashed_node = HashedNode(_hash=b"\x00" * 32)
        mpt: IncrementalMPT[Bytes, Bytes] = IncrementalMPT(
            secured=False,
            default=b"",
            root_node=hashed_node,
            _data={},
        )
        with pytest.raises(AssertionError, match="cannot be invalidated"):
            mpt_set(mpt, b"\x01", b"value")

    def test_delete_from_hashed_node_raises(self) -> None:
        """Deleting from a HashedNode raises AssertionError."""
        hashed_node = HashedNode(_hash=b"\x00" * 32)
        mpt: IncrementalMPT[Bytes, Bytes] = IncrementalMPT(
            secured=False,
            default=b"",
            root_node=hashed_node,
            _data={},
        )
        with pytest.raises(AssertionError, match="cannot be invalidated"):
            mpt_set(mpt, b"\x01", b"")

    def test_witness_traversal_on_hashed_node_raises(self) -> None:
        """Witness traversal on a HashedNode raises AssertionError."""
        hashed_node = HashedNode(_hash=b"\x00" * 32)
        mpt: IncrementalMPT[Bytes, Bytes] = IncrementalMPT(
            secured=False,
            default=b"",
            root_node=hashed_node,
            _data={},
        )
        with pytest.raises(AssertionError, match="cannot be witnessed"):
            mpt_get(mpt, b"\x01")


def _build_trie_and_collect_nodes(
    data: dict[Bytes, Bytes], secured: bool
) -> tuple[Root, dict[Bytes, Bytes]]:
    """
    Build a standard trie, then build an IncrementalMPT and collect
    all witness nodes by traversing every key.

    Return (root_hash, node_db).
    """
    from ethereum.forks.amsterdam.incremental_mpt import (
        _encode_mutable_node,
    )

    # Compute the expected root via standard trie
    std_trie: Trie[Bytes, Bytes] = Trie(secured=secured, default=b"")
    for k, v in data.items():
        trie_set(std_trie, k, v)
    expected_root = root(std_trie)

    # Build incremental MPT and collect witness nodes
    inc_mpt = build_mpt(data, secured=secured, default=b"")
    for k in data:
        mpt_get(inc_mpt, k)

    node_db: dict[Bytes, Bytes] = dict(inc_mpt.witness.accessed_nodes)

    # Small root nodes (RLP < 32 bytes) are not recorded in the
    # witness because they have no hash.  Ensure the root is
    # always present in node_db.
    if inc_mpt.root_node is not None and expected_root not in node_db:
        root_rlp = rlp.encode(_encode_mutable_node(inc_mpt.root_node))
        node_db[keccak256(root_rlp)] = root_rlp

    return expected_root, node_db


def _decode_root_from_rlp(
    root_rlp: Bytes,
    *,
    secured: bool = False,
) -> IncrementalMPT[Bytes, Bytes]:
    """Decode a single synthetic witness root from its RLP bytes."""
    root_hash = Root(keccak256(root_rlp))
    return decode_witness_to_mpt(
        {Bytes(root_hash): root_rlp},
        root_hash,
        secured=secured,
        default=b"",
    )


class TestDecodeWitnessToMpt:
    """Test decode_witness_to_mpt with synthetic witness data."""

    def test_empty_trie(self) -> None:
        """Decoding an empty trie returns an empty MPT."""
        node_db: dict[Bytes, Bytes] = {}
        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, EMPTY_TRIE_ROOT, secured=False, default=b""
        )
        assert mpt.root_node is None
        assert mpt_root(mpt) == EMPTY_TRIE_ROOT

    def test_single_entry(self) -> None:
        """Decode a trie with a single key-value pair."""
        data = {b"key1": b"value1"}
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=False
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=False, default=b""
        )
        assert mpt_root(mpt) == expected_root


class TestMalformedWitnessNodes:
    """Test malformed witness node decoding failures."""

    def test_malformed_rlp_bytes(self) -> None:
        """Malformed RLP should fail before node-shape validation."""
        with pytest.raises(rlp.DecodingError):
            _decode_root_from_rlp(Bytes(b"\xc1"))

    def test_nonempty_byte_string_node(self) -> None:
        """A decoded byte string node must be the empty node only."""
        with pytest.raises(AssertionError, match="Expected empty node"):
            _decode_root_from_rlp(Bytes(rlp.encode(b"\x01")))

    def test_invalid_rlp_node_length(self) -> None:
        """Only 2-item and 17-item node lists are valid."""
        with pytest.raises(AssertionError, match="Invalid RLP node length: 3"):
            _decode_root_from_rlp(
                Bytes(rlp.encode([b"\x01", b"\x02", b"\x03"]))
            )

    def test_extension_with_empty_child_ref(self) -> None:
        """Extension nodes must point to a branch child."""
        root_rlp = Bytes(
            rlp.encode([nibble_list_to_compact(Bytes(b"\x01"), False), b""])
        )

        with pytest.raises(
            AssertionError, match="ExtensionNode child must be a BranchNode"
        ):
            _decode_root_from_rlp(root_rlp)

    def test_extension_pointing_to_leaf(self) -> None:
        """Extensions may not point directly to leaf nodes."""
        leaf = [nibble_list_to_compact(Bytes(b"\x02"), True), b"value"]
        root_rlp = Bytes(
            rlp.encode([nibble_list_to_compact(Bytes(b"\x01"), False), leaf])
        )

        with pytest.raises(
            AssertionError, match="ExtensionNode child must be a BranchNode"
        ):
            _decode_root_from_rlp(root_rlp)

    def test_extension_pointing_to_extension(self) -> None:
        """Extensions may not point directly to other extensions."""
        branch: list[Any] = [b""] * 17
        branch[0] = [nibble_list_to_compact(Bytes(b"\x03"), True), b"left"]
        branch[1] = [nibble_list_to_compact(Bytes(b"\x04"), True), b"right"]
        inner_extension: list[Any] = [
            nibble_list_to_compact(Bytes(b"\x02"), False),
            branch,
        ]
        root_rlp = Bytes(
            rlp.encode(
                [
                    nibble_list_to_compact(Bytes(b"\x01"), False),
                    inner_extension,
                ]
            )
        )

        with pytest.raises(
            AssertionError, match="ExtensionNode child must be a BranchNode"
        ):
            _decode_root_from_rlp(root_rlp)

    def test_extension_child_raw_nonzero_non_hash_bytes(self) -> None:
        """Non-empty byte refs inside extensions must be 32-byte hashes."""
        root_rlp = Bytes(
            rlp.encode(
                [nibble_list_to_compact(Bytes(b"\x01"), False), b"\x01"]
            )
        )

        with pytest.raises(
            AssertionError, match="Unexpected child ref length"
        ):
            _decode_root_from_rlp(root_rlp)

    def test_branch_with_zero_occupied_entries(self) -> None:
        """A branch node must encode at least two occupied entries."""
        with pytest.raises(
            AssertionError,
            match="BranchNode must have at least 2 occupied entries",
        ):
            _decode_root_from_rlp(Bytes(rlp.encode([b""] * 17)))

    def test_branch_with_single_occupied_entry(self) -> None:
        """A branch node with only one child is non-canonical."""
        branch: list[Any] = [b""] * 17
        branch[0] = [nibble_list_to_compact(Bytes(b"\x01"), True), b"value"]

        with pytest.raises(
            AssertionError,
            match="BranchNode must have at least 2 occupied entries",
        ):
            _decode_root_from_rlp(Bytes(rlp.encode(branch)))

    def test_extension_with_empty_path(self) -> None:
        """Tries must reject empty extension segments."""
        branch: list[Any] = [b""] * 17
        branch[0] = [nibble_list_to_compact(Bytes(b"\x01"), True), b"left"]
        branch[1] = [nibble_list_to_compact(Bytes(b"\x02"), True), b"right"]
        root_rlp = Bytes(
            rlp.encode([nibble_list_to_compact(Bytes(b""), False), branch])
        )

        with pytest.raises(
            AssertionError,
            match="ExtensionNode must have a non-empty path",
        ):
            _decode_root_from_rlp(root_rlp)


class TestDecodeWitnessToMptMore:
    """Additional decode_witness_to_mpt roundtrip coverage."""

    def test_multiple_entries(self) -> None:
        """Decode a trie with multiple entries and verify root."""
        data = {
            b"do": b"verb",
            b"dog": b"puppy",
            b"doge": b"coin",
            b"horse": b"stallion",
        }
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=False
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=False, default=b""
        )
        assert mpt_root(mpt) == expected_root

    def test_secured_trie(self) -> None:
        """Decode a secured (hashed-key) trie."""
        data = {
            b"account1": b"data1",
            b"account2": b"data2",
            b"account3": b"data3",
        }
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=True
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=True, default=b""
        )
        assert mpt_root(mpt) == expected_root

    def test_decode_then_modify(self) -> None:
        """Decode from witness, modify a key, verify new root."""
        data = {b"aa": b"val_a", b"ab": b"val_b", b"ba": b"val_c"}
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=False
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=False, default=b""
        )
        assert mpt_root(mpt) == expected_root

        # Modify a key
        mpt_set(mpt, b"aa", b"new_val")

        # Build expected trie with the modification
        data_modified = dict(data)
        data_modified[b"aa"] = b"new_val"
        std_trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
        for k, v in data_modified.items():
            trie_set(std_trie, k, v)
        new_expected_root = root(std_trie)

        assert mpt_root(mpt) == new_expected_root

    def test_decode_then_delete(self) -> None:
        """Decode from witness, delete a key, verify new root."""
        data = {b"aa": b"val_a", b"ab": b"val_b"}
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=False
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=False, default=b""
        )

        # Delete a key
        mpt_set(mpt, b"aa", b"")

        # Build expected trie with the deletion
        std_trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
        trie_set(std_trie, b"ab", b"val_b")
        new_expected_root = root(std_trie)

        assert mpt_root(mpt) == new_expected_root

    def test_decode_then_insert(self) -> None:
        """Decode from witness, insert a new key, verify root."""
        data = {b"aa": b"val_a", b"ab": b"val_b"}
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=False
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=False, default=b""
        )

        # Insert a new key
        mpt_set(mpt, b"ac", b"val_c")

        # Build expected trie with the insertion
        data_with_insert = dict(data)
        data_with_insert[b"ac"] = b"val_c"
        std_trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
        for k, v in data_with_insert.items():
            trie_set(std_trie, k, v)
        new_expected_root = root(std_trie)

        assert mpt_root(mpt) == new_expected_root


class TestPartialWitness:
    """Test decode_witness_to_mpt with incomplete witness data."""

    def test_partial_witness_preserves_root(self) -> None:
        """
        Build a trie, collect witness for only some keys.
        Decode from partial witness. Root should still match
        because hashed nodes preserve hashes of unvisited subtrees.
        """
        data = {
            b"aa": b"val_a",
            b"ab": b"val_b",
            b"ba": b"val_c",
            b"bb": b"val_d",
        }

        # Build the full trie to get the root
        std_trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
        for k, v in data.items():
            trie_set(std_trie, k, v)
        expected_root = root(std_trie)

        # Build incremental MPT but only access some keys
        inc_mpt = build_mpt(data, secured=False, default=b"")
        mpt_get(inc_mpt, b"aa")
        mpt_get(inc_mpt, b"ab")
        # Intentionally NOT accessing b"ba" and b"bb"

        partial_db: dict[Bytes, Bytes] = dict(inc_mpt.witness.accessed_nodes)

        # Also need the root node itself
        root_rlp = rlp.encode(
            _encode_root_for_db(inc_mpt.root_node)  # type: ignore[arg-type]
        )
        root_hash = Root(keccak256(root_rlp))
        partial_db[root_hash] = root_rlp

        decoded_mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            partial_db, expected_root, secured=False, default=b""
        )

        # Root should match even with hashed nodes for b"ba"/b"bb"
        assert mpt_root(decoded_mpt) == expected_root

    def test_partial_witness_modify_known_path(self) -> None:
        """
        Decode from partial witness, modify a key on a known path.
        The hashed node subtrees should remain intact.
        """
        data = {
            b"aa": b"val_a",
            b"ab": b"val_b",
            b"ba": b"val_c",
            b"bb": b"val_d",
        }

        # Full trie for expected roots
        std_trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
        for k, v in data.items():
            trie_set(std_trie, k, v)

        # Build incremental MPT, access only "a*" keys
        inc_mpt = build_mpt(data, secured=False, default=b"")
        mpt_get(inc_mpt, b"aa")
        mpt_get(inc_mpt, b"ab")

        partial_db: dict[Bytes, Bytes] = dict(inc_mpt.witness.accessed_nodes)
        root_rlp = rlp.encode(
            _encode_root_for_db(inc_mpt.root_node)  # type: ignore[arg-type]
        )
        root_hash = Root(keccak256(root_rlp))
        partial_db[root_hash] = root_rlp

        decoded_mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            partial_db, root_hash, secured=False, default=b""
        )

        # Modify a known key
        mpt_set(decoded_mpt, b"aa", b"new_a")

        # Build expected root with modification
        data_mod = dict(data)
        data_mod[b"aa"] = b"new_a"
        mod_trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
        for k, v in data_mod.items():
            trie_set(mod_trie, k, v)
        expected_mod_root = root(mod_trie)

        assert mpt_root(decoded_mpt) == expected_mod_root

    def test_partial_witness_insert_into_hashed_node_fails(self) -> None:
        """
        Decode from partial witness, try to modify a key in the
        hashed node region. Should raise AssertionError.
        """
        data = {
            b"aa": b"val_a",
            b"ab": b"val_b",
            b"ba": b"val_c",
            b"bb": b"val_d",
        }

        inc_mpt = build_mpt(data, secured=False, default=b"")
        mpt_get(inc_mpt, b"aa")
        mpt_get(inc_mpt, b"ab")

        partial_db: dict[Bytes, Bytes] = dict(inc_mpt.witness.accessed_nodes)
        root_rlp = rlp.encode(
            _encode_root_for_db(inc_mpt.root_node)  # type: ignore[arg-type]
        )
        root_hash = Root(keccak256(root_rlp))
        partial_db[root_hash] = root_rlp

        decoded_mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            partial_db, root_hash, secured=False, default=b""
        )

        # Try to insert into the hashed node subtree
        with pytest.raises(AssertionError, match="cannot be invalidated"):
            mpt_set(decoded_mpt, b"ba", b"new_c")

    def test_partial_witness_delete_collapses_to_hashed_node(self) -> None:
        """
        Delete a key whose sibling is a HashedNode.

        When a branch has two children and one is deleted, the branch
        must collapse. If the remaining child is a HashedNode (from a
        partial witness), _collapse_branch cannot merge the nibble into
        it because its structure is unknown. This currently raises
        AssertionError.
        """
        fake_hash = keccak256(b"some large subtree")
        hashed_child = HashedNode(_hash=fake_hash)

        # Branch with a leaf at nibble 0 and a HashedNode at nibble 1.
        # Key b"\x01" -> nibbles [0, 1]: child index 0, rest_of_key [1].
        branch = MutableBranchNode(
            children=[None] * 16,
            value=b"",
        )
        branch.children[0] = MutableLeafNode(
            rest_of_key=Bytes(b"\x01"),
            value=b"hello",
        )
        branch.children[1] = hashed_child

        mpt: IncrementalMPT[Bytes, Bytes] = IncrementalMPT(
            secured=False,
            default=b"",
            root_node=branch,
            _data={Bytes(b"\x01"): b"hello"},
        )

        # Deleting the leaf at nibble 0 leaves only the HashedNode,
        # triggering a branch collapse. _collapse_branch calls
        # _record_witness on the remaining child, which fails
        # because HashedNode cannot be witnessed.
        with pytest.raises(
            AssertionError, match="HashedNode cannot be witnessed"
        ):
            mpt_set(mpt, Bytes(b"\x01"), b"")


def _encode_root_for_db(
    node: object,
) -> object:
    """Encode a MutableNode root into its RLP-encodable form."""
    from ethereum.forks.amsterdam.incremental_mpt import (
        _encode_mutable_node,
    )

    return _encode_mutable_node(node)  # type: ignore[arg-type]


class TestBuildVsDecode:
    """
    Verify that decode_witness_to_mpt produces tries equivalent to
    build_mpt by checking root hashes after identical mutations.
    """

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({b"a": b"1"}, id="single"),
            pytest.param({b"a": b"1", b"b": b"2"}, id="two-keys"),
            pytest.param(
                {
                    b"do": b"verb",
                    b"dog": b"puppy",
                    b"doge": b"coin",
                    b"horse": b"stallion",
                },
                id="ethereum-example",
            ),
            pytest.param(
                {bytes([i]): bytes([i]) for i in range(20)},
                id="many-keys",
            ),
        ],
    )
    def test_roots_match_after_mutation(
        self, data: dict[Bytes, Bytes]
    ) -> None:
        """Build and decode produce same root after same mutations."""
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=False
        )

        # Decode
        decoded: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=False, default=b""
        )
        assert mpt_root(decoded) == expected_root

        # Build fresh
        built = build_mpt(data, secured=False, default=b"")
        assert mpt_root(built) == expected_root

        # Now mutate both identically — add a new key
        new_key = b"\xff"
        new_val = b"new"
        mpt_set(decoded, new_key, new_val)
        mpt_set(built, new_key, new_val)

        assert mpt_root(decoded) == mpt_root(built)


class TestDecodeEdgeCases:
    """Test decode_witness_to_mpt edge cases."""

    def test_branch_with_value(self) -> None:
        """
        Decode a trie where a key terminates at a branch node.

        Keys "ab" and "abc" coexist, so "ab" occupies the branch
        value slot (index 16) rather than a leaf child.
        """
        data = {b"ab": b"short", b"abc": b"longer"}
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=False
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=False, default=b""
        )
        assert mpt_root(mpt) == expected_root

    def test_secured_trie_modify_and_delete(self) -> None:
        """Modify and delete keys in a secured (hashed-key) trie."""
        data = {
            b"account1": b"data1",
            b"account2": b"data2",
            b"account3": b"data3",
        }
        expected_root, node_db = _build_trie_and_collect_nodes(
            data, secured=True
        )

        mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            node_db, expected_root, secured=True, default=b""
        )

        # Modify one key, delete another
        mpt_set(mpt, b"account1", b"updated")
        mpt_set(mpt, b"account3", b"")

        # Build expected trie with same changes
        std_trie: Trie[Bytes, Bytes] = Trie(secured=True, default=b"")
        trie_set(std_trie, b"account1", b"updated")
        trie_set(std_trie, b"account2", b"data2")
        new_expected_root = root(std_trie)

        assert mpt_root(mpt) == new_expected_root

    def test_partial_witness_delete_known_path(self) -> None:
        """Delete a key on a known path while hashed nodes exist elsewhere."""
        data = {
            b"aa": b"val_a",
            b"ab": b"val_b",
            b"ba": b"val_c",
            b"bb": b"val_d",
        }

        # Build incremental MPT, access only "a*" keys
        inc_mpt = build_mpt(data, secured=False, default=b"")
        mpt_get(inc_mpt, b"aa")
        mpt_get(inc_mpt, b"ab")

        partial_db: dict[Bytes, Bytes] = dict(inc_mpt.witness.accessed_nodes)
        root_rlp = rlp.encode(
            _encode_root_for_db(inc_mpt.root_node)  # type: ignore[arg-type]
        )
        root_hash = Root(keccak256(root_rlp))
        partial_db[root_hash] = root_rlp

        decoded_mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
            partial_db, root_hash, secured=False, default=b""
        )

        # Delete a known key
        mpt_set(decoded_mpt, b"aa", b"")

        # Build expected root with the deletion
        data_del = dict(data)
        del data_del[b"aa"]
        std_trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
        for k, v in data_del.items():
            trie_set(std_trie, k, v)
        expected_del_root = root(std_trie)

        assert mpt_root(decoded_mpt) == expected_del_root
