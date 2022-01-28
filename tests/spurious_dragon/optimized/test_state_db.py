import sys
from typing import Any, List, Optional, Tuple

import pytest

import ethereum.spurious_dragon.state as state
import ethereum.spurious_dragon.trie as normal_trie
from ethereum.base_types import U256, Bytes
from ethereum.spurious_dragon.eth_types import EMPTY_ACCOUNT
from ethereum.spurious_dragon.utils.hexadecimal import hex_to_address

try:
    import ethereum_optimized.spurious_dragon.state_db as state_db
except ImportError:
    pass


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


def fake_get_internal_key(key: Bytes) -> Bytes:
    """
    Replacing `state_db.get_internal_key()` with this function switches
    `state_db` to a unsecured trie which is necessary for some tests.
    """
    return normal_trie.bytes_to_nibble_list(key)


@pytest.mark.skipif(
    "ethereum_optimized.tangerine_whistle.state_db" not in sys.modules,
    reason="missing dependency (use `pip install 'ethereum[optimized]'`)",
)
def test_trie() -> None:
    trie_normal: normal_trie.Trie[Bytes, Optional[Bytes]] = normal_trie.Trie(
        False, None
    )
    backup_get_internal_key = state_db.get_internal_key
    state_db.get_internal_key = fake_get_internal_key
    with state_db.State() as state:
        state_db.begin_db_transaction(state)
        for insert_list in operations:
            for (key, value) in insert_list:
                normal_trie.trie_set(trie_normal, key, value)
                state_db.set_account(state, key, value)  # type: ignore
            root = normal_trie.root(trie_normal)
            assert root == state_db.state_root(state)
    state_db.get_internal_key = backup_get_internal_key


@pytest.mark.skipif(
    "ethereum_optimized.tangerine_whistle.state_db" not in sys.modules,
    reason="missing dependency (use `pip install 'ethereum[optimized]'`)",
)
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


@pytest.mark.skipif(
    "ethereum_optimized.tangerine_whistle.state_db" not in sys.modules,
    reason="missing dependency (use `pip install 'ethereum[optimized]'`)",
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
