"""
Tests for `ethereum.state_pbt`.

The first group covers `embed_flat_state`: each kind of state
(account fields, code chunks, storage slots) must land in the tree
as exactly the expected leaves, with expected keys and values built
by hand from the derivation functions.

The second group covers the provider: `compute_state_root` applies a
block diff (deletions, zero-writes, freshly deployed code) and embeds
the result, checked either against a post-state built directly in the
MPT-backed container or against a known invariant (the empty root, a
zero-write matching a never-written slot, and so on).

Later groups pin exact key sets, the BASIC_DATA leaf's byte layout,
and further provider semantics: `storage_clears` ordering,
account-delete/storage-orphan interactions, the asymmetry between
`set_account` and the diff path, pre-state immutability, sequential
diffs, and the storage sub-index boundaries. Key sets are rebuilt
from raw `blake3` and literal zone/sub-index bytes, never by calling
the derivation functions under test, so a wrong key that still
produces the right leaf count -- a swapped zone byte, an off-by-one
sub-index -- is still caught; a leaf count alone would miss it.

EIP-8297's "Zero values and deletion" section now requires what this
module's `State` does: a write of 32 zero bytes resolves to a
deletion, and deleting an account removes its header leaves and its
storage leaves. The roots asserted below are conformance, not merely
pinned current behavior.

Two things the EIP settles that are easy to misread as bugs. Zero
means absent over the whole value space, so a chunk of 31 zero bytes
and the basic data of an account with zero nonce, zero balance and
no code are all left out of the tree; presence of a leaf is not what
makes an account or a code chunk exist.
`test_trie.py::test_zero_value_is_not_absence` still holds and is
not in tension with that: the raw `BinaryTrie` does keep a
zero-valued leaf, and collapsing zero onto absence is the state
model's job, done in `embedding.state_write`.

Where this provider parts company with `state_mpt` is storage owned
by no account. The EIP fixes `account_has_storage` to whether a slot
leaf of the address exists, so a write to an address the same diff
deletes is dropped here; `state_mpt` keeps it. See
`test_differential_mpt.py::test_account_delete_diverges_on_account_has_storage`
for the EIP-7610-visible consequence, which the EIP resolves for the
tree and leaves open for the Merkle Patricia Trie.
"""  # noqa: E501

import random
from typing import Dict, Optional

import pytest
from blake3 import blake3
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U32, U64, U256, Uint

from ethereum.binary_trie.embedding import (
    HEADER_STORAGE_OFFSET,
    HEADER_STORAGE_SLOTS,
    address20_to_address32,
    chunkify_code,
    encode_basic_data,
    get_tree_key_for_basic_data,
    get_tree_key_for_code_chunk,
    get_tree_key_for_code_hash,
    get_tree_key_for_storage_slot,
)
from ethereum.binary_trie.trie import (
    EMPTY_TRIE_ROOT,
    BinaryTrie,
    root,
    trie_set,
)
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import (
    BalanceOverflowError,
    InvalidBlock,
    UnknownCodeHashError,
)
from ethereum.state import EMPTY_CODE_HASH, Account, BlockDiff
from ethereum.state_mpt import State as MptState
from ethereum.state_mpt import set_account as mpt_set_account
from ethereum.state_mpt import set_storage as mpt_set_storage
from ethereum.state_mpt import store_code as mpt_store_code
from ethereum.state_pbt import (
    State,
    apply_changes_to_state,
    apply_diff_to_trie,
    embed_flat_state,
    set_account,
    set_storage,
    state_root,
    store_code,
)

ADDRESS_A = Bytes20(b"\xaa" * 20)
ADDRESS_B = Bytes20(b"\xbb" * 20)
ADDRESS_C = Bytes20(b"\xcc" * 20)

# EIP-7702 delegation designators: the main protocol-reachable code
# change on an existing account, and always a single content-addressed
# chunk, shared by every authority delegating to the same target.
DELEGATION_A = Bytes(b"\xef\x01\x00" + b"\x11" * 20)
DELEGATION_B = Bytes(b"\xef\x01\x00" + b"\x22" * 20)


def embed_state(state: MptState) -> BinaryTrie:
    """
    Embed every account, code chunk, and storage slot of the
    MPT-backed `state` into a fresh `BinaryTrie`.
    """
    accounts = {
        address: account
        for address, account in state._main_trie._data.items()
        if account is not None
    }
    storages = {
        address: dict(trie._data)
        for address, trie in state._storage_tries.items()
    }
    return embed_flat_state(accounts, storages, state.get_code)


def test_empty_state_embeds_to_empty_root() -> None:
    """
    A state with no accounts embeds to the empty tree.
    """
    assert root(embed_state(MptState())) == EMPTY_TRIE_ROOT


def test_eoa_embeds_basic_data_and_code_hash_leaves() -> None:
    """
    An EOA produces exactly its two header leaves: packed basic data
    and the empty-code hash. No chunk or storage leaves appear.
    """
    state = MptState()
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(5), balance=U256(1000), code_hash=EMPTY_CODE_HASH),
    )

    embedded = embed_state(state)

    address32 = address20_to_address32(ADDRESS_A)
    expected = BinaryTrie()
    trie_set(
        expected,
        get_tree_key_for_basic_data(address32),
        encode_basic_data(code_size=U32(0), nonce=U64(5), balance=U256(1000)),
    )
    trie_set(
        expected,
        get_tree_key_for_code_hash(address32),
        Bytes32(EMPTY_CODE_HASH),
    )
    assert len(embedded._data) == 2
    assert root(embedded) == root(expected)


def test_contract_embeds_chunks_and_storage_slots() -> None:
    """
    A contract account produces its header leaves, one leaf per code
    chunk, and one leaf per non-zero storage slot, header slot and
    overflow slot alike.
    """
    code = Bytes(b"\x01" * 40)  # two chunks, in the code zone
    state = MptState()
    code_hash = mpt_store_code(state, code)
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )
    mpt_set_storage(
        state, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7)
    )
    mpt_set_storage(
        state, ADDRESS_A, Bytes32(U256(100).to_be_bytes32()), U256(9)
    )

    embedded = embed_state(state)

    address32 = address20_to_address32(ADDRESS_A)
    expected = BinaryTrie()
    trie_set(
        expected,
        get_tree_key_for_basic_data(address32),
        encode_basic_data(code_size=U32(40), nonce=U64(1), balance=U256(0)),
    )
    trie_set(
        expected,
        get_tree_key_for_code_hash(address32),
        Bytes32(code_hash),
    )
    for chunk_id, chunk in enumerate(chunkify_code(code)):
        trie_set(
            expected,
            get_tree_key_for_code_chunk(code_hash, Uint(chunk_id)),
            chunk,
        )
    trie_set(
        expected,
        get_tree_key_for_storage_slot(address32, U256(1)),
        U256(7).to_be_bytes32(),
    )
    trie_set(
        expected,
        get_tree_key_for_storage_slot(address32, U256(100)),
        U256(9).to_be_bytes32(),
    )
    assert len(embedded._data) == 6
    assert root(embedded) == root(expected)


def test_identical_bytecode_shares_chunk_leaves() -> None:
    """
    Two contracts with the same bytecode share every chunk leaf: the
    embedded tree holds one content-addressed copy of each chunk,
    plus per-account header leaves.
    """
    code = Bytes(b"\x01" * 4000)  # 130 chunks
    state = MptState()
    code_hash = mpt_store_code(state, code)
    for address in (ADDRESS_A, ADDRESS_B):
        mpt_set_account(
            state,
            address,
            Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
        )

    embedded = embed_state(state)

    assert len(chunkify_code(code)) == 130
    # Per account: basic data and code hash. The 130 chunks are
    # content-addressed and stored once, shared by both accounts.
    assert len(embedded._data) == 2 * 2 + 130


def test_empty_provider_commits_to_empty_root() -> None:
    """
    A provider with no accounts commits to the empty tree.
    """
    assert state_root(State()) == EMPTY_TRIE_ROOT


def test_empty_diff_root_matches_direct_embedding() -> None:
    """
    With no changes, the root is the embedding of the pre-state.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(100), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(state, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7))

    mpt_state = MptState()
    mpt_set_account(
        mpt_state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(100), code_hash=EMPTY_CODE_HASH),
    )
    mpt_set_storage(
        mpt_state, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7)
    )

    assert state_root(state) == root(embed_state(mpt_state))


def test_diff_root_matches_directly_built_post_state() -> None:
    """
    A diff deploying code, touching storage, zeroing a slot, and
    deleting an account produces the same root as building the
    post-state directly in the MPT container and embedding it.

    The zeroed slot is deleted and the deleted account's storage
    goes with it, both as EIP-8297 requires, so the two ways of
    reaching the post state agree.
    """
    code = Bytes(b"\x01" * 40)
    code_hash = keccak256(code)

    pre_state = State()
    set_account(
        pre_state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(100), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(
        pre_state, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7)
    )
    set_account(
        pre_state,
        ADDRESS_B,
        Account(nonce=Uint(9), balance=U256(5), code_hash=EMPTY_CODE_HASH),
    )

    # The block: account A becomes a contract (deployed code, new
    # storage written, old slot zeroed) and account B is deleted.
    post_account_a = Account(
        nonce=Uint(2), balance=U256(50), code_hash=code_hash
    )
    computed = pre_state.compute_state_root(
        BlockDiff(
            account_changes={ADDRESS_A: post_account_a, ADDRESS_B: None},
            storage_changes={
                ADDRESS_A: {
                    Bytes32(U256(1).to_be_bytes32()): U256(0),
                    Bytes32(U256(2).to_be_bytes32()): U256(11),
                }
            },
            code_changes={code_hash: code},
        )
    )

    post_state = MptState()
    assert mpt_store_code(post_state, code) == code_hash
    mpt_set_account(post_state, ADDRESS_A, post_account_a)
    mpt_set_storage(
        post_state, ADDRESS_A, Bytes32(U256(2).to_be_bytes32()), U256(11)
    )

    assert computed == root(embed_state(post_state))


def test_deleting_the_only_account_empties_the_tree() -> None:
    """
    Deleting the last account, bare as deletable accounts must be,
    leaves the empty tree commitment.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH),
    )

    computed = state.compute_state_root(
        BlockDiff(account_changes={ADDRESS_A: None})
    )

    assert computed == EMPTY_TRIE_ROOT


def test_zero_write_matches_never_written() -> None:
    """
    Writing a slot to zero commits identically to never having
    written it: zero resolves to a deletion, as EIP-8297 requires
    and as the MPT state semantics already had it.
    """

    def fresh() -> State:
        state = State()
        set_account(
            state,
            ADDRESS_A,
            Account(nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH),
        )
        return state

    written_then_zeroed = fresh()
    set_storage(written_then_zeroed, ADDRESS_A, Bytes32(b"\x05" * 32), U256(9))
    set_storage(written_then_zeroed, ADDRESS_A, Bytes32(b"\x05" * 32), U256(0))

    assert state_root(written_then_zeroed) == state_root(fresh())

    # And via a block diff rather than direct writes.
    with_slot = fresh()
    set_storage(with_slot, ADDRESS_A, Bytes32(b"\x05" * 32), U256(9))
    zeroed_by_diff = with_slot.compute_state_root(
        BlockDiff(
            storage_changes={ADDRESS_A: {Bytes32(b"\x05" * 32): U256(0)}}
        )
    )
    assert zeroed_by_diff == state_root(fresh())


def _clone(state: State) -> State:
    """Deep-copy a provider state's three mappings."""
    return State(
        _accounts=dict(state._accounts),
        _storage={
            address: dict(slots) for address, slots in state._storage.items()
        },
        _code_store=dict(state._code_store),
    )


def _flat_oracle_root(pre: State, diff: BlockDiff) -> bytes:
    """
    Compute the post-root the pre-incremental way: apply the diff to
    a copy of the flat state and re-embed everything from scratch.
    """
    post = _clone(pre)
    apply_changes_to_state(post, diff)
    return bytes(state_root(post))


def test_storage_clear_deletes_every_slot_leaf() -> None:
    """
    Clearing an account's storage removes its header-stem slot
    leaves and its overflow-subtree slot leaves, leaving the root of
    a state where the storage was never written.
    """

    def account_only() -> State:
        state = State()
        set_account(
            state,
            ADDRESS_A,
            Account(nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH),
        )
        return state

    pre = account_only()
    set_storage(pre, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7))
    set_storage(pre, ADDRESS_A, Bytes32(U256(100).to_be_bytes32()), U256(9))

    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    apply_diff_to_trie(trie, pre, BlockDiff(storage_clears={ADDRESS_A}))

    assert root(trie) == state_root(account_only())


def test_delegation_change_deletes_stale_chunks() -> None:
    """
    Re-delegating and un-delegating change the account's code hash,
    so the old designator's content-addressed chunk is dropped once
    no account in the resulting state holds it -- here there is only
    the one authority -- and the new designator's chunk, if any, is
    written. Both leave the root of a state that only ever held the
    final code.
    """
    for new_code in (DELEGATION_B, Bytes(b"")):
        pre = State()
        old_hash = store_code(pre, DELEGATION_A)
        set_account(
            pre,
            ADDRESS_A,
            Account(nonce=Uint(1), balance=U256(1), code_hash=old_hash),
        )

        new_hash = keccak256(new_code)
        post_account = Account(
            nonce=Uint(2), balance=U256(1), code_hash=new_hash
        )
        diff = BlockDiff(
            account_changes={ADDRESS_A: post_account},
            code_changes={new_hash: new_code} if new_code else {},
        )

        fresh = State()
        assert store_code(fresh, new_code) == new_hash
        set_account(fresh, ADDRESS_A, post_account)

        assert pre.compute_state_root(diff) == state_root(fresh), (
            f"new code {new_code.hex()}"
        )


def test_deleting_a_sole_holder_removes_its_short_code() -> None:
    """
    Short code is content-addressed like any other: deleting the only
    holder drops its chunk leaves, resolved from the bytecode rather
    than from any per-account key range, and the state commits to the
    empty root.
    """
    pre = State()
    code_hash = store_code(pre, Bytes(b"\x01" * 40))
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )

    diff = BlockDiff(account_changes={ADDRESS_A: None})

    assert bytes(pre.compute_state_root(diff)) == _flat_oracle_root(pre, diff)
    assert pre.compute_state_root(diff) == EMPTY_TRIE_ROOT


def test_deleting_the_last_holder_removes_its_code() -> None:
    """
    Content-addressed chunks may go once no account in the resulting
    state has their code hash. With the only holder deleted, nothing
    references the code and its shared leaves go with it.
    """
    pre = State()
    code_hash = store_code(pre, Bytes(b"\x01" * 4000))  # 130 chunks
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )

    diff = BlockDiff(account_changes={ADDRESS_A: None})

    assert bytes(pre.compute_state_root(diff)) == _flat_oracle_root(pre, diff)
    assert pre.compute_state_root(diff) == EMPTY_TRIE_ROOT


def test_deleting_one_holder_keeps_shared_code() -> None:
    """
    A second account still running the bytecode keeps its chunks
    alive: they are removed only if no account in the resulting state
    has the code hash.
    """
    code = Bytes(b"\x01" * 4000)  # 130 chunks
    pre = State()
    code_hash = store_code(pre, code)
    for address in (ADDRESS_A, ADDRESS_B):
        set_account(
            pre,
            address,
            Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
        )

    diff = BlockDiff(account_changes={ADDRESS_A: None})
    post = pre.compute_state_root(diff)

    assert bytes(post) == _flat_oracle_root(pre, diff)

    survivor = State()
    assert store_code(survivor, code) == code_hash
    set_account(
        survivor,
        ADDRESS_B,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )
    assert post == state_root(survivor)


def test_deleting_an_account_removes_its_storage_leaves() -> None:
    """
    An account can hold storage without holding code: genesis
    allocates such accounts directly, and no bytecode is needed to
    keep slots that were allocated rather than written. Touching one
    empties it under EIP-161, and the deletion emits no storage diff
    of its own, so the deletion must drop the slot leaves the account
    still owns in the pre-state tree.
    """
    pre = State()
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(0), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    # A header-stem slot and an overflow-subtree slot.
    set_storage(pre, ADDRESS_A, Bytes32(U256(3).to_be_bytes32()), U256(4))
    set_storage(pre, ADDRESS_A, Bytes32(U256(300).to_be_bytes32()), U256(5))
    set_account(
        pre,
        ADDRESS_B,
        Account(nonce=Uint(1), balance=U256(9), code_hash=EMPTY_CODE_HASH),
    )

    diff = BlockDiff(account_changes={ADDRESS_A: None})

    assert bytes(pre.compute_state_root(diff)) == _flat_oracle_root(pre, diff)


def test_deleting_a_cleared_account_removes_its_storage_leaves() -> None:
    """
    A pre-EIP-6780 `SELFDESTRUCT` wipes storage and removes the
    account in one diff. The wipe is recorded against the tree, not
    against the pre-state, so the deletion cannot tell that the
    storage is already gone; removing the leaves twice must still
    land on the post-state root.
    """
    pre = State()
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(pre, ADDRESS_A, Bytes32(U256(3).to_be_bytes32()), U256(4))

    diff = BlockDiff(
        storage_clears={ADDRESS_A}, account_changes={ADDRESS_A: None}
    )

    assert bytes(pre.compute_state_root(diff)) == _flat_oracle_root(pre, diff)


def test_storage_written_to_a_deleted_account_is_not_embedded() -> None:
    """
    Storage belongs to an account: [`embed_flat_state`] ignores slots
    whose address has no account, so a write landing on an address
    the same block deletes must not reach the tree either.

    [`embed_flat_state`]: ref:ethereum.state_pbt.embed_flat_state
    """
    pre = State()
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH),
    )

    diff = BlockDiff(
        account_changes={ADDRESS_A: None},
        storage_changes={
            ADDRESS_A: {Bytes32(U256(3).to_be_bytes32()): U256(7)}
        },
    )

    assert bytes(pre.compute_state_root(diff)) == _flat_oracle_root(pre, diff)


def test_code_change_swaps_the_chunk_leaves() -> None:
    """
    Replacing an account's code is handled like a deletion of the
    old bytecode: its chunks are dropped once no account in the
    resulting state holds their hash -- here the changing account
    was the only holder -- and the new code's chunks are embedded.
    The result commits to the root of a state that only ever held
    the new code.
    """
    old_code = Bytes(b"\x01" * 4000)  # 130 chunks
    new_code = Bytes(b"\x02" * 40)

    pre = State()
    old_hash = store_code(pre, old_code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=old_hash),
    )

    new_hash = keccak256(new_code)
    diff = BlockDiff(
        account_changes={
            ADDRESS_A: Account(
                nonce=Uint(1), balance=U256(1), code_hash=new_hash
            )
        },
        code_changes={new_hash: new_code},
    )

    fresh = State()
    assert store_code(fresh, new_code) == new_hash
    set_account(
        fresh,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=new_hash),
    )

    assert pre.compute_state_root(diff) == state_root(fresh)


def test_random_diffs_match_flat_application_and_rebuild() -> None:
    """
    Randomized protocol-shaped diffs, covering deletions of accounts
    with and without allocated storage, delegation churn, contract
    storage writes and zeroes, and fresh deployments, produce the
    same root through incremental trie application as through
    applying the diff to the flat state and re-embedding everything.
    """
    rng = random.Random(8297)
    long_code = Bytes(bytes(range(256)) * 16)  # 133 chunks, varied bytes

    for trial in range(10):
        pre = State()
        long_hash = store_code(pre, long_code)
        delegation_hashes = [
            store_code(pre, code) for code in (DELEGATION_A, DELEGATION_B)
        ]

        # EOAs: empty code or a pre-existing delegation. Some hold
        # allocated storage, which no bytecode is needed to keep and
        # which a deletion must take with it.
        eoas = [Bytes20(rng.randbytes(20)) for _ in range(6)]
        for address in eoas:
            set_account(
                pre,
                address,
                Account(
                    nonce=Uint(rng.randrange(1, 5)),
                    balance=U256(rng.randrange(1, 10**9)),
                    code_hash=rng.choice(
                        [EMPTY_CODE_HASH, EMPTY_CODE_HASH] + delegation_hashes
                    ),
                ),
            )
            if rng.random() < 0.4:
                for _ in range(rng.randrange(1, 3)):
                    slot = rng.choice(
                        [rng.randrange(0, 64), rng.randrange(64, 10**9)]
                    )
                    set_storage(
                        pre,
                        address,
                        Bytes32(U256(slot).to_be_bytes32()),
                        U256(rng.randrange(1, 100)),
                    )

        # Contracts: immutable code, mutable storage.
        contracts = [Bytes20(rng.randbytes(20)) for _ in range(3)]
        for address in contracts:
            set_account(
                pre,
                address,
                Account(
                    nonce=Uint(1),
                    balance=U256(rng.randrange(1, 10**9)),
                    code_hash=long_hash,
                ),
            )
            for _ in range(rng.randrange(1, 4)):
                # Header slots (0-63) and overflow slots alike.
                slot = rng.choice(
                    [rng.randrange(0, 64), rng.randrange(64, 10**9)]
                )
                set_storage(
                    pre,
                    address,
                    Bytes32(U256(slot).to_be_bytes32()),
                    U256(rng.randrange(1, 100)),
                )

        account_changes: Dict[Bytes20, Optional[Account]] = {}
        storage_changes: Dict[Bytes20, Dict[Bytes32, U256]] = {}
        for address in eoas:
            roll = rng.random()
            bare = pre._accounts[address].code_hash == EMPTY_CODE_HASH
            if roll < 0.25 and bare:
                # EIP-6780-style same-transaction deletion.
                account_changes[address] = None
            elif roll < 0.6:
                # Delegate, re-delegate, or un-delegate.
                account_changes[address] = Account(
                    nonce=Uint(rng.randrange(1, 5)),
                    balance=U256(rng.randrange(1, 10**9)),
                    code_hash=rng.choice(
                        [EMPTY_CODE_HASH] + delegation_hashes
                    ),
                )
        for address in contracts:
            if rng.random() < 0.5:
                account_changes[address] = Account(
                    nonce=Uint(1),
                    balance=U256(rng.randrange(1, 10**9)),
                    code_hash=long_hash,
                )
            if rng.random() < 0.7:
                storage_changes[address] = {
                    Bytes32(U256(1).to_be_bytes32()): U256(rng.choice([0, 7])),
                    Bytes32(U256(100).to_be_bytes32()): U256(
                        rng.choice([0, 9])
                    ),
                }

        fresh_code = Bytes(rng.randbytes(200))
        fresh_hash = keccak256(fresh_code)
        created = Bytes20(rng.randbytes(20))
        account_changes[created] = Account(
            nonce=Uint(1), balance=U256(5), code_hash=fresh_hash
        )
        storage_changes[created] = {Bytes32(U256(2).to_be_bytes32()): U256(9)}

        diff = BlockDiff(
            account_changes=account_changes,
            storage_changes=storage_changes,
            code_changes={fresh_hash: fresh_code},
        )

        assert bytes(pre.compute_state_root(diff)) == _flat_oracle_root(
            pre, diff
        ), f"trial {trial}"


def test_header_root_matches_the_advanced_chain_state() -> None:
    """
    The fork commits a block's header root with
    [`compute_state_root`] but advances the chain with
    [`apply_changes_to_state`]. The two are separate
    implementations, one walking the tree and the other the flat
    mappings, so every block's header root must equal the root of
    the state the chain
    carries into the next block, or the second block of a chain is
    built on a state the first block never committed to.

    [`compute_state_root`]: ref:ethereum.state_pbt.State.compute_state_root
    [`apply_changes_to_state`]: ref:ethereum.state_pbt.apply_changes_to_state
    """  # noqa: E501
    chain = State()
    delegation_hash = store_code(chain, DELEGATION_A)
    set_account(
        chain,
        ADDRESS_A,
        Account(nonce=Uint(0), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(chain, ADDRESS_A, Bytes32(U256(3).to_be_bytes32()), U256(4))
    set_storage(chain, ADDRESS_A, Bytes32(U256(300).to_be_bytes32()), U256(5))
    set_account(
        chain,
        ADDRESS_B,
        Account(nonce=Uint(1), balance=U256(9), code_hash=EMPTY_CODE_HASH),
    )

    deployed = Bytes(b"\x60\x01" * 100)
    deployed_hash = keccak256(deployed)

    blocks = [
        # Touching an empty account that still holds storage deletes
        # it under EIP-161, storage leaves and all.
        BlockDiff(account_changes={ADDRESS_A: None}),
        # Delegating an existing EOA writes a content-addressed chunk.
        BlockDiff(
            account_changes={
                ADDRESS_B: Account(
                    nonce=Uint(2), balance=U256(9), code_hash=delegation_hash
                )
            }
        ),
        # A fresh deployment, with storage, on the delegated account's
        # neighbour, plus the delegation being revoked.
        BlockDiff(
            account_changes={
                ADDRESS_B: Account(
                    nonce=Uint(3), balance=U256(9), code_hash=EMPTY_CODE_HASH
                ),
                ADDRESS_A: Account(
                    nonce=Uint(1), balance=U256(2), code_hash=deployed_hash
                ),
            },
            storage_changes={
                ADDRESS_A: {Bytes32(U256(7).to_be_bytes32()): U256(8)}
            },
            code_changes={deployed_hash: deployed},
        ),
    ]

    for number, diff in enumerate(blocks):
        header_root = chain.compute_state_root(diff)
        apply_changes_to_state(chain, diff)
        assert header_root == state_root(chain), f"block {number}"


def test_store_code_round_trips() -> None:
    """
    Stored bytecode is retrievable by its hash, and the empty code
    hash resolves to empty bytes without storage.
    """
    state = State()
    code = Bytes(b"\x60\x00")
    code_hash = store_code(state, code)

    assert state.get_code(code_hash) == code
    assert state.get_code(EMPTY_CODE_HASH) == b""


def _account_header_stem(address32: bytes) -> bytes:
    """
    Build an account's 33-byte header stem from scratch.

    The stem is `0x00 || blake3(address32)`: the account zone byte
    followed by the address digest, computed here independently of
    `get_tree_key_for_header`.
    """
    return bytes([0]) + blake3(address32).digest()


def _storage_overflow_stem(address32: bytes, tree_index: int) -> bytes:
    """
    Build a 65-byte overflow storage stem from scratch.

    The stem is `0xff || blake3(address32) ||
    blake3(address32 || tree_index)`, computed here independently of
    `get_tree_key_for_storage_slot`.
    """
    prefix = blake3(address32).digest()
    suffix = blake3(address32 + tree_index.to_bytes(32, "big")).digest()
    return bytes([255]) + prefix + suffix


def _code_zone_stem(code_hash: bytes, tree_index: int) -> bytes:
    """
    Build a 33-byte code zone stem from scratch.

    The stem is `0x01 || blake3(code_hash || tree_index)`, computed
    here independently of `get_tree_key_for_code_chunk`.
    """
    digest = blake3(code_hash + tree_index.to_bytes(32, "big")).digest()
    return bytes([1]) + digest


def test_embedded_key_set_for_a_crafted_contract() -> None:
    """
    One contract, crafted so its code and storage exercise every
    sub-index boundary the embedding defines, embeds to an exact,
    independently rebuilt key set.

    Code spanning 129 chunks (`31 * 129 = 3999` bytes) fills
    code-zone sub-indices 0-128 of group 0; storage at slots 63, 64,
    and 256 puts one slot in the header and two in the storage zone,
    each its own overflow group.
    """
    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    code = Bytes(b"\x01" * (31 * 129))
    state = MptState()
    code_hash = mpt_store_code(state, code)
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )
    for slot, value in ((63, 1), (64, 2), (256, 3)):
        mpt_set_storage(
            state,
            ADDRESS_A,
            Bytes32(U256(slot).to_be_bytes32()),
            U256(value),
        )

    embedded = embed_state(state)

    header_stem = _account_header_stem(address32)
    expected_keys = {
        header_stem + bytes([0]),  # basic data
        header_stem + bytes([1]),  # code hash
        header_stem + bytes([127]),  # storage slot 63
    }
    expected_keys |= {
        _code_zone_stem(code_hash, 0) + bytes([chunk_id])
        for chunk_id in range(129)
    }
    expected_keys.add(_storage_overflow_stem(address32, 0) + bytes([64]))
    expected_keys.add(_storage_overflow_stem(address32, 1) + bytes([0]))

    assert set(embedded._data.keys()) == expected_keys
    assert all(len(key) in (34, 66) for key in expected_keys)


def test_embedded_keys_never_use_a_reserved_zone_byte() -> None:
    """
    Every key's first byte is one of the three zones this embedding
    defines -- `ACCOUNT_ZONE` (0x00), `CODE_ZONE` (0x01), or
    `STORAGE_ZONE` (0xFF) -- never one of the `0x02`-`0xFE` zone bytes
    EIP-8297 reserves for future state categories ("New categories
    MUST be allocated from `0x02`-`0xFE` and MUST keep their keys
    mutually prefix-free").

    Reuses `test_embedded_key_set_for_a_crafted_contract`'s crafted
    contract, so the embedded state populates every leaf category:
    header leaves, header and overflow storage, and content-addressed
    code.
    """
    code = Bytes(b"\x01" * (31 * 129))
    state = MptState()
    code_hash = mpt_store_code(state, code)
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )
    for slot, value in ((63, 1), (64, 2), (256, 3)):
        mpt_set_storage(
            state,
            ADDRESS_A,
            Bytes32(U256(slot).to_be_bytes32()),
            U256(value),
        )

    embedded = embed_state(state)

    allowed_zone_bytes = {0x00, 0x01, 0xFF}
    for key in embedded._data:
        assert key[0] in allowed_zone_bytes, (
            f"key {key.hex()} uses zone byte {key[0]:#04x}, outside "
            "the three zones this embedding defines"
        )


def test_embedded_state_root_is_pinned() -> None:
    """
    The same crafted state as `test_embedded_key_set_for_a_crafted_contract`
    commits to a hardcoded root hash.

    A deliberate change-detector for the hash function, node tags,
    prefix encoding, and the embedding built on top of them -- same
    spirit as `test_trie.py::test_fixed_trie_root_is_pinned`. Every
    other root assertion in this module compares two roots the code
    itself computed, so a systematic but deterministic bug in the hash
    function or merkleization would move both sides identically and
    pass unnoticed there; only a value hardcoded from a known-good run
    catches that. To regenerate after a deliberate, reviewed change:
    print `root(embedded).hex()` for this same state and paste the new
    value below.
    """
    code = Bytes(b"\x01" * (31 * 129))
    state = MptState()
    code_hash = mpt_store_code(state, code)
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )
    for slot, value in ((63, 1), (64, 2), (256, 3)):
        mpt_set_storage(
            state,
            ADDRESS_A,
            Bytes32(U256(slot).to_be_bytes32()),
            U256(value),
        )

    embedded = embed_state(state)

    assert root(embedded) == bytes.fromhex(
        "84d204064e6f2d3f8862bf399d9c1d7eb46a47d041930beec3c1d1dd124e6bc8"
    )


def test_embedded_key_set_for_a_fully_occupied_header_stem() -> None:
    """
    An account with 64 header storage slots fills every header
    sub-index this embedding can ever populate, and embeds to exactly
    that key set plus its code's content-addressed leaves.

    Storage slots 0-63 fill header sub-indices 64-127; together with
    basic data (0) and the code hash (1) that is the whole allocated
    header range, the maximum-occupancy case the EIP's
    `HEADER_STORAGE_OFFSET + HEADER_STORAGE_SLOTS <=
    STEM_SUBTREE_WIDTH` invariant exists to protect.

    Most of the 256 sub-indices are unreachable by any account:
    2-63 sit permanently unassigned between the code hash (1) and the
    first header storage slot (64), and 128-255 -- the old code range
    -- are unallocated since code moved wholly into the code zone.
    The expected header set is `{0, 1} | set(range(64, 128))`, and
    the code's 128 chunks all land in the code zone.
    """
    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    code = Bytes(b"\x01" * (31 * 128))  # 128 chunks
    state = MptState()
    code_hash = mpt_store_code(state, code)
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )
    for slot in range(64):
        mpt_set_storage(
            state,
            ADDRESS_A,
            Bytes32(U256(slot).to_be_bytes32()),
            U256(slot + 1),
        )

    embedded = embed_state(state)

    header_stem = _account_header_stem(address32)
    header_keys = {
        key for key in embedded._data if key.startswith(header_stem)
    }
    header_sub_indices = {key[-1] for key in header_keys}

    assert header_sub_indices == {0, 1} | set(range(64, 128))
    code_zone_keys = {key for key in embedded._data if key[0] == 1}
    assert code_zone_keys == {
        _code_zone_stem(code_hash, 0) + bytes([chunk_id])
        for chunk_id in range(128)
    }
    assert embedded._data.keys() == header_keys | code_zone_keys, (
        "a fully-occupied header plus its code must produce no other key"
    )


def test_identical_code_shares_every_chunk_key() -> None:
    """
    Two accounts with identical 129-chunk code produce one shared set
    of content-addressed chunk keys, and no chunk key anywhere else.

    Pins this by KEY, not leaf count: the code zone must hold exactly
    the 129 keys of the shared bytecode's group 0, and each account's
    header stem must carry nothing beyond its basic data and code
    hash.
    """
    code = Bytes(b"\x01" * (31 * 129))
    state = MptState()
    code_hash = mpt_store_code(state, code)
    for address in (ADDRESS_A, ADDRESS_B):
        mpt_set_account(
            state,
            address,
            Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
        )

    embedded = embed_state(state)

    stem_a = _account_header_stem(b"\x00" * 12 + bytes(ADDRESS_A))
    stem_b = _account_header_stem(b"\x00" * 12 + bytes(ADDRESS_B))
    for stem in (stem_a, stem_b):
        header_sub_indices = {
            key[-1] for key in embedded._data if key.startswith(stem)
        }
        assert header_sub_indices == {0, 1}

    code_zone_keys = {key for key in embedded._data if key[0] == 1}
    assert code_zone_keys == {
        _code_zone_stem(code_hash, 0) + bytes([chunk_id])
        for chunk_id in range(129)
    }


_NON_PUSH_BYTES = [b for b in range(256) if not (0x60 <= b <= 0x7F)]
"""
The 224 byte values outside the `PUSH1`..`PUSH32` opcode range.
"""


def _code_chunk_filler_byte(chunk_id: int) -> int:
    """
    Map a chunk index to a filler byte never in the `PUSH1`..`PUSH32`
    range (0x60-0x7F), so a chunk of repeats carries no push data.

    Cycles through the non-push byte values, so any two chunks fewer
    than `len(_NON_PUSH_BYTES)` apart -- in particular any
    neighbours -- get distinct filler bytes.
    """
    return _NON_PUSH_BYTES[chunk_id % len(_NON_PUSH_BYTES)]


def _distinct_chunk_code(chunk_count: int, *, salt: int = 1) -> Bytes:
    """
    Build code of `chunk_count` chunks, chunk `i` filled with 31
    repeats of `_code_chunk_filler_byte(salt + i)`.

    The default salt starts past filler byte zero, so every chunk of
    a short code is nonzero and present in the tree; two codes built
    with salts fewer than `len(_NON_PUSH_BYTES)` apart share no
    chunk value across their overlapping indices.
    """
    return Bytes(
        b"".join(
            bytes([_code_chunk_filler_byte(salt + i)]) * 31
            for i in range(chunk_count)
        )
    )


def test_chunk_values_are_distinct_across_the_code_group_boundary() -> None:
    r"""
    Chunks 254-257, each filled with its own distinct byte, get their
    exact 32-byte values pinned by rebuilt key: group 0's last two
    chunks (254, 255) and group 1's first two (256, 257) -- covering
    the one boundary in EIP-8297 where a code key's stem changes, the
    `tree_index` advancing while the sub-index wraps to zero.

    Every other coverage of this boundary in this suite builds code as
    `b"\\x01" * N`, making neighbouring chunks identical and
    interchangeable: swapping two chunks' stored values inside
    `embed_flat_state` would pass every one of those tests, key-set
    assertions included. Filling chunk `i` with
    `_code_chunk_filler_byte(i)` keeps every filler byte outside the
    `PUSH1`..`PUSH32` range, so each chunk's expected value is
    trivially `0x00` followed by 31 repeats of its own filler byte.
    """
    chunk_count = 258  # chunks 0..257: 31 * 258 = 7998, well under
    # MAX_CODE_SIZE, and comfortably covers chunks 254-257.
    code = Bytes(
        b"".join(
            bytes([_code_chunk_filler_byte(i)]) * 31
            for i in range(chunk_count)
        )
    )
    assert len(code) == 31 * chunk_count == 7998

    state = State()
    code_hash = store_code(state, code)
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )

    trie = embed_flat_state(state._accounts, state._storage, state.get_code)

    group_0_stem = _code_zone_stem(code_hash, 0)
    group_1_stem = _code_zone_stem(code_hash, 1)

    def expected_chunk(chunk_id: int) -> Bytes32:
        filler = bytes([_code_chunk_filler_byte(chunk_id)])
        return Bytes32(bytes([0]) + filler * 31)

    # Chunks 0-255 share group 0's stem at sub-index chunk_id; chunk
    # 256 is the first of group 1, at sub-index 0; 257 is the next.
    assert trie._data[group_0_stem + bytes([254])] == expected_chunk(254)
    assert trie._data[group_0_stem + bytes([255])] == expected_chunk(255)
    assert trie._data[group_1_stem + bytes([0])] == expected_chunk(256)
    assert trie._data[group_1_stem + bytes([1])] == expected_chunk(257)


def test_short_identical_code_shares_both_chunk_leaves() -> None:
    """
    Two accounts with the same 2-chunk code -- the common case under
    content addressing -- embed to exactly six leaves: two header
    pairs and one shared copy of each chunk, with the chunk values
    pinned per key.

    The two chunks carry distinct bytes, so a wrong chunk landing in
    the right key set -- swapped values, a copy under a wrong stem --
    cannot cancel out.
    """
    code = _distinct_chunk_code(2)
    state = MptState()
    code_hash = mpt_store_code(state, code)
    for address in (ADDRESS_A, ADDRESS_B):
        mpt_set_account(
            state,
            address,
            Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
        )

    embedded = embed_state(state)

    stem_a = _account_header_stem(b"\x00" * 12 + bytes(ADDRESS_A))
    stem_b = _account_header_stem(b"\x00" * 12 + bytes(ADDRESS_B))
    code_stem = _code_zone_stem(code_hash, 0)
    assert set(embedded._data.keys()) == {
        stem_a + bytes([0]),
        stem_a + bytes([1]),
        stem_b + bytes([0]),
        stem_b + bytes([1]),
        code_stem + bytes([0]),
        code_stem + bytes([1]),
    }
    for chunk_id, chunk in enumerate(chunkify_code(code)):
        assert embedded._data[code_stem + bytes([chunk_id])] == chunk


@pytest.mark.parametrize(
    "survivor_placement",
    [
        pytest.param("pre_state", id="survivor_untouched_in_pre_state"),
        pytest.param("diff_first", id="survivor_listed_before_the_loser"),
        pytest.param("diff_last", id="survivor_listed_after_the_loser"),
    ],
)
def test_code_change_keeps_chunks_a_survivor_still_holds(
    survivor_placement: str,
) -> None:
    """
    Account A's code hash changes from H to H' while account B still
    holds H: H's chunks must survive, H''s must appear, and the root
    must equal a fresh embed of the post state.

    `code_hash_survives` has two arms -- the diff's own values and
    the untouched pre-state -- and a survivor can satisfy either, so
    the diff arm is exercised beside the pre-state one. Within the
    diff, the survivor's position matters more than it looks: listed
    after the loser, `embed_account` re-writes whatever a broken
    removal took, so only the survivor-first ordering detects an
    implementation that skips the diff arm entirely. The two codes
    share no chunk value, so removing the wrong bytecode's leaves
    cannot go unnoticed.
    """
    old_code = _distinct_chunk_code(3)
    new_code = _distinct_chunk_code(2, salt=10)

    pre = State()
    old_hash = store_code(pre, old_code)
    new_hash = keccak256(new_code)
    for address in (ADDRESS_A, ADDRESS_B):
        set_account(
            pre,
            address,
            Account(nonce=Uint(1), balance=U256(1), code_hash=old_hash),
        )

    changed = Account(nonce=Uint(1), balance=U256(1), code_hash=new_hash)
    survivor = Account(nonce=Uint(1), balance=U256(1), code_hash=old_hash)
    touched = Account(nonce=Uint(1), balance=U256(2), code_hash=old_hash)
    account_changes: Dict[Bytes20, Optional[Account]] = {}
    if survivor_placement == "diff_first":
        survivor = touched
        account_changes[ADDRESS_B] = survivor
    account_changes[ADDRESS_A] = changed
    if survivor_placement == "diff_last":
        survivor = touched
        account_changes[ADDRESS_B] = survivor
    diff = BlockDiff(
        account_changes=account_changes,
        code_changes={new_hash: new_code},
    )

    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    apply_diff_to_trie(trie, pre, diff)
    old_stem = _code_zone_stem(old_hash, 0)
    new_stem = _code_zone_stem(new_hash, 0)
    for chunk_id in range(3):
        assert old_stem + bytes([chunk_id]) in trie._data
    for chunk_id in range(2):
        assert new_stem + bytes([chunk_id]) in trie._data

    fresh = State()
    assert store_code(fresh, old_code) == old_hash
    assert store_code(fresh, new_code) == new_hash
    set_account(fresh, ADDRESS_A, changed)
    set_account(fresh, ADDRESS_B, survivor)
    assert pre.compute_state_root(diff) == state_root(fresh)


def test_code_change_by_the_last_holder_drops_every_group() -> None:
    """
    The changing account was the only holder of a code spanning two
    code groups (257 chunks): its change must remove group 1's
    chunks as well as group 0's, leaving the code zone holding only
    the new code and the root that of a fresh embed.

    Every legacy-size code in this suite fits inside group 0, so a
    removal bug scoped to `tree_index == 0` -- sweeping sub-indices
    without ever advancing the group -- is caught only here.
    """
    old_code = _distinct_chunk_code(257)
    new_code = Bytes(bytes(range(1, 63)))  # 2 chunks, no push opcodes

    pre = State()
    old_hash = store_code(pre, old_code)
    new_hash = keccak256(new_code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=old_hash),
    )

    changed = Account(nonce=Uint(1), balance=U256(1), code_hash=new_hash)
    diff = BlockDiff(
        account_changes={ADDRESS_A: changed},
        code_changes={new_hash: new_code},
    )

    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    apply_diff_to_trie(trie, pre, diff)
    new_stem = _code_zone_stem(new_hash, 0)
    code_zone_keys = {key for key in trie._data if key[0] == 1}
    assert code_zone_keys == {
        new_stem + bytes([0]),
        new_stem + bytes([1]),
    }

    fresh = State()
    assert store_code(fresh, new_code) == new_hash
    set_account(fresh, ADDRESS_A, changed)
    assert pre.compute_state_root(diff) == state_root(fresh)


def test_shared_delegation_designator_follows_its_last_authority() -> None:
    """
    Two EOAs delegating to the same target share one designator
    chunk. One authority re-delegating to a different target must
    leave that chunk in place for the other while writing the new
    designator's chunk; the remaining authority clearing its
    delegation afterwards removes it, leaving only the re-delegated
    designator.

    Re-delegating to the *same* target would be a code-hash no-op
    that exercises nothing, so the staircase switches targets.
    """
    pre = State()
    hash_a = store_code(pre, DELEGATION_A)
    for address in (ADDRESS_A, ADDRESS_B):
        set_account(
            pre,
            address,
            Account(nonce=Uint(1), balance=U256(1), code_hash=hash_a),
        )

    stem_a = _code_zone_stem(hash_a, 0)
    initial = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    assert {key for key in initial._data if key[0] == 1} == {
        stem_a + bytes([0])
    }, "both authorities must share one designator leaf"

    hash_b = keccak256(DELEGATION_B)
    step_1 = BlockDiff(
        account_changes={
            ADDRESS_A: Account(
                nonce=Uint(2), balance=U256(1), code_hash=hash_b
            )
        },
        code_changes={hash_b: DELEGATION_B},
    )
    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    apply_diff_to_trie(trie, pre, step_1)
    stem_b = _code_zone_stem(hash_b, 0)
    assert {key for key in trie._data if key[0] == 1} == {
        stem_a + bytes([0]),
        stem_b + bytes([0]),
    }, "exactly the two designators' leaves, the old one kept for B"

    step_1_post = State()
    assert store_code(step_1_post, DELEGATION_A) == hash_a
    assert store_code(step_1_post, DELEGATION_B) == hash_b
    set_account(
        step_1_post,
        ADDRESS_A,
        Account(nonce=Uint(2), balance=U256(1), code_hash=hash_b),
    )
    set_account(
        step_1_post,
        ADDRESS_B,
        Account(nonce=Uint(1), balance=U256(1), code_hash=hash_a),
    )
    assert pre.compute_state_root(step_1) == state_root(step_1_post)

    apply_changes_to_state(pre, step_1)
    step_2 = BlockDiff(
        account_changes={
            ADDRESS_B: Account(
                nonce=Uint(2), balance=U256(1), code_hash=EMPTY_CODE_HASH
            )
        },
    )
    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    apply_diff_to_trie(trie, pre, step_2)
    assert {key for key in trie._data if key[0] == 1} == {
        stem_b + bytes([0])
    }, "the last authority leaving must take the old designator with it"

    step_2_post = State()
    assert store_code(step_2_post, DELEGATION_B) == hash_b
    set_account(
        step_2_post,
        ADDRESS_A,
        Account(nonce=Uint(2), balance=U256(1), code_hash=hash_b),
    )
    set_account(
        step_2_post,
        ADDRESS_B,
        Account(nonce=Uint(2), balance=U256(1), code_hash=EMPTY_CODE_HASH),
    )
    assert pre.compute_state_root(step_2) == state_root(step_2_post)


def test_shared_code_survives_until_the_last_holder_is_gone() -> None:
    """
    Three accounts share one bytecode. Deleting them one block at a
    time keeps the chunk leaves through the first two deletions --
    pinned by key after each step -- and the third deletion takes
    them with it, returning the tree to empty.
    """
    code = _distinct_chunk_code(3)
    addresses = (ADDRESS_A, ADDRESS_B, ADDRESS_C)

    pre = State()
    code_hash = store_code(pre, code)
    for address in addresses:
        set_account(
            pre,
            address,
            Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
        )

    stem = _code_zone_stem(code_hash, 0)
    chunk_keys = {stem + bytes([chunk_id]) for chunk_id in range(3)}

    for deletions_so_far, address in enumerate(addresses):
        diff = BlockDiff(account_changes={address: None})
        trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
        apply_diff_to_trie(trie, pre, diff)
        present = chunk_keys & set(trie._data.keys())
        if deletions_so_far < 2:
            assert present == chunk_keys, (
                f"deletion {deletions_so_far + 1} of 3 must keep the "
                "shared chunks"
            )
        else:
            assert present == set()
            assert root(trie) == EMPTY_TRIE_ROOT
        apply_changes_to_state(pre, diff)


def test_two_holders_deleted_in_one_block_drop_the_code_once() -> None:
    """
    Both remaining holders of a bytecode go in the same block: the
    first removal drops the shared chunks and the second finds them
    already gone, a no-op rather than an error, leaving the empty
    root.
    """
    code = _distinct_chunk_code(2)

    pre = State()
    code_hash = store_code(pre, code)
    for address in (ADDRESS_A, ADDRESS_B):
        set_account(
            pre,
            address,
            Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
        )

    diff = BlockDiff(account_changes={ADDRESS_A: None, ADDRESS_B: None})

    assert pre.compute_state_root(diff) == EMPTY_TRIE_ROOT


def test_contract_deleted_then_recreated_with_different_code() -> None:
    """
    A sole holder's deletion drops its chunks in one block; the next
    block re-creates the address with different code through its own
    diff. Each block's root is computed incrementally and must match
    a fresh embed of that block's post state -- the drop and the
    re-add land in separate tries, rebuilt from the advanced flat
    state, so nothing of the old code may linger.
    """
    old_code = _distinct_chunk_code(3)
    new_code = _distinct_chunk_code(2, salt=40)

    pre = State()
    old_hash = store_code(pre, old_code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=old_hash),
    )

    delete = BlockDiff(account_changes={ADDRESS_A: None})
    assert pre.compute_state_root(delete) == EMPTY_TRIE_ROOT
    apply_changes_to_state(pre, delete)

    new_hash = keccak256(new_code)
    recreated = Account(nonce=Uint(1), balance=U256(2), code_hash=new_hash)
    recreate = BlockDiff(
        account_changes={ADDRESS_A: recreated},
        code_changes={new_hash: new_code},
    )

    fresh = State()
    assert store_code(fresh, new_code) == new_hash
    set_account(fresh, ADDRESS_A, recreated)
    assert pre.compute_state_root(recreate) == state_root(fresh)


def test_code_change_and_storage_writes_share_a_diff() -> None:
    """
    One diff both replaces a sole holder's code -- dropping the old
    chunks -- and writes its storage. The sweeps touch disjoint
    zones and the storage loop runs after the account loop; the
    combination must land on the root of a fresh embed of the post
    state.
    """
    old_code = _distinct_chunk_code(3)
    new_code = _distinct_chunk_code(2, salt=50)
    slot = Bytes32(U256(2).to_be_bytes32())

    pre = State()
    old_hash = store_code(pre, old_code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=old_hash),
    )
    set_storage(pre, ADDRESS_A, slot, U256(5))

    new_hash = keccak256(new_code)
    changed = Account(nonce=Uint(2), balance=U256(1), code_hash=new_hash)
    diff = BlockDiff(
        account_changes={ADDRESS_A: changed},
        storage_changes={ADDRESS_A: {slot: U256(9)}},
        code_changes={new_hash: new_code},
    )

    fresh = State()
    assert store_code(fresh, new_code) == new_hash
    set_account(fresh, ADDRESS_A, changed)
    set_storage(fresh, ADDRESS_A, slot, U256(9))
    assert pre.compute_state_root(diff) == state_root(fresh)


def test_group_exact_code_fills_group_zero_and_nothing_more() -> None:
    """
    Code of exactly 256 chunks fills code group 0 to its last
    sub-index and derives no key in group 1: the group boundary is
    exclusive on the right, `chunk_id // 256`.
    """
    code = Bytes(b"\x01" * (31 * 256))  # 256 chunks, none zero

    pre = State()
    code_hash = store_code(pre, code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )

    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)

    group_0_stem = _code_zone_stem(code_hash, 0)
    group_1_stem = _code_zone_stem(code_hash, 1)
    code_zone_keys = {key for key in trie._data if key[0] == 1}
    assert code_zone_keys == {
        group_0_stem + bytes([sub_index]) for sub_index in range(256)
    }
    assert not any(key.startswith(group_1_stem) for key in trie._data)


def test_change_to_an_unresolvable_code_hash_is_a_pre_state_error() -> None:
    """
    A diff that points an account at a code hash resolvable neither
    from its `code_changes` nor from the store fails with
    `UnknownCodeHashError` when the root is computed: malformed
    input, deliberately not an invalid block.
    """
    pre = State()
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH),
    )
    phantom = keccak256(b"never stored")
    diff = BlockDiff(
        account_changes={
            ADDRESS_A: Account(
                nonce=Uint(1), balance=U256(1), code_hash=phantom
            )
        },
    )

    with pytest.raises(UnknownCodeHashError):
        pre.compute_state_root(diff)
    assert not issubclass(UnknownCodeHashError, InvalidBlock)


def test_absent_chunk_in_a_later_group_does_not_stall_removal() -> None:
    """
    A multi-group code with an all-zero chunk in group 1 has a hole
    where that leaf would sit. Deleting the last holder must remove
    every present chunk on both sides of the hole, leaving the empty
    root.
    """
    chunk_count = 258
    mutable = bytearray(b"\x01" * (31 * chunk_count))
    mutable[31 * 256 : 31 * 257] = b"\x00" * 31  # chunk 256, group 1
    code = Bytes(bytes(mutable))

    pre = State()
    code_hash = store_code(pre, code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )

    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    group_1_stem = _code_zone_stem(code_hash, 1)
    assert group_1_stem + bytes([0]) not in trie._data  # the hole
    assert group_1_stem + bytes([1]) in trie._data

    diff = BlockDiff(account_changes={ADDRESS_A: None})

    assert pre.compute_state_root(diff) == EMPTY_TRIE_ROOT


def test_push_data_continuation_chunk_of_zero_bytes_is_present() -> None:
    """
    A chunk whose 31 code bytes are all zero is absent only when its
    leading byte is zero too. The EIP, "Code": "Zero bytes that
    continue PUSHDATA from an earlier chunk do not qualify, since
    byte 0 then records the continuation."

    Here `PUSH32` ends chunk 0 and its data fills chunk 1 with 31
    zero bytes, so chunk 1 encodes to `0x1f` followed by zeros -- not
    the zero value -- and its leaf must be in the tree. An
    implementation keying absence off the 31-byte code slice alone
    would drop it and corrupt the committed code. Deleting the last
    holder must still take it away with the rest.
    """
    # PUSH32 at position 30: data occupies positions 31..62, so chunk
    # 1's code bytes are 31 zero bytes of push data.
    code = Bytes(b"\x01" * 30 + b"\x7f" + b"\x00" * 31)
    assert len(code) == 62  # two chunks

    pre = State()
    code_hash = store_code(pre, code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )

    trie = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    stem = _code_zone_stem(code_hash, 0)
    continuation_key = stem + bytes([1])
    assert continuation_key in trie._data
    assert trie._data[continuation_key] == Bytes32(
        bytes([31]) + b"\x00" * 31
    )

    diff = BlockDiff(account_changes={ADDRESS_A: None})

    assert pre.compute_state_root(diff) == EMPTY_TRIE_ROOT


def test_account_has_storage_matches_the_embedded_leaf_set() -> None:
    """
    EIP-8297 defines non-empty storage by leaf existence: a leaf at
    one of the header's storage sub-indices or anywhere in the
    address's storage bucket. The provider answers from its flat
    map, which stays equivalent only through upkeep on every
    mutation path; this pins the equivalence itself, over states
    reached through `set_*` calls and through applied diffs.

    The one deliberate exception is storage orphaned by
    `set_account(..., None)`, whose flat/leaf divergence
    `test_set_account_none_leaves_storage_while_the_diff_path_clears_it`
    pins separately.
    """

    def storage_leaf_exists(state: State, address: Bytes20) -> bool:
        trie = embed_flat_state(
            state._accounts, state._storage, state.get_code
        )
        address32 = b"\x00" * 12 + bytes(address)
        header_stem = _account_header_stem(address32)
        bucket_prefix = bytes([0xFF]) + blake3(address32).digest()
        first = int(HEADER_STORAGE_OFFSET)
        last = int(HEADER_STORAGE_OFFSET + HEADER_STORAGE_SLOTS) - 1
        return any(
            (key.startswith(header_stem) and first <= key[-1] <= last)
            or key.startswith(bucket_prefix)
            for key in trie._data
        )

    key_header = Bytes32(U256(3).to_be_bytes32())
    key_bucket = Bytes32(U256(1000).to_be_bytes32())
    account = Account(
        nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH
    )

    def fresh(*slots: Bytes32) -> State:
        state = State()
        set_account(state, ADDRESS_A, account)
        for slot in slots:
            set_storage(state, ADDRESS_A, slot, U256(7))
        return state

    no_storage = fresh()
    header_only = fresh(key_header)
    bucket_only = fresh(key_bucket)
    zeroed = fresh(key_header)
    apply_changes_to_state(
        zeroed, BlockDiff(storage_changes={ADDRESS_A: {key_header: U256(0)}})
    )
    deleted = fresh(key_header, key_bucket)
    apply_changes_to_state(
        deleted, BlockDiff(account_changes={ADDRESS_A: None})
    )
    cleared = fresh(key_header, key_bucket)
    apply_changes_to_state(cleared, BlockDiff(storage_clears={ADDRESS_A}))

    expectations = [
        (no_storage, False),
        (header_only, True),
        (bucket_only, True),
        (zeroed, False),
        (deleted, False),
        (cleared, False),
    ]
    for state, expected in expectations:
        assert state.account_has_storage(ADDRESS_A) is expected
        assert storage_leaf_exists(state, ADDRESS_A) is expected


def test_deleting_an_unknown_address_is_a_no_op() -> None:
    """
    A diff may delete an address the pre-state never held. Removing
    the absent account's regions is a no-op, and the code check is
    skipped outright -- there is no previous account to read a code
    hash from -- leaving the root exactly where the pre-state's was.
    """
    pre = State()
    code_hash = store_code(pre, _distinct_chunk_code(2))
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )
    before = state_root(pre)

    diff = BlockDiff(account_changes={ADDRESS_B: None})

    assert pre.compute_state_root(diff) == before


def test_removing_code_with_an_absent_first_chunk_leaves_nothing() -> None:
    """
    A code whose first chunk is 31 zero bytes has no leaf at chunk 0
    -- zero collapses to absence -- so a presence probe on any fixed
    chunk could call the code leafless and leak the rest. Deleting
    the last holder must remove every later chunk regardless,
    leaving the empty root.
    """
    code = Bytes(b"\x00" * 31 + bytes(_distinct_chunk_code(2)))

    pre = State()
    code_hash = store_code(pre, code)
    set_account(
        pre,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=code_hash),
    )

    stem = _code_zone_stem(code_hash, 0)
    before = embed_flat_state(pre._accounts, pre._storage, pre.get_code)
    assert stem + bytes([0]) not in before._data
    assert stem + bytes([1]) in before._data
    assert stem + bytes([2]) in before._data

    diff = BlockDiff(account_changes={ADDRESS_A: None})

    assert pre.compute_state_root(diff) == EMPTY_TRIE_ROOT


def test_basic_data_leaf_bytes_carry_code_size_nonce_and_balance() -> None:
    """
    The BASIC_DATA leaf's 32 bytes pack the resolved code's length,
    not any field stored on `Account` itself.

    `Account` has no `code_size` field, so this proves the provider
    derives it from `get_code(code_hash)` at embed time, not from
    anything cached.
    """
    code = Bytes(b"\x01" * 40)
    state = MptState()
    code_hash = mpt_store_code(state, code)
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(7), balance=U256(12345), code_hash=code_hash),
    )

    embedded = embed_state(state)

    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    key = _account_header_stem(address32) + bytes([0])
    leaf = embedded._data[key]

    assert leaf[0:1] == b"\x00"  # version
    assert leaf[1:4] == b"\x00" * 3  # reserved
    assert leaf[4:8] == len(code).to_bytes(4, "big")  # code_size
    assert leaf[8:16] == (7).to_bytes(8, "big")  # nonce
    assert leaf[16:32] == (12345).to_bytes(16, "big")  # balance


def test_balance_at_or_above_the_sixteen_byte_field_rejects_at_root_time() -> (
    None
):
    """
    A balance of exactly `2**128` is rejected when the root is
    computed, not when it is set.

    `Account.balance` is a full `U256` and `set_account` stays
    unbounded, so the sixteen-byte field EIP-8297 packs it into is
    enforced at commitment time, as `BalanceOverflowError` -- an
    `InvalidBlock` -- rather than a raw `AssertionError`.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(
            nonce=Uint(0),
            balance=U256(2) ** U256(128),
            code_hash=EMPTY_CODE_HASH,
        ),
    )

    with pytest.raises(BalanceOverflowError):
        state_root(state)


def test_block_diff_minting_over_cap_balance_rejects_the_block() -> None:
    """
    A diff that raises an account's balance to `2**128` makes
    `compute_state_root` raise `BalanceOverflowError`: the block
    minting the balance is invalid, and the pre-state, whose balance
    still fits the field, embeds cleanly afterwards.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(
            nonce=Uint(0),
            balance=U256(2) ** U256(128) - U256(1),
            code_hash=EMPTY_CODE_HASH,
        ),
    )
    diff = BlockDiff(
        account_changes={
            ADDRESS_A: Account(
                nonce=Uint(0),
                balance=U256(2) ** U256(128),
                code_hash=EMPTY_CODE_HASH,
            )
        }
    )

    with pytest.raises(BalanceOverflowError):
        state.compute_state_root(diff)

    assert state.compute_state_root(BlockDiff()) == state_root(state)


def test_empty_code_contract_embeds_like_an_eoa() -> None:
    """
    A contract account whose code is explicitly `b""`, stored through
    `store_code` rather than merely defaulted, embeds identically to
    an EOA: exactly the two header leaves and no code chunk leaves.

    Unlike `test_eoa_embeds_basic_data_and_code_hash_leaves` (which
    never calls `store_code`), this pins that routing empty bytes
    through the store still resolves to `EMPTY_CODE_HASH`.
    """
    state = State()
    code_hash = store_code(state, Bytes(b""))
    assert code_hash == EMPTY_CODE_HASH

    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(3), balance=U256(42), code_hash=code_hash),
    )

    trie = embed_flat_state(state._accounts, state._storage, state.get_code)

    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    header_stem = _account_header_stem(address32)
    basic_data_key = header_stem + bytes([0])
    code_hash_key = header_stem + bytes([1])

    assert set(trie._data.keys()) == {basic_data_key, code_hash_key}
    assert trie._data[code_hash_key] == EMPTY_CODE_HASH


def test_delegation_designator_account_embedding() -> None:
    """
    An EIP-7702 delegation designator (`0xef0100` followed by a
    20-byte address, 23 bytes total) embeds as a single
    content-addressed code chunk beside the authority's two header
    leaves, its key derived from the designator's own hash so every
    authority delegating to the same target shares it. The designator
    starts with no push opcode, so its chunk's leading byte is 0.
    """
    designator = Bytes(b"\xef\x01\x00" + bytes(ADDRESS_B))
    assert len(designator) == 23

    state = MptState()
    code_hash = mpt_store_code(state, designator)
    mpt_set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )

    embedded = embed_state(state)

    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    header_stem = _account_header_stem(address32)
    basic_data_key = header_stem + bytes([0])
    code_hash_key = header_stem + bytes([1])
    chunk_key = _code_zone_stem(code_hash, 0) + bytes([0])

    assert set(embedded._data.keys()) == {
        basic_data_key,
        code_hash_key,
        chunk_key,
    }
    assert embedded._data[code_hash_key] == keccak256(designator)

    basic_data = embedded._data[basic_data_key]
    assert basic_data[4:8] == (23).to_bytes(4, "big")  # code_size

    chunk = embedded._data[chunk_key]
    assert chunk[0] == 0  # no push data reaches this, the only, chunk
    assert chunk[1:] == designator + b"\x00" * (31 - len(designator))


def test_get_code_raises_for_an_unknown_code_hash() -> None:
    """
    An account whose `code_hash` was never stored raises
    `UnknownCodeHashError` when the root is computed, because
    `embed_flat_state` resolves every account's code through
    `get_code` to size it.

    Only `EMPTY_CODE_HASH` needs no store entry. An unstored hash is
    a malformed pre-state, not an invalid block, so the error is an
    `EthereumException` but deliberately not an `InvalidBlock`.
    """
    assert not issubclass(UnknownCodeHashError, InvalidBlock)

    state = State()
    unknown_hash = keccak256(b"never stored")
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=unknown_hash),
    )

    assert state.get_code(EMPTY_CODE_HASH) == b""
    with pytest.raises(UnknownCodeHashError):
        state.get_code(unknown_hash)
    with pytest.raises(UnknownCodeHashError):
        state_root(state)


def test_storage_clears_removes_slots_before_other_changes() -> None:
    """
    `storage_clears` empties an address's storage before
    `storage_changes` is applied: a pre-existing slot is cleared like
    any other, while a brand-new key written by the same diff still
    lands with its new value.

    `binary_tree`'s own `extract_block_diff` (copied from Amsterdam,
    post-EIP-6780) never sets this field, so the branch is reachable
    only from this unit test today; pinning it keeps the provider
    honest in case a pre-Cancun-style tracker is ever wired up to it.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    key_1 = Bytes32(U256(1).to_be_bytes32())
    key_2 = Bytes32(U256(2).to_be_bytes32())
    set_storage(state, ADDRESS_A, key_1, U256(7))

    apply_changes_to_state(
        state,
        BlockDiff(
            storage_clears={ADDRESS_A},
            storage_changes={ADDRESS_A: {key_2: U256(9)}},
        ),
    )

    assert state.get_storage(ADDRESS_A, key_1) == U256(0)
    assert state.get_storage(ADDRESS_A, key_2) == U256(9)
    assert state._storage[ADDRESS_A] == {key_2: U256(9)}


def test_account_deletion_also_drops_its_storage() -> None:
    """
    Deleting an account through a diff also pops its storage:
    `_storage` no longer has an entry for the address, so
    `account_has_storage` reads back `False`.

    `test_differential_mpt.py`'s
    `test_account_delete_diverges_on_account_has_storage` pins the
    contrasting MPT behavior, where storage survives an account
    delete; this test only pins PBT's own side of that divergence.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(state, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7))
    assert state.account_has_storage(ADDRESS_A) is True

    apply_changes_to_state(state, BlockDiff(account_changes={ADDRESS_A: None}))

    assert ADDRESS_A not in state._storage
    assert state.account_has_storage(ADDRESS_A) is False


def test_storage_written_for_a_deleted_account_is_dropped() -> None:
    """
    A diff that deletes an account and writes to its storage in the
    same step leaves no storage behind at all.

    Storage belongs to an account, so a write to an address the diff
    leaves without one is dropped rather than kept as an orphan no
    account owns. That keeps `account_has_storage` answering as
    [EIP-8297] requires, from whether any slot leaf of the address
    exists: `embed_flat_state` would skip such an orphan anyway, so
    reporting storage for it would claim leaves the tree does not
    have.

    [EIP-8297]: https://eips.ethereum.org/EIPS/eip-8297
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    set_account(
        state,
        ADDRESS_B,
        Account(nonce=Uint(2), balance=U256(5), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(state, ADDRESS_B, Bytes32(U256(9).to_be_bytes32()), U256(3))

    key = Bytes32(U256(1).to_be_bytes32())
    apply_changes_to_state(
        state,
        BlockDiff(
            account_changes={ADDRESS_A: None},
            storage_changes={ADDRESS_A: {key: U256(7)}},
        ),
    )

    assert state.get_account_optional(ADDRESS_A) is None
    assert state.account_has_storage(ADDRESS_A) is False
    assert state.get_storage(ADDRESS_A, key) == U256(0)

    without_a = State()
    set_account(
        without_a,
        ADDRESS_B,
        Account(nonce=Uint(2), balance=U256(5), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(
        without_a, ADDRESS_B, Bytes32(U256(9).to_be_bytes32()), U256(3)
    )

    assert state_root(state) == state_root(without_a)


def test_all_zero_storage_change_drops_the_address_entry() -> None:
    """
    A diff writing only zeros to slots an account already holds
    empties `_storage[address]` down to nothing, and the address key
    itself is dropped, not left mapped to an empty dict.

    `account_has_storage` reads back `False` and the root matches a
    state that was never written to, which is the answer EIP-8297
    fixes for the tree: no slot leaf of the address survives.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    key_1 = Bytes32(U256(1).to_be_bytes32())
    key_2 = Bytes32(U256(2).to_be_bytes32())
    set_storage(state, ADDRESS_A, key_1, U256(7))
    set_storage(state, ADDRESS_A, key_2, U256(9))
    assert state.account_has_storage(ADDRESS_A) is True

    apply_changes_to_state(
        state,
        BlockDiff(
            storage_changes={ADDRESS_A: {key_1: U256(0), key_2: U256(0)}}
        ),
    )

    assert ADDRESS_A not in state._storage
    assert state.account_has_storage(ADDRESS_A) is False

    never_written = State()
    set_account(
        never_written,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    assert state_root(state) == state_root(never_written)


def test_set_account_none_leaves_storage_while_the_diff_path_clears_it() -> (
    None
):
    """
    `set_account(state, A, None)` pops the account but never touches
    its storage, while the diff path pops both together.

    Two identically set-up states, one deleted through `set_account`
    and the other through `apply_changes_to_state`, diverge on
    `account_has_storage` depending only on which route deleted the
    account.

    Rooting both states shows the divergence stops at the flat map:
    the embedding skips storage whose address has no account, so the
    orphaned slots never reach the tree and both states commit to
    the empty root.
    """
    key = Bytes32(U256(1).to_be_bytes32())

    via_set_account = State()
    set_account(
        via_set_account,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(via_set_account, ADDRESS_A, key, U256(7))
    set_account(via_set_account, ADDRESS_A, None)

    via_diff = State()
    set_account(
        via_diff,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(via_diff, ADDRESS_A, key, U256(7))
    apply_changes_to_state(
        via_diff, BlockDiff(account_changes={ADDRESS_A: None})
    )

    assert via_set_account.get_account_optional(ADDRESS_A) is None
    assert via_diff.get_account_optional(ADDRESS_A) is None
    assert via_set_account.account_has_storage(ADDRESS_A) is True
    assert via_diff.account_has_storage(ADDRESS_A) is False
    assert state_root(via_set_account) == EMPTY_TRIE_ROOT
    assert state_root(via_diff) == EMPTY_TRIE_ROOT


def test_set_storage_requires_an_existing_account() -> None:
    """
    `set_storage` asserts the account already exists; it is not a
    valid way to create storage for an address with no account.
    """
    state = State()
    with pytest.raises(AssertionError):
        set_storage(
            state, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7)
        )


def test_compute_state_root_leaves_the_pre_state_untouched() -> None:
    """
    `compute_state_root` applies the diff to a copy: calling it twice
    with a non-trivial diff returns the same root both times, and the
    pre-state's accounts, storage, and code store are unchanged.
    """
    code = Bytes(b"\x01" * 40)
    code_hash = keccak256(code)

    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(100), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(state, ADDRESS_A, Bytes32(U256(1).to_be_bytes32()), U256(7))

    accounts_before = dict(state._accounts)
    storage_before = {
        address: dict(slots) for address, slots in state._storage.items()
    }
    code_store_before = dict(state._code_store)

    diff = BlockDiff(
        account_changes={
            ADDRESS_A: Account(
                nonce=Uint(2), balance=U256(50), code_hash=code_hash
            ),
            ADDRESS_B: Account(
                nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH
            ),
        },
        storage_changes={
            ADDRESS_A: {Bytes32(U256(1).to_be_bytes32()): U256(0)}
        },
        code_changes={code_hash: code},
    )

    first_root = state.compute_state_root(diff)
    second_root = state.compute_state_root(diff)

    assert first_root == second_root
    assert state._accounts == accounts_before
    assert state._storage == storage_before
    assert state._code_store == code_store_before


def test_sequential_block_diffs_evolve_the_root() -> None:
    """
    Three sequential diffs applied to the same live `State` via
    `apply_changes_to_state`: writing a slot changes the root,
    writing a second slot changes it again, and zeroing the second
    slot returns the root to exactly what it was after the first
    write.

    Zero-means-absent composes across separate blocks, not just
    within one diff.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    key_1 = Bytes32(U256(1).to_be_bytes32())
    key_2 = Bytes32(U256(2).to_be_bytes32())
    root_empty = state_root(state)

    apply_changes_to_state(
        state, BlockDiff(storage_changes={ADDRESS_A: {key_1: U256(7)}})
    )
    root_after_first_write = state_root(state)
    assert root_after_first_write != root_empty

    apply_changes_to_state(
        state, BlockDiff(storage_changes={ADDRESS_A: {key_2: U256(9)}})
    )
    root_after_second_write = state_root(state)
    assert root_after_second_write != root_after_first_write

    apply_changes_to_state(
        state, BlockDiff(storage_changes={ADDRESS_A: {key_2: U256(0)}})
    )
    assert state_root(state) == root_after_first_write


def test_storage_boundary_slots_through_the_provider() -> None:
    """
    Slots 0, 63, 64, 255, 256, and `2**256 - 1`, set on one account
    through `set_storage`, land on whichever of the header (0, 63)
    or overflow (64, 255, 256, `2**256 - 1`) forms the embedding
    defines for that slot, holding the exact 32-byte value
    `set_storage` wrote there -- not merely a key that exists.

    Rebuilt here from raw `blake3` and literal zone/sub-index bytes,
    not `get_tree_key_for_storage_slot`. Each slot gets its own
    distinct value (`index + 1`), so a swap between any two of the six
    leaves is detectable: every other boundary-focused test in this
    module asserts key sets only, so mutating all header (or all
    overflow) leaf values inside `embed_flat_state` would otherwise go
    uncaught here.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=EMPTY_CODE_HASH),
    )
    slots = (0, 63, 64, 255, 256, 2**256 - 1)
    values = {slot: U256(index + 1) for index, slot in enumerate(slots)}
    for slot, value in values.items():
        set_storage(
            state, ADDRESS_A, Bytes32(U256(slot).to_be_bytes32()), value
        )

    trie = embed_flat_state(state._accounts, state._storage, state.get_code)

    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    header_stem = _account_header_stem(address32)
    storage_keys = {
        0: header_stem + bytes([64]),
        63: header_stem + bytes([127]),
        64: _storage_overflow_stem(address32, 0) + bytes([64]),
        255: _storage_overflow_stem(address32, 0) + bytes([255]),
        256: _storage_overflow_stem(address32, 1) + bytes([0]),
        2**256 - 1: _storage_overflow_stem(address32, 2**248 - 1)
        + bytes([255]),
    }
    expected_keys = {
        header_stem + bytes([0]),  # basic data
        header_stem + bytes([1]),  # code hash
        *storage_keys.values(),
    }

    assert set(trie._data.keys()) == expected_keys
    for slot, key in storage_keys.items():
        assert trie._data[key] == values[slot].to_be_bytes32(), (
            f"slot {slot}: unexpected leaf value"
        )
