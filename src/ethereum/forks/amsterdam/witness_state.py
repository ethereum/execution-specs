"""
Witness-backed PreState.

Implement the ``PreState`` protocol using execution witness data
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.merkle_patricia_trie import EMPTY_TRIE_ROOT
from ethereum.state import (
    EMPTY_CODE_HASH,
    Account,
    Address,
    BlockDiff,
    Root,
)

from .incremental_mpt import (
    IncrementalMPT,
    decode_witness_to_mpt,
    mpt_get,
    mpt_root,
    mpt_set,
    mpt_set_storage_slots,
)


def build_node_db(state_entries: Tuple[Bytes, ...]) -> Dict[Bytes, Bytes]:
    """Build hash -> RLP mapping from witness state preimages."""
    return {keccak256(entry): entry for entry in state_entries}


def build_code_db(code_entries: Tuple[Bytes, ...]) -> Dict[Hash32, Bytes]:
    """Build code_hash -> bytecode mapping from witness codes."""
    return {keccak256(code): code for code in code_entries}


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
    _decoded_secure_tries: Dict[Root, IncrementalMPT[Bytes, Bytes]] = field(
        default_factory=dict
    )

    def _get_decoded_secure_trie(
        self, root_hash: Root
    ) -> IncrementalMPT[Bytes, Bytes]:
        """Decode and cache a secured trie for read-only lookups."""
        if root_hash not in self._decoded_secure_tries:
            self._decoded_secure_tries[root_hash] = decode_witness_to_mpt(
                self._node_db,
                root_hash,
                secured=True,
                default=b"",
            )
        return self._decoded_secure_tries[root_hash]

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """
        Get the account at an address.

        Return ``None`` if there is no account at the address.
        """
        leaf = mpt_get(
            self._get_decoded_secure_trie(self._state_root), address
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

        leaf = mpt_get(self._get_decoded_secure_trie(storage_root), key)
        if leaf is None:
            return U256(0)
        return rlp.decode_to(U256, leaf)

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

        Build partial ``IncrementalMPT`` tries from the witness,
        apply diffs, and compute the new root.
        """
        account_changes = block_diff.account_changes
        storage_changes = block_diff.storage_changes
        storage_clears = block_diff.storage_clears
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
            mpt_set_storage_slots(storage_mpt, slots)
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
                    mpt_set(
                        state_mpt,
                        address,
                        account,
                        new_storage_roots.get(address, EMPTY_TRIE_ROOT),
                    )

        def get_storage_root(addr: Address) -> Root:
            if addr in new_storage_roots:
                return new_storage_roots[addr]
            if addr in storage_clears:
                return EMPTY_TRIE_ROOT
            return self._storage_root_cache.get(addr, EMPTY_TRIE_ROOT)

        for address, account in account_changes.items():
            mpt_set(state_mpt, address, account, get_storage_root(address))

        return mpt_root(state_mpt)
