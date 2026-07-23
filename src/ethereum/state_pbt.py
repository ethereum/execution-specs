"""
Binary-tree-backed implementation of the shared state model.

The [`State`] class here is the [EIP-8297] counterpart of
[`ethereum.state_mpt`]: an in-memory implementation of the
[`PreState`] protocol whose state roots are binary tree commitments.
Accounts and storage live in plain mappings; [`embed_flat_state`]
maps them to tree keys and values through
[`ethereum.binary_trie.embedding`], and [`compute_state_root`]
commits the result with [`ethereum.binary_trie.trie`].

This provider makes two deliberate simplifications:

- No transition machinery. On mainnet the EIP's tree would start
  empty beside a frozen Merkle Patricia Trie; here all state is in
  the tree from the start, which keeps the commitment testable in
  isolation.
- Zero means absent. A storage slot written to zero is removed
  rather than kept as a zero-valued leaf, matching
  [`ethereum.state_mpt`], even though the tree itself can represent
  both.

[EIP-8297]: https://eips.ethereum.org/EIPS/eip-8297
[`State`]: ref:ethereum.state_pbt.State
[`PreState`]: ref:ethereum.state.PreState
[`embed_flat_state`]: ref:ethereum.state_pbt.embed_flat_state
[`compute_state_root`]: ref:ethereum.state_pbt.State.compute_state_root
[`ethereum.state_mpt`]: ref:ethereum.state_mpt
[`ethereum.binary_trie.embedding`]: ref:ethereum.binary_trie.embedding
[`ethereum.binary_trie.trie`]: ref:ethereum.binary_trie.trie
"""  # noqa: E501

from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Optional, final

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U32, U64, U256, Uint

from ethereum.binary_trie.embedding import (
    address20_to_address32,
    chunkify_code,
    encode_basic_data,
    get_tree_key_for_basic_data,
    get_tree_key_for_code_chunk,
    get_tree_key_for_code_hash,
    get_tree_key_for_storage_slot,
)
from ethereum.binary_trie.trie import BinaryTrie, trie_set
from ethereum.binary_trie.trie import root as binary_tree_root
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import EMPTY_CODE_HASH, Account, Address, BlockDiff, Root


def embed_flat_state(
    accounts: Mapping[Address, Account],
    storages: Mapping[Address, Mapping[Bytes32, U256]],
    get_code: Callable[[Hash32], Bytes],
) -> BinaryTrie:
    """
    Embed a flat snapshot of state into a fresh binary tree.

    `accounts` maps addresses to their account records, `storages`
    maps addresses to their storage slots keyed by the raw 32-byte
    slot key, and `get_code` resolves a code hash to its bytecode.
    Every account contributes its basic data and code hash leaves,
    one leaf per code chunk, and one leaf per storage slot it has in
    `storages`.

    Addresses appearing in `storages` but not in `accounts` are
    ignored: storage belongs to an account, so slots without one
    have no place in the tree.
    """
    trie = BinaryTrie()

    for address, account in accounts.items():
        address32 = address20_to_address32(address)
        code = get_code(account.code_hash)

        trie_set(
            trie,
            get_tree_key_for_basic_data(address32),
            encode_basic_data(
                code_size=U32(len(code)),
                nonce=U64(account.nonce),
                balance=account.balance,
            ),
        )
        trie_set(
            trie,
            get_tree_key_for_code_hash(address32),
            Bytes32(account.code_hash),
        )
        for chunk_id, chunk in enumerate(chunkify_code(code)):
            trie_set(
                trie,
                get_tree_key_for_code_chunk(
                    address32, account.code_hash, Uint(chunk_id)
                ),
                chunk,
            )

    for address, slots in storages.items():
        if address not in accounts:
            continue
        address32 = address20_to_address32(address)
        for key, value in slots.items():
            trie_set(
                trie,
                get_tree_key_for_storage_slot(
                    address32, U256.from_be_bytes(key)
                ),
                value.to_be_bytes32(),
            )

    return trie


@final
@dataclass
class State:
    """
    Contains all information that is preserved between transactions.
    """

    _accounts: Dict[Address, Account] = field(default_factory=dict)
    _storage: Dict[Address, Dict[Bytes32, U256]] = field(default_factory=dict)
    _code_store: Dict[Hash32, Bytes] = field(
        default_factory=dict, compare=False
    )

    def get_code(self, code_hash: Hash32) -> Bytes:
        """
        Get the bytecode for a given code hash.

        Return ``b""`` for ``EMPTY_CODE_HASH``.
        """
        if code_hash == EMPTY_CODE_HASH:
            return b""
        return self._code_store[code_hash]

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """
        Get the account at an address.

        Return ``None`` if there is no account at the address.
        """
        return self._accounts.get(address)

    def get_storage(self, address: Address, key: Bytes32) -> U256:
        """
        Get a storage value.

        Return ``U256(0)`` if the key has not been set.
        """
        return self._storage.get(address, {}).get(key, U256(0))

    def account_has_storage(self, address: Address) -> bool:
        """
        Check whether an account has any storage.

        Only needed for EIP-7610.
        """
        return address in self._storage

    def compute_state_root(self, block_diff: BlockDiff) -> Root:
        """
        Compute the state root after applying `block_diff` to the
        pre-state. The pre-state itself is not modified.

        The diff's ``code_changes`` are needed here, unlike in the
        Merkle Patricia Trie: code chunk leaves commit the code
        itself, not just its hash, and newly deployed code is not yet
        in the code store when the root is computed.

        An account mapped to ``None`` is deleted along with its
        storage, and a storage slot written to zero is deleted.

        Return the new state root.
        """
        accounts = dict(self._accounts)
        storages = {
            address: dict(slots)
            for address, slots in self._storage.items()
            if address not in block_diff.storage_clears
        }

        for address, account in block_diff.account_changes.items():
            if account is None:
                accounts.pop(address, None)
                storages.pop(address, None)
            else:
                accounts[address] = account

        for address, slots in block_diff.storage_changes.items():
            slot_values = storages.setdefault(address, {})
            for key, value in slots.items():
                if value == U256(0):
                    slot_values.pop(key, None)
                else:
                    slot_values[key] = value

        def get_code(code_hash: Hash32) -> Bytes:
            if code_hash in block_diff.code_changes:
                return block_diff.code_changes[code_hash]
            return self.get_code(code_hash)

        return binary_tree_root(embed_flat_state(accounts, storages, get_code))


def apply_changes_to_state(state: State, diff: BlockDiff) -> None:
    """
    Apply block-level diff to the ``State`` for the next block.

    Parameters
    ----------
    state :
        The state to update.
    diff :
        Account, storage, and code changes to apply.

    """
    for address in diff.storage_clears:
        state._storage.pop(address, None)

    for address, account in diff.account_changes.items():
        if account is None:
            state._accounts.pop(address, None)
            state._storage.pop(address, None)
        else:
            state._accounts[address] = account

    for address, slots in diff.storage_changes.items():
        slot_values = state._storage.setdefault(address, {})
        for key, value in slots.items():
            if value == U256(0):
                slot_values.pop(key, None)
            else:
                slot_values[key] = value
        if slot_values == {}:
            del state._storage[address]

    state._code_store.update(diff.code_changes)


def store_code(state: State, code: Bytes) -> Hash32:
    """
    Store bytecode in ``State``.
    """
    code_hash = keccak256(code)
    if code_hash != EMPTY_CODE_HASH:
        state._code_store[code_hash] = code
    return code_hash


def set_account(
    state: State,
    address: Address,
    account: Optional[Account],
) -> None:
    """
    Set an account in a ``State``.

    Setting to ``None`` deletes the account.
    """
    if account is None:
        state._accounts.pop(address, None)
    else:
        state._accounts[address] = account


def set_storage(
    state: State,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """
    Set a storage value in a ``State``.

    Setting to ``U256(0)`` deletes the key.
    """
    assert address in state._accounts

    slot_values = state._storage.setdefault(address, {})
    if value == U256(0):
        slot_values.pop(key, None)
    else:
        slot_values[key] = value
    if slot_values == {}:
        del state._storage[address]


def state_root(state: State) -> Root:
    """
    Compute the state root of the current state.
    """
    return state.compute_state_root(BlockDiff())
