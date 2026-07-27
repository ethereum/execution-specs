"""
Tests for the embedding of state into the binary tree.
"""

from typing import List

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

CODE_HASH = Bytes32(blake3(b"some code").digest())


def _header_stem(address: Address32) -> bytes:
    """
    Build `0x00 || H(address)`, the 33-byte account header stem, from
    scratch.
    """
    return bytes([0]) + blake3(bytes(address)).digest()


def _storage_overflow_key(
    address: Address32, tree_index_bytes: bytes, sub_index: int
) -> bytes:
    """
    Build `0xFF || H(A) || H(A || tree_index_bytes) || sub_index`,
    the 66-byte overflow storage key, from scratch.
    """
    prefix = blake3(bytes(address)).digest()
    suffix = blake3(bytes(address) + tree_index_bytes).digest()
    return bytes([255]) + prefix + suffix + bytes([sub_index])


def _code_overflow_key(
    code_hash: Bytes32, tree_index_bytes: bytes, sub_index: int
) -> bytes:
    """
    Build `0x01 || H(C || tree_index_bytes) || sub_index`, the
    34-byte overflow code-chunk key, from scratch.
    """
    digest = blake3(bytes(code_hash) + tree_index_bytes).digest()
    return bytes([1]) + digest + bytes([sub_index])


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


@pytest.mark.parametrize(
    "slot",
    [
        pytest.param(0, id="slot-0-header-first"),
        pytest.param(1, id="slot-1-header"),
        pytest.param(62, id="slot-62-header-last-but-one"),
        pytest.param(65, id="slot-65-overflow-group-0"),
        pytest.param(255, id="slot-255-group-0-last"),
        pytest.param(256, id="slot-256-group-1-first"),
        pytest.param(257, id="slot-257-group-1"),
        pytest.param(511, id="slot-511-group-1-last"),
        pytest.param(512, id="slot-512-group-2-first"),
        pytest.param(2**32, id="slot-2-32"),
        pytest.param(2**256 - 1, id="slot-max-u256"),
    ],
)
def test_storage_slot_key_matrix(slot: int) -> None:
    """
    A matrix of storage slots rebuilds each expected key from
    scratch, header form below 64 and overflow form at and above it.

    The overflow cases cross every group rollover in range: 255 is
    group 0's last sub-index, 256 opens group 1 at sub-index 0, 511
    is group 1's last sub-index, and 512 opens group 2.
    """
    if slot < 64:
        expected = _header_stem(ADDRESS) + bytes([64 + slot])
        expected_length = 34
    else:
        tree_index = slot // 256
        sub_index = slot % 256
        expected = _storage_overflow_key(
            ADDRESS, tree_index.to_bytes(32, "big"), sub_index
        )
        expected_length = 66

    key = get_tree_key_for_storage_slot(ADDRESS, U256(slot))

    assert key == expected
    assert len(key) == expected_length


def test_storage_group_zero_never_uses_low_sub_indices() -> None:
    """
    Group 0 of the storage zone is short.

    Slots 0 through 63 stay in the account header, so group 0's
    overflow leaves cover only sub-indices 64 through 255 -- 192
    slots rather than the 256 every later group has. Every overflow
    key derived from a group-0 slot must therefore end in a byte of
    at least 64.
    """
    group_zero_slots = 0
    for slot in range(64, 1001):
        if slot // 256 != 0:
            continue
        group_zero_slots += 1
        key = get_tree_key_for_storage_slot(ADDRESS, U256(slot))
        assert key[-1] >= 64, (
            f"slot {slot}: group-0 overflow key ends in {key[-1]}, "
            "below the 64 floor"
        )
    assert group_zero_slots == 192


def test_storage_tree_index_is_a_32_byte_big_endian_suffix() -> None:
    """
    The overflow position's group half hashes the tree index as a
    full 32-byte big-endian integer, not some narrower width.

    Encoding the same tree index over only 8 bytes changes the hash
    input and therefore the key, so a future narrowing regression
    would be caught here.
    """
    slot = 256 * 5
    tree_index = slot // 256
    sub_index = slot % 256
    assert tree_index == 5

    key = get_tree_key_for_storage_slot(ADDRESS, U256(slot))
    wide_key = _storage_overflow_key(
        ADDRESS, tree_index.to_bytes(32, "big"), sub_index
    )
    narrow_key = _storage_overflow_key(
        ADDRESS, tree_index.to_bytes(8, "big"), sub_index
    )

    assert key == wide_key
    assert key != narrow_key


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


@pytest.mark.parametrize(
    "chunk_id",
    [
        pytest.param(0, id="chunk-0-header-first"),
        pytest.param(126, id="chunk-126-header"),
        pytest.param(127, id="chunk-127-header-last"),
        pytest.param(128, id="chunk-128-overflow-group-0-first"),
        pytest.param(129, id="chunk-129-overflow-group-0"),
        pytest.param(383, id="chunk-383-overflow-group-0-last"),
        pytest.param(384, id="chunk-384-overflow-group-1-first"),
        pytest.param(385, id="chunk-385-overflow-group-1"),
    ],
)
def test_code_chunk_key_matrix(chunk_id: int) -> None:
    """
    A matrix of code chunk ids rebuilds each expected key from
    scratch, header form below 128 and content-addressed overflow
    form at and above it.

    Both forms are 34 bytes, but the zone byte switches from
    `ACCOUNT_ZONE` (0) to `CODE_ZONE` (1) exactly at the 127 -> 128
    boundary.
    """
    if chunk_id < 128:
        expected = _header_stem(ADDRESS) + bytes([128 + chunk_id])
        expected_zone = 0
    else:
        overflow = chunk_id - 128
        tree_index = overflow // 256
        sub_index = overflow % 256
        expected = _code_overflow_key(
            CODE_HASH, tree_index.to_bytes(32, "big"), sub_index
        )
        expected_zone = 1

    key = get_tree_key_for_code_chunk(ADDRESS, CODE_HASH, Uint(chunk_id))

    assert key == expected
    assert len(key) == 34
    assert key[0] == expected_zone


def test_max_code_size_chunk_keys() -> None:
    """
    `MAX_CODE_SIZE` (0x10000 = 65536 bytes, defined in
    `ethereum.forks.binary_tree.vm.interpreter`) chunkifies into
    `ceil(65536 / 31) == 2115` chunks.

    The last chunk, id 2114, is well past the 128-chunk header and
    lands in the code zone at group 7, sub-index 194; the
    group/sub-index are computed here from the EIP formula, with the
    concrete numbers also asserted so the arithmetic stays pinned.
    """
    max_code_size = 0x10000
    chunk_count = (max_code_size + 30) // 31
    assert chunk_count == 2115

    last_chunk_id = chunk_count - 1
    overflow = last_chunk_id - 128
    tree_index = overflow // 256
    sub_index = overflow % 256
    assert (tree_index, sub_index) == (7, 194)

    key = get_tree_key_for_code_chunk(ADDRESS, CODE_HASH, Uint(last_chunk_id))
    expected = _code_overflow_key(
        CODE_HASH, tree_index.to_bytes(32, "big"), sub_index
    )

    assert key == expected
    assert len(key) == 34


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


def _reference_chunkify(code: bytes) -> List[bytes]:
    """
    Chunkify `code` with an independent reimplementation.

    A direct transcription of EIP-8297's own `chunkify_code`
    pseudocode, kept separate from `chunkify_code` so the two can be
    cross-checked: same structure, but the EIP text's own variable
    names (`bytes_to_exec_data`, `pos`, `x`, `pushdata_bytes`, and
    `pos` reused as the closing comprehension's loop variable), not
    `chunkify_code`'s (`remaining_push_data`, `position`, `offset`,
    `push_data_bytes`, `start`).
    """
    push_offset = 95
    push1 = push_offset + 1
    push32 = push_offset + 32

    if len(code) % 31 != 0:
        code = code + b"\x00" * (31 - (len(code) % 31))
    bytes_to_exec_data = [0] * (len(code) + 32)
    pos = 0
    while pos < len(code):
        if push1 <= code[pos] <= push32:
            pushdata_bytes = code[pos] - push_offset
        else:
            pushdata_bytes = 0
        pos += 1
        for x in range(pushdata_bytes):
            bytes_to_exec_data[pos + x] = pushdata_bytes - x
        pos += pushdata_bytes
    return [
        bytes([min(bytes_to_exec_data[pos], 31)]) + code[pos : pos + 31]
        for pos in range(0, len(code), 31)
    ]


def test_chunkify_push0_is_not_push_data() -> None:
    """
    `PUSH0` (0x5F) carries no push data.

    `PUSH_OFFSET` (95) sits one below `PUSH1` (96), so the `PUSH1`
    through `PUSH32` range (96 through 127) deliberately excludes
    `PUSH0`; a run of `PUSH0` bytes therefore chunkifies as plain
    non-push code, every chunk's leading byte staying 0.
    """
    code = Bytes(b"\x5f" * 40)

    chunks = chunkify_code(code)

    assert len(chunks) == 2
    for chunk in chunks:
        assert chunk[0] == 0


def test_chunkify_push_data_overhanging_into_padding() -> None:
    """
    Padding happens before the push-data scan, so a push instruction
    truncated by the end of the code can have its declared data
    overhang into the padding.

    `PUSH32` demands 32 data bytes but this 32-byte code (opcode
    plus 31 data bytes) supplies only 31, so the scan -- which runs
    over the already-padded buffer -- counts the first zero padding
    byte as the push's 32nd data byte too. Chunk 1's leading byte is
    therefore 2 (the last real data byte plus that one padding
    byte), one short of what an un-truncated `PUSH32` would leave.
    """
    push32 = 0x7F
    data = bytes(range(1, 32))  # 31 bytes: 1, 2, ..., 31
    code = Bytes(bytes([push32]) + data)
    assert len(code) == 32

    chunks = chunkify_code(code)

    assert len(chunks) == 2
    # The PUSH32 opcode itself is not push data.
    assert chunks[0] == Bytes32(bytes([0, push32]) + data[:30])
    # Byte 31 (last real data byte) and byte 32 (first padding byte)
    # both count as carried-over push data.
    assert chunks[1] == Bytes32(bytes([2]) + bytes([31]) + b"\x00" * 30)


def test_chunkify_push_ending_exactly_at_chunk_boundary() -> None:
    """
    A push whose data ends exactly on a chunk's last payload byte
    leaves no push data carried into the next chunk.

    The `PUSH1` at position 29 has its one data byte at position 30,
    chunk 0's last payload byte; chunk 1 opens with a plain opcode
    byte, so its leading byte is 0 and no phantom extra chunk
    appears.
    """
    push1 = 0x60
    code = Bytes(b"\x00" * 29 + bytes([push1, 0xAB]) + b"\x00" * 31)
    assert len(code) == 62

    chunks = chunkify_code(code)

    assert len(chunks) == 2
    assert chunks[0] == Bytes32(
        bytes([0]) + b"\x00" * 29 + bytes([push1, 0xAB])
    )
    assert chunks[1] == Bytes32(bytes([0]) + b"\x00" * 31)


@pytest.mark.parametrize(
    "length",
    [
        pytest.param(30, id="length-30-needs-padding"),
        pytest.param(31, id="length-31-exact-multiple"),
        pytest.param(32, id="length-32-needs-padding"),
        pytest.param(62, id="length-62-exact-multiple"),
        pytest.param(93, id="length-93-exact-multiple"),
    ],
)
def test_chunkify_code_length_multiples_need_no_padding(
    length: int,
) -> None:
    """
    Chunk count always follows `ceil(len(code) / 31)`.

    When the code length is itself a multiple of 31 (31, 62, and 93
    bytes here), no padding byte is introduced: the final chunk's
    31-byte payload is entirely original code. Filling the code with
    a non-zero repeating byte (0xAB, never a push opcode) makes any
    padding zero bytes stand out.
    """
    fill = 0xAB
    code = Bytes(bytes([fill]) * length)

    chunks = chunkify_code(code)

    expected_chunk_count = (length + 30) // 31
    assert len(chunks) == expected_chunk_count

    if length % 31 == 0:
        last_chunk = chunks[-1]
        assert last_chunk[0] == 0
        assert last_chunk[1:] == bytes([fill]) * 31


def test_chunkify_all_push32_code_matches_reference_scanner() -> None:
    """
    `chunkify_code` agrees with an independent reimplementation of
    the EIP pseudocode for code built entirely of `PUSH32`
    instructions.

    31 repeats of a 33-byte `PUSH32 || 32 data bytes` instruction is
    1023 bytes -- divisible by both the 33-byte instruction and the
    31-byte chunk -- exercising a full alignment cycle between the
    two. Chunk 32, the last of 33, additionally gets a hand-derived
    pin that stands on its own, independent of the reference scanner:
    the last (31st) instruction opens at position 990, so its data
    (positions 991-1022, values 1..32) still has 31 bytes remaining
    once chunk 32 opens at position 992, one byte into that data.
    """
    instruction = bytes([0x7F]) + bytes(range(1, 33))
    assert len(instruction) == 33
    code = Bytes(instruction * 31)
    assert len(code) == 1023

    chunks = chunkify_code(code)

    assert chunks == [Bytes32(c) for c in _reference_chunkify(bytes(code))]
    assert len(chunks) == 33
    assert chunks[32] == Bytes32(bytes([31]) + bytes(range(2, 33)))


def test_chunkify_push_data_containing_push_opcodes() -> None:
    """
    Bytes that fall inside a push instruction's data are never
    reinterpreted as fresh opcodes, even when their value (0x60
    through 0x7F) would otherwise mean `PUSH1` through `PUSH32`.

    Each `PUSH2` here carries `0x7F` and `0x60` as its two data
    bytes; the scanner must skip both wholesale rather than restart
    a push count on them. Chunk 2 additionally gets a hand-derived
    pin that stands on its own, independent of the reference
    scanner: the 16th `PUSH2` (at position 60) has its second data
    byte, the `0x60`, at position 62 -- chunk 2's first byte -- so
    chunk 2 opens with exactly one byte of carried-over push data.
    A scanner that wrongly restarted counting on a push-opcode-valued
    data byte would instead read `0x7F` (at position 61) as a fresh
    `PUSH32` and report 31 there, not 1.
    """
    push2 = 0x61
    code = Bytes((bytes([push2, 0x7F, 0x60]) + b"\x00") * 16)

    chunks = chunkify_code(code)

    assert chunks == [Bytes32(c) for c in _reference_chunkify(bytes(code))]
    assert len(chunks) == 3
    assert chunks[2] == Bytes32(bytes([1, 0x60]) + b"\x00" * 30)


def test_chunkify_consecutive_pushes_across_boundary() -> None:
    """
    Back-to-back pushes straddling a chunk edge chunkify consistently
    with the reference scanner.

    A `PUSH4` positioned so its fourth data byte falls exactly on
    chunk 1's first byte is immediately followed by a `PUSH1` and a
    `PUSH3`, both entirely inside chunk 1; chunk 1 opens with exactly
    one carried-over push-data byte.
    """
    push4, push1, push3 = 0x63, 0x60, 0x62
    code = Bytes(
        b"\x00" * 27  # positions 0-26
        + bytes([push4, 1, 2, 3, 4])  # opcode 27, data 28-31
        + bytes([push1, 0xAA])  # opcode 32, data 33
        + bytes([push3, 0xBB, 0xCC, 0xDD])  # opcode 34, data 35-37
        + b"\x00" * 24  # positions 38-61
    )
    assert len(code) == 62

    chunks = chunkify_code(code)

    assert chunks == [Bytes32(c) for c in _reference_chunkify(bytes(code))]
    assert chunks[1][0] == 1


def test_chunkify_delegation_designator() -> None:
    """
    An EIP-7702 delegation designator chunkifies like any other code.

    `0xEF0100` followed by the 20-byte delegate address is 23 bytes;
    `0xEF` is not a push opcode, so the single chunk's leading byte
    is 0 and the payload is zero-padded from 23 to 31 bytes.
    """
    designator = bytes([0xEF, 0x01, 0x00]) + b"\xcc" * 20
    assert len(designator) == 23
    code = Bytes(designator)

    chunks = chunkify_code(code)

    assert len(chunks) == 1
    assert chunks[0] == Bytes32(bytes([0]) + designator + b"\x00" * 8)


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


def test_encode_basic_data_maximum_fields() -> None:
    """
    Every field at its type's maximum packs into the expected 32
    bytes.

    `code_size` fills all four of its bytes at offset 4 -- the
    layout the in-code TODO flags as one byte wider than EIP-7864's
    three-byte field at offset 5 -- `nonce` fills its eight bytes,
    and `balance` fills its sixteen.
    """
    value = encode_basic_data(
        code_size=U32(2**32 - 1),
        nonce=U64(2**64 - 1),
        balance=U256(2**128 - 1),
    )

    expected = (
        bytes([0])  # version
        + b"\x00" * 3  # reserved
        + b"\xff" * 4  # code_size
        + b"\xff" * 8  # nonce
        + b"\xff" * 16  # balance
    )
    assert len(expected) == 32
    assert value == Bytes32(expected)


def test_encode_basic_data_all_zero() -> None:
    """
    The all-zero leaf -- a freshly created, codeless, nonce-0,
    balance-0 account -- packs to 32 zero bytes.

    `nonce` is typed `U64`, narrower than the four bytes
    `encode_basic_data` gives `code_size` at offset 4 (see the
    code_size-layout TODO on `encode_basic_data` for the
    offset-5/three-byte EIP-7864 divergence this pins); a nonce past
    the `U64` range is rejected at construction, before it ever
    reaches the packing.
    """
    value = encode_basic_data(code_size=U32(0), nonce=U64(0), balance=U256(0))

    assert value == Bytes32(b"\x00" * 32)

    with pytest.raises(OverflowError):
        U64(2**64)
