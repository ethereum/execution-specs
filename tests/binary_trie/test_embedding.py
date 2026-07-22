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
    encode_basic_data,
    get_tree_key,
    get_tree_key_for_basic_data,
    get_tree_key_for_code_chunk,
    get_tree_key_for_code_hash,
    get_tree_key_for_header,
    get_tree_key_for_storage_slot,
    key_hash,
)
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
    assert len(get_tree_key_for_basic_data(ADDRESS)) == 34


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
    assert len(key) == 66
    # Storage keys carry the storage zone byte.
    assert key[0] == 0xFF


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
    assert len(key) == 34


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
