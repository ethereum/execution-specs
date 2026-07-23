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
    embed_flat_state,
    set_account,
    set_storage,
    state_root,
    store_code,
)

ADDRESS_A = Bytes20(b"\xaa" * 20)
ADDRESS_B = Bytes20(b"\xbb" * 20)


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
    Deleting the last account leaves the empty tree commitment.
    """
    state = State()
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(1), code_hash=EMPTY_CODE_HASH),
    )
    set_storage(state, ADDRESS_A, Bytes32(U256(3).to_be_bytes32()), U256(4))

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
