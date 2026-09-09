"""Helpers for `ExecutionWitness.state` tests."""

from collections.abc import Mapping, Sequence

from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256, Uint
from execution_testing import Account, Address, Alloc, Bytes, Storage
from execution_testing.forks import Amsterdam

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.forks.amsterdam.incremental_mpt import (
    build_mpt,
    mpt_get,
    mpt_root,
    mpt_set,
)
from ethereum.merkle_patricia_trie import EMPTY_TRIE_ROOT
from ethereum.state import (
    EMPTY_CODE_HASH,
    Root,
)
from ethereum.state import (
    Account as StateAccount,
)
from ethereum.state import (
    Address as StateAddress,
)


def large_storage_value(slot: int) -> int:
    """Return a 32-byte non-zero value so the leaf node is hashed."""
    return (1 << 255) + slot


def build_large_storage(slots: Sequence[int]) -> dict[int, int]:
    """Build a slot->value mapping with large deterministic values."""
    return {slot: large_storage_value(slot) for slot in slots}


def as_storage(storage: Mapping[int, int]) -> Storage:
    """Convert an int-keyed storage mapping into a `Storage`."""
    return Storage.model_validate(dict(storage.items()))


def _slot(slot: int) -> Bytes32:
    """Convert an integer slot into a 32-byte storage key."""
    return Bytes32(slot.to_bytes(32, byteorder="big"))


def _storage_mpt_input(storage: Mapping[int, int]) -> dict[Bytes32, U256]:
    """Convert int-based storage into the internal MPT key/value types."""
    return {_slot(slot): U256(value) for slot, value in storage.items()}


def _collect_storage_node_set(
    storage: Mapping[int, int],
    slots: Sequence[int],
) -> set[bytes]:
    """Collect hashed witness nodes for the given storage proof paths."""
    storage_mpt = build_mpt(
        _storage_mpt_input(storage), secured=True, default=U256(0)
    )
    for slot in slots:
        mpt_get(storage_mpt, _slot(slot))
    return set(storage_mpt.witness.accessed_nodes.values())


def _nodes(nodes: set[bytes]) -> list[Bytes]:
    """Return nodes as execution-testing bytes."""
    return [Bytes(node) for node in nodes]


def collect_storage_proof_nodes(
    storage: Mapping[int, int],
    slots: Sequence[int],
) -> list[Bytes]:
    """Collect the pre-state proof nodes for the given storage slots."""
    return _nodes(_collect_storage_node_set(storage, slots))


def collect_storage_delete_auxiliary_nodes(
    storage: Mapping[int, int],
    slot_to_delete: int,
) -> list[Bytes]:
    """Collect nodes added only because a delete compressed the trie."""
    storage_mpt = build_mpt(
        _storage_mpt_input(storage), secured=True, default=U256(0)
    )
    mpt_get(storage_mpt, _slot(slot_to_delete))
    before = set(storage_mpt.witness.accessed_nodes.values())
    mpt_set(storage_mpt, _slot(slot_to_delete), U256(0))
    after = set(storage_mpt.witness.accessed_nodes.values())
    return _nodes(after - before)


def collect_storage_path_only_nodes(
    storage: Mapping[int, int],
    slot: int,
    relative_to_slots: Sequence[int],
) -> list[Bytes]:
    """Collect nodes unique to one proof path relative to others."""
    slot_nodes = _collect_storage_node_set(storage, [slot])
    reference_nodes = _collect_storage_node_set(storage, relative_to_slots)
    return _nodes(slot_nodes - reference_nodes)


def collect_storage_post_state_only_nodes(
    pre_storage: Mapping[int, int],
    post_storage: Mapping[int, int],
    slot: int,
    pre_state_reference_slots: Sequence[int],
) -> list[Bytes]:
    """Collect nodes that appear only on the post-state proof path."""
    post_state_nodes = _collect_storage_node_set(post_storage, [slot])
    pre_state_nodes = _collect_storage_node_set(
        pre_storage, pre_state_reference_slots
    )
    return _nodes(post_state_nodes - pre_state_nodes)


def find_account_with_shared_secured_nibble(
    target: Address,
    excluded: set[Address],
) -> Address:
    """Return an occupied address that deepens one account absence proof."""
    target_nibble = keccak256(bytes(target))[0] >> 4
    for value in range(0x100, 0x1000):
        address = Address(value)
        if address in excluded:
            continue
        if (keccak256(bytes(address))[0] >> 4) == target_nibble:
            return address
    raise AssertionError("failed to find non-precompile sibling address")


def merge_with_amsterdam_pre_alloc(pre: Alloc) -> Alloc:
    """Merge test-local accounts with Amsterdam's implicit pre-allocation."""
    return Alloc.merge(
        Alloc.model_validate(Amsterdam.pre_allocation_blockchain()),
        pre,
    )


def _storage_root_for_account(account: Account) -> Root:
    """Compute the storage root for one execution-testing account."""
    if not account.storage.root:
        return EMPTY_TRIE_ROOT
    storage_mpt = build_mpt(
        {
            _slot(int(slot)): U256(int(value))
            for slot, value in account.storage.root.items()
        },
        secured=True,
        default=U256(0),
    )
    return mpt_root(storage_mpt)


def _state_account(account: Account) -> StateAccount:
    """Convert an execution-testing account into the spec account type."""
    code = bytes(account.code)
    code_hash = EMPTY_CODE_HASH if len(code) == 0 else Hash32(keccak256(code))
    return StateAccount(
        nonce=Uint(int(account.nonce)),
        balance=U256(int(account.balance)),
        code_hash=code_hash,
    )


def _collect_account_proof_node_rlps(
    alloc: Alloc,
    addresses: Sequence[StateAddress | bytes],
) -> set[bytes]:
    """Collect witness node RLPs for hashed account proof-path nodes."""
    storage_roots: dict[StateAddress, Root] = {}
    accounts: dict[StateAddress, StateAccount | None] = {}

    for address, account in alloc.items():
        state_address = StateAddress(bytes(address))
        if account is None:
            accounts[state_address] = None
            continue
        storage_roots[state_address] = _storage_root_for_account(account)
        accounts[state_address] = _state_account(account)

    def get_storage_root(address: StateAddress) -> Root:
        return storage_roots.get(address, EMPTY_TRIE_ROOT)

    account_mpt = build_mpt(
        accounts,
        secured=True,
        default=None,
        get_storage_root=get_storage_root,
    )
    for addr in addresses:
        mpt_get(account_mpt, StateAddress(bytes(addr)))
    return set(account_mpt.witness.accessed_nodes.values())


def collect_account_proof_nodes(
    alloc: Alloc,
    addresses: Sequence[StateAddress | bytes],
) -> list[Bytes]:
    """Collect account-trie proof nodes for the given addresses."""
    return _nodes(_collect_account_proof_node_rlps(alloc, addresses))


def collect_account_path_only_nodes(
    alloc: Alloc,
    address: StateAddress | bytes,
    relative_to_addresses: Sequence[StateAddress | bytes],
) -> list[Bytes]:
    """Collect nodes unique to one account proof path relative to others."""
    address_nodes = _collect_account_proof_node_rlps(alloc, [address])
    reference_nodes = _collect_account_proof_node_rlps(
        alloc, relative_to_addresses
    )
    return _nodes(address_nodes - reference_nodes)
