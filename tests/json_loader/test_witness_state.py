"""Tests for WitnessState."""

from typing import Any, Optional

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.forks.amsterdam.fork_types import encode_account
from ethereum.forks.amsterdam.incremental_mpt import (
    IncrementalMPT,
    build_mpt,
    mpt_get,
    mpt_root,
)
from ethereum.forks.amsterdam.witness_state import (
    WitnessState,
    build_code_db,
    build_node_db,
)
from ethereum.merkle_patricia_trie import (
    EMPTY_TRIE_ROOT,
    bytes_to_nibble_list,
    nibble_list_to_compact,
)
from ethereum.state import EMPTY_CODE_HASH, Account, Address, Root

_ADDR1 = Address(b"\x01" * 20)
_ADDR2 = Address(b"\x02" * 20)

_CODE = b"\x60\x00\x56"
_CODE_HASH = Hash32(keccak256(_CODE))

_SLOT1 = Bytes32(b"\x00" * 31 + b"\x01")
_SLOT2 = Bytes32(b"\x00" * 31 + b"\x02")


def _acct(balance: int = 0, nonce: int = 1) -> Account:
    return Account(
        nonce=Uint(nonce), balance=U256(balance), code_hash=EMPTY_CODE_HASH
    )


def _build_witness(
    accounts: dict[Address, Optional[Account]],
    storage: dict[Address, dict[Bytes32, U256]],
) -> tuple[Root, dict[Bytes, Bytes]]:
    """Build a (state_root, node_db) witness from account and storage data."""
    storage_mpts: dict[Address, IncrementalMPT[Bytes32, U256]] = {}
    for addr, slots in storage.items():
        storage_mpt: IncrementalMPT[Bytes32, U256] = build_mpt(
            slots, secured=True, default=U256(0)
        )
        for key in slots:
            mpt_get(storage_mpt, key)
        storage_mpts[addr] = storage_mpt

    def get_storage_root(addr: Address) -> Root:
        if addr in storage_mpts:
            return mpt_root(storage_mpts[addr])
        return EMPTY_TRIE_ROOT

    account_mpt: IncrementalMPT[Address, Optional[Account]] = build_mpt(
        accounts, secured=True, default=None, get_storage_root=get_storage_root
    )
    for addr in accounts:
        mpt_get(account_mpt, addr)

    state_root = mpt_root(account_mpt)
    node_db: dict[Bytes, Bytes] = dict(account_mpt.witness.accessed_nodes)
    for storage_mpt in storage_mpts.values():
        node_db.update(storage_mpt.witness.accessed_nodes)

    return state_root, node_db


def _make_ws(
    accounts: dict[Address, Optional[Account]],
    storage: dict[Address, dict[Bytes32, U256]] | None = None,
    code_db: dict[Hash32, Bytes] | None = None,
) -> WitnessState:
    """Build a WitnessState from account and storage data."""
    state_root, node_db = _build_witness(accounts, storage or {})
    return WitnessState(
        _node_db=node_db, _state_root=state_root, _code_db=code_db or {}
    )


def _root_witness(root_rlp: Bytes) -> tuple[Root, dict[Bytes, Bytes]]:
    """Build a synthetic witness DB keyed by one root node."""
    root_hash = Root(keccak256(root_rlp))
    return root_hash, {Bytes(root_hash): root_rlp}


def _single_account_state_witness(
    *,
    address: Address = _ADDR1,
    storage_root: Root = EMPTY_TRIE_ROOT,
) -> tuple[Root, dict[Bytes, Bytes]]:
    """Build a valid one-account state witness with a custom storage root."""
    account_leaf = [
        nibble_list_to_compact(bytes_to_nibble_list(keccak256(address)), True),
        encode_account(_acct(), storage_root),
    ]
    return _root_witness(Bytes(rlp.encode(account_leaf)))


class TestBuildNodeDb:
    """Test build_node_db."""

    def test_empty(self) -> None:
        """Empty input produces empty mapping."""
        assert build_node_db(()) == {}

    def test_single_entry(self) -> None:
        """Each entry is keyed by its keccak256 hash."""
        data = b"some_rlp_node_data_long_enough_to_be_realistic"
        db = build_node_db((data,))
        assert db == {keccak256(data): data}

    def test_multiple_entries(self) -> None:
        """Multiple entries all appear in the mapping."""
        a, b = b"node_aaa", b"node_bbb"
        db = build_node_db((a, b))
        assert db[keccak256(a)] == a
        assert db[keccak256(b)] == b


class TestBuildCodeDb:
    """Test build_code_db."""

    def test_empty(self) -> None:
        """Empty input produces empty mapping."""
        assert build_code_db(()) == {}

    def test_single_entry(self) -> None:
        """Entry is keyed by code hash."""
        db = build_code_db((_CODE,))
        assert db == {_CODE_HASH: _CODE}

    def test_multiple_entries(self) -> None:
        """Multiple bytecodes all appear."""
        code2 = b"\x60\x01\x56"
        db = build_code_db((_CODE, code2))
        assert db[keccak256(_CODE)] == _CODE
        assert db[keccak256(code2)] == code2


class TestGetAccountOptional:
    """Test WitnessState.get_account_optional."""

    def test_existing_account(self) -> None:
        """Returns the account stored in the trie."""
        witness_state = _make_ws({_ADDR1: _acct(balance=1000, nonce=5)})
        result = witness_state.get_account_optional(_ADDR1)
        assert result is not None
        assert result.nonce == Uint(5)
        assert result.balance == U256(1000)
        assert result.code_hash == EMPTY_CODE_HASH

    def test_missing_account(self) -> None:
        """Returns None for an address not in the trie."""
        witness_state = _make_ws({_ADDR1: _acct()})
        assert witness_state.get_account_optional(_ADDR2) is None

    def test_multiple_accounts(self) -> None:
        """Correctly distinguishes between multiple accounts."""
        witness_state = _make_ws(
            {_ADDR1: _acct(balance=100), _ADDR2: _acct(balance=200)}
        )
        r1 = witness_state.get_account_optional(_ADDR1)
        r2 = witness_state.get_account_optional(_ADDR2)
        assert r1 is not None and r1.balance == U256(100)
        assert r2 is not None and r2.balance == U256(200)


class TestGetStorage:
    """Test WitnessState.get_storage."""

    def test_existing_slot(self) -> None:
        """Returns the storage value for a known slot."""
        witness_state = _make_ws(
            {_ADDR1: _acct()}, {_ADDR1: {_SLOT1: U256(42)}}
        )
        assert witness_state.get_storage(_ADDR1, _SLOT1) == U256(42)

    def test_missing_slot(self) -> None:
        """Returns U256(0) for a slot not in the trie."""
        witness_state = _make_ws(
            {_ADDR1: _acct()}, {_ADDR1: {_SLOT1: U256(42)}}
        )
        assert witness_state.get_storage(_ADDR1, _SLOT2) == U256(0)

    def test_no_storage_account(self) -> None:
        """Returns U256(0) for an account with no storage."""
        witness_state = _make_ws({_ADDR1: _acct(balance=100)})
        assert witness_state.get_storage(_ADDR1, _SLOT1) == U256(0)

    def test_multiple_slots(self) -> None:
        """Correctly distinguishes between multiple storage slots."""
        witness_state = _make_ws(
            {_ADDR1: _acct()}, {_ADDR1: {_SLOT1: U256(10), _SLOT2: U256(20)}}
        )
        assert witness_state.get_storage(_ADDR1, _SLOT1) == U256(10)
        assert witness_state.get_storage(_ADDR1, _SLOT2) == U256(20)


class TestGetCode:
    """Test WitnessState.get_code."""

    def test_empty_code_hash(self) -> None:
        """EMPTY_CODE_HASH always returns b'' without a lookup."""
        witness_state = _make_ws({})
        assert witness_state.get_code(EMPTY_CODE_HASH) == b""

    def test_known_code(self) -> None:
        """Returns the bytecode for a known code hash."""
        witness_state = _make_ws({}, code_db=build_code_db((_CODE,)))
        assert witness_state.get_code(_CODE_HASH) == _CODE


class TestComputeStateRoot:
    """Test WitnessState.compute_state_root_and_trie_changes."""

    def test_account_balance_change(self) -> None:
        """Changing an account balance produces the correct new state root."""
        witness_state = _make_ws({_ADDR1: _acct(balance=100)})
        new_acct = _acct(balance=200)
        new_root, _ = witness_state.compute_state_root_and_trie_changes(
            {_ADDR1: new_acct}, {}
        )
        expected_root, _ = _build_witness({_ADDR1: new_acct}, {})
        assert new_root == expected_root

    def test_storage_slot_change(self) -> None:
        """Changing a storage slot produces the correct new state root."""
        acct = _acct()
        witness_state = _make_ws({_ADDR1: acct}, {_ADDR1: {_SLOT1: U256(10)}})
        new_root, _ = witness_state.compute_state_root_and_trie_changes(
            {}, {_ADDR1: {_SLOT1: U256(99)}}
        )
        expected_root, _ = _build_witness(
            {_ADDR1: acct}, {_ADDR1: {_SLOT1: U256(99)}}
        )
        assert new_root == expected_root

    def test_no_changes_preserves_root(self) -> None:
        """Empty diffs leave the state root unchanged."""
        state_root, node_db = _build_witness({_ADDR1: _acct(balance=100)}, {})
        witness_state = WitnessState(
            _node_db=node_db, _state_root=state_root, _code_db={}
        )
        new_root, _ = witness_state.compute_state_root_and_trie_changes({}, {})
        assert new_root == state_root


class TestCanonicalSecureTrieValidation:
    """Test state/storage-trie canonicality checks in WitnessState."""

    def test_account_trie_rejects_zero_length_extension_path(self) -> None:
        """Account tries must reject empty extension segments."""
        branch: list[Any] = [b""] * 17
        branch[0] = [nibble_list_to_compact(Bytes(b"\x01"), True), b"left"]
        branch[1] = [nibble_list_to_compact(Bytes(b"\x02"), True), b"right"]
        root_rlp = Bytes(
            rlp.encode([nibble_list_to_compact(Bytes(b""), False), branch])
        )
        state_root, node_db = _root_witness(root_rlp)
        witness_state = WitnessState(
            _node_db=node_db,
            _state_root=state_root,
            _code_db={},
        )

        with pytest.raises(
            AssertionError,
            match="ExtensionNode must have a non-empty path",
        ):
            witness_state.get_account_optional(_ADDR1)

    def test_storage_trie_rejects_zero_length_extension_path(self) -> None:
        """Storage tries must reject empty extension segments."""
        branch: list[Any] = [b""] * 17
        branch[0] = [nibble_list_to_compact(Bytes(b"\x01"), True), b"left"]
        branch[1] = [nibble_list_to_compact(Bytes(b"\x02"), True), b"right"]
        root_rlp = Bytes(
            rlp.encode([nibble_list_to_compact(Bytes(b""), False), branch])
        )
        storage_root, storage_node_db = _root_witness(root_rlp)
        state_root, state_node_db = _single_account_state_witness(
            storage_root=storage_root
        )
        witness_state = WitnessState(
            _node_db={**state_node_db, **storage_node_db},
            _state_root=state_root,
            _code_db={},
        )

        with pytest.raises(
            AssertionError,
            match="ExtensionNode must have a non-empty path",
        ):
            witness_state.get_storage(_ADDR1, _SLOT1)

    def test_account_trie_rejects_unresolved_hashed_node(self) -> None:
        """Secured account lookups must not silently pass unresolved hashes."""
        fake_hash = Bytes(b"\x11" * 32)
        key_nibbles = bytes_to_nibble_list(keccak256(_ADDR1))
        root_rlp = Bytes(
            rlp.encode(
                [nibble_list_to_compact(key_nibbles[:1], False), fake_hash]
            )
        )
        state_root, node_db = _root_witness(root_rlp)
        witness_state = WitnessState(
            _node_db=node_db,
            _state_root=state_root,
            _code_db={},
        )

        with pytest.raises(
            AssertionError,
            match="Encountered unresolved HashedNode during witness lookup",
        ):
            witness_state.get_account_optional(_ADDR1)

    def test_storage_trie_rejects_unresolved_hashed_node(self) -> None:
        """Secured storage lookups must not silently pass unresolved hashes."""
        fake_hash = Bytes(b"\x22" * 32)
        key_nibbles = bytes_to_nibble_list(keccak256(_SLOT1))
        root_rlp = Bytes(
            rlp.encode(
                [nibble_list_to_compact(key_nibbles[:1], False), fake_hash]
            )
        )
        storage_root, storage_node_db = _root_witness(root_rlp)
        state_root, state_node_db = _single_account_state_witness(
            storage_root=storage_root
        )
        witness_state = WitnessState(
            _node_db={**state_node_db, **storage_node_db},
            _state_root=state_root,
            _code_db={},
        )

        with pytest.raises(
            AssertionError,
            match="Encountered unresolved HashedNode during witness lookup",
        ):
            witness_state.get_storage(_ADDR1, _SLOT1)
