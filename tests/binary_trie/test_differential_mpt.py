"""
Differential tests between `ethereum.state_mpt` and `ethereum.state_pbt`.

Both modules implement the same `PreState` protocol (`ethereum.state`),
and on the `binary_tree` fork `ethereum.state_pbt` is meant to be a
pure commitment-scheme swap for `ethereum.state_mpt`: every
provider-level observable (accounts, storage, code,
`account_has_storage`) should agree given identical inputs.

The first group of tests directs specific `BlockDiff`s at both
providers, built from identical pre-states, pinning a real,
already-discovered divergence: MPT's `apply_changes_to_state` never
pops a deleted account's storage trie (`state_mpt.py`, ~156-157) while
PBT's pops it in the same branch that pops the account
(`state_pbt.py`, 211-214). This is visible through EIP-7610, which
gates `CREATE2` on `account_has_storage`, and is an open consensus
question for EIP-8297, not a bug in either provider: each test pins
today's behavior rather than a verdict on which provider is "right".

The second group applies random sequences of 5-8 diffs to both
providers, built from identical random pre-states, and checks
observable equivalence after every diff, except at addresses known to
carry the divergence above, tracked via a `divergent` set.
"""

import random
from typing import Dict, List, Optional, Set, Tuple

import pytest
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import (
    EMPTY_ACCOUNT,
    EMPTY_CODE_HASH,
    Account,
    Address,
    BlockDiff,
)
from ethereum.state_mpt import State as MptState
from ethereum.state_mpt import (
    apply_changes_to_state as mpt_apply_changes_to_state,
)
from ethereum.state_mpt import set_account as mpt_set_account
from ethereum.state_mpt import set_storage as mpt_set_storage
from ethereum.state_mpt import state_root as mpt_state_root
from ethereum.state_mpt import store_code as mpt_store_code
from ethereum.state_pbt import State as PbtState
from ethereum.state_pbt import (
    apply_changes_to_state as pbt_apply_changes_to_state,
)
from ethereum.state_pbt import set_account as pbt_set_account
from ethereum.state_pbt import set_storage as pbt_set_storage
from ethereum.state_pbt import state_root as pbt_state_root
from ethereum.state_pbt import store_code as pbt_store_code

ADDRESS_X = Bytes20(b"\xaa" * 20)
STORAGE_KEY = Bytes32(U256(1).to_be_bytes32())
STORAGE_VALUE = U256(7)
STORAGE_KEY_2 = Bytes32(U256(2).to_be_bytes32())
STORAGE_VALUE_2 = U256(9)

CODELESS_ACCOUNT = Account(
    nonce=Uint(1), balance=U256(1000), code_hash=EMPTY_CODE_HASH
)

NEW_CODE = Bytes(b"\x60\x00\x60\x00\x00")
NEW_CODE_HASH = keccak256(NEW_CODE)

# Fixed 12-address universe and probe-key set for the randomized
# differential test below; small and reused across diffs so deletes
# and recreates of the same address collide often.
RANDOM_ADDRESSES = [Bytes20(bytes([i]) * 20) for i in range(1, 13)]
WRITABLE_KEYS = [Bytes32(bytes([i]) * 32) for i in range(1, 6)]
NEVER_WRITTEN_KEY = Bytes32(b"\xff" * 32)
PROBE_KEYS = WRITABLE_KEYS + [NEVER_WRITTEN_KEY]


def test_account_delete_diverges_on_account_has_storage() -> None:
    """
    Deleting an account leaves its storage trie intact under MPT but
    pops it under PBT.

    Both providers start identical: account `X` with code-less
    storage `{STORAGE_KEY: STORAGE_VALUE}`. A single diff deletes `X`
    and touches no storage. MPT's `apply_changes_to_state`
    (state_mpt.py:156-157) writes the `account_changes` value straight
    into `_main_trie` and never touches `_storage_tries`, so the
    storage trie survives the delete. PBT's `apply_changes_to_state`
    (state_pbt.py:211-214) pops `_storage[address]` in the same branch
    that pops the account.

    This is the EIP-7610-visible divergence: right after this diff, a
    `CREATE2` at `X` would be rejected under MPT (`account_has_storage`
    still `True`) but allowed under PBT (`account_has_storage` now
    `False`). Which behavior EIP-8297 should adopt is an open
    consensus question; this test pins today's behavior of each
    provider, not a verdict on which is right.
    """
    mpt_state = MptState()
    pbt_state = PbtState()
    mpt_set_account(mpt_state, ADDRESS_X, CODELESS_ACCOUNT)
    pbt_set_account(pbt_state, ADDRESS_X, CODELESS_ACCOUNT)
    mpt_set_storage(mpt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)
    pbt_set_storage(pbt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)

    diff = BlockDiff(account_changes={ADDRESS_X: None})
    mpt_apply_changes_to_state(mpt_state, diff)
    pbt_apply_changes_to_state(pbt_state, diff)

    assert mpt_state.get_account_optional(ADDRESS_X) is None
    assert pbt_state.get_account_optional(ADDRESS_X) is None
    assert mpt_state.account_has_storage(ADDRESS_X) is True
    assert pbt_state.account_has_storage(ADDRESS_X) is False


def test_delete_then_recreate_resurrects_storage_only_under_mpt() -> None:
    """
    Recreating a deleted account resurrects its old storage value
    under MPT but starts empty under PBT.

    Continues the sequence pinned by
    `test_account_delete_diverges_on_account_has_storage`: after `X`
    is deleted while holding `{STORAGE_KEY: STORAGE_VALUE}`, a second
    diff recreates `X` as a fresh `EMPTY_ACCOUNT`, writing no storage
    of its own. MPT's orphaned storage trie (state_mpt.py:156-157) is
    untouched by either diff, so the pre-delete value reappears with
    no write ever setting it during the new account's lifetime. PBT's
    `_storage` was popped on delete (state_pbt.py:211-214) and nothing
    refills it, so the slot reads back as never written.
    """
    mpt_state = MptState()
    pbt_state = PbtState()
    mpt_set_account(mpt_state, ADDRESS_X, CODELESS_ACCOUNT)
    pbt_set_account(pbt_state, ADDRESS_X, CODELESS_ACCOUNT)
    mpt_set_storage(mpt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)
    pbt_set_storage(pbt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)

    delete_diff = BlockDiff(account_changes={ADDRESS_X: None})
    mpt_apply_changes_to_state(mpt_state, delete_diff)
    pbt_apply_changes_to_state(pbt_state, delete_diff)

    recreate_diff = BlockDiff(account_changes={ADDRESS_X: EMPTY_ACCOUNT})
    mpt_apply_changes_to_state(mpt_state, recreate_diff)
    pbt_apply_changes_to_state(pbt_state, recreate_diff)

    assert mpt_state.get_storage(ADDRESS_X, STORAGE_KEY) == STORAGE_VALUE
    assert pbt_state.get_storage(ADDRESS_X, STORAGE_KEY) == U256(0)


def test_account_delete_with_same_diff_storage_writes() -> None:
    """
    A single diff that both deletes an account and writes its storage
    leaves an MPT trie holding the old key alongside the new one, and
    a PBT dict that only ever sees the new one.

    `X` starts holding `{STORAGE_KEY: STORAGE_VALUE}`. One diff sets
    `account_changes={X: None}` and, in the same diff,
    `storage_changes={X: {STORAGE_KEY_2: STORAGE_VALUE_2}}`. MPT
    applies `account_changes` and `storage_changes` against separate
    containers (state_mpt.py:156-167): deleting the account never
    touches `_storage_tries`, so the write lands in the very trie that
    still holds `STORAGE_KEY`. PBT's account-delete branch pops the
    whole `_storage[X]` dict (state_pbt.py:211-214) before the
    `storage_changes` loop's `setdefault` (state_pbt.py:218-226)
    recreates `_storage[X]` from empty, so `STORAGE_KEY` is gone but
    `STORAGE_KEY_2` is there. Same divergence family as
    `test_account_delete_diverges_on_account_has_storage`, surfacing
    within one diff instead of across two.

    Both providers still agree the account is gone, that the freshly
    written key reads back, and that `account_has_storage` is `True`
    (an orphan entry with no account — PBT's `embed_flat_state` skips
    exactly this case, state_pbt.py:102-104), and both still compute a
    state root without error.
    """
    mpt_state = MptState()
    pbt_state = PbtState()
    mpt_set_account(mpt_state, ADDRESS_X, CODELESS_ACCOUNT)
    pbt_set_account(pbt_state, ADDRESS_X, CODELESS_ACCOUNT)
    mpt_set_storage(mpt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)
    pbt_set_storage(pbt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)

    diff = BlockDiff(
        account_changes={ADDRESS_X: None},
        storage_changes={ADDRESS_X: {STORAGE_KEY_2: STORAGE_VALUE_2}},
    )
    mpt_apply_changes_to_state(mpt_state, diff)
    pbt_apply_changes_to_state(pbt_state, diff)

    assert mpt_state.get_account_optional(ADDRESS_X) is None
    assert pbt_state.get_account_optional(ADDRESS_X) is None

    # The freshly written key: both providers agree.
    key_2 = STORAGE_KEY_2
    assert mpt_state.get_storage(ADDRESS_X, key_2) == STORAGE_VALUE_2
    assert pbt_state.get_storage(ADDRESS_X, key_2) == STORAGE_VALUE_2

    # The pre-existing key: MPT resurrects it, PBT does not.
    assert mpt_state.get_storage(ADDRESS_X, STORAGE_KEY) == STORAGE_VALUE
    assert pbt_state.get_storage(ADDRESS_X, STORAGE_KEY) == U256(0)

    assert mpt_state.account_has_storage(ADDRESS_X) is True
    assert pbt_state.account_has_storage(ADDRESS_X) is True

    assert len(mpt_state_root(mpt_state)) == 32
    assert len(pbt_state_root(pbt_state)) == 32


def test_all_zero_storage_changes_matches_never_written() -> None:
    """
    Writing only zeros to slots an account never held reads back
    identically to never having written them in both providers, and
    PBT additionally commits to the same root either way. MPT is
    checked only via `get_storage`/`account_has_storage`; its root is
    never computed in this test.
    """
    diff = BlockDiff(
        storage_changes={
            ADDRESS_X: {STORAGE_KEY: U256(0), STORAGE_KEY_2: U256(0)}
        }
    )

    mpt_state = MptState()
    mpt_set_account(mpt_state, ADDRESS_X, CODELESS_ACCOUNT)
    mpt_apply_changes_to_state(mpt_state, diff)

    pbt_state = PbtState()
    pbt_set_account(pbt_state, ADDRESS_X, CODELESS_ACCOUNT)
    never_written_root = pbt_state_root(pbt_state)
    pbt_apply_changes_to_state(pbt_state, diff)

    assert mpt_state.get_storage(ADDRESS_X, STORAGE_KEY) == U256(0)
    assert mpt_state.get_storage(ADDRESS_X, STORAGE_KEY_2) == U256(0)
    assert pbt_state.get_storage(ADDRESS_X, STORAGE_KEY) == U256(0)
    assert pbt_state.get_storage(ADDRESS_X, STORAGE_KEY_2) == U256(0)
    assert mpt_state.account_has_storage(
        ADDRESS_X
    ) == pbt_state.account_has_storage(ADDRESS_X)
    assert pbt_state_root(pbt_state) == never_written_root


def test_code_changes_only_diff() -> None:
    """
    A diff carrying only `code_changes` leaves every observable
    account and storage slot unchanged in both providers, and the new
    bytecode becomes retrievable by hash in both.
    """
    mpt_state = MptState()
    pbt_state = PbtState()
    mpt_set_account(mpt_state, ADDRESS_X, CODELESS_ACCOUNT)
    pbt_set_account(pbt_state, ADDRESS_X, CODELESS_ACCOUNT)
    mpt_set_storage(mpt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)
    pbt_set_storage(pbt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)

    diff = BlockDiff(code_changes={NEW_CODE_HASH: NEW_CODE})
    mpt_apply_changes_to_state(mpt_state, diff)
    pbt_apply_changes_to_state(pbt_state, diff)

    assert mpt_state.get_account_optional(ADDRESS_X) == CODELESS_ACCOUNT
    assert pbt_state.get_account_optional(ADDRESS_X) == CODELESS_ACCOUNT
    assert mpt_state.get_storage(ADDRESS_X, STORAGE_KEY) == STORAGE_VALUE
    assert pbt_state.get_storage(ADDRESS_X, STORAGE_KEY) == STORAGE_VALUE

    assert mpt_state.get_code(NEW_CODE_HASH) == NEW_CODE
    assert pbt_state.get_code(NEW_CODE_HASH) == NEW_CODE

    assert len(mpt_state_root(mpt_state)) == 32
    assert len(pbt_state_root(pbt_state)) == 32


def test_zero_write_to_existing_slot_deletes_in_both() -> None:
    """
    Zeroing an account's only storage slot deletes it identically in
    both providers, agreeing that the account no longer has storage.

    Unlike the delete-account divergence pinned above, no account
    deletion is involved here: MPT's storage_changes loop
    (state_mpt.py:159-167) and PBT's (state_pbt.py:218-226) both
    discard their now-empty container for the address once its one
    key is zeroed, so `account_has_storage` agrees (`False`) in both.
    """
    diff = BlockDiff(storage_changes={ADDRESS_X: {STORAGE_KEY: U256(0)}})

    mpt_state = MptState()
    mpt_set_account(mpt_state, ADDRESS_X, CODELESS_ACCOUNT)
    mpt_set_storage(mpt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)
    mpt_apply_changes_to_state(mpt_state, diff)

    never_had_key_state = PbtState()
    pbt_set_account(never_had_key_state, ADDRESS_X, CODELESS_ACCOUNT)
    never_had_key_root = pbt_state_root(never_had_key_state)

    pbt_state = PbtState()
    pbt_set_account(pbt_state, ADDRESS_X, CODELESS_ACCOUNT)
    pbt_set_storage(pbt_state, ADDRESS_X, STORAGE_KEY, STORAGE_VALUE)
    pbt_apply_changes_to_state(pbt_state, diff)

    assert mpt_state.get_storage(ADDRESS_X, STORAGE_KEY) == U256(0)
    assert pbt_state.get_storage(ADDRESS_X, STORAGE_KEY) == U256(0)
    assert mpt_state.account_has_storage(ADDRESS_X) is False
    assert pbt_state.account_has_storage(ADDRESS_X) is False
    assert pbt_state_root(pbt_state) == never_had_key_root


def _random_account(rng: random.Random, code_hash: Hash32) -> Account:
    """
    Build an `Account` with `code_hash`, a random nonce below `2**64`,
    and a random balance below `2**128`.

    The balance cap is not cosmetic: `encode_basic_data` asserts
    balance fits its sixteen-byte field, so a balance at or past
    `2**128` would crash root computation instead of merely being an
    unrealistic value.
    """
    return Account(
        nonce=Uint(rng.randrange(0, 2**64)),
        balance=U256(rng.randrange(0, 2**128)),
        code_hash=code_hash,
    )


def _random_new_code(rng: random.Random) -> Tuple[Hash32, Bytes]:
    """
    Generate a random 1-39-byte code blob and return it with its
    keccak hash.
    """
    length = rng.randrange(1, 40)
    code = Bytes(bytes(rng.randrange(0, 256) for _ in range(length)))
    return keccak256(code), code


def _random_storage_slots(rng: random.Random) -> Dict[Bytes32, U256]:
    """
    Build a random mix of zero and non-zero writes over a random
    subset of `WRITABLE_KEYS`.
    """
    slots: Dict[Bytes32, U256] = {}
    for key in rng.sample(WRITABLE_KEYS, rng.randint(1, len(WRITABLE_KEYS))):
        slots[key] = (
            U256(0) if rng.random() < 0.3 else U256(rng.randrange(1, 2**64))
        )
    return slots


def _build_random_initial_state(
    rng: random.Random,
) -> Tuple[MptState, PbtState, List[Tuple[Hash32, Bytes]]]:
    """
    Build identical initial states over 5-10 of `RANDOM_ADDRESSES`,
    mixing EOAs and contracts with code and storage.

    Return the two providers, plus the pool of every code hash and
    blob deployed so far, seeded on both providers via `store_code`.
    """
    mpt_state = MptState()
    pbt_state = PbtState()
    code_pool: List[Tuple[Hash32, Bytes]] = []

    initial_count = rng.randint(5, 10)
    for address in rng.sample(RANDOM_ADDRESSES, initial_count):
        code_hash = EMPTY_CODE_HASH
        if rng.random() < 0.5:
            code_hash, code = _random_new_code(rng)
            mpt_store_code(mpt_state, code)
            pbt_store_code(pbt_state, code)
            code_pool.append((code_hash, code))

        account = _random_account(rng, code_hash)
        mpt_set_account(mpt_state, address, account)
        pbt_set_account(pbt_state, address, account)

        if code_hash != EMPTY_CODE_HASH:
            for key, value in _random_storage_slots(rng).items():
                mpt_set_storage(mpt_state, address, key, value)
                pbt_set_storage(pbt_state, address, key, value)

    return mpt_state, pbt_state, code_pool


def _random_block_diff(
    rng: random.Random, code_pool: List[Tuple[Hash32, Bytes]]
) -> BlockDiff:
    """
    Build one random `BlockDiff` mixing account create/modify, account
    delete, storage writes (including zeros), and new code.

    Appends any newly introduced bytecode to `code_pool` in place so
    later diffs may deploy an account that references it.
    """
    code_changes: Dict[Hash32, Bytes] = {}
    if rng.random() < 0.4:
        new_code_hash, new_code = _random_new_code(rng)
        code_changes[new_code_hash] = new_code
        code_pool.append((new_code_hash, new_code))

    account_changes: Dict[Address, Optional[Account]] = {}
    storage_changes: Dict[Address, Dict[Bytes32, U256]] = {}

    touch_count = rng.randint(2, 6)
    for address in rng.sample(RANDOM_ADDRESSES, touch_count):
        if rng.random() < 0.25:
            account_changes[address] = None
        else:
            chosen_hash, _ = (
                rng.choice(code_pool)
                if code_pool
                else (EMPTY_CODE_HASH, Bytes(b""))
            )
            account_changes[address] = _random_account(rng, chosen_hash)

        if rng.random() < 0.7:
            storage_changes[address] = _random_storage_slots(rng)

    return BlockDiff(
        account_changes=account_changes,
        storage_changes=storage_changes,
        code_changes=code_changes,
    )


def _mark_divergent(
    mpt_state: MptState,
    pbt_state: PbtState,
    diff: BlockDiff,
    divergent: Set[Address],
) -> None:
    """
    Add every address `diff` deletes while it still holds storage (in
    either provider) to `divergent`, before `diff` is applied.

    Same divergence family as
    `test_account_delete_diverges_on_account_has_storage`: MPT never
    pops a deleted account's storage trie (state_mpt.py:156-157) while
    PBT does (state_pbt.py:211-214), so once an address is deleted
    while holding storage, the two providers may disagree on that
    address's storage for the rest of the run.
    """
    for address, account in diff.account_changes.items():
        if account is not None:
            continue
        has_storage = mpt_state.account_has_storage(
            address
        ) or pbt_state.account_has_storage(address)
        if has_storage:
            divergent.add(address)


def _assert_equivalent(
    mpt_state: MptState,
    pbt_state: PbtState,
    divergent: Set[Address],
    code_pool: List[Tuple[Hash32, Bytes]],
) -> None:
    """
    Assert both providers agree on every observable over the full
    random address universe, skipping storage-related checks for
    `divergent` addresses, and check every code hash ever stored.

    Each provider's own root is also sanity-checked -- MPT's only by
    length, PBT's by recomputing it and checking determinism -- but
    the two roots are never compared against each other: they commit
    to different schemes, so there is nothing for such a comparison
    to mean.
    """
    for address in RANDOM_ADDRESSES:
        assert mpt_state.get_account_optional(
            address
        ) == pbt_state.get_account_optional(address)

        if address in divergent:
            continue

        assert mpt_state.account_has_storage(
            address
        ) == pbt_state.account_has_storage(address)
        for key in PROBE_KEYS:
            assert mpt_state.get_storage(
                address, key
            ) == pbt_state.get_storage(address, key)

    assert mpt_state.get_code(EMPTY_CODE_HASH) == b""
    assert pbt_state.get_code(EMPTY_CODE_HASH) == b""
    for code_hash, code in code_pool:
        assert mpt_state.get_code(code_hash) == code
        assert pbt_state.get_code(code_hash) == code

    assert len(mpt_state_root(mpt_state)) == 32
    first_pbt_root = pbt_state_root(pbt_state)
    second_pbt_root = pbt_state_root(pbt_state)
    assert first_pbt_root == second_pbt_root


@pytest.mark.parametrize("seed", [8297, 7610, 20260727])
def test_random_diff_sequences_keep_providers_equivalent(seed: int) -> None:
    """
    Random sequences of block diffs keep both providers equivalent at
    every step, except at addresses known to carry the delete-while-
    holding-storage divergence pinned by the directed tests above.
    """
    rng = random.Random(seed)
    mpt_state, pbt_state, code_pool = _build_random_initial_state(rng)

    divergent: Set[Address] = set()

    for _ in range(rng.randint(5, 8)):
        diff = _random_block_diff(rng, code_pool)
        _mark_divergent(mpt_state, pbt_state, diff, divergent)

        mpt_apply_changes_to_state(mpt_state, diff)
        pbt_apply_changes_to_state(pbt_state, diff)

        _assert_equivalent(mpt_state, pbt_state, divergent, code_pool)
