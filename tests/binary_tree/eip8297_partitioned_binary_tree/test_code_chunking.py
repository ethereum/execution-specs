"""
Code-chunking tests for the EIP-8297 partitioned binary tree: EIP-8297
stores bytecode as content-addressed 31-byte chunks, grouped 256 to a
stem ("code groups"), making code SIZE and code SHAPE newly
consensus-relevant. These tests pin that the chunking layer stays
completely invisible to execution semantics at every boundary that
matters: chunk edges, the code-group split, code identity, and the
code-size/initcode-size limits.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
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

# The SSTORE(slot, value) + STOP prefix `sstore_then_pad` below
# actually builds (value=0xCAFE, a PUSH2) is this many bytes; below
# this, `sstore_then_pad` cannot fit the write (see
# test_deploy_and_execute_at_code_size's 0- and 1-byte cases, which
# omit the write instead of calling it). Not a general claim about the
# smallest write-carrying code size: e.g. `CODESIZE CODESIZE SSTORE`
# writes a nonzero value (the code's own size, always >= 3 for any
# code containing this snippet) in 3 bytes -- unlike `CALLDATASIZE
# CALLDATASIZE SSTORE`, which with empty calldata is `SSTORE(0, 0)`,
# a zero write this suite's own convention treats as not observable.
_MIN_WRITE_PREFIX_LEN = len(Op.SSTORE(0, 0xCAFE) + Op.STOP)

# 31 * 256: one code group -- an aligned range of STEM_SUBTREE_WIDTH
# chunks sharing a stem -- holds exactly this many code bytes. Code of
# this size fills group 0 exactly; one more byte starts a chunk in
# group 1, whose keys carry a new `tree_index` and therefore a new
# stem (see "Code" in the EIP).
GROUP_CODE_BYTES = Spec.CODE_CHUNK_SIZE * Spec.STEM_SUBTREE_WIDTH


@pytest.mark.parametrize(
    "code_size",
    [
        pytest.param(0, id="0_bytes_empty_code"),
        pytest.param(1, id="1_byte"),
        pytest.param(31, id="31_bytes_single_chunk"),
        pytest.param(32, id="32_bytes_crosses_first_boundary"),
        pytest.param(GROUP_CODE_BYTES, id="7936_bytes_group_exact"),
        pytest.param(
            GROUP_CODE_BYTES + 1, id="7937_bytes_first_of_second_group"
        ),
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
    (possibly tiny, or entirely absent) executable prefix, reports the
    exact size back through `EXTCODESIZE`, and reports the plain
    `keccak256` of its own code back through `EXTCODEHASH` -- across
    sizes spanning empty code, a single chunk, the first chunk
    boundary, the exact code-group split, and the first chunk of the
    second group, proving the group rollover does not alter code
    identity.

    The 0- and 1-byte contracts have no room for a `SSTORE` (the
    minimal encoding needs `_MIN_WRITE_PREFIX_LEN` bytes), so those
    are just `STOP` (or no code at all); `target` is omitted from
    `post` for these two sizes since they trivially cannot write
    storage regardless of whether execution ran at all.
    """
    value_slot, size_slot, call_slot, hash_slot = 0, 1, 2, 3
    value = 0xCAFE

    has_write = code_size >= _MIN_WRITE_PREFIX_LEN
    target_code: Bytecode
    if code_size == 0:
        target_code = Bytecode()
    elif has_write:
        target_code = sstore_then_pad(
            slot=value_slot, value=value, total_size=code_size
        )
    else:
        target_code = Op.STOP + Op.INVALID * (code_size - 1)
    assert len(target_code) == code_size

    target = pre.deploy_contract(code=target_code)
    checker = pre.deploy_contract(
        code=Op.SSTORE(size_slot, Op.EXTCODESIZE(target))
        + Op.SSTORE(hash_slot, Op.EXTCODEHASH(target))
        + Op.SSTORE(call_slot, Op.CALL(address=target))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=checker)

    post = {
        checker: Account(
            storage={
                size_slot: code_size,
                hash_slot: keccak256(bytes(target_code)),
                call_slot: 1,
            }
        ),
    }
    if has_write:
        post[target] = Account(storage={value_slot: value})
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "opcode_index, push_width, pushed_value, expected_chunks",
    [
        pytest.param(
            Spec.CODE_CHUNK_SIZE - 2,
            4,
            0xDEADBEEF,
            {0, 1},
            id="single_chunk_boundary",
        ),
        pytest.param(
            Spec.CODE_CHUNK_SIZE - 1,
            32,
            int.from_bytes(bytes(range(1, 33)), "big"),
            {0, 1, 2},
            id="two_chunk_boundaries",
        ),
        pytest.param(
            GROUP_CODE_BYTES - 2,
            4,
            0xDEADBEEF,
            {255, 256},
            id="code_group_boundary",
        ),
    ],
)
def test_push_data_straddles_chunk_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode_index: int,
    push_width: int,
    pushed_value: int,
    expected_chunks: set[int],
) -> None:
    """
    Verify a PUSH instruction positioned so its immediate straddles a
    chunk boundary still pushes the correct value, at three
    boundaries: a single-chunk edge (`PUSH4`, chunks 0/1), a `PUSH32`
    immediate wide enough to touch three consecutive chunks (0, 1, 2 --
    the opcode byte itself has to sit in the chunk before the data,
    since a 32-byte immediate alone can touch at most two), and the
    code-group split at byte `GROUP_CODE_BYTES` (7936), chunks
    255/256 -- the first boundary where key derivation moves to a
    new stem (the `tree_index` advances) rather than just the next
    sub-index.

    What this pins is that a client's chunk *assembly* -- stripping
    exactly one metadata byte per chunk when reconstructing code --
    must do so correctly at every one of these boundaries, since
    getting that wrong is what would corrupt the pushed value.
    """
    slot = 0
    push_op = getattr(Op, f"PUSH{push_width}")

    code = (
        Op.JUMPDEST * opcode_index
        + push_op(pushed_value)
        + Op.PUSH1(slot)
        + Op.SSTORE
        + Op.STOP
    )
    code_bytes = bytes(code)
    data_start, data_end = opcode_index + 1, opcode_index + push_width
    chunks_touched = {
        i // Spec.CODE_CHUNK_SIZE for i in range(opcode_index, data_end + 1)
    }
    assert chunks_touched == expected_chunks, (
        f"opcode + immediate must span exactly chunks {expected_chunks}, "
        f"got {chunks_touched}"
    )
    assert code_bytes[data_start : data_end + 1] == pushed_value.to_bytes(
        push_width, "big"
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
    carried-over push data, so there is no chunk metadata describing
    byte 5 here at all. The target's own `SSTORE` after the jump is
    never reached, so its slot stays absent, and the wrapping `CALL`
    reports failure.

    Slot 1 is an unconditional canary written right after the `CALL`:
    it only reads back 1 if the caller's own execution truly
    continued, distinguishing this from the caller's own frame
    unexpectedly reverting.
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
        pytest.param(GROUP_CODE_BYTES, id="byte_7936_into_second_group"),
    ],
)
def test_jumpdest_at_chunk_boundary_is_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    dest: int,
) -> None:
    """
    Verify a real `JUMPDEST` located exactly at a chunk boundary --
    byte 31 (the first byte of chunk 1) and, separately, byte 7936
    (the first byte of the second code group) -- is jumpable, and
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
    only 93-99 real code): starting 2 bytes before the real end and
    reading 32 bytes crosses both chunk 3's own internal padding and
    the padding past the last chunk entirely, proving the former
    reads back as zero too, not just the classic past-the-end case.
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


def test_byte_identical_code_two_contracts_independent(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify two contracts deployed with byte-identical code -- long
    enough (7937 bytes) to span two code groups -- execute correctly
    and independently: each SSTOREs its own call's calldata into the
    same slot, proving via distinct post-state storage that the two
    never share execution state.

    Chunk leaves are shared in the tree (content-addressed) between
    byte-identical contracts; that sharing must stay invisible to
    execution. Leaf-level sharing itself is pinned in
    `test_state_pbt.py`, not here.
    """
    slot = 0
    size = GROUP_CODE_BYTES + 1
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

    Slot 1 is an unconditional canary written right after the
    `CREATE`: it only reads back 1 if execution truly continued past
    the failure rather than reverting the whole call.
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
    Verify an EIP-7702-delegated EOA executes a chunked (7937-byte,
    two-code-group) delegate's code and writes to the AUTHORITY's own
    storage.

    Storage landing on the authority is already pinned generally in
    `test_storage_ops.py`; the point here is narrower -- that an
    authority's 23-byte designator, which is a header leaf and never
    chunked, works together with a delegate whose own code spans two
    code groups.
    """
    slot, value = 5, 0xC0FFEE
    size = GROUP_CODE_BYTES + 1
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
