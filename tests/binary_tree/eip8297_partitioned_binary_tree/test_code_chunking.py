"""
Code-chunking tests for the EIP-8297 partitioned binary tree: EIP-8297
stores bytecode as 31-byte chunks (128 per-account header chunks, then
content-addressed overflow chunks), making code SIZE and code SHAPE
newly consensus-relevant. These tests pin that the chunking layer stays
completely invisible to execution semantics at every boundary that
matters: chunk edges, the header/overflow split, code identity, and the
code-size/initcode-size limits.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create_address,
    keccak256,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .helpers import sstore_then_pad
from .spec import Spec, ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")

# A single SSTORE(slot, value) + STOP prefix, at minimum encoding, is
# this many bytes; below this no code size can carry an observable
# write (see test_deploy_and_execute_at_code_size's 1-byte case).
_MIN_WRITE_PREFIX_LEN = len(Op.SSTORE(0, 1) + Op.STOP)

# 31 * 128: the account header holds exactly this many code bytes
# before overflowing into content-addressed chunks -- 128 is the
# COUNT of header code chunks (STEM_SUBTREE_WIDTH - CODE_OFFSET), not
# CODE_OFFSET itself, which is the sub-index chunk 0 starts at (see
# "Tree embedding" in the EIP).
HEADER_CODE_BYTES = Spec.CODE_CHUNK_SIZE * (
    Spec.STEM_SUBTREE_WIDTH - Spec.CODE_OFFSET
)


@pytest.mark.parametrize(
    "code_size",
    [
        pytest.param(1, id="1_byte"),
        pytest.param(31, id="31_bytes_single_chunk"),
        pytest.param(32, id="32_bytes_crosses_first_boundary"),
        pytest.param(HEADER_CODE_BYTES, id="3968_bytes_header_exact"),
        pytest.param(HEADER_CODE_BYTES + 1, id="3969_bytes_first_overflow"),
        # Deliberately not marked `slow`, despite the large code size.
        pytest.param(65536, id="65536_bytes_max_code_size"),
    ],
)
def test_deploy_and_execute_at_code_size(
    state_test: StateTestFiller,
    pre: Alloc,
    code_size: int,
) -> None:
    """
    Verify a contract padded to an exact byte size executes its
    (possibly tiny) executable prefix and reports the exact size back
    through `EXTCODESIZE`, across sizes spanning a single chunk, the
    first chunk boundary, the exact header/overflow split, and the
    first overflow chunk.

    A 1-byte contract has no room for a `SSTORE` (the minimal encoding
    already needs `_MIN_WRITE_PREFIX_LEN` bytes), so that case is just
    `STOP`: it only pins that the smallest possible chunked contract is
    callable and reports size 1, without a storage-write assertion.
    """
    value_slot, size_slot, call_slot = 0, 1, 2
    value = 0xCAFE

    has_write = code_size >= _MIN_WRITE_PREFIX_LEN
    target_code = (
        sstore_then_pad(slot=value_slot, value=value, total_size=code_size)
        if has_write
        else Op.STOP + Op.INVALID * (code_size - 1)
    )
    assert len(target_code) == code_size

    target = pre.deploy_contract(code=target_code)
    checker = pre.deploy_contract(
        code=Op.SSTORE(size_slot, Op.EXTCODESIZE(target))
        + Op.SSTORE(call_slot, Op.CALL(address=target))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=checker)

    post = {
        checker: Account(storage={size_slot: code_size, call_slot: 1}),
        target: Account(storage={value_slot: value} if has_write else {}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_empty_code_account_is_callable_noop(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a deployed account with empty code (`code=b""`, zero
    chunks) is callable as a no-op, reports `EXTCODESIZE` 0, and
    `EXTCODEHASH` equal to the empty-code hash.
    """
    call_slot, size_slot, hash_slot = 0, 1, 2

    target = pre.deploy_contract(code=b"")
    checker = pre.deploy_contract(
        code=Op.SSTORE(call_slot, Op.CALL(address=target))
        + Op.SSTORE(size_slot, Op.EXTCODESIZE(target))
        + Op.SSTORE(hash_slot, Op.EXTCODEHASH(target))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=checker)

    post = {
        checker: Account(
            storage={
                call_slot: 1,
                size_slot: 0,
                hash_slot: keccak256(b""),
            }
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_push_data_straddles_single_chunk_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a `PUSH4` positioned so its 4-byte immediate straddles the
    chunk-0/chunk-1 boundary (opcode at byte 29, data at bytes 30-33,
    crossing the boundary at byte 31) still pushes the correct value.

    Each chunk's payload (bytes 1..31) is always that fixed 31-byte
    slice of the code, regardless of the leading metadata byte; what
    this pins is that a client's chunk *assembly* -- stripping
    exactly one metadata byte per chunk when reconstructing code from
    chunks -- must do so correctly, since getting that wrong (not a
    shift in which bytes are payload) is what would corrupt the
    pushed value.
    """
    slot = 0
    pushed_value = 0xDEADBEEF
    opcode_index = Spec.CODE_CHUNK_SIZE - 2  # 29

    code = (
        Op.JUMPDEST * opcode_index
        + Op.PUSH4(pushed_value)
        + Op.PUSH1(slot)
        + Op.SSTORE
        + Op.STOP
    )
    code_bytes = bytes(code)
    data_start, data_end = opcode_index + 1, opcode_index + 4
    start_chunk = data_start // Spec.CODE_CHUNK_SIZE
    end_chunk = data_end // Spec.CODE_CHUNK_SIZE
    assert start_chunk != end_chunk, "PUSH4 data must straddle a boundary"
    assert code_bytes[data_start : data_end + 1] == pushed_value.to_bytes(
        4, "big"
    )

    contract = pre.deploy_contract(code=code)
    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(storage={slot: pushed_value})}
    state_test(pre=pre, post=post, tx=tx)


def test_push32_data_straddles_two_chunk_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a `PUSH32` positioned so its opcode sits in chunk 0 and its
    32-byte immediate crosses from chunk 1 into chunk 2 (opcode at byte
    30, data at bytes 31-62) still pushes the correct value.

    A 32-byte immediate alone can touch at most two chunks: 32 <= 31
    + 1, so at most one leftover byte of an earlier chunk plus one
    whole chunk get used, with nothing left to spill into a third.
    To actually touch three chunks -- crossing two boundaries -- the
    opcode byte itself must sit in the chunk before the data.
    """
    slot = 0
    pushed_value = int.from_bytes(bytes(range(1, 33)), "big")
    opcode_index = Spec.CODE_CHUNK_SIZE - 1  # 30

    code = (
        Op.JUMPDEST * opcode_index
        + Op.PUSH32(pushed_value)
        + Op.PUSH1(slot)
        + Op.SSTORE
        + Op.STOP
    )
    code_bytes = bytes(code)
    data_start, data_end = opcode_index + 1, opcode_index + 32
    chunks_touched = {
        i // Spec.CODE_CHUNK_SIZE for i in range(opcode_index, data_end + 1)
    }
    assert chunks_touched == {0, 1, 2}, (
        "opcode + immediate must span exactly chunks 0, 1 and 2"
    )
    assert code_bytes[data_start : data_end + 1] == pushed_value.to_bytes(
        32, "big"
    )

    contract = pre.deploy_contract(code=code)
    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(storage={slot: pushed_value})}
    state_test(pre=pre, post=post, tx=tx)


def test_push_data_straddles_header_overflow_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a `PUSH4` positioned so its 4-byte immediate straddles byte
    `HEADER_CODE_BYTES` (3968) -- the header/overflow zone boundary,
    the only chunk boundary where key derivation changes ZONE (account
    header to content-addressed code) and switches from address-keyed
    to content-addressed, rather than merely advancing the chunk index
    within the same zone -- still pushes the correct value.

    Byte layout: opcode at `HEADER_CODE_BYTES - 2` (3966), the 4-byte
    immediate at 3967-3970. Byte 3967 is the last header code byte;
    3968-3970 are the first three bytes of the first overflow chunk.

    Each chunk's payload is still that fixed 31-byte code slice
    regardless of zone; crossing zones only changes how the chunk's
    *key* is derived, not which bytes are payload. What this pins is
    that a client's chunk assembly must treat the zone-crossing
    boundary like any other when stripping the leading metadata
    byte, since getting that wrong -- not a payload shift -- is what
    would corrupt the pushed value.
    """
    slot = 0
    pushed_value = 0xDEADBEEF
    opcode_index = HEADER_CODE_BYTES - 2  # 3966

    code = (
        Op.JUMPDEST * opcode_index
        + Op.PUSH4(pushed_value)
        + Op.PUSH1(slot)
        + Op.SSTORE
        + Op.STOP
    )
    code_bytes = bytes(code)
    data_start, data_end = opcode_index + 1, opcode_index + 4
    assert data_start < HEADER_CODE_BYTES <= data_end, (
        "PUSH4 data must straddle the header/overflow boundary"
    )
    assert code_bytes[data_start : data_end + 1] == pushed_value.to_bytes(
        4, "big"
    )

    contract = pre.deploy_contract(code=code)
    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(storage={slot: pushed_value})}
    state_test(pre=pre, post=post, tx=tx)


def test_jump_into_pushdata_is_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a `JUMP` into a byte that carries the numeric value of
    `JUMPDEST` (0x5B) but is actually `PUSH1`'s immediate data still
    fails as an invalid jump.

    This is the classic invalid-jump-into-PUSH-data rule, independent
    of chunking: the 12-byte target is a single chunk with no
    carried-over push data (chunk 0's leading byte is 0, since
    nothing precedes it), so there is no chunk metadata describing
    byte 5 here at all. The target's own `SSTORE` after the jump is
    never reached when the jump is correctly rejected, so its slot
    stays absent, and the wrapping `CALL` reports failure.

    A failed `CALL` and the caller's own frame unexpectedly reverting
    would both otherwise leave the caller's slot 0 reading back as
    absent (0 is absent by this suite's storage convention), so slot 1
    is an unconditional canary written right after the `CALL`: it only
    reads back as 1 if the caller's own execution truly continued.
    """
    slot = 0
    dest = 5  # index of PUSH1's data byte below

    target_code = (
        Op.PUSH2(dest)
        + Op.JUMP
        + Op.PUSH1(0x5B)  # opcode@4, data(0x5B)@5: looks like JUMPDEST
        + Op.SSTORE(slot, 1)
        + Op.STOP
    )
    assert bytes(target_code)[dest] == 0x5B

    target = pre.deploy_contract(code=target_code)
    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(gas=Op.GAS, address=target))
        + Op.SSTORE(1, 1)
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        caller: Account(storage={0: 0, 1: 1}),
        target: Account(storage={}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "dest",
    [
        pytest.param(Spec.CODE_CHUNK_SIZE, id="byte_31_first_boundary"),
        pytest.param(HEADER_CODE_BYTES, id="byte_3968_into_overflow"),
    ],
)
def test_jumpdest_at_chunk_boundary_is_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    dest: int,
) -> None:
    """
    Verify a real `JUMPDEST` located exactly at a chunk boundary --
    byte 31 (the first byte of chunk 1) and, separately, byte 3968
    (the first byte of the first overflow chunk) -- is jumpable, and
    execution resumes normally past it.
    """
    slot = 0
    push_size = max(1, (dest.bit_length() + 7) // 8)
    push_op = getattr(Op, f"PUSH{push_size}")

    prefix = push_op(dest) + Op.JUMP
    filler_len = dest - len(prefix)
    assert filler_len >= 0

    target_code = (
        prefix
        + Op.INVALID * filler_len
        + Op.JUMPDEST
        + Op.SSTORE(slot, 1)
        + Op.STOP
    )
    assert bytes(target_code)[dest] == 0x5B

    target = pre.deploy_contract(code=target_code)
    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(gas=Op.GAS, address=target)) + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        caller: Account(storage={0: 1}),
        target: Account(storage={slot: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_extcodecopy_full_and_partial_across_chunk_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify `EXTCODECOPY` of a chunked contract returns the exact
    original bytes both for a full copy and for a partial copy whose
    offset starts mid-chunk and whose length crosses a chunk boundary.

    The target's 200 bytes span chunks 0-6; the partial copy starts at
    byte 40 (9 bytes into chunk 1, not a chunk start) with length 50,
    ending at byte 89 (chunk 2) -- crossing the chunk 1/2 boundary.
    """
    size = 200
    pattern = bytes((i * 37 + 5) % 256 for i in range(size))
    offset, length = 40, 50
    assert offset % Spec.CODE_CHUNK_SIZE != 0, "offset must be mid-chunk"
    start_chunk = offset // Spec.CODE_CHUNK_SIZE
    end_chunk = (offset + length - 1) // Spec.CODE_CHUNK_SIZE
    assert end_chunk > start_chunk, "copy must cross a chunk boundary"

    target = pre.deploy_contract(code=pattern)

    full_hash_slot, partial_hash_slot = 0, 1
    caller_code = (
        Op.EXTCODECOPY(target, 0, 0, size)
        + Op.SSTORE(full_hash_slot, Op.SHA3(0, size))
        + Op.EXTCODECOPY(target, 0x200, offset, length)
        + Op.SSTORE(partial_hash_slot, Op.SHA3(0x200, length))
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code)

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        caller: Account(
            storage={
                full_hash_slot: keccak256(pattern),
                partial_hash_slot: keccak256(
                    pattern[offset : offset + length]
                ),
            }
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_extcodecopy_past_end_zero_pads(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify `EXTCODECOPY` reading past the end of a chunked contract's
    code zero-pads (classic semantics, re-verified under chunking).

    The 100-byte target ends mid-chunk (chunk 3 spans bytes 93-123,
    but only bytes 93-99 hold real code): the copy starts 2 bytes
    before the real end and reads 32 bytes, so of the 30 zero bytes
    read, 24 (positions 100-123) are chunk 3's own internal padding
    and 6 (positions 124-129) are past the last chunk entirely --
    proving the chunk's own internal padding, not just the classic
    "past the last chunk" case, reads back as zero.
    """
    size = 100
    pattern = bytes((i * 11 + 1) % 256 for i in range(size))
    offset, length = size - 2, 32

    target = pre.deploy_contract(code=pattern)
    caller = pre.deploy_contract(
        code=Op.EXTCODECOPY(target, 0, offset, length)
        + Op.SSTORE(0, Op.MLOAD(0))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    expected_word = pattern[offset:size] + bytes(length - 2)
    post = {caller: Account(storage={0: expected_word})}
    state_test(pre=pre, post=post, tx=tx)


def test_extcodehash_and_size_of_overflow_chunk_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify `EXTCODEHASH`/`EXTCODESIZE` of a 3969-byte contract -- one
    byte past the account header's 3968-byte code capacity, so it has
    exactly one overflow chunk -- equal the plain keccak256/length of
    the code, proving the overflow chunk does not alter code identity.
    """
    size = HEADER_CODE_BYTES + 1
    pattern = bytes(i % 256 for i in range(size))
    target = pre.deploy_contract(code=pattern)

    size_slot, hash_slot = 0, 1
    checker = pre.deploy_contract(
        code=Op.SSTORE(size_slot, Op.EXTCODESIZE(target))
        + Op.SSTORE(hash_slot, Op.EXTCODEHASH(target))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=checker)

    post = {
        checker: Account(
            storage={size_slot: size, hash_slot: keccak256(pattern)}
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_byte_identical_code_two_contracts_independent(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify two contracts deployed with byte-identical code -- long
    enough (3969 bytes) to need an overflow chunk -- execute correctly
    and independently: each SSTOREs its OWN call's calldata into the
    same slot, and the two calls carry different calldata, so distinct
    post-state storage proves the two accounts never share execution
    state.

    Overflow chunks are content-addressed and so may be shared in the
    tree between byte-identical contracts; that sharing must stay
    invisible to execution. Leaf-level sharing itself is pinned in
    `tests/binary_trie/test_state_pbt.py`, not here.
    """
    slot = 0
    size = HEADER_CODE_BYTES + 1
    write_from_calldata = Op.SSTORE(slot, Op.CALLDATALOAD(0)) + Op.STOP
    shared_code = write_from_calldata + Op.INVALID * (
        size - len(write_from_calldata)
    )
    assert len(shared_code) == size

    contract_a = pre.deploy_contract(code=shared_code)
    contract_b = pre.deploy_contract(code=shared_code)
    assert contract_a != contract_b

    value_a, value_b = 0xAAAA, 0xBBBB
    driver = pre.deploy_contract(
        code=Op.MSTORE(0, value_a)
        + Op.POP(Op.CALL(address=contract_a, args_offset=0, args_size=32))
        + Op.MSTORE(0, value_b)
        + Op.POP(Op.CALL(address=contract_b, args_offset=0, args_size=32))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=driver)

    post = {
        contract_a: Account(storage={slot: value_a}),
        contract_b: Account(storage={slot: value_b}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "code_size_delta",
    [
        pytest.param(0, id="at_max"),
        # Not `exception_test`: a CREATE returning oversized code is an
        # EVM-level failure (CREATE just returns 0), not a transaction
        # exception -- the enclosing transaction itself still succeeds.
        pytest.param(1, id="over_max"),
    ],
)
def test_code_deposit_limit_via_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    code_size_delta: int,
) -> None:
    """
    Verify `CREATE` returning `MAX_CODE_SIZE` bytes of deploy code
    succeeds, while returning one byte more fails: no contract
    materializes at the child address, and the creator -- which stores
    `CREATE`'s return value itself, rather than merely being inferred
    from the child's absence -- observes and survives the failure.

    A failed `CREATE` returning 0 and a full-frame revert would both
    otherwise leave the creator's slot 0 reading back as absent (0 is
    absent by this suite's storage convention), so slot 1 is an
    unconditional canary written right after the `CREATE`: it only
    reads back as 1 if execution truly continued past the failure
    rather than reverting the whole call.
    """
    code_size = fork.max_code_size() + code_size_delta
    deploy_code = Op.JUMPDEST * code_size
    initcode = Initcode(deploy_code=deploy_code)
    initcode_bytes = bytes(initcode)

    creator_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, Op.CREATE(value=0, offset=0, size=Op.CALLDATASIZE))
        + Op.SSTORE(1, 1)
        + Op.STOP
    )
    creator = pre.deploy_contract(code=creator_code)
    created = compute_create_address(address=creator, nonce=1)

    # Omitting `gas_limit` relies on the framework's implicit gas-limit
    # fill (clamped to the fork/block cap), the same as the equivalent
    # EIP-7954 `test_max_code_size_via_create` case: deposit gas for up
    # to MAX_CODE_SIZE bytes is a plain function of the fork's declared
    # gas costs, independent of the binary-tree commitment swap.
    tx = Transaction(sender=pre.fund_eoa(), to=creator, data=initcode_bytes)

    succeeded = code_size <= fork.max_code_size()
    post = {
        creator: Account(storage={0: created if succeeded else 0, 1: 1}),
        created: (
            Account(code=deploy_code) if succeeded else Account.NONEXISTENT
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "initcode_size_delta",
    [
        pytest.param(0, id="at_max"),
        pytest.param(1, id="over_max", marks=pytest.mark.exception_test),
    ],
)
def test_initcode_size_limit_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size_delta: int,
) -> None:
    """
    Verify a contract-creating transaction with initcode at
    `max_initcode_size()` succeeds, while one byte more is rejected
    with `INITCODE_SIZE_EXCEEDED` before any execution.
    """
    deploy_code = Op.STOP
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_length=fork.max_initcode_size() + initcode_size_delta,
    )

    over_limit = initcode_size_delta > 0
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)

    # Omitting `gas_limit` matches the proven EIP-3860
    # `test_contract_creating_tx` case: the initcode-size check is a
    # transaction-validity gate that fires before gas even matters, and
    # the framework's implicit gas fill already covers the at-limit
    # deploy (a single `STOP`, negligible deployment gas).
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        error=(
            TransactionException.INITCODE_SIZE_EXCEEDED if over_limit else None
        ),
    )

    post = {
        created: (
            Account.NONEXISTENT if over_limit else Account(code=deploy_code)
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_delegated_eoa_executes_chunked_delegate(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify an EIP-7702-delegated EOA executes a chunked (3969-byte,
    overflow-chunk-carrying) delegate's code and writes to the
    AUTHORITY's own storage.

    Storage landing on the authority rather than the delegate is
    already pinned generally in
    `test_storage_ops.test_storage_under_7702_delegation_lands_on_authority`;
    the point here is narrower -- that a 23-byte delegation designator
    plus a delegate large enough to need an overflow chunk both work
    together.
    """
    slot, value = 5, 0xC0FFEE
    size = HEADER_CODE_BYTES + 1
    delegate_code = sstore_then_pad(slot=slot, value=value, total_size=size)

    delegate = pre.deploy_contract(code=delegate_code)
    authority = pre.fund_eoa(delegation=delegate)

    tx = Transaction(sender=pre.fund_eoa(), to=authority)

    post = {
        authority: Account(
            storage={slot: value},
            code=Spec7702.delegation_designation(delegate),
        ),
        delegate: Account(storage={}),
    }
    state_test(pre=pre, post=post, tx=tx)
