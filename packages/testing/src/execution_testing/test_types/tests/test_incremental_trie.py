"""
Parity tests for the incremental tries behind `Alloc` state roots.

Random tries, block diffs and block sequences are checked against the spec's
`merkle_patricia_trie` and `state_mpt` implementations, along with the
`Alloc` paths that use the incremental trie: `state_root`,
`compute_state_root`, `apply_diff` and `structural_copy`.
"""

import random
from typing import Dict, List, Optional, Set, Tuple

import ethereum.state as spec_state
import ethereum.state_mpt as spec_state_mpt
import pytest
from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import (
    Trie,
    bytes_to_nibble_list,
    root,
    trie_set,
)
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint

from execution_testing.base_types import Address, StateCommitment
from execution_testing.test_types import Account, Alloc
from execution_testing.test_types.account_types import _Phase
from execution_testing.test_types.incremental_trie import (
    IncrementalStateTrie,
    IncrementalTrie,
    _secured_key,
)

SpecAccount = spec_state.Account
Slots = Dict[Bytes32, U256]

CODES = [b"", bytes.fromhex("60016002"), bytes.fromhex("6005600555")]


def _random_slots(rng: random.Random, count: int) -> Slots:
    """Return `count` random storage slots from a small key space."""
    return {
        Bytes32(rng.randrange(64).to_bytes(32, "big")): U256(
            rng.choice([0, 1, rng.randrange(2**256)])
        )
        for _ in range(count)
    }


def _random_account(rng: random.Random) -> SpecAccount:
    """Return a random spec account, sometimes empty."""
    code = rng.choice(CODES)
    return SpecAccount(
        nonce=Uint(rng.choice([0, 1, rng.randrange(2**64)])),
        balance=U256(rng.choice([0, rng.randrange(2**256)])),
        code_hash=keccak256(code) if code else spec_state.EMPTY_CODE_HASH,
    )


def _spec_storage_root(slots: Slots) -> Bytes:
    """Return the storage root the spec computes for `slots`."""
    trie: Trie[Bytes32, U256] = Trie(secured=True, default=U256(0))
    for key, value in slots.items():
        trie_set(trie, key, value)
    return root(trie)


def _incremental_storage_trie(slots: Slots) -> IncrementalTrie:
    """Build an incremental storage trie for `slots`."""
    return IncrementalTrie.build(
        {
            _secured_key(key): rlp.encode(value)
            for key, value in slots.items()
            if value != 0
        }
    )


@pytest.mark.parametrize("size", [0, 1, 2, 3, 17, 300])
def test_trie_root_matches_spec(size: int) -> None:
    """A freshly built trie has the spec's root, including tiny tries."""
    rng = random.Random(size)
    slots = _random_slots(rng, size)
    assert _incremental_storage_trie(slots).root() == _spec_storage_root(slots)


@pytest.mark.parametrize("seed", range(5))
def test_trie_with_changes_matches_spec(seed: int) -> None:
    """Inserts, updates and deletions keep the root equal to a rebuild."""
    rng = random.Random(seed)
    slots = _random_slots(rng, 40)
    trie = _incremental_storage_trie(slots)
    trie.root()
    for _ in range(20):
        before = trie.root()
        changes = _random_slots(rng, rng.randrange(1, 8))
        if slots and rng.random() < 0.5:
            # Delete every remaining slot now and then.
            changes.update({key: U256(0) for key in slots})
        new_trie = trie.with_changes(
            {
                _secured_key(key): rlp.encode(value) if value != 0 else None
                for key, value in changes.items()
            }
        )
        slots.update(changes)
        slots = {key: value for key, value in slots.items() if value != 0}
        assert new_trie.root() == _spec_storage_root(slots)
        assert len(new_trie) == len(slots)
        # The original trie is left untouched.
        assert trie.root() == before
        trie = new_trie


def _random_state(
    rng: random.Random, size: int
) -> Dict[Bytes20, Tuple[SpecAccount, Slots]]:
    """Return random accounts, some with storage."""
    return {
        Bytes20(rng.randbytes(20)): (
            _random_account(rng),
            _random_slots(rng, rng.choice([0, 0, 3, 12])),
        )
        for _ in range(size)
    }


def _random_diff(
    rng: random.Random, addresses: List[Bytes20]
) -> spec_state.BlockDiff:
    """
    Return a block diff the EVM could produce for `addresses`: deleted
    accounts have their storage cleared and storage only changes for
    accounts that exist after the block.
    """
    account_changes: Dict[Bytes20, Optional[SpecAccount]] = {}
    storage_changes: Dict[Bytes20, Slots] = {}
    storage_clears: Set[Bytes20] = set()
    new_addresses = [Bytes20(rng.randbytes(20)) for _ in range(3)]
    for address in rng.sample(addresses, min(len(addresses), 8)):
        action = rng.choice(["update", "delete", "recreate", "storage"])
        if action == "delete":
            account_changes[address] = None
            storage_clears.add(address)
            continue
        if action == "recreate":
            storage_clears.add(address)
        if action != "storage":
            account_changes[address] = _random_account(rng)
        storage_changes[address] = _random_slots(rng, rng.randrange(1, 6))
    for address in new_addresses:
        account_changes[address] = _random_account(rng)
        storage_changes[address] = _random_slots(rng, rng.randrange(0, 4))
    return spec_state.BlockDiff(
        account_changes=account_changes,
        storage_changes=storage_changes,
        storage_clears=storage_clears,
    )


def _spec_state(
    accounts: Dict[Bytes20, Tuple[SpecAccount, Slots]],
) -> spec_state_mpt.State:
    """Build a spec `State` holding `accounts`."""
    state = spec_state_mpt.State()
    for address, (account, slots) in accounts.items():
        spec_state_mpt.set_account(state, address, account)
        for key, value in slots.items():
            spec_state_mpt.set_storage(state, address, key, value)
    return state


@pytest.mark.parametrize("seed", range(5))
def test_state_trie_matches_spec_across_blocks(seed: int) -> None:
    """
    Each block's root, and the root of the state it leaves behind, match
    the spec over a sequence of random blocks.
    """
    rng = random.Random(seed)
    accounts = _random_state(rng, 60)
    state = _spec_state(accounts)
    trie = IncrementalStateTrie.build(
        (
            bytes(address),
            account,
            {bytes(key): int(value) for key, value in slots.items()},
        )
        for address, (account, slots) in accounts.items()
    )
    assert trie.root() == spec_state_mpt.state_root(state)
    for _ in range(10):
        live = list(trie._accounts)
        diff = _random_diff(rng, [Bytes20(address) for address in live])
        next_trie = trie.with_diff(diff)
        assert next_trie.root() == state.compute_state_root(diff)
        spec_state_mpt.apply_changes_to_state(state, diff)
        trie = next_trie
    assert trie.root() == spec_state_mpt.state_root(state)


def _alloc(rng: random.Random, size: int) -> Alloc:
    """Return a random `Alloc` under construction."""
    alloc = Alloc.model_validate(
        {
            Bytes20(rng.randbytes(20)): {
                "nonce": rng.randrange(3),
                "balance": rng.randrange(2**64),
                "code": "0x" + rng.choice(CODES).hex(),
                "storage": {
                    rng.randrange(64): rng.randrange(1, 2**64)
                    for _ in range(rng.choice([0, 2, 5]))
                },
            }
            for _ in range(size)
        }
    )
    alloc.migrate_state_commitment(StateCommitment.MPT)
    return alloc


def _spec_root_of(alloc: Alloc) -> Bytes:
    """Return the spec's state root for the accounts in `alloc`."""
    return alloc._materialize_state().compute_state_root(
        spec_state.BlockDiff()
    )


def test_alloc_state_root_follows_mutations() -> None:
    """
    A cached trie is rebuilt after `root` changes, whether through
    `__setitem__`, `__delitem__` or a direct write.
    """
    rng = random.Random(0)
    alloc = _alloc(rng, 20)
    assert alloc.state_root() == _spec_root_of(alloc)
    first, second = list(alloc.root)[:2]
    alloc[first] = Account(nonce=7, balance=1)
    assert alloc.state_root() == _spec_root_of(alloc)
    del alloc[second]
    assert alloc.state_root() == _spec_root_of(alloc)
    alloc.root[Address(rng.randbytes(20))] = Account(balance=5, storage={1: 2})
    assert alloc.state_root() == _spec_root_of(alloc)


def _diff_for(rng: random.Random, alloc: Alloc) -> spec_state.BlockDiff:
    """Return a random diff for `alloc`, with code for new code hashes."""
    diff = _random_diff(rng, [Bytes20(address) for address in alloc.root])
    diff.code_changes = {keccak256(code): Bytes(code) for code in CODES[1:]}
    return diff


@pytest.mark.parametrize("seed", range(3))
def test_structural_copies_across_blocks(seed: int) -> None:
    """
    Chained structural copies compute the spec's roots and leave every
    earlier allocation unchanged.
    """
    rng = random.Random(seed)
    genesis = _alloc(rng, 40)
    genesis_root = genesis.state_root()
    genesis_accounts = dict(genesis.root)
    alloc = genesis
    for _ in range(5):
        copied = alloc.structural_copy()
        # The copy shares the trie its source built or advanced.
        assert copied._state_trie is alloc._state_trie is not None
        diff = _diff_for(rng, copied)
        expected = copied._materialize_state().compute_state_root(diff)
        assert copied.compute_state_root(diff) == expected
        assert copied._phase is _Phase.LIVE
        copied.apply_diff(diff)
        advanced = copied._state_trie
        assert copied.state_root() == expected
        assert _spec_root_of(copied) == expected
        # The trie advanced by `apply_diff` is used, not rebuilt.
        assert copied._state_trie is advanced
        alloc = copied
    assert genesis._phase is _Phase.CONSTRUCTION
    assert genesis.root == genesis_accounts
    assert genesis.state_root() == genesis_root == _spec_root_of(genesis)


def test_structural_copy_has_its_own_private_attributes() -> None:
    """Changing a copy's private attributes leaves the original alone."""
    alloc = _alloc(random.Random(0), 3)
    copied = alloc.structural_copy()
    copied.migrate_state_commitment(None)
    copied._code_store.clear()
    assert alloc.state_commitment() is StateCommitment.MPT
    assert alloc._code_store


def test_calculate_diff_skips_shared_accounts() -> None:
    """Only accounts replaced by a block appear in the diff."""
    rng = random.Random(0)
    genesis = _alloc(rng, 10)
    copied = genesis.structural_copy()
    address = next(iter(copied.root))
    diff = spec_state.BlockDiff(
        account_changes={
            Bytes20(address): SpecAccount(
                nonce=Uint(99),
                balance=U256(0),
                code_hash=spec_state.EMPTY_CODE_HASH,
            )
        }
    )
    copied.compute_state_root(diff)
    copied.apply_diff(diff)
    assert list(copied.calculate_diff(genesis).root) == [address]


def test_apply_diff_ignores_a_root_computed_for_another_diff() -> None:
    """`apply_diff` only reuses the trie of the diff it is given."""
    rng = random.Random(0)
    copied = _alloc(rng, 20).structural_copy()
    copied.compute_state_root(_diff_for(rng, copied))
    copied.apply_diff(_diff_for(rng, copied))
    assert copied.state_root() == _spec_root_of(copied)


def test_deleted_account_storage_is_dropped() -> None:
    """
    An account deleted without a storage clear and created again in a later
    block starts with empty storage, as with `Alloc.apply_diff`.
    """
    alloc = _alloc(random.Random(0), 5)
    address = Address(Bytes20(b"\x01" * 20))
    alloc[address] = Account(balance=1, storage={1: 2})
    copied = alloc.structural_copy()
    for account in (None, _random_account(random.Random(1))):
        diff = spec_state.BlockDiff(
            account_changes={Bytes20(address): account}
        )
        copied.compute_state_root(diff)
        copied.apply_diff(diff)
        assert copied.state_root() == _spec_root_of(copied)
    recreated = copied.root[address]
    assert recreated is not None and recreated.storage.root == {}


def _set_based_diff(post: Alloc, base: Alloc) -> Dict[Address, object]:
    """Return the diff as computed over the union of both address sets."""
    diff: Dict[Address, object] = {}
    for address in set(post.root) | set(base.root):
        before, after = base.root.get(address), post.root.get(address)
        if before is not None and after is None:
            diff[address] = None
        elif before != after:
            diff[address] = after
    return diff


@pytest.mark.parametrize("seed", range(5))
def test_calculate_diff_matches_set_based_diff(seed: int) -> None:
    """Shared, replaced, created, deleted and absent accounts all match."""
    rng = random.Random(seed)
    base = _alloc(rng, 30)
    base.root[Address(rng.randbytes(20))] = None
    post = base.structural_copy()
    addresses = list(post.root)
    for address in rng.sample(addresses, 5):
        del post.root[address]
    for address in rng.sample(addresses, 5):
        post.root[address] = Account(balance=rng.randrange(3))
    for _ in range(3):
        post.root[Address(rng.randbytes(20))] = rng.choice(
            [None, Account(nonce=1)]
        )
    assert post.calculate_diff(base).root == _set_based_diff(post, base)


def test_apply_diff_drops_zero_storage_from_every_account() -> None:
    """
    Zero storage values from the pre-state are dropped from untouched
    accounts too, and the original keeps them.
    """
    alloc = _alloc(random.Random(0), 5)
    holder = Address(Bytes20(b"\x02" * 20))
    alloc[holder] = Account(balance=1, storage={1: 0, 2: 5})
    copied = alloc.structural_copy()
    other = next(address for address in copied.root if address != holder)
    diff = spec_state.BlockDiff(
        account_changes={
            Bytes20(other): SpecAccount(
                nonce=Uint(1),
                balance=U256(1),
                code_hash=spec_state.EMPTY_CODE_HASH,
            )
        }
    )
    copied.compute_state_root(diff)
    copied.apply_diff(diff)
    after, before = copied.root[holder], alloc.root[holder]
    assert after is not None and after.storage.root == {2: 5}
    assert before is not None and before.storage.root == {1: 0, 2: 5}
    assert all(
        int(value) != 0
        for account in copied.root.values()
        if account is not None
        for value in account.storage.root.values()
    )
    assert copied.state_root() == _spec_root_of(copied)


@pytest.mark.parametrize("seed", range(20))
def test_unsecured_trie_matches_spec(seed: int) -> None:
    """
    Short, variable-length keys exercise what secured tries almost never
    reach: embedded nodes, an embedded root and branch values.
    """
    rng = random.Random(seed)
    spec: Trie[Bytes, Bytes] = Trie(secured=False, default=Bytes(b""))
    trie = IncrementalTrie.build({})
    for _ in range(30):
        key = Bytes(rng.randbytes(rng.randrange(4)))
        value = Bytes(rng.randbytes(rng.choice([0, 1, 4, 40])))
        trie_set(spec, key, value)
        trie = trie.with_changes(
            {bytes(bytes_to_nibble_list(key)): bytes(value) or None}
        )
        assert trie.root() == root(spec)


def test_apply_diff_ignores_a_pending_trie_from_before_a_rebuild() -> None:
    """
    A trie computed for a diff is not reused once `root` changes and the
    caches are rebuilt, even when the same diff is applied.
    """
    rng = random.Random(0)
    copied = _alloc(rng, 10).structural_copy()
    diff = _diff_for(rng, copied)
    copied.compute_state_root(diff)
    copied.root[Address(rng.randbytes(20))] = Account(balance=3)
    copied.state_root()
    copied.apply_diff(diff)
    assert copied.state_root() == _spec_root_of(copied)
