from pathlib import Path
from typing import Any, List, Tuple

import ethereum.frontier.state as state
import ethereum.frontier.trie as normal_trie
import ethereum_optimized.frontier.state_db as state_db
from ethereum.base_types import U256, Bytes, Optional
from ethereum.frontier.eth_types import EMPTY_ACCOUNT
from ethereum.frontier.utils.hexadecimal import hex_to_address

ADDRESS_FOO = hex_to_address("0x00000000219ab540356cbb839cbe05303d7705fa")

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
    with state_db.State() as state:
        state_db.begin_db_transaction(state)
        for insert_list in operations:
            for (key, value) in insert_list:
                normal_trie.trie_set(trie_normal, key, value)
                state_db.set_account_debug(state, key, value)
            root = normal_trie.root(trie_normal)
            assert root == state_db.state_root(state)


def test_storage_key() -> None:
    def actions(impl: Any) -> Any:
        obj = impl.State()
        impl.set_account(obj, ADDRESS_FOO, EMPTY_ACCOUNT)
        impl.set_storage(obj, ADDRESS_FOO, b"", U256(42))
        impl.state_root(obj)
        return obj

    state_normal = actions(state)
    state_optimized = actions(state_db)
    assert state.get_storage(
        state_normal, ADDRESS_FOO, b""
    ) == state_db.get_storage(state_optimized, ADDRESS_FOO, b"")
    assert state.state_root(state_normal) == state_db.state_root(
        state_optimized
    )


def test_resurrection() -> None:
    def actions(impl: Any) -> Any:
        obj = impl.State()
        impl.set_account(obj, ADDRESS_FOO, EMPTY_ACCOUNT)
        impl.set_storage(obj, ADDRESS_FOO, b"", U256(42))
        impl.state_root(obj)
        impl.destroy_account(obj, ADDRESS_FOO)
        impl.state_root(obj)
        impl.set_account(obj, ADDRESS_FOO, EMPTY_ACCOUNT)
        return obj

    state_normal = actions(state)
    state_optimized = actions(state_db)
    assert state.get_storage(
        state_normal, ADDRESS_FOO, b""
    ) == state_db.get_storage(state_optimized, ADDRESS_FOO, b"")
    assert state.state_root(state_normal) == state_db.state_root(
        state_optimized
    )
