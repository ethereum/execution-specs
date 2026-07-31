"""
Tests for `ethereum.state_pbt`.

The first group covers `embed_flat_state`: each kind of state
(account fields, code chunks, storage slots) must land in the tree
as exactly the expected leaves, with expected keys and values built
by hand from the derivation functions. The `embed_state` helper
adapts an MPT-backed `State` into the flat mappings the walk takes,
so the inputs are real account objects.

The second group covers the provider. `compute_state_root` applies
a block diff (deletions, zero-writes, freshly deployed code) and
embeds the result; each test builds the same post-state directly in
the MPT-backed container and checks that both roots agree.
"""

import random
from typing import Dict, Optional

import pytest
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
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
from ethereum.binary_trie.trie import (
    EMPTY_TRIE_ROOT,
    BinaryTrie,
    root,
    trie_set,
)
from ethereum.crypto.hash import keccak256
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

# EIP-7702 delegation designators: the only protocol-reachable code
# change on an existing account, and always a single header chunk.
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
    code = Bytes(b"\x01" * 40)  # two chunks, both in the header
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
            get_tree_key_for_code_chunk(address32, code_hash, Uint(chunk_id)),
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


def test_identical_bytecode_shares_overflow_chunk_leaves() -> None:
    """
    Two contracts with the same bytecode long enough to overflow the
    header share their overflow chunk leaves: the embedded tree holds
    one copy of each overflow chunk, plus per-account header leaves.
    """
    code = Bytes(b"\x01" * 4000)  # 130 chunks: 128 header, 2 overflow
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
    # Per account: basic data, code hash, and 128 header chunks. The
    # two overflow chunks are content-addressed and stored once.
    assert len(embedded._data) == 2 * (2 + 128) + 2


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
    written it: the provider treats zero as absence, mirroring the
    MPT state semantics.
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
    Re-delegating overwrites the single header chunk in place;
    un-delegating deletes it. Both leave the root of a state that
    only ever held the final code.
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


def test_deleting_an_account_removes_its_header_code_chunks() -> None:
    """
    Header code chunks are keyed by address, so the sweep that
    removes an account takes them with it; no bytecode has to be
    looked up to know how many there were.
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


def test_deleting_the_last_holder_removes_its_overflow_code() -> None:
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


def test_deleting_one_holder_keeps_shared_overflow_code() -> None:
    """
    A second account still running the bytecode keeps its chunks
    alive: they are removed only if no account in the resulting state
    has the code hash.
    """
    code = Bytes(b"\x01" * 4000)  # 130 chunks: 128 header, 2 overflow
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


def test_code_change_on_deployed_contract_is_rejected() -> None:
    """
    Replacing code whose chunks overflow the header stem is not
    protocol-reachable, since deployed code is immutable and
    delegation designators are a single chunk, and fails loudly,
    since the old overflow chunks are content-addressed and
    possibly shared.
    """
    old_code = Bytes(b"\x01" * 4000)  # overflows the header stem
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

    with pytest.raises(AssertionError):
        pre.compute_state_root(diff)


def test_random_diffs_match_flat_application_and_rebuild() -> None:
    """
    Randomized protocol-shaped diffs, covering deletions of accounts
    with and without allocated storage, delegation churn, contract
    storage writes and zeroes, and fresh deployments, produce the
    same root through incremental trie application as through
    applying the diff to the flat state and re-embedding everything.
    """
    rng = random.Random(8297)
    long_code = Bytes(bytes(range(256)) * 16)  # overflows the header

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
        # Delegating an existing EOA writes a header code chunk.
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
