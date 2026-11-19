"""Properties of the shared Merkle Patricia Trie implementation."""

import random
from typing import Dict, List, Tuple

import pytest
from ethereum_types.bytes import Bytes
from execution_testing.base_types import EmptyTrieRoot
from hypothesis import assume, given, target
from hypothesis import strategies as st
from trie import HexaryTrie

from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import (
    Trie,
    copy_trie,
    root,
    trie_get,
    trie_set,
)

secured = st.booleans()


def trie_items(
    max_items: int = 32,
) -> st.SearchStrategy[List[Tuple[Bytes, Bytes]]]:
    """
    Return `(key, value)` lists with unique keys, many sharing a prefix so
    the trie gets branch and extension nodes.
    """
    clustered_keys = st.lists(
        st.sampled_from([0x00, 0x01, 0x10, 0x11, 0xFF]),
        min_size=1,
        max_size=4,
    ).map(bytes)
    keys = st.one_of(
        clustered_keys,
        st.binary(min_size=1, max_size=8),
    ).map(Bytes)
    values = st.binary(min_size=1, max_size=32).map(Bytes)
    return st.dictionaries(keys, values, max_size=max_items).map(
        lambda d: list(d.items())
    )


def make_trie(
    is_secured: bool, items: List[Tuple[Bytes, Bytes]]
) -> Trie[Bytes, Bytes]:
    """Build a trie from (key, value) items."""
    trie: Trie[Bytes, Bytes] = Trie(secured=is_secured, default=Bytes(b""))
    for key, value in items:
        trie_set(trie, key, value)
    return trie


def py_trie_root(is_secured: bool, items: List[Tuple[Bytes, Bytes]]) -> bytes:
    """Return py-trie's root, hashing each key first in a secured trie."""
    reference = HexaryTrie(db={})
    for key, value in items:
        reference.set(keccak256(key) if is_secured else key, value)
    return reference.root_hash


@given(is_secured=secured, items=trie_items(max_items=64))
def test_root_matches_py_trie(
    is_secured: bool, items: List[Tuple[Bytes, Bytes]]
) -> None:
    """
    The root of any trie matches py-trie's, with keys hashed first in a
    secured trie.
    """
    target(len(items), label="items in the trie")
    assert root(make_trie(is_secured, items)) == py_trie_root(
        is_secured, items
    )


@given(
    keys=st.lists(
        st.binary(min_size=1, max_size=4).map(Bytes),
        min_size=1,
        max_size=3,
        unique=True,
    ),
    fill=st.integers(0, 255),
)
def test_nodes_around_32_bytes_match_py_trie(
    keys: List[Bytes], fill: int
) -> None:
    """
    As the first value grows, its leaf's encoding passes 32 bytes, where
    the leaf stops being inlined in its parent and is hashed instead, and
    the root still matches py-trie's.
    """
    for size in range(1, 41):
        items = [(keys[0], Bytes(bytes([fill]) * size))]
        items += [(key, Bytes(b"\x01")) for key in keys[1:]]
        assert root(make_trie(False, items)) == py_trie_root(False, items)


@given(is_secured=secured, items=trie_items(), seed=st.randoms())
def test_root_is_insertion_order_independent(
    is_secured: bool, items: List[Tuple[Bytes, Bytes]], seed: random.Random
) -> None:
    """The root commits to contents, not insertion order."""
    # Bigger tries have deeper branch and extension nodes to reorder.
    target(len(items), label="items in the trie")
    shuffled = items[:]
    seed.shuffle(shuffled)
    assert root(make_trie(is_secured, items)) == root(
        make_trie(is_secured, shuffled)
    )


@given(
    is_secured=secured,
    items=trie_items(),
    extra_key=st.binary(min_size=1, max_size=8).map(Bytes),
    extra_value=st.binary(min_size=1, max_size=32).map(Bytes),
)
def test_setting_the_default_deletes(
    is_secured: bool,
    items: List[Tuple[Bytes, Bytes]],
    extra_key: Bytes,
    extra_value: Bytes,
) -> None:
    """
    Storing the default value removes the key: inserting a key and setting
    it back restores the root, and setting every key back leaves the empty
    trie root.
    """
    trie = make_trie(is_secured, items)
    assume(trie_get(trie, extra_key) == trie.default)
    original_root = root(trie)
    trie_set(trie, extra_key, extra_value)
    trie_set(trie, extra_key, trie.default)
    assert root(trie) == original_root

    for key, _ in items:
        trie_set(trie, key, trie.default)
    assert root(trie) == EmptyTrieRoot


@given(is_secured=secured, items=trie_items())
def test_copy_preserves_root_and_isolates_mutation(
    is_secured: bool, items: List[Tuple[Bytes, Bytes]]
) -> None:
    """A copy shares the root but not subsequent mutations."""
    trie = make_trie(is_secured, items)
    original_root = root(trie)
    copied = copy_trie(trie)
    assert root(copied) == original_root
    trie_set(copied, Bytes(b"\xde\xad"), Bytes(b"\xbe\xef"))
    assert root(trie) == original_root


# "dogs" has key segments of odd length only, and "puppy" adds even ones,
# which the compact encoding packs differently.
@pytest.mark.parametrize(
    "items,expected_root",
    [
        pytest.param(
            {b"doe": b"reindeer", b"dog": b"puppy", b"dogglesworth": b"cat"},
            "8aad789dff2f538bca5d8ea56e8abe10f4c7ba3a5dea95fea4cd6e7c3a1168d3",
            id="dogs",
        ),
        pytest.param(
            {
                b"do": b"verb",
                b"horse": b"stallion",
                b"doge": b"coin",
                b"dog": b"puppy",
            },
            "5991bb8c6514148a29db676a14ac506cd2cd5775ace63c30a4fe457715e9ac84",
            id="puppy",
        ),
    ],
)
def test_known_root(items: Dict[bytes, bytes], expected_root: str) -> None:
    """An unsecured trie matches a vector in ethereum/tests."""
    trie = make_trie(
        False, [(Bytes(key), Bytes(value)) for key, value in items.items()]
    )
    assert root(trie) == bytes.fromhex(expected_root)
