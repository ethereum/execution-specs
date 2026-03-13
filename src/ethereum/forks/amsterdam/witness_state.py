"""
Witness-backed PreState.

Implement the ``PreState`` protocol using execution witness data
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import (
    EMPTY_CODE_HASH,
    Account,
    Address,
    InternalNode,
    Root,
)

from .incremental_mpt import (
    IncrementalMPT,
    compact_to_nibbles,
    decode_witness_to_mpt,
    mpt_root,
    mpt_set,
)
from .trie import EMPTY_TRIE_ROOT


def build_node_db(state_entries: Tuple[Bytes, ...]) -> Dict[Bytes, Bytes]:
    """Build hash -> RLP mapping from witness state preimages."""
    db: Dict[Bytes, Bytes] = {}
    for entry in state_entries:
        db[keccak256(entry)] = entry
    return db


def build_code_db(code_entries: Tuple[Bytes, ...]) -> Dict[Hash32, Bytes]:
    """Build code_hash -> bytecode mapping from witness codes."""
    db: Dict[Hash32, Bytes] = {}
    for code in code_entries:
        db[keccak256(code)] = code
    return db


def _resolve_node_ref(
    node_db: Dict[Bytes, Bytes],
    ref: object,
) -> object:
    """
    Resolve a node reference to a decoded RLP object.

    Handle inline nodes (lists), 32-byte hash references (look up
    in node_db), and empty bytes (absent node).
    """
    if isinstance(ref, list):
        return ref
    if isinstance(ref, (bytes, bytearray)):
        ref_bytes = Bytes(ref)
        if len(ref_bytes) == 0:
            return None
        if len(ref_bytes) == 32:
            if ref_bytes not in node_db:
                return None
            return rlp.decode(node_db[ref_bytes])
        return rlp.decode(ref_bytes)
    return None


def _trie_lookup(
    node_db: Dict[Bytes, Bytes],
    root_hash: Root,
    key_hash: Hash32,
) -> Optional[Bytes]:
    """
    Walk MPT from root following nibblized key_hash.

    Return leaf value or ``None`` if not found.

    Parameters
    ----------
    node_db :
        Mapping from node hash to RLP-encoded node data.
    root_hash :
        Root hash of the trie.
    key_hash :
        Hashed key to look up (will be nibblized).

    """
    if root_hash == EMPTY_TRIE_ROOT:
        return None
    if root_hash not in node_db:
        return None

    nibbles = bytearray()
    for byte in key_hash:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)

    node = _resolve_node_ref(node_db, root_hash)
    pos = 0

    while node is not None:
        if not isinstance(node, list):
            return None

        if len(node) == 2:
            path = node[0]
            assert isinstance(path, (bytes, bytearray))
            segment, is_leaf = compact_to_nibbles(Bytes(path))
            remaining = bytes(nibbles[pos:])

            if is_leaf:
                if remaining == segment:
                    value = node[1]
                    assert isinstance(value, (bytes, bytearray))
                    return Bytes(value)
                return None
            else:
                if not remaining[: len(segment)] == segment:
                    return None
                pos += len(segment)
                node = _resolve_node_ref(node_db, node[1])

        elif len(node) == 17:
            if pos >= len(nibbles):
                value = node[16]
                if isinstance(value, (bytes, bytearray)) and len(value) > 0:
                    return Bytes(value)
                return None
            idx = nibbles[pos]
            pos += 1
            node = _resolve_node_ref(node_db, node[idx])
        else:
            return None

    return None


def _decode_account_from_leaf(
    leaf_value: Bytes,
) -> Tuple[Account, Root]:
    """
    Decode (nonce, balance, storage_root, code_hash) from trie leaf.

    Return the ``Account`` and the ``storage_root`` separately
    (storage_root is not stored on ``Account``).
    """
    decoded = rlp.decode(leaf_value)
    assert isinstance(decoded, list) and len(decoded) == 4

    nonce = Uint(int.from_bytes(decoded[0], "big")) if decoded[0] else Uint(0)
    balance = (
        U256(int.from_bytes(decoded[1], "big")) if decoded[1] else U256(0)
    )
    storage_root = Root(decoded[2]) if decoded[2] else EMPTY_TRIE_ROOT
    code_hash = Hash32(decoded[3]) if decoded[3] else EMPTY_CODE_HASH

    account = Account(
        nonce=nonce,
        balance=balance,
        code_hash=code_hash,
    )
    return account, storage_root


@dataclass
class WitnessState:
    """
    ``PreState`` backed by execution witness data.

    Serve account, storage, and code reads from trie-node
    preimages and bytecodes provided in the execution witness.
    """

    _node_db: Dict[Bytes, Bytes]
    _state_root: Root
    _code_db: Dict[Hash32, Bytes]
    _storage_root_cache: Dict[Address, Root] = field(default_factory=dict)

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """
        Get the account at an address.

        Return ``None`` if there is no account at the address.
        """
        key_hash = keccak256(address)
        leaf = _trie_lookup(self._node_db, self._state_root, key_hash)
        if leaf is None:
            self._storage_root_cache[address] = EMPTY_TRIE_ROOT
            return None
        account, storage_root = _decode_account_from_leaf(leaf)
        self._storage_root_cache[address] = storage_root
        return account

    def get_storage(self, address: Address, key: Bytes32) -> U256:
        """
        Get a storage value.

        Return ``U256(0)`` if the key has not been set.
        """
        if address not in self._storage_root_cache:
            self.get_account_optional(address)
        storage_root = self._storage_root_cache.get(address, EMPTY_TRIE_ROOT)
        if storage_root == EMPTY_TRIE_ROOT:
            return U256(0)

        key_hash = keccak256(key)
        leaf = _trie_lookup(self._node_db, storage_root, key_hash)
        if leaf is None:
            return U256(0)

        decoded = rlp.decode(leaf)
        if isinstance(decoded, (bytes, bytearray)):
            if len(decoded) == 0:
                return U256(0)
            return U256(int.from_bytes(decoded, "big"))
        return U256(0)

    def get_code(self, code_hash: Hash32) -> Bytes:
        """
        Get the bytecode for a given code hash.

        Return ``b""`` for ``EMPTY_CODE_HASH``.
        """
        if code_hash == EMPTY_CODE_HASH:
            return b""
        return self._code_db[code_hash]

    def account_has_storage(self, address: Address) -> bool:
        """
        Check whether an account has any storage.

        Only needed for EIP-7610.
        """
        if address not in self._storage_root_cache:
            self.get_account_optional(address)
        storage_root = self._storage_root_cache.get(address, EMPTY_TRIE_ROOT)
        return storage_root != EMPTY_TRIE_ROOT

    def compute_state_root_and_trie_changes(
        self,
        account_changes: Dict[Address, Optional[Account]],
        storage_changes: Dict[Address, Dict[Bytes32, U256]],
    ) -> Tuple[Root, List[InternalNode]]:
        """
        Compute the state root after applying changes.

        Build partial ``IncrementalMPT`` tries from the witness,
        apply diffs, and compute the new root.
        """
        new_storage_roots: Dict[Address, Root] = {}

        for address, slots in storage_changes.items():
            if address not in self._storage_root_cache:
                self.get_account_optional(address)
            old_root = self._storage_root_cache.get(address, EMPTY_TRIE_ROOT)
            storage_mpt: IncrementalMPT[Bytes32, U256] = decode_witness_to_mpt(
                self._node_db,
                old_root,
                secured=True,
                default=U256(0),
            )
            # Mirror host-side witness construction: replay insert/update
            # writes first, then deletions, to avoid transient branch
            # compressions that would incorrectly require extra witness nodes.
            for key, value in slots.items():
                if value != 0:
                    mpt_set(storage_mpt, key, value)
            for key, value in slots.items():
                if value == 0:
                    mpt_set(storage_mpt, key, value)
            new_storage_roots[address] = mpt_root(storage_mpt)

        state_mpt: IncrementalMPT[Address, Optional[Account]] = (
            decode_witness_to_mpt(
                self._node_db,
                self._state_root,
                secured=True,
                default=None,
            )
        )

        for address in storage_changes:
            if address not in account_changes:
                account = self.get_account_optional(address)
                if account is not None:
                    sr = new_storage_roots.get(address, EMPTY_TRIE_ROOT)

                    def _sr_fn(_a: Address, _sr: Root = sr) -> Root:
                        return _sr

                    mpt_set(
                        state_mpt,
                        address,
                        account,
                        get_storage_root=_sr_fn,
                    )

        def get_storage_root(addr: Address) -> Root:
            if addr in new_storage_roots:
                return new_storage_roots[addr]
            return self._storage_root_cache.get(addr, EMPTY_TRIE_ROOT)

        for address, account in account_changes.items():
            mpt_set(
                state_mpt,
                address,
                account,
                get_storage_root=get_storage_root,
            )

        return mpt_root(state_mpt), []
