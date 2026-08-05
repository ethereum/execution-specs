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
    embed_account,
    embed_storage_slot,
    encode_basic_data,
    get_tree_key,
    get_tree_key_for_basic_data,
    get_tree_key_for_code_chunk,
    get_tree_key_for_code_hash,
    get_tree_key_for_header,
    get_tree_key_for_storage_slot,
    key_hash,
    remove_account,
    remove_all_storage,
    remove_code_chunks,
    remove_storage_slot,
)
from ethereum.binary_trie.trie import BinaryTrie, root
from ethereum.exceptions import BalanceOverflowError, InvalidBlock
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


def _code_chunk_key(
    code_hash: Bytes32, tree_index_bytes: bytes, sub_index: int
) -> bytes:
    """
    Build `0x01 || H(C || tree_index_bytes) || sub_index`, the
    34-byte content-addressed code-chunk key, from scratch.
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
    # Vacuity control: `key[-1] >= 64` above is this loop's only
    # assertion (there is no set-equality assertion anywhere in this
    # test to imply it), so it is also the loop's sole guard against
    # running zero times. If a future edit narrows `range(64, 1001)`
    # or the `continue` guard so the body never executes, this line
    # is what still catches the test passing vacuously.
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


def test_code_chunk_vector() -> None:
    """
    EIP key vector: code chunk 5 lives in the code zone at sub-index
    0x05, with the 33-byte stem `0x01 || H(C || 0)`.
    """
    code_hash = Bytes32(blake3(b"some code").digest())

    key = get_tree_key_for_code_chunk(code_hash, Uint(5))
    assert key == _code_chunk_key(code_hash, (0).to_bytes(32, "big"), 0x05)


def test_code_chunk_second_group_vector() -> None:
    """
    EIP key vector: chunk 300 lands in code group 1 at sub-index
    0x2C, with the 33-byte stem `0x01 || H(C || 1)`.
    """
    code_hash = Bytes32(blake3(b"some code").digest())

    key = get_tree_key_for_code_chunk(code_hash, Uint(300))
    assert key == _code_chunk_key(code_hash, (1).to_bytes(32, "big"), 0x2C)


def test_code_keys_are_content_addressed() -> None:
    """
    Chunk keys depend only on the code hash and chunk id: no address
    takes part in the derivation, so accounts sharing bytecode share
    every chunk key, and distinct bytecodes share none, their stems
    diverging at the hash.
    """
    code_hash = Bytes32(blake3(b"shared bytecode").digest())
    other_hash = Bytes32(blake3(b"different bytecode").digest())

    for chunk_id in (0, 5, 200):
        ours = get_tree_key_for_code_chunk(code_hash, Uint(chunk_id))
        theirs = get_tree_key_for_code_chunk(other_hash, Uint(chunk_id))
        assert ours != theirs
        assert ours[:-1] != theirs[:-1], "stems must differ, not just keys"


@pytest.mark.parametrize(
    "chunk_id",
    [
        pytest.param(0, id="chunk-0-group-0-first"),
        pytest.param(1, id="chunk-1-group-0"),
        pytest.param(255, id="chunk-255-group-0-last"),
        pytest.param(256, id="chunk-256-group-1-first"),
        pytest.param(257, id="chunk-257-group-1"),
        pytest.param(511, id="chunk-511-group-1-last"),
        pytest.param(512, id="chunk-512-group-2-first"),
    ],
)
def test_code_chunk_key_matrix(chunk_id: int) -> None:
    """
    A matrix of code chunk ids rebuilds each expected key from
    scratch: every chunk is content-addressed in the code zone, and
    the stem changes exactly where `chunk_id // 256` does. The
    rollover itself is pinned separately by
    `test_code_group_rollover_changes_the_stem`.
    """
    tree_index = chunk_id // 256
    sub_index = chunk_id % 256
    expected = _code_chunk_key(
        CODE_HASH, tree_index.to_bytes(32, "big"), sub_index
    )

    key = get_tree_key_for_code_chunk(CODE_HASH, Uint(chunk_id))

    assert key == expected
    assert len(key) == 34
    assert key[0] == 1


def test_code_group_rollover_changes_the_stem() -> None:
    """
    Crossing a code-group boundary changes the key's stem, not just
    its sub-index: chunk 255 sits at group 0's last sub-index and
    chunk 256 opens group 1 under a fresh hash-derived stem, and
    likewise at 511 -> 512. Kept out of the key matrix so narrowing
    the matrix's parameters can never silently retire this check.
    """
    for last_of_group, first_of_next in ((255, 256), (511, 512)):
        last_key = get_tree_key_for_code_chunk(CODE_HASH, Uint(last_of_group))
        next_key = get_tree_key_for_code_chunk(CODE_HASH, Uint(first_of_next))
        assert last_key[-1] == 255
        assert next_key[-1] == 0
        assert last_key[:-1] != next_key[:-1], "rollover must change stem"


def test_max_code_size_chunk_keys() -> None:
    """
    `MAX_CODE_SIZE` (0x10000 = 65536 bytes, defined in
    `ethereum.forks.binary_tree.vm.interpreter`) chunkifies into
    `ceil(65536 / 31) == 2115` chunks.

    The last chunk, id 2114, lands in the code zone at group 8,
    sub-index 66; the group/sub-index are computed here from the EIP
    formula, with the concrete numbers also asserted so the
    arithmetic stays pinned.
    """
    max_code_size = 0x10000
    chunk_count = (max_code_size + 30) // 31
    assert chunk_count == 2115

    last_chunk_id = chunk_count - 1
    tree_index = last_chunk_id // 256
    sub_index = last_chunk_id % 256
    assert (tree_index, sub_index) == (8, 66)

    key = get_tree_key_for_code_chunk(CODE_HASH, Uint(last_chunk_id))
    expected = _code_chunk_key(
        CODE_HASH, tree_index.to_bytes(32, "big"), sub_index
    )

    assert key == expected
    assert len(key) == 34


def test_key_derivations_assert_their_own_key_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Every key-deriving function asserts the length of the key it
    builds before returning it (EIP-8297, "Tree embedding":
    "Implementations MUST assert the length of every key they
    construct").

    Monkeypatching `key_hash` to return a too-short digest breaks
    that invariant for whichever derivation calls it, so each of the
    three length asserts in `embedding.py` --
    `get_tree_key_for_header`'s `ACCOUNT_KEY_LENGTH`,
    `get_tree_key_for_storage_slot`'s `STORAGE_KEY_LENGTH`, and
    `get_tree_key_for_code_chunk`'s `CODE_KEY_LENGTH` -- fires
    instead of silently returning a malformed key. The storage slot
    is chosen in the storage zone's range, so the call reaches that
    function's own assert rather than delegating to
    `get_tree_key_for_header`'s; every code chunk id reaches the
    code derivation directly.
    """
    monkeypatch.setattr(
        "ethereum.binary_trie.embedding.key_hash",
        lambda _data: b"\x00" * 16,
    )

    with pytest.raises(AssertionError):
        get_tree_key_for_header(ADDRESS, Uint(0))

    with pytest.raises(AssertionError):
        get_tree_key_for_storage_slot(ADDRESS, U256(1000))

    with pytest.raises(AssertionError):
        get_tree_key_for_code_chunk(CODE_HASH, Uint(300))


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
    pseudocode, using the EIP text's own variable names rather than
    `chunkify_code`'s, so the two implementations are genuinely
    independent, not a copy-paste.
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

    `PUSH32` demands 32 data bytes but this 32-byte code (opcode plus
    31 data bytes) supplies only 31, so the scan -- which runs over
    the already-padded buffer -- counts the first zero padding byte
    as the push's 32nd data byte too.
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
    chunk 0's last payload byte, so chunk 1 opens with a plain opcode
    byte and no phantom extra chunk appears.
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
    1023 bytes, exercising a full alignment cycle between the
    33-byte instruction and the 31-byte chunk. Chunk 32 additionally
    gets a hand-derived pin independent of the reference scanner, so
    a bug shared by both scanners would still be caught.
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
    bytes; the scanner must skip both wholesale rather than restart a
    push count on them. Chunk 2 additionally gets a hand-derived pin
    independent of the reference scanner: a scanner that wrongly
    restarted counting on a push-opcode-valued data byte would read
    31 there instead of 1.
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
    offsets given by the EIP, and the all-zero leaf -- a freshly
    created, codeless, nonce-0, balance-0 account -- packs to 32 zero
    bytes.
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

    # The all-zero leaf can't distinguish WHERE code_size sits (every
    # offset reads zero either way), so it doesn't pin the
    # offset-4/offset-5 EIP-7864 divergence noted on
    # `encode_basic_data`; `test_encode_basic_data_maximum_fields` is
    # what pins that.
    all_zero = encode_basic_data(
        code_size=U32(0), nonce=U64(0), balance=U256(0)
    )
    assert all_zero == Bytes32(b"\x00" * 32)


def test_encode_basic_data_rejects_balance_past_sixteen_bytes() -> None:
    """
    A balance that does not fit the sixteen-byte field raises
    `BalanceOverflowError` -- an `InvalidBlock` -- rather than being
    silently truncated by `to_bytes`.
    """
    assert issubclass(BalanceOverflowError, InvalidBlock)
    with pytest.raises(BalanceOverflowError):
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


def test_remove_account_takes_header_and_storage_with_it() -> None:
    """
    An account owns its header stem and its overflow storage
    subtree, so removing it undoes its basic data, code hash, and
    storage on both sides of the header boundary, without being told
    which slots it held. Its code chunks are content-addressed, not
    owned, and stay behind until `remove_code_chunks` drops them.
    """
    code = Bytes(b"\x01" * 40)  # two chunks, both in the code zone
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
    assert root(trie) != before, "content-addressed chunks stay behind"
    remove_code_chunks(trie, code_hash, code)
    assert root(trie) == before


def test_remove_account_never_reaches_the_code_zone() -> None:
    """
    The sweep covers the account and storage zones only, so
    content-addressed chunks -- a neighbour's or the removed
    account's own -- are untouched by a removal beside them.
    """
    long_code = Bytes(b"\x01" * 4000)  # 130 chunks, one code group
    long_hash = Bytes32(b"\x33" * 32)
    short_code = Bytes(b"\x02" * 40)  # two chunks
    short_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    embed_account(trie, OTHER_ADDRESS, U64(1), U256(5), long_hash, long_code)
    before = root(trie)

    embed_account(trie, ADDRESS, U64(2), U256(9), short_hash, short_code)
    remove_account(trie, ADDRESS)

    for chunk_id in (Uint(0), Uint(129)):
        assert get_tree_key_for_code_chunk(long_hash, chunk_id) in trie._data
    for chunk_id in (Uint(0), Uint(1)):
        assert get_tree_key_for_code_chunk(short_hash, chunk_id) in trie._data

    remove_code_chunks(trie, short_hash, short_code)
    assert root(trie) == before


def test_remove_account_leaves_code_for_the_caller() -> None:
    """
    Removing an account never takes content-addressed chunks with
    it: whether they may go depends on the resulting state, which
    the embedding cannot see. They are dropped separately, once the
    caller has established nothing else runs the code.
    """
    code = Bytes(b"\x01" * 4000)  # 130 chunks
    code_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    empty = root(trie)
    embed_account(trie, ADDRESS, U64(1), U256(5), code_hash, code)

    remove_account(trie, ADDRESS)

    residue = [
        get_tree_key_for_code_chunk(code_hash, Uint(chunk_id))
        for chunk_id in range(130)
    ]
    assert sorted(trie._data) == sorted(residue)

    remove_code_chunks(trie, code_hash, code)
    assert root(trie) == empty


def test_remove_code_chunks_spares_the_header() -> None:
    """
    Dropping a code's shared leaves removes exactly the code zone's
    keys for it: a holder's basic data and code hash leaves are in
    the account zone and survive untouched.
    """
    code = Bytes(b"\x01" * 4000)  # 130 chunks
    code_hash = Bytes32(b"\x22" * 32)

    trie = BinaryTrie()
    embed_account(trie, ADDRESS, U64(1), U256(5), code_hash, code)

    remove_code_chunks(trie, code_hash, code)

    assert all(key[0] != 1 for key in trie._data)
    assert get_tree_key_for_basic_data(ADDRESS) in trie._data
    assert trie._data[get_tree_key_for_code_hash(ADDRESS)] == code_hash


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
        key = get_tree_key_for_code_chunk(code_hash, chunk_id)
        assert key not in trie._data
    # The account is still distinguished from one with no code.
    assert trie._data[get_tree_key_for_code_hash(ADDRESS)] == code_hash


def test_remove_all_storage_keeps_the_account_and_its_code() -> None:
    """
    A storage wipe straddles the header boundary: slots `0`-`63`
    share the header stem with the basic data and code hash that
    must survive, while the rest live in the overflow subtree. The
    account's code chunks sit in the code zone, out of the sweep's
    reach entirely.
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


def test_encode_basic_data_maximum_fields() -> None:
    """
    Every field at its type's maximum packs into the expected 32
    bytes.

    `code_size` fills all four of its bytes at offset 4 -- one byte
    wider than EIP-7864's three-byte field at offset 5, as
    `encode_basic_data`'s note records -- `nonce` fills eight bytes
    and `balance` sixteen.
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
