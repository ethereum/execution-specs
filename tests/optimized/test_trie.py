from typing import List, Tuple

import ethereum.frontier.trie as normal_trie
import ethereum_optimized.trie as optimized_trie
from ethereum.base_types import Bytes

operations: List[List[Tuple[Bytes, Bytes]]] = [
    [],  # Empty Trie
    [(b"1234", b"foo")],  # Add a leaf
    [(b"1234", b"bar")],  # Change the value of a leaf
    [(b"1234", b"")],  # Delete a leaf
    [(b"abcde", b"foo"), (b"abcdef", b"foo")],  # Make an extension node
    [(b"abc", b"foo")],  # Split an extension node
    [(b"abcde", b"")],  # Merge an extension and leaf
    [(b"abcde1", b"foo"), (b"abcde2", b"")],  # Split a leaf node
    [  # Delete all subnodes of an extension node but not the value at the node
        (b"abcde1", b""),
        (b"abcde2", b""),
        (b"abcdef", b""),
    ],
    [(b"abcde", b"")],
    [(b"abcde1", b"foo"), (b"abcde2", b"")],
    [  # Delete all subnodes of an extension node and the value at the node
        (b"abcde1", b""),
        (b"abcde2", b""),
        (b"abcde", b""),
    ],
    [(b"a", b"foo"), (b"aaa", b"foo"), (b"aaaa", b"foo")],
    [(b"a", b""), (b"aa", b"foo")],
    [(b"\x00\x00\x00\x00", b"foo"), (b"\x00\x00\x00\x01", b"foo")],
    [(b"\x00\x00\x00\x10", b"foo")],
    [(b"a", b"foo"), (b"b", b"foo"), (b"c", b"foo"), (b"d", b"foo")],
]


def test_trie() -> None:
    trie_normal = normal_trie.Trie(False, b"")
    trie_optimized = optimized_trie.Trie(False, b"")
    for insert_list in operations:
        for (key, value) in insert_list:
            normal_trie.trie_set(trie_normal, key, value)
            optimized_trie.trie_set(trie_optimized, key, value)
        assert normal_trie.root(trie_normal) == optimized_trie.root(
            trie_optimized
        )
