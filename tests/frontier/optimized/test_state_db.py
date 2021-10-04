from pathlib import Path
from typing import List, Tuple

import ethereum.frontier.trie as normal_trie
import ethereum_optimized.frontier.state_db as state_db
from ethereum.base_types import Bytes, Optional

operations: List[List[Tuple[Bytes, Optional[Bytes]]]] = [
    [],
    [(b"001234", b"foo")],
    [(b"001234", b"bar")],
    [(b"001234", None)],
    [(b"abcdeg", b"baz"), (b"abcdef", b"foobar")],
    [(b"ab1234", b"bar")],
    [(b"abcdeg", None)],
    [(b"abcde1", b"foo"), (b"abcde2", b"foo")],
    [
        (b"abcde1", None),
        (b"abcde2", None),
        (b"abcdeg", None),
        (b"abcdef", None),
    ],
    [(b"ab\x00\x00\x00\x00", b"zero"), (b"ab\x00\x00\x00\x01", b"one")],
    [(b"ab\x00\x00\x00\x10", b"foo")],
    [(b"Ab1234", b"foo")],
    [(b"123456", b"foo"), (b"12345a", b"foo"), (b"123a56", b"foo")],
    [(b"123a56", None)],
]


def test_trie() -> None:
    trie_normal: normal_trie.Trie[Bytes, Optional[Bytes]] = normal_trie.Trie(
        False, None
    )
    state = state_db.State()
    state_db.begin_db_transaction(state)
    for insert_list in operations:
        for (key, value) in insert_list:
            normal_trie.trie_set(trie_normal, key, value)
            state_db.set_account_debug(state, key, value)
        root = normal_trie.root(trie_normal)
        assert root == state_db.state_root(state)
