"""
Incremental Merkle Patricia Trie roots for allocation state roots.

The spec builds every trie from scratch, which costs time proportional to the
whole state on every block. Fixtures that share a large genesis
(pre-allocation groups) pay that cost for every block of every test.

The tries here compute the same roots with the spec's node types and
encoders, but cache every subtree encoding by its nibble prefix. Applying
changes drops only the cached prefixes of the changed keys, so the next root
re-encodes roughly `changes x depth` nodes instead of the whole trie.
"""

from bisect import bisect_left, insort
from typing import Any, Dict, Iterable, List, Mapping, Optional, Self, Tuple

from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import (
    EMPTY_TRIE_ROOT,
    BranchNode,
    ExtensionNode,
    LeafNode,
    bytes_to_nibble_list,
    encode_account,
    encode_internal_node,
)
from ethereum.state import Account, BlockDiff, Root
from ethereum_rlp import Extended, rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256

_EMPTY_NODE = encode_internal_node(None)


class IncrementalTrie:
    """
    Secured trie over nibble keys, caching each subtree encoding by prefix.

    Instances are immutable: `with_changes` returns a new trie and leaves
    the original (and its cache) untouched.
    """

    __slots__ = ("_keys", "_values", "_cache")

    def __init__(
        self,
        keys: List[bytes],
        values: Dict[bytes, bytes],
        cache: Dict[bytes, Extended],
    ) -> None:
        """Wrap sorted `keys`, their encoded `values` and a node cache."""
        self._keys = keys
        self._values = values
        self._cache = cache

    @classmethod
    def build(cls, items: Mapping[bytes, bytes]) -> Self:
        """Build a trie from nibble keys and RLP-encoded values."""
        return cls(sorted(items), dict(items), {})

    def __len__(self) -> int:
        """Return the number of keys."""
        return len(self._keys)

    def __deepcopy__(self, memo: Dict[int, Any]) -> Self:
        """Return `self`, as the trie is immutable."""
        return self

    def with_changes(self, changes: Mapping[bytes, Optional[bytes]]) -> Self:
        """Return a trie with `changes` applied, where `None` deletes."""
        if not changes:
            return self
        keys = list(self._keys)
        values = dict(self._values)
        cache = dict(self._cache)
        for key, value in changes.items():
            if value is None:
                if key in values:
                    del values[key]
                    del keys[bisect_left(keys, key)]
            else:
                if key not in values:
                    insort(keys, key)
                values[key] = value
            for length in range(len(key) + 1):
                cache.pop(key[:length], None)
        return type(self)(keys, values, cache)

    def _node(self, prefix: bytes) -> Extended:
        """
        Return the encoded node for the keys under `prefix`, mirroring the
        spec's `patricialize` at level `len(prefix)`.
        """
        cached = self._cache.get(prefix)
        if cached is not None:
            return cached
        keys = self._keys
        low = bisect_left(keys, prefix)
        high = bisect_left(keys, prefix + b"\x10", low)
        if low == high:
            return _EMPTY_NODE
        level = len(prefix)
        first = keys[low]
        if high - low == 1:
            encoded = encode_internal_node(
                LeafNode(Bytes(first[level:]), self._values[first])
            )
        else:
            # Keys are sorted, so the prefix shared by all of them is the
            # prefix shared by the first and the last.
            last = keys[high - 1]
            limit = min(len(first), len(last))
            end = level
            while end < limit and first[end] == last[end]:
                end += 1
            if end > level:
                encoded = encode_internal_node(
                    ExtensionNode(
                        Bytes(first[level:end]), self._node(first[:end])
                    )
                )
            else:
                value = self._values[first] if len(first) == level else b""
                subnodes = tuple(
                    self._node(prefix + bytes((nibble,)))
                    for nibble in range(16)
                )
                encoded = encode_internal_node(
                    BranchNode(subnodes, value)  # type: ignore[arg-type]
                )
        self._cache[prefix] = encoded
        return encoded

    def root(self) -> Root:
        """Return the root hash, as the spec's `merkle_patricia_trie.root`."""
        root_node = self._node(b"")
        encoded = rlp.encode(root_node)
        if len(encoded) < 32:
            return keccak256(encoded)
        assert isinstance(root_node, bytes)
        return Root(root_node)


_EMPTY_TRIE = IncrementalTrie([], {}, {})


def _secured_key(preimage: bytes) -> bytes:
    """Return the nibble key a secured trie stores `preimage` under."""
    return bytes(bytes_to_nibble_list(keccak256(preimage)))


def _encode_storage_value(value: int) -> bytes:
    """Return the RLP encoding of a storage value."""
    return rlp.encode(U256(value))


class IncrementalStateTrie:
    """
    State trie of an allocation: the account trie plus one incremental
    storage trie per account with storage.

    `with_diff` applies a `BlockDiff` the way `Alloc.apply_diff` does, so the
    trie of an allocation stays in step with its accounts across blocks.
    """

    __slots__ = ("_accounts", "_storage", "_account_trie")

    def __init__(
        self,
        accounts: Dict[bytes, Account],
        storage: Dict[bytes, IncrementalTrie],
        account_trie: IncrementalTrie,
    ) -> None:
        """Wrap the accounts, their storage tries and the account trie."""
        self._accounts = accounts
        self._storage = storage
        self._account_trie = account_trie

    def __deepcopy__(self, memo: Dict[int, Any]) -> Self:
        """Return `self`, as the trie is immutable."""
        return self

    @classmethod
    def build(
        cls,
        items: Iterable[Tuple[bytes, Account, Mapping[bytes, int]]],
    ) -> Self:
        """
        Build from `(address, account, {storage key: value})` triples,
        skipping zero storage values as the spec's `set_storage` does.
        """
        accounts: Dict[bytes, Account] = {}
        storage: Dict[bytes, IncrementalTrie] = {}
        leaves: Dict[bytes, bytes] = {}
        for address, account, slots in items:
            accounts[address] = account
            encoded_slots = {
                _secured_key(key): _encode_storage_value(value)
                for key, value in slots.items()
                if value != 0
            }
            if encoded_slots:
                storage[address] = IncrementalTrie.build(encoded_slots)
            leaves[_secured_key(address)] = encode_account(
                account, _storage_root(storage, address)
            )
        return cls(accounts, storage, IncrementalTrie.build(leaves))

    def with_diff(self, diff: BlockDiff) -> Self:
        """Return the state trie after `Alloc.apply_diff(diff)`."""
        accounts = dict(self._accounts)
        storage = dict(self._storage)
        touched = set()

        for raw_address in diff.storage_clears:
            address = bytes(raw_address)
            touched.add(address)
            if address in accounts:
                storage.pop(address, None)

        for raw_address, account in diff.account_changes.items():
            address = bytes(raw_address)
            touched.add(address)
            if account is None:
                accounts.pop(address, None)
                storage.pop(address, None)
                continue
            accounts[address] = account

        for raw_address, slots in diff.storage_changes.items():
            address = bytes(raw_address)
            touched.add(address)
            if address not in accounts:
                continue
            trie = storage.get(address, _EMPTY_TRIE).with_changes(
                {
                    _secured_key(bytes(key)): (
                        _encode_storage_value(int(value))
                        if int(value) != 0
                        else None
                    )
                    for key, value in slots.items()
                }
            )
            if len(trie):
                storage[address] = trie
            else:
                storage.pop(address, None)

        leaves: Dict[bytes, Optional[bytes]] = {}
        for address in touched:
            account = accounts.get(address)
            leaves[_secured_key(address)] = (
                encode_account(account, _storage_root(storage, address))
                if account is not None
                else None
            )
        return type(self)(
            accounts, storage, self._account_trie.with_changes(leaves)
        )

    def root(self) -> Root:
        """Return the state root."""
        return self._account_trie.root()


def _storage_root(
    storage: Mapping[bytes, IncrementalTrie], address: bytes
) -> Root:
    """Return the storage root of `address`."""
    trie = storage.get(address)
    return trie.root() if trie is not None else EMPTY_TRIE_ROOT
