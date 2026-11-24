"""
Benchmark the worst cases of an
[EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction.

Each test fills a block with work a client repeats per frame or per
call that the frame itself does not pay for. Senders are contracts
approving from their own code, so no transaction carries a signature
entry of its own.
"""

import math
from itertools import count
from typing import Any, List

import pytest
from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Bytes,
    Environment,
    ExtCallGenerator,
    Fork,
    FrameSignature,
    Op,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    APPROVE_ALL,
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.signature_helpers import (
    DIGEST,
    canonical_entry,
    valid_p256_entry,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.repricing
@pytest.mark.parametrize(
    "scheme",
    [
        pytest.param(Spec.SCHEME_SECP256K1, id="secp256k1"),
        pytest.param(Spec.SCHEME_P256, id="p256"),
    ],
)
@pytest.mark.parametrize(
    "batch_size",
    [1, 16, 256, pytest.param(None, id="batch_max")],
)
def test_signature_batch_size(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    scheme: int,
    batch_size: int | None,
) -> None:
    """
    Fill a block with signature entries batched `batch_size` per
    transaction.

    The EIP caps frames but not signatures, and every entry is verified
    before any frame runs.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    target = pre.deploy_contract(code=Op.STOP)

    def entry() -> FrameSignature:
        if scheme == Spec.SCHEME_SECP256K1:
            return canonical_entry(pre.fund_eoa(amount=0), msg=Bytes(DIGEST))
        if scheme == Spec.SCHEME_P256:
            # P256 signing is randomized, so reuse the suite's signature.
            return valid_p256_entry()
        raise ValueError(f"unknown signature scheme: {scheme}")

    def transaction(entry_count: int, **overrides: Any) -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                sender_frame(
                    target=target,
                    code=Op.STOP,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
            ],
            signatures=[entry() for _ in range(entry_count)],
            **overrides,
        )

    payload_gas = gas_benchmark_value // math.ceil(
        gas_benchmark_value / min(tx_gas_limit, gas_benchmark_value)
    )
    # The floor makes gas piecewise affine in the count, so iterate
    # until the estimate lands on the piece holding the target.
    largest_batch = 0
    for _ in range(4):
        base = transaction(largest_batch, nonce=0).block_gas_used()
        entry_gas = (
            transaction(largest_batch + 1, nonce=0).block_gas_used() - base
        )
        largest_batch += (payload_gas - base) // entry_gas
    entry_count = largest_batch if batch_size is None else batch_size
    if entry_count > largest_batch:
        pytest.skip(
            f"a batch of {entry_count} entries exceeds the "
            f"{largest_batch} the transaction gas cap allows"
        )

    first = transaction(entry_count, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(entry_count, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_entries = 0
    for _ in range(4):
        base = transaction(tail_entries, nonce=0).block_gas_used()
        tail_gas = (
            transaction(tail_entries + 1, nonce=0).block_gas_used() - base
        )
        tail_entries = max(
            0, min(entry_count, tail_entries + (leftover - base) // tail_gas)
        )
    if transaction(tail_entries, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_entries, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("frame_count", [1, 16, 63])
def test_frame_logs(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    frame_count: int,
) -> None:
    """
    Fill a block with a fixed number of logs per frame over
    `frame_count` frames.

    Each frame owns a sub-receipt, so a client re-walking the logs at
    every frame boundary does work growing with frames as well as logs.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    # Expand memory once so each log pays only for its own data.
    logs_per_frame = 16
    emitter_code = (
        Op.MSTORE(992, 0, new_memory_size=1024, old_memory_size=0)
        + Op.LOG0(
            0,
            1024,
            data_size=1024,
            new_memory_size=1024,
            old_memory_size=1024,
        )
        * logs_per_frame
        + Op.STOP
    )
    emitter = pre.deploy_contract(code=emitter_code)

    def transaction(
        emitting_frames: int, **overrides: Any
    ) -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            )
        ]
        while len(frames) <= emitting_frames:
            frames.append(
                sender_frame(
                    target=emitter,
                    code=emitter_code,
                    warm=len(frames) > 1,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(frame_count, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(frame_count, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_frames = 1
    for _ in range(4):
        base = transaction(tail_frames, nonce=0).block_gas_used()
        frame_gas = (
            transaction(tail_frames + 1, nonce=0).block_gas_used() - base
        )
        if frame_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_frames = frame_count
            break
        tail_frames = max(
            1, min(frame_count, tail_frames + (leftover - base) // frame_gas)
        )
    if transaction(tail_frames, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_frames, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("outstanding_slots", [0, 64])
def test_late_frame_calls(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    outstanding_slots: bool,
) -> None:
    """
    Fill a block with calling frames behind a frame that leaves
    state-gas charges outstanding.

    A client snapshotting state-gas ownership around each call repeats
    that work per call, which the calls do not pay for.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    callee = pre.deploy_contract(code=Op.STOP)
    # Deployed per transaction, so every SSTORE creates a slot.
    creator_code = (
        sum(
            (
                Op.SSTORE(
                    key,
                    1,
                    key_warm=False,
                    original_value=0,
                    current_value=0,
                    new_value=1,
                )
                for key in range(outstanding_slots)
            ),
            Bytecode(),
        )
        # Warm the callee for the calling frames.
        + Op.POP(Op.STATICCALL(address=callee, address_warm=False))
        + Op.STOP
    )
    caller_code = (
        Op.POP(Op.STATICCALL(address=callee, address_warm=True)) * 64 + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code)

    def transaction(frames_used: int, **overrides: Any) -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            ),
            sender_frame(
                target=pre.deploy_contract(code=creator_code),
                code=creator_code,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            ),
        ]
        while len(frames) < frames_used:
            frames.append(
                sender_frame(
                    target=caller,
                    code=caller_code,
                    warm=len(frames) > 2,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(Spec.MAX_FRAMES, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(Spec.MAX_FRAMES, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_frames = 3
    for _ in range(4):
        base = transaction(tail_frames, nonce=0).block_gas_used()
        frame_gas = (
            transaction(tail_frames + 1, nonce=0).block_gas_used() - base
        )
        if frame_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_frames = Spec.MAX_FRAMES
            break
        tail_frames = max(
            3,
            min(Spec.MAX_FRAMES, tail_frames + (leftover - base) // frame_gas),
        )
    if transaction(tail_frames, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_frames, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "carrier",
    [
        pytest.param("frame_data", id="frame_data"),
        pytest.param("signature", id="arbitrary_signature"),
    ],
)
def test_oversized_payload(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    carrier: str,
) -> None:
    """
    Fill a block with one large payload per transaction, as frame data
    or as an `ARBITRARY` signature.

    The signature hash commits to both, so each hash pass walks the
    whole payload.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    target = pre.deploy_contract(code=Op.STOP)

    def transaction(length: int, **overrides: Any) -> FrameTransaction:
        payload = b"\xff" * length
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                default_frame(
                    target=target,
                    code=Op.STOP,
                    data=payload if carrier == "frame_data" else b"",
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
            ],
            signatures=(
                [
                    FrameSignature(
                        scheme=Spec.SCHEME_ARBITRARY,
                        signature=Bytes(payload),
                    )
                ]
                if carrier == "signature"
                else []
            ),
            **overrides,
        )

    payload_gas = gas_benchmark_value // math.ceil(
        gas_benchmark_value / min(tx_gas_limit, gas_benchmark_value)
    )
    # The floor makes gas piecewise affine in the length, so iterate
    # until the estimate lands on the piece holding the target.
    length = 0
    for _ in range(4):
        base = transaction(length, nonce=0).block_gas_used()
        byte_gas = transaction(length + 1, nonce=0).block_gas_used() - base
        length += (payload_gas - base) // byte_gas

    first = transaction(length, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(length, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]

    block_rlp_limit = fork.block_rlp_size_limit()
    if block_rlp_limit is not None:
        assert iteration_count * length < block_rlp_limit, (
            "the block's payload outgrew the EIP-7934 block RLP size "
            "limit: the data is no longer priced above the limit's "
            "share of the benchmark gas"
        )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
def test_atomic_batch_rollback(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """
    Fill a block with the largest atomic batch, failing on its last
    frame, so one rollback undoes the most journaled work.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    writer_code = (
        Op.MSTORE(992, 0, new_memory_size=1024, old_memory_size=0)
        + Op.LOG0(
            0,
            1024,
            data_size=1024,
            new_memory_size=1024,
            old_memory_size=1024,
        )
        * 8
        + Op.STOP
    )
    writer = pre.deploy_contract(code=writer_code)
    reverter_code = Op.REVERT(0, 0)
    reverter = pre.deploy_contract(code=reverter_code)

    def transaction(frames_used: int, **overrides: Any) -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            )
        ]
        while len(frames) < frames_used - 1:
            frames.append(
                sender_frame(
                    flags=Spec.ATOMIC_BATCH_FLAG,
                    target=writer,
                    code=writer_code,
                    warm=len(frames) > 1,
                    outcome=Outcome.UNROLLED,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            )
        frames.append(
            sender_frame(
                target=reverter,
                code=reverter_code,
                outcome=Outcome.REVERT,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            )
        )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(Spec.MAX_FRAMES, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(Spec.MAX_FRAMES, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_frames = 3
    for _ in range(4):
        base = transaction(tail_frames, nonce=0).block_gas_used()
        frame_gas = (
            transaction(tail_frames + 1, nonce=0).block_gas_used() - base
        )
        if frame_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_frames = Spec.MAX_FRAMES
            break
        tail_frames = max(
            3,
            min(Spec.MAX_FRAMES, tail_frames + (leftover - base) // frame_gas),
        )
    if transaction(tail_frames, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_frames, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("churned_slots", [0, 32])
def test_state_gas_refill_churn(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    churned_slots: int,
) -> None:
    """
    Fill a block with frames clearing slots an earlier frame created.

    The refill is credited back to the creating frame, reaching into a
    receipt the transaction has already written.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)

    # A refill is keyed by slot, so one contract creates and clears.
    def churn_code(**charge: Any) -> Bytecode:
        return (
            sum(
                (
                    Op.SSTORE(key, Op.CALLDATALOAD(0), **charge)
                    for key in range(churned_slots)
                ),
                Bytecode(),
            )
            + Op.STOP
        )

    # Same bytes, priced as creating and as clearing respectively.
    creating_code = churn_code(
        key_warm=False, original_value=0, current_value=0, new_value=1
    )
    clearing_code = churn_code(
        key_warm=True, original_value=0, current_value=1, new_value=0
    )
    churner = pre.deploy_contract(code=creating_code)

    def transaction() -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL, gas_limit_delta=0, state_gas_limit_delta=0
            ),
            default_frame(
                target=churner,
                code=creating_code,
                data=(1).to_bytes(32, "big"),
                gas_limit_delta=0,
                state_gas_limit_delta=0,
                # Refilled by the clearing frame.
                state_gas_used=0,
            ),
            default_frame(
                target=churner,
                code=clearing_code,
                data=bytes(32),
                warm=True,
                # EIP-2200 needs more than the call stipend left to SSTORE.
                gas_limit_delta=fork.gas_costs().CALL_STIPEND + 1,
                state_gas_limit=0,
                state_gas_used=0,
            ),
        ]
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=next(nonces),
            settle=False,
            refund=clearing_code.refund(fork),
            frames=frames,
        )

    first = transaction()
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [transaction() for _ in range(iteration_count - 1)]

    benchmark_test(
        pre=pre,
        post={
            churner: Account(storage=dict.fromkeys(range(churned_slots), 0))
        },
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("warm_keys", [0, 2048])
def test_warm_set_amplification(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    warm_keys: int,
) -> None:
    """
    Fill a block with cheap frames behind a frame warming many slots.

    Every later frame inherits the shared warm set for the price of a
    frame, however large it grew.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    warming_code = (
        sum(
            (
                Op.POP(Op.SLOAD(key, key_warm=False))
                for key in range(warm_keys)
            ),
            Bytecode(),
        )
        + Op.STOP
    )
    warmer = pre.deploy_contract(code=warming_code)

    def transaction(frame_count: int, **overrides: Any) -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            ),
            sender_frame(
                target=warmer,
                code=warming_code,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            ),
        ]
        # The coinbase is warm and codeless; an empty target would
        # resolve to the sender and rerun its approval.
        while len(frames) < frame_count:
            frames.append(
                sender_frame(
                    target=Environment().fee_recipient,
                    code=Bytecode(),
                    warm=True,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(Spec.MAX_FRAMES, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(Spec.MAX_FRAMES, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_frames = 3
    for _ in range(4):
        base = transaction(tail_frames, nonce=0).block_gas_used()
        frame_gas = (
            transaction(tail_frames + 1, nonce=0).block_gas_used() - base
        )
        if frame_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_frames = Spec.MAX_FRAMES
            break
        tail_frames = max(
            3,
            min(Spec.MAX_FRAMES, tail_frames + (leftover - base) // frame_gas),
        )
    if transaction(tail_frames, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_frames, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("transient_slots", [0, 512])
def test_transient_storage_boundaries(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    transient_slots: int,
) -> None:
    """
    Fill a block with frames that each fill transient storage the frame
    boundary then discards.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    # Frame data offsets the keys, so no two frames touch the same key.
    filler_code = (
        sum(
            (
                Op.TSTORE(Op.ADD(Op.CALLDATALOAD(0), offset), 1)
                for offset in range(transient_slots)
            ),
            Bytecode(),
        )
        + Op.STOP
    )
    filler = pre.deploy_contract(code=filler_code)

    def transaction(frame_count: int, **overrides: Any) -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            )
        ]
        while len(frames) < frame_count:
            frames.append(
                sender_frame(
                    target=filler,
                    code=filler_code,
                    data=((len(frames) - 1) * transient_slots).to_bytes(
                        32, "big"
                    ),
                    warm=len(frames) > 1,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(Spec.MAX_FRAMES, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(Spec.MAX_FRAMES, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_frames = 2
    for _ in range(4):
        base = transaction(tail_frames, nonce=0).block_gas_used()
        frame_gas = (
            transaction(tail_frames + 1, nonce=0).block_gas_used() - base
        )
        if frame_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_frames = Spec.MAX_FRAMES
            break
        tail_frames = max(
            2,
            min(Spec.MAX_FRAMES, tail_frames + (leftover - base) // frame_gas),
        )
    if transaction(tail_frames, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_frames, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("slots_per_frame", [0, 64])
def test_cold_storage_cache_eviction(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    slots_per_frame: int,
) -> None:
    """
    Fill a block with frames that each sweep slots no other frame
    touches, so every read is cold and evicts rather than hits a cache.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    sweep_code = (
        sum(
            (
                Op.POP(
                    Op.SLOAD(
                        Op.ADD(Op.CALLDATALOAD(0), offset), key_warm=False
                    )
                )
                for offset in range(slots_per_frame)
            ),
            Bytecode(),
        )
        + Op.STOP
    )

    def transaction(frame_count: int, **overrides: Any) -> FrameTransaction:
        # A fresh contract per transaction, so no slot is read twice.
        sweeper = pre.deploy_contract(code=sweep_code)
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            )
        ]
        while len(frames) < frame_count:
            frames.append(
                sender_frame(
                    target=sweeper,
                    code=sweep_code,
                    data=(len(frames) * slots_per_frame).to_bytes(32, "big"),
                    warm=len(frames) > 1,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(Spec.MAX_FRAMES, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(Spec.MAX_FRAMES, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_frames = 2
    for _ in range(4):
        base = transaction(tail_frames, nonce=0).block_gas_used()
        frame_gas = (
            transaction(tail_frames + 1, nonce=0).block_gas_used() - base
        )
        if frame_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_frames = Spec.MAX_FRAMES
            break
        tail_frames = max(
            2,
            min(Spec.MAX_FRAMES, tail_frames + (leftover - base) // frame_gas),
        )
    if transaction(tail_frames, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_frames, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "rolled_back",
    [
        pytest.param(True, id="rolled_back"),
        pytest.param(False, id="kept"),
    ],
)
@pytest.mark.parametrize(
    "frames_used",
    [2, pytest.param(Spec.MAX_FRAMES, id="frames_max")],
)
def test_rolled_back_state_growth(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    rolled_back: bool,
    frames_used: int,
) -> None:
    """
    Fill a block with frames that create slots, then keep or revert.

    A reverted frame records no state gas, so the block's state
    dimension stays empty however many slots it wrote.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    write = Op.SSTORE(
        0, 1, key_warm=False, original_value=0, current_value=0, new_value=1
    )
    writing_frames = frames_used - 1
    # The frames together declare the block's whole state budget.
    slots = gas_benchmark_value // write.state_cost(fork) // writing_frames
    # Frame data offsets the keys, so every frame creates its own slots.
    writer_code = sum(
        (
            Op.SSTORE(
                Op.ADD(Op.CALLDATALOAD(0), offset),
                1,
                key_warm=False,
                original_value=0,
                current_value=0,
                new_value=1,
            )
            for offset in range(slots)
        ),
        Bytecode(),
    ) + (Op.REVERT(0, 0) if rolled_back else Op.STOP)

    def transaction(frame_count: int, **overrides: Any) -> FrameTransaction:
        # A fresh contract per transaction, so kept slots are new ones.
        writer = pre.deploy_contract(code=writer_code)
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL, gas_limit_delta=0, state_gas_limit_delta=0
            )
        ]
        while len(frames) < frame_count:
            frames.append(
                sender_frame(
                    target=writer,
                    code=writer_code,
                    data=((len(frames) - 1) * slots).to_bytes(32, "big"),
                    # A reverting frame discards its accesses.
                    warm=not rolled_back and len(frames) > 1,
                    outcome=(
                        Outcome.REVERT if rolled_back else Outcome.SUCCESS
                    ),
                    gas_limit_delta=0,
                    state_gas_limit=writer_code.state_cost(fork),
                )
            )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(frames_used, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(frames_used, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_frames = 2
    for _ in range(4):
        base = transaction(tail_frames, nonce=0).block_gas_used()
        frame_gas = (
            transaction(tail_frames + 1, nonce=0).block_gas_used() - base
        )
        if frame_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_frames = frames_used
            break
        tail_frames = max(
            2, min(frames_used, tail_frames + (leftover - base) // frame_gas)
        )
    if transaction(tail_frames, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_frames, nonce=next(nonces)))

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("envelope_bytes", [0, 128 * 1024])
def test_signature_hash_reads(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    envelope_bytes: int,
) -> None:
    """
    Fill a block with signature hash reads behind an envelope of
    `envelope_bytes`.

    The read price ignores the envelope, so a client deriving the hash
    per read pays its length per read; the empty envelope is the control.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    reader = ExtCallGenerator(
        attack_block=Op.TXPARAM(Spec.TXPARAM_SIG_HASH)
    ).deploy_contracts(pre=pre, fork=fork)

    def transaction(frame_gas: int, **overrides: Any) -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                default_frame(
                    target=reader,
                    gas_limit=frame_gas,
                    state_gas_limit=0,
                    outcome=Outcome.HALT,
                ),
            ],
            signatures=(
                [
                    FrameSignature(
                        scheme=Spec.SCHEME_ARBITRARY,
                        signature=Bytes(b"\xff" * envelope_bytes),
                    )
                ]
                if envelope_bytes
                else []
            ),
            **overrides,
        )

    # Only the frame budget grows, so one probe large enough for the
    # execution dimension to bind measures the fixed overhead.
    payload_gas = gas_benchmark_value // math.ceil(
        gas_benchmark_value / min(tx_gas_limit, gas_benchmark_value)
    )
    probe_gas = payload_gas // 2
    overhead = transaction(probe_gas, nonce=0).block_gas_used() - probe_gas
    frame_gas = payload_gas - overhead
    if frame_gas <= 0:
        pytest.skip("the envelope alone exceeds the benchmark gas value")
    first = transaction(frame_gas, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(frame_gas, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )
