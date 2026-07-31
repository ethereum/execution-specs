"""
Tests for the embedding of state into the binary tree.
"""

import pytest
from blake3 import blake3
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U8, U32, U64, U256, Uint

from ethereum.binary_trie.embedding import (
    EMPTY_CODE_HASH,
    Address32,
    Zone,
    address20_to_address32,
    chunkify_code,
    embed_account,
    embed_storage_slot,
    encode_basic_data,
    get_tree_key,
    get_tree_key_for_basic_data,
    get_tree_key_for_code_chunk,
    get_tree_key_for_code_hash,
    get_tree_key_for_header,
    get_tree_key_for_overflow_code_chunk,
    get_tree_key_for_storage_slot,
    has_overflow_code_chunks,
    key_hash,
    remove_account,
    remove_all_storage,
    remove_code_chunks,
    remove_overflow_code_chunks,
    remove_storage_slot,
)
from ethereum.binary_trie.trie import BinaryTrie, root, trie_set
from ethereum.state import EMPTY_CODE_HASH as MPT_STATE_EMPTY_CODE_HASH

ADDRESS = Address32(b"\x00" * 12 + b"\xaa" * 20)


def _header_stem(address: Address32) -> bytes:
    """
    Build `0x00 || H(address)`, the 33-byte account header stem, from
    scratch.
    """
    return bytes([0]) + blake3(bytes(address)).digest()


def test_address20_to_address32_prepends_zeros() -> None:
    """
    Legacy addresses convert by prepending 12 zero bytes.
    """
    address = Bytes20(b"\xaa" * 20)
    expected = Address32(b"\x00" * 12 + b"\xaa" * 20)
    assert address20_to_address32(address) == expected


def test_empty_code_hash_is_keccak_of_empty() -> None:
    """
    The empty-code leaf value is the classic Keccak empty-code hash,
    and agrees with the shared MPT state module's definition.
    """
    assert EMPTY_CODE_HASH == bytes.fromhex(
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    )
    assert EMPTY_CODE_HASH == MPT_STATE_EMPTY_CODE_HASH


def test_key_hash_is_blake3() -> None:
    """
    Key derivation hashes with BLAKE3.
    """
    assert key_hash(ADDRESS) == blake3(bytes(ADDRESS)).digest()


def test_get_tree_key_concatenates_its_three_parts() -> None:
    """
    A key is the zone byte, the whole hash-derived position, and the
    sub-index byte.
    """
    digest = blake3(b"digest").digest()
    for zone in (0, 1, 2, 254, 255):
        key = get_tree_key(Zone(zone), digest, U8(7))
        assert len(key) == 34
        assert key == bytes([zone]) + digest + b"\x07"


def test_zone_wider_than_one_byte_is_unrepresentable() -> None:
    """
    A zone identifier that does not fit in the zone byte fails at
    construction: the type is one byte wide.
    """
    with pytest.raises(OverflowError):
        Zone(256)


def test_header_sub_index_wider_than_one_byte_is_rejected() -> None:
    """
    A header sub-index that does not fit the key's final byte fails
    at the narrowing to one byte inside the derivation.
    """
    with pytest.raises(OverflowError):
        get_tree_key_for_header(ADDRESS, Uint(256))


def test_header_key_vectors() -> None:
    """
    Header keys are `0x00 || H(A)` plus the leaf's sub-index,
    34 bytes in total.
    """
    stem = _header_stem(ADDRESS)

    assert get_tree_key_for_basic_data(ADDRESS) == stem + b"\x00"
    assert get_tree_key_for_code_hash(ADDRESS) == stem + b"\x01"


def test_storage_slot_in_header_vector() -> None:
    """
    EIP sub-index vector: storage slot 5 lives in the header at
    sub-index 0x45.
    """
    key = get_tree_key_for_storage_slot(ADDRESS, U256(5))
    assert key == _header_stem(ADDRESS) + bytes([0x45])


def test_storage_slot_overflow_vector() -> None:
    """
    Slot 1000 maps to tree index 3, sub-index 0xE8, with the 65-byte
    stem `0xFF || H(A) || H(A || 3)`.
    """
    prefix = blake3(bytes(ADDRESS)).digest()
    suffix = blake3(bytes(ADDRESS) + (3).to_bytes(32, "big")).digest()
    stem = bytes([255]) + prefix + suffix

    key = get_tree_key_for_storage_slot(ADDRESS, U256(1000))
    assert key == stem + bytes([0xE8])


def test_storage_slot_boundary_is_64() -> None:
    """
    Slot 63 is the last header slot and slot 64 the first overflow
    slot, landing at tree index 0, sub-index 64.
    """
    assert get_tree_key_for_storage_slot(ADDRESS, U256(63)) == _header_stem(
        ADDRESS
    ) + bytes([127])

    overflow_stem = (
        bytes([255])
        + blake3(bytes(ADDRESS)).digest()
        + blake3(bytes(ADDRESS) + (0).to_bytes(32, "big")).digest()
    )
    assert get_tree_key_for_storage_slot(
        ADDRESS, U256(64)
    ) == overflow_stem + bytes([64])


def test_code_chunk_in_header_vector() -> None:
    """
    EIP sub-index vector: code chunk 5 lives in the header at
    sub-index 0x85.
    """
    code_hash = Bytes32(blake3(b"some code").digest())

    key = get_tree_key_for_code_chunk(ADDRESS, code_hash, Uint(5))
    assert key == _header_stem(ADDRESS) + bytes([0x85])


def test_code_chunk_overflow_vector() -> None:
    """
    Chunk 300 overflows to sub-index 0xAC with the 33-byte stem
    `0x01 || H(C || 0)`.
    """
    code_hash = Bytes32(blake3(b"some code").digest())
    digest = blake3(code_hash + (0).to_bytes(32, "big")).digest()
    stem = bytes([1]) + digest

    key = get_tree_key_for_code_chunk(ADDRESS, code_hash, Uint(300))
    assert key == stem + bytes([0xAC])


def test_overflow_code_is_content_addressed() -> None:
    """
    Overflow chunks depend only on the code hash; header chunks stay
    per-account.
    """
    code_hash = Bytes32(blake3(b"shared bytecode").digest())
    other = Address32(b"\x00" * 12 + b"\xbb" * 20)

    assert get_tree_key_for_code_chunk(
        ADDRESS, code_hash, Uint(200)
    ) == get_tree_key_for_code_chunk(other, code_hash, Uint(200))
    assert get_tree_key_for_code_chunk(
        ADDRESS, code_hash, Uint(5)
    ) != get_tree_key_for_code_chunk(other, code_hash, Uint(5))


def test_chunkify_empty_code() -> None:
    """
    Empty code produces no chunks.
    """
    assert chunkify_code(Bytes(b"")) == []


def test_chunkify_code_without_pushes_pads_to_31_bytes() -> None:
    """
    Code shorter than a chunk is zero-padded to 31 bytes.
    """
    code = Bytes(b"\x01\x02\x03")  # ADD MUL SUB

    chunks = chunkify_code(code)

    # The leading byte is the push-data offset count (zero here), not
    # padding; only the trailing zeros pad the code to 31 bytes.
    assert chunks == [Bytes32(b"\x00" + code + b"\x00" * 28)]


def test_chunkify_code_eip_example() -> None:
    """
    EIP example: push data spanning a chunk boundary is recorded in
    the second chunk's leading byte.
    """
    # `...PUSH4 99 98 | 97 96 PUSH1 128 MSTORE...` where `|` begins a
    # new chunk; the second chunk records that its first 2 bytes are
    # push data.
    push4 = 0x63
    push1 = 0x60
    mstore = 0x52
    code = Bytes(
        b"\x00" * 28 + bytes([push4, 99, 98, 97, 96, push1, 128, mstore])
    )

    chunks = chunkify_code(code)

    assert len(chunks) == 2
    assert chunks[0] == Bytes32(b"\x00" * 29 + bytes([push4, 99, 98]))
    assert chunks[1] == Bytes32(
        bytes([2, 97, 96, push1, 128, mstore]) + b"\x00" * 26
    )


def test_chunkify_code_caps_leading_push_data_count_at_31() -> None:
    """
    A chunk consisting entirely of push data reports 31 leading push
    data bytes, the chunk-payload maximum, rather than 32.
    """
    push32 = 0x7F
    push_data = bytes(range(1, 33))
    code = Bytes(b"\x00" * 30 + bytes([push32]) + push_data)

    chunks = chunkify_code(code)

    assert len(chunks) == 3
    assert chunks[0] == Bytes32(b"\x00" * 31 + bytes([push32]))
    assert chunks[1] == Bytes32(bytes([31]) + push_data[:31])
    assert chunks[2] == Bytes32(bytes([1]) + push_data[31:] + b"\x00" * 30)


def test_chunkify_code_push_data_truncated_by_end_of_code() -> None:
    """
    A push instruction with its data cut off by the end of the code
    still chunks cleanly.
    """
    push32 = 0x7F
    code = Bytes(bytes([push32]))

    chunks = chunkify_code(code)

    assert chunks == [Bytes32(b"\x00" + bytes([push32]) + b"\x00" * 30)]


def test_encode_basic_data_layout() -> None:
    """
    Basic data packs version, code size, nonce, and balance at the
    offsets given by the EIP.
    """
    code_size_hex = "11223344"
    nonce_hex = "5566778899aabbcc"
    balance_hex = "0123456789abcdef0123456789abcdef"

    value = encode_basic_data(
        code_size=U32(int(code_size_hex, 16)),
        nonce=U64(int(nonce_hex, 16)),
        balance=U256(int(balance_hex, 16)),
    )

    assert len(value) == 32
    assert value[0] == 0  # version
    assert value[1:4] == b"\x00" * 3  # reserved
    assert value[4:8] == bytes.fromhex(code_size_hex)
    assert value[8:16] == bytes.fromhex(nonce_hex)
    assert value[16:32] == bytes.fromhex(balance_hex)


def test_encode_basic_data_rejects_balance_past_sixteen_bytes() -> None:
    """
    A balance that does not fit the sixteen-byte field is rejected,
    rather than silently truncated by `to_bytes`.
    """
    with pytest.raises(AssertionError):
        encode_basic_data(
            code_size=U32(0),
            nonce=U64(0),
            balance=U256(2) ** U256(128),
        )


OTHER_ADDRESS = Address32(b"\x00" * 12 + b"\xbb" * 20)


def test_remove_account_restores_prior_root() -> None:
    """
    Removing a bare account deletes exactly its two header leaves,
    restoring the commitment to what it was before the account was
    embedded.
    """
    trie = BinaryTrie()
    embed_account(
        trie, OTHER_ADDRESS, U64(1), U256(5), EMPTY_CODE_HASH, Bytes(b"")
    )
    before = root(trie)

    embed_account(trie, ADDRESS, U64(2), U256(9), EMPTY_CODE_HASH, Bytes(b""))
    assert root(trie) != before
    remove_account(trie, ADDRESS)
    assert root(trie) == before


def test_remove_account_takes_code_chunks_and_storage_with_it() -> None:
    """
    An account owns its header stem and its overflow storage
    subtree, so removing it undoes everything embedding it wrote,
    header code chunks and storage on both sides of the header
    boundary included, without being told which slots it held.
    """
    code = Bytes(b"\x01" * 40)  # two header chunks
    code_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    embed_account(
        trie, OTHER_ADDRESS, U64(1), U256(5), EMPTY_CODE_HASH, Bytes(b"")
    )
    before = root(trie)

    embed_account(trie, ADDRESS, U64(2), U256(9), code_hash, code)
    for slot in (U256(0), U256(63), U256(64), U256(1000), U256(2**200)):
        embed_storage_slot(trie, ADDRESS, slot, Bytes32(b"\x07" * 32))
    assert root(trie) != before

    remove_account(trie, ADDRESS)
    assert root(trie) == before


def test_remove_account_never_reaches_the_code_zone() -> None:
    """
    The sweep covers the account and storage zones only, so a
    neighbour's content-addressed overflow chunks are untouched by
    a removal beside them.
    """
    long_code = Bytes(b"\x01" * 4000)  # 130 chunks: 128 header, 2 overflow
    long_hash = Bytes32(b"\x33" * 32)
    short_code = Bytes(b"\x02" * 40)  # two header chunks
    short_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    embed_account(trie, OTHER_ADDRESS, U64(1), U256(5), long_hash, long_code)
    before = root(trie)

    embed_account(trie, ADDRESS, U64(2), U256(9), short_hash, short_code)
    remove_account(trie, ADDRESS)

    assert root(trie) == before
    for chunk_id in (Uint(128), Uint(129)):
        key = get_tree_key_for_code_chunk(OTHER_ADDRESS, long_hash, chunk_id)
        assert key in trie._data


def test_remove_account_leaves_overflow_code_for_the_caller() -> None:
    """
    Removing an account never takes content-addressed chunks with
    it: whether they may go depends on the resulting state, which
    the embedding cannot see. They are dropped separately, once the
    caller has established nothing else runs the code.
    """
    code = Bytes(b"\x01" * 4000)  # 130 chunks: 128 header, 2 overflow
    code_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    empty = root(trie)
    embed_account(trie, ADDRESS, U64(1), U256(5), code_hash, code)
    assert has_overflow_code_chunks(trie, code_hash)

    remove_account(trie, ADDRESS)

    overflow = [
        get_tree_key_for_overflow_code_chunk(code_hash, chunk_id)
        for chunk_id in (Uint(128), Uint(129))
    ]
    assert sorted(trie._data) == sorted(overflow)

    remove_overflow_code_chunks(trie, code_hash, code)
    assert root(trie) == empty
    assert not has_overflow_code_chunks(trie, code_hash)


def test_remove_overflow_code_chunks_spares_the_header() -> None:
    """
    Header chunks are keyed per account and go with the account, so
    dropping a code's shared leaves leaves an account still holding
    it otherwise intact.
    """
    code = Bytes(b"\x01" * 4000)
    code_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    embed_account(trie, ADDRESS, U64(1), U256(5), code_hash, code)

    remove_overflow_code_chunks(trie, code_hash, code)

    for chunk_id in (Uint(0), Uint(127)):
        key = get_tree_key_for_code_chunk(ADDRESS, code_hash, chunk_id)
        assert key in trie._data
    assert get_tree_key_for_basic_data(ADDRESS) in trie._data


def test_all_zero_basic_data_is_absent_from_the_tree() -> None:
    """
    Zero resolves to absence over the whole value space, basic data
    included: an account with zero nonce, zero balance and no code
    packs to 32 zero bytes, since the version and reserved bytes are
    zero too. Its code hash leaf still distinguishes it from an
    account that is not there at all.
    """
    trie = BinaryTrie()
    embed_account(trie, ADDRESS, U64(0), U256(0), EMPTY_CODE_HASH, Bytes(b""))

    assert encode_basic_data(
        code_size=U32(0), nonce=U64(0), balance=U256(0)
    ) == Bytes32(b"\x00" * 32)
    assert get_tree_key_for_basic_data(ADDRESS) not in trie._data
    assert trie._data[get_tree_key_for_code_hash(ADDRESS)] == EMPTY_CODE_HASH


def test_emptying_basic_data_removes_its_leaf() -> None:
    """
    The rule applies to updates as well as fresh writes: an account
    drained to zero nonce and balance loses the leaf rather than
    keeping a zero-valued one, landing on the commitment of a state
    where it was always zero.
    """
    fresh = BinaryTrie()
    embed_account(fresh, ADDRESS, U64(0), U256(0), EMPTY_CODE_HASH, Bytes(b""))

    drained = BinaryTrie()
    embed_account(
        drained, ADDRESS, U64(3), U256(99), EMPTY_CODE_HASH, Bytes(b"")
    )
    assert root(drained) != root(fresh)

    embed_account(
        drained, ADDRESS, U64(0), U256(0), EMPTY_CODE_HASH, Bytes(b"")
    )
    assert root(drained) == root(fresh)


def test_zero_code_chunks_are_absent_from_the_tree() -> None:
    """
    A chunk of 31 zero bytes encodes to 32 zero bytes and is left
    absent like any other zero value, so chunk presence does not
    delimit the code.
    """
    code = Bytes(b"\x00" * 62)  # two chunks, both entirely zero
    code_hash = Bytes32(b"\x22" * 32)

    assert chunkify_code(code) == [Bytes32(b"\x00" * 32)] * 2

    trie = BinaryTrie()
    embed_account(trie, ADDRESS, U64(1), U256(5), code_hash, code)

    for chunk_id in (Uint(0), Uint(1)):
        key = get_tree_key_for_code_chunk(ADDRESS, code_hash, chunk_id)
        assert key not in trie._data
    # The account is still distinguished from one with no code.
    assert trie._data[get_tree_key_for_code_hash(ADDRESS)] == code_hash


def test_remove_all_storage_keeps_the_account_and_its_code() -> None:
    """
    A storage wipe straddles the header boundary: slots `0`-`63`
    share the header stem with the basic data and code chunks that
    must survive, while the rest live in the overflow subtree.
    """
    code = Bytes(b"\x01" * 40)
    code_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    embed_account(trie, ADDRESS, U64(1), U256(9), code_hash, code)
    before = root(trie)

    for slot in (U256(0), U256(63), U256(64), U256(1000), U256(2**200)):
        embed_storage_slot(trie, ADDRESS, slot, Bytes32(b"\x07" * 32))
    assert root(trie) != before

    remove_all_storage(trie, ADDRESS)
    assert root(trie) == before


def test_embed_and_remove_storage_slot_roundtrip() -> None:
    """
    A header slot and an overflow slot each embed as one leaf, and
    removing them restores the prior commitment.
    """
    trie = BinaryTrie()
    embed_account(trie, ADDRESS, U64(1), U256(1), EMPTY_CODE_HASH, Bytes(b""))
    before = root(trie)

    embed_storage_slot(trie, ADDRESS, U256(1), Bytes32(b"\x07" * 32))
    embed_storage_slot(trie, ADDRESS, U256(1000), Bytes32(b"\x09" * 32))
    assert root(trie) != before

    remove_storage_slot(trie, ADDRESS, U256(1))
    remove_storage_slot(trie, ADDRESS, U256(1000))
    assert root(trie) == before


def test_remove_code_chunks_leaves_the_other_header_leaves() -> None:
    """
    Sweeping the header code range deletes every chunk leaf and
    nothing else: the account's basic data and code hash leaves
    remain.
    """
    code = Bytes(b"\x01" * 40)  # two header chunks
    code_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    embed_account(trie, ADDRESS, U64(1), U256(0), code_hash, code)
    remove_code_chunks(trie, ADDRESS, code_hash)

    expected = BinaryTrie()
    trie_set(
        expected,
        get_tree_key_for_basic_data(ADDRESS),
        encode_basic_data(code_size=U32(40), nonce=U64(1), balance=U256(0)),
    )
    trie_set(expected, get_tree_key_for_code_hash(ADDRESS), code_hash)
    assert root(trie) == root(expected)
