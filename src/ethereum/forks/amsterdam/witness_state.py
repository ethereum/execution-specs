"""
Witness-backed PreState.

Implement the ``PreState`` protocol using execution witness data
"""

from dataclasses import dataclass, field
from typing import AbstractSet, Dict, List, Optional, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.merkle_patricia_trie import EMPTY_TRIE_ROOT, InternalNode
from ethereum.state import (
    EMPTY_CODE_HASH,
    Account,
    Address,
    BlockDiff,
    Root,
)

from .incremental_mpt import (
    HashedNode,
    IncrementalMPT,
    MutableBranchNode,
    MutableExtensionNode,
    MutableLeafNode,
    MutableNode,
    decode_witness_to_mpt,
    mpt_root,
    mpt_set,
)


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


def _trie_lookup(
    root_node: MutableNode,
    key_hash: Hash32,
) -> Optional[Bytes]:
    """
    Walk a decoded MPT from root following nibblized key_hash.

    Return leaf value or ``None`` if not found.

    """
    nibbles = bytearray()
    for byte in key_hash:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)

    node = root_node
    pos = 0

    while node is not None:
        if isinstance(node, HashedNode):
            raise AssertionError(
                "Encountered unresolved HashedNode during witness lookup"
            )

        if isinstance(node, MutableLeafNode):
            if bytes(nibbles[pos:]) == node.rest_of_key:
                return node.value
            return None

        if isinstance(node, MutableExtensionNode):
            segment = node.key_segment
            if bytes(nibbles[pos : pos + len(segment)]) != segment:
                return None
            pos += len(segment)
            node = node.child
            continue

        assert isinstance(node, MutableBranchNode), (
            f"Unexpected node type {type(node)}"
        )

        if pos == len(nibbles):
            return node.value or None
        idx = nibbles[pos]
        pos += 1
        node = node.children[idx]

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


@final
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
    _decoded_secure_roots: Dict[Root, MutableNode] = field(
        default_factory=dict
    )

    def _get_decoded_secure_root(self, root_hash: Root) -> MutableNode:
        """Decode and cache a secured trie root for read-only lookups."""
        if root_hash == EMPTY_TRIE_ROOT:
            return None
        if root_hash not in self._decoded_secure_roots:
            decoded_mpt: IncrementalMPT[Bytes, Bytes] = decode_witness_to_mpt(
                self._node_db,
                root_hash,
                secured=True,
                default=b"",
            )
            self._decoded_secure_roots[root_hash] = decoded_mpt.root_node
        return self._decoded_secure_roots[root_hash]

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """
        Get the account at an address.

        Return ``None`` if there is no account at the address.
        """
        key_hash = keccak256(address)
        leaf = _trie_lookup(
            self._get_decoded_secure_root(self._state_root), key_hash
        )
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
        leaf = _trie_lookup(
            self._get_decoded_secure_root(storage_root), key_hash
        )
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

    def compute_state_root(self, block_diff: BlockDiff) -> Root:
        """
        Compute the state root after applying ``block_diff``.

        Conform to the implementation-agnostic ``PreState`` protocol while
        reusing the witness-backed incremental MPT calculation.
        """
        state_root, _ = self.compute_state_root_and_trie_changes(
            block_diff.account_changes,
            block_diff.storage_changes,
            block_diff.storage_clears,
        )
        return state_root

    def compute_state_root_and_trie_changes(
        self,
        account_changes: Dict[Address, Optional[Account]],
        storage_changes: Dict[Address, Dict[Bytes32, U256]],
        storage_clears: AbstractSet[Address] = frozenset(),
    ) -> Tuple[Root, List[InternalNode]]:
        """
        Compute the state root after applying changes.

        Build partial ``IncrementalMPT`` tries from the witness,
        apply diffs, and compute the new root.
        """
        new_storage_roots: Dict[Address, Root] = {}

        for address, slots in storage_changes.items():
            if (
                address not in storage_clears
                and address not in self._storage_root_cache
            ):
                self.get_account_optional(address)
            old_root = (
                EMPTY_TRIE_ROOT
                if address in storage_clears
                else self._storage_root_cache.get(address, EMPTY_TRIE_ROOT)
            )
            storage_mpt: IncrementalMPT[Bytes32, U256] = decode_witness_to_mpt(
                self._node_db,
                old_root,
                secured=True,
                default=U256(0),
            )
            # We must do insertions+updates before deletions to minimize branch
            # compressions.
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

        storage_touched = set(storage_changes) | set(storage_clears)
        for address in storage_touched:
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
            if addr in storage_clears:
                return EMPTY_TRIE_ROOT
            return self._storage_root_cache.get(addr, EMPTY_TRIE_ROOT)

        for address, account in account_changes.items():
            mpt_set(
                state_mpt,
                address,
                account,
                get_storage_root=get_storage_root,
            )

        return mpt_root(state_mpt), []
