"""
Tests for `ethereum.state_pbt`.

The first group covers `embed_flat_state`: each kind of state
(account fields, code chunks, storage slots) must land in the tree
as exactly the expected leaves, with expected keys and values built
by hand from the derivation functions. The `embed_state` helper
adapts an MPT-backed `State` into the flat mappings the walk takes,
so the inputs are real account objects.

The second group covers the provider: `compute_state_root` applies
a block diff (deletions, zero-writes, freshly deployed code) and
embeds the result. Two of its six tests check the resulting root
against a post-state built directly in the MPT-backed container; the
other four check it against a known invariant instead (the empty
root, a zero-write matching a never-written slot, and so on).

Later groups pin exact key sets (rebuilt from raw `blake3` and
literal zone/sub-index bytes, never the derivation functions under
test), the BASIC_DATA leaf's byte layout, and further provider
semantics: `storage_clears` ordering, account-delete/storage-orphan
interactions, the asymmetry between `set_account` and the diff
path, pre-state immutability, sequential diffs, and the storage
sub-index boundaries. Rebuilding keys independently, rather than by
calling the derivation functions under test, means a wrong key that
still produces the right leaf count -- a swapped zone byte, an
off-by-one sub-index -- is still caught; a leaf count alone would
miss it.

EIP-8297's "Zero values and deletion" section is normative today:
"a zero-valued leaf is distinct from an absent key, committing to a
different root," and "removing entries is reserved for a future
state-expiry mechanism." This module's `State` does the opposite --
zero-write deletes the slot, and deleting an account drops its
storage outright (disclosed in `state_pbt.py`'s own module
docstring) -- so every root-equality and deletion assertion below
pins this provider's current behavior, not EIP-8297 conformance. If
`state_pbt` is ever made conformant, the roots pinned here must be
regenerated. `tests/binary_trie/test_trie.py::test_zero_value_is_not_absence`
is the one conformant test in this tree: the raw `BinaryTrie` does
keep a zero-valued leaf; only this provider layer removes it.
"""

import pytest
from blake3 import blake3
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

    Not EIP-8297-conformant (see the module docstring): the zeroed
    slot and the deleted account's storage both pin current provider
    behavior, not the EIP's own zero/deletion semantics.
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

    Not EIP-8297-conformant (see the module docstring): this pins
    current provider behavior -- dropping a deleted account's storage
    outright -- not the EIP's own zero/deletion semantics.
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

    That match with MPT is exactly what is not EIP-8297-conformant
    (see the module docstring): the pinned root equality here is
    current provider behavior, not the EIP's own zero/deletion
    semantics.
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


def _code_overflow_stem(code_hash: bytes, tree_index: int) -> bytes:
    """
    Build a 33-byte overflow code stem from scratch.

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

    Code spanning 129 chunks (`31 * 129 = 3999` bytes) puts chunks
    0-127 in the header and chunk 128 in the code zone; storage at
    slots 63, 64, and 256 puts one slot in the header and two in the
    storage zone, each its own overflow group. The expected keys are
    rebuilt from raw `blake3` and literal zone/sub-index bytes, never
    by calling the embedding's own derivation, so a swapped zone byte
    or an off-by-one sub-index would be caught here even though it
    cannot change a leaf count.
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
        header_stem + bytes([128 + chunk_id]) for chunk_id in range(128)
    }
    expected_keys.add(_code_overflow_stem(code_hash, 0) + bytes([0]))
    expected_keys.add(_storage_overflow_stem(address32, 0) + bytes([64]))
    expected_keys.add(_storage_overflow_stem(address32, 1) + bytes([0]))

    assert set(embedded._data.keys()) == expected_keys
    assert all(len(key) in (34, 66) for key in expected_keys)


def test_embedded_state_root_is_pinned() -> None:
    """
    The same crafted state as `test_embedded_key_set_for_a_crafted_contract`
    -- one contract whose 129-chunk code and slots 63/64/256 exercise
    every sub-index boundary the embedding defines -- commits to a
    hardcoded root hash.

    This is a deliberate change-detector for the hash function, node
    tags, prefix encoding, and the embedding built on top of them, in
    the same spirit as `test_trie.py::test_fixed_trie_root_is_pinned`
    (which pins a root over a raw, hand-built trie rather than a state
    that went through `embed_flat_state`): the EIP's hash choice is
    explicitly not final, and this test is meant to fail loudly the
    moment any of the above changes. Every other root assertion in
    this module compares two roots the code itself computed --
    `root(embedded) == root(expected)`, or against `EMPTY_TRIE_ROOT` --
    so a systematic, but still fully deterministic, bug in the hash
    function or merkleization would move both sides identically and
    pass unnoticed there; only a hardcoded value, pinned from a
    known-good run, can catch that. To regenerate the constant after a
    deliberate, reviewed change: print `root(embedded).hex()` for this
    same state and paste the new value below.
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
        "f38237c7932ace841cf21fc94a6a715b4c88494285ffbe5703c1828054b0433d"
    )


def test_embedded_key_set_for_a_fully_occupied_header_stem() -> None:
    """
    An account with 64 header storage slots and 128 header code
    chunks fills every header sub-index this embedding can ever
    populate, and embeds to exactly that key set with no overflow-zone
    key at all.

    `31 * 128 = 3968` bytes of code fills header chunks 0-127
    (sub-indices 128-255) without spilling into the code zone;
    storage slots 0-63 fill header slots 0-63 (sub-indices 64-127)
    without spilling into the storage zone. Together with basic data
    (sub-index 0) and the code hash (sub-index 1), this is the
    maximum-occupancy case the EIP's `STEM_SUBTREE_WIDTH > CODE_OFFSET
    > HEADER_STORAGE_OFFSET` invariant exists to protect -- today's
    `test_embedded_key_set_for_a_crafted_contract` reaches only 131 of
    the 256 possible sub-indices.

    The full 256 is unreachable by any account: sub-indices 2-63 are
    never assigned to anything by this embedding (`HEADER_STORAGE_OFFSET
    = 64` leaves them permanently between the code hash at 1 and the
    first header storage slot at 64), so the true maximum is 194, and
    the expected set below is exactly `{0, 1} | set(range(64, 256))`,
    not `set(range(256))`.
    """
    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    code = Bytes(b"\x01" * (31 * 128))
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

    assert header_sub_indices == {0, 1} | set(range(64, 256))
    assert embedded._data.keys() == header_keys, (
        "a fully-occupied header stem must produce no overflow-zone key"
    )


def test_header_code_chunks_are_per_account_while_overflow_is_shared() -> None:
    """
    Two accounts with identical 129-chunk code are disjoint on
    header chunk keys but share their one overflow chunk key.

    Pins this by KEY, not leaf count: per-account header chunks
    (sub-indices 128-255 under each account's own header stem) must
    never collide between the two accounts, while the single chunk
    that overflows the header (chunk 128) must land on the exact
    same content-addressed key for both, so the tree stores it once.
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
    header_chunk_keys_a = {
        stem_a + bytes([128 + chunk_id]) for chunk_id in range(128)
    }
    header_chunk_keys_b = {
        stem_b + bytes([128 + chunk_id]) for chunk_id in range(128)
    }

    assert header_chunk_keys_a.isdisjoint(header_chunk_keys_b)
    assert header_chunk_keys_a <= set(embedded._data.keys())
    assert header_chunk_keys_b <= set(embedded._data.keys())

    overflow_key = _code_overflow_stem(code_hash, 0) + bytes([0])
    code_zone_keys = {key for key in embedded._data if key[0] == 1}
    assert code_zone_keys == {overflow_key}


def _code_chunk_filler_byte(chunk_id: int) -> int:
    """
    Map a chunk index to a filler byte, distinct per chunk and never
    in the `PUSH1`..`PUSH32` range (0x60-0x7F).

    Below 0x60 the byte is the chunk index itself; from 0x60 up it is
    shifted by 32 to jump clear over the push range entirely. Both
    branches stay injective and never collide with each other's
    output range (the first tops out at 0x5F, the second starts at
    0x80), so distinct chunk ids always get distinct filler bytes.
    """
    return chunk_id if chunk_id <= 0x5F else chunk_id + 32


def test_chunk_values_are_distinct_across_the_header_overflow_boundary() -> (
    None
):
    r"""
    Chunks 126-129, each filled with its own distinct byte, get their
    exact 32-byte values pinned by rebuilt key: the header's last two
    chunks (126, 127) and the overflow zone's first two (128, 129) --
    covering the one boundary in EIP-8297 where the zone byte changes
    from `ACCOUNT_ZONE` to `CODE_ZONE` and keying switches from
    address-derived to content-addressed.

    Every other coverage of this boundary in this suite (this module's
    own `test_embedded_key_set_for_a_crafted_contract` and
    `test_header_code_chunks_are_per_account_while_overflow_is_shared`,
    and `test_embedding.py`'s `test_code_chunk_key_matrix`) builds code
    as `b"\\x01" * N`, so chunk 127 and chunk 128 hold identical bytes
    and are interchangeable: before this test, swapping their stored
    values inside `embed_flat_state` passed every one of those tests,
    and indeed the entire suite, key-set assertions included. Filling
    chunk `i` with
    `_code_chunk_filler_byte(i)` keeps every filler byte outside the
    `PUSH1`..`PUSH32` range, so `chunkify_code` reports a leading
    push-data-count byte of 0 for every chunk (nothing carries over
    from a previous chunk when no byte anywhere is a push opcode), and
    each chunk's expected value is trivially `0x00` followed by 31
    repeats of its own filler byte.
    """
    address32 = b"\x00" * 12 + bytes(ADDRESS_A)
    chunk_count = 130  # chunks 0..129: 31 * 130 = 4030, well under
    # MAX_CODE_SIZE, and comfortably covers chunks 126-129.
    code = Bytes(
        b"".join(
            bytes([_code_chunk_filler_byte(i)]) * 31
            for i in range(chunk_count)
        )
    )
    assert len(code) == 31 * chunk_count == 4030

    state = State()
    code_hash = store_code(state, code)
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )

    trie = embed_flat_state(state._accounts, state._storage, state.get_code)

    header_stem = _account_header_stem(address32)
    overflow_stem = _code_overflow_stem(code_hash, 0)

    def expected_chunk(chunk_id: int) -> Bytes32:
        filler = bytes([_code_chunk_filler_byte(chunk_id)])
        return Bytes32(bytes([0]) + filler * 31)

    # Chunks 0-127 live in the header at sub-index 128 + chunk_id;
    # chunk 128 is the first content-addressed overflow chunk, at
    # sub-index 0 of tree index 0; chunk 129 is the next, sub-index 1.
    assert trie._data[header_stem + bytes([128 + 126])] == expected_chunk(126)
    assert trie._data[header_stem + bytes([128 + 127])] == expected_chunk(127)
    assert trie._data[overflow_stem + bytes([0])] == expected_chunk(128)
    assert trie._data[overflow_stem + bytes([1])] == expected_chunk(129)


def test_basic_data_leaf_bytes_carry_code_size_nonce_and_balance() -> None:
    """
    The BASIC_DATA leaf's 32 bytes pack the resolved code's length,
    not any field stored on `Account` itself.

    `Account` has no `code_size` field, so reading the leaf back out
    by its independently rebuilt key and checking it byte range by
    byte range is proof the provider derives the size from
    `get_code(code_hash)` at embed time, not from anything cached.
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


def test_balance_at_or_above_the_sixteen_byte_field_fails_at_root_time() -> (
    None
):
    """
    A balance of exactly `2**128` crashes `state_root` with an
    `AssertionError` instead of being rejected when it is set.

    `Account.balance` is a full `U256`; nothing between `set_account`
    and `encode_basic_data`'s own bounds assertion enforces the
    sixteen-byte field EIP-8297 packs it into. There is no
    protocol-level cap on balance today, so an over-cap value crashes
    root computation rather than invalidating the block at the point
    it was set — a known spec gap being pinned here, not endorsed.
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

    with pytest.raises(AssertionError):
        state_root(state)


def test_empty_code_contract_embeds_like_an_eoa() -> None:
    """
    A contract account whose code is explicitly `b""`, stored through
    `store_code` rather than merely defaulted, embeds identically to
    an EOA: exactly the two header leaves and no code chunk leaves.

    Distinct from `test_eoa_embeds_basic_data_and_code_hash_leaves`,
    which never calls `store_code` at all; this pins that routing
    empty bytes through the store still resolves to `EMPTY_CODE_HASH`
    and that `chunkify_code(b"") == []` leaves no chunk leaf behind.
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
    20-byte address, 23 bytes total) embeds as a single header code
    chunk: short enough to need no overflow, and starting with no
    push opcode so its chunk's leading byte is 0.
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
    chunk_key = header_stem + bytes([128])

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
    An account whose `code_hash` was never stored raises `KeyError`
    when the root is computed, because `embed_flat_state` resolves
    every account's code through `get_code` to size it.

    Only `EMPTY_CODE_HASH` needs no store entry; any other hash that
    was never handed to `store_code` (or `code_changes`) is missing
    from `_code_store` and `get_code` raises directly.
    """
    state = State()
    unknown_hash = keccak256(b"never stored")
    set_account(
        state,
        ADDRESS_A,
        Account(nonce=Uint(1), balance=U256(0), code_hash=unknown_hash),
    )

    assert state.get_code(EMPTY_CODE_HASH) == b""
    with pytest.raises(KeyError):
        state.get_code(unknown_hash)
    with pytest.raises(KeyError):
        state_root(state)


def test_storage_clears_removes_slots_before_other_changes() -> None:
    """
    `storage_clears` empties an address's storage before
    `storage_changes` is applied: a pre-existing slot is cleared like
    any other, while a brand-new key written by the same diff still
    lands with its new value.

    Several pre-EIP-6780 forks (frontier through shanghai) still
    populate `storage_clears` in their own trackers, and
    `state_mpt`'s `apply_changes_to_state` consumes it too — but
    none of them use `state_pbt`. `binary_tree`, the only fork wired
    to this provider, copies Amsterdam's `extract_block_diff`, which
    never sets the field: EIP-6780 removed the full-storage-wipe
    `SELFDESTRUCT` semantics that motivated it. So this branch is
    reachable only from unit tests today; pinning it keeps the
    provider honest in case a pre-Cancun-style tracker is ever wired
    up to it.
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

    `tests/binary_trie/test_differential_mpt.py`'s
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


def test_storage_written_for_a_deleted_account_is_orphaned_but_not_embedded() -> (  # noqa: E501
    None
):
    """
    A diff that deletes an account and writes to its storage in the
    same step leaves an orphaned storage entry that never reaches the
    tree.

    The account is gone, but `storage_changes`'s `setdefault`
    recreates `_storage[A]` after the delete popped it, so
    `account_has_storage` reads back `True` for an address with no
    account. `embed_flat_state` skips storage for addresses missing
    from `accounts`, so the orphan is invisible to the root: it
    matches a state that never had `A` at all, alongside an unrelated
    account that did.

    Not EIP-8297-conformant (see the module docstring): the
    account-deletion-drops-storage behavior this relies on pins
    current provider behavior, not the EIP's own semantics.
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
    assert state.account_has_storage(ADDRESS_A) is True

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
    state that was never written to.

    Not EIP-8297-conformant (see the module docstring): this pins
    current provider behavior, not the EIP's own zero/deletion
    semantics.
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

    Not EIP-8297-conformant (see the module docstring): this pins
    current provider behavior, not the EIP's own zero/deletion
    semantics.
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

    Rebuilt here from raw `blake3` and literal zone/sub-index bytes
    rather than by calling `get_tree_key_for_storage_slot`. Slots 64
    and 255 share one overflow stem (tree index 0); the other two
    each open their own. Each slot gets its own distinct value
    (`index + 1`), so a swap between any two of the six leaves is
    detectable: mutating all header storage leaf values, or all
    overflow storage leaf values, inside `embed_flat_state` used to be
    caught only by `test_contract_embeds_chunks_and_storage_slots`
    (slots 1 and 100, neither near a boundary) -- every boundary-
    focused test, this one included until now, asserted key sets only.
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
