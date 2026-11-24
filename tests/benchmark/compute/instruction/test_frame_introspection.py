"""
Benchmark the frame transaction introspection instructions of
[EIP-8141](https://eips.ethereum.org/EIPS/eip-8141).

Supported Opcodes:
- TXPARAM
- FRAMEPARAM
- SIGPARAM
- FRAMEDATALOAD
- FRAMEDATACOPY
- SIGDATACOPY
"""

import math
from typing import Any

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Bytes,
    ExtCallGenerator,
    Fork,
    FrameSignature,
    JumpLoopGenerator,
    Op,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    FrameTransaction,
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.signature_helpers import (
    canonical_entry,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

READABLE_LENGTH = 32
"""Bytes of data per readable frame and per `ARBITRARY` signature."""

LOOP_FRAME = Spec.MAX_FRAMES - 1

READABLE_FRAMES = range(LOOP_FRAME)
"""Frames completed before the loop runs, so every parameter is readable."""

DATA_FRAMES = range(1, LOOP_FRAME)

ARBITRARY_ENTRIES = DATA_FRAMES
"""One `ARBITRARY` entry per data frame; entry 0 is the sender's."""


def sweep(instruction: Any, indices: range, param: int) -> Bytecode:
    """Return `instruction` reading `param` at every one of `indices`."""
    return sum(
        (Op.POP(instruction(index, param)) for index in indices),
        Bytecode(),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "opcode,attack_block",
    [
        # Every selector is priced alike, but the work behind each is not.
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_TYPE),
            id="txparam_type",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_NONCE),
            id="txparam_nonce",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_SENDER),
            id="txparam_sender",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_MAX_PRIORITY_FEE_PER_GAS),
            id="txparam_max_priority_fee_per_gas",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_MAX_FEE),
            id="txparam_max_fee",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_BLOB_COUNT),
            id="txparam_blob_count",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_SIG_HASH),
            id="txparam_sig_hash",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_FRAME_COUNT),
            id="txparam_frame_count",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_CURRENT_FRAME_INDEX),
            id="txparam_current_frame_index",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_SIGNATURE_COUNT),
            id="txparam_signature_count",
        ),
        pytest.param(
            Op.TXPARAM,
            Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT),
            id="txparam_state_gas_left",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_RESOLVED_TARGET,
            ),
            id="frameparam_resolved_target",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_EXECUTION_GAS_LIMIT,
            ),
            id="frameparam_execution_gas_limit",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_MODE,
            ),
            id="frameparam_mode",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_FLAGS,
            ),
            id="frameparam_flags",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_DATA_LENGTH,
            ),
            id="frameparam_data_length",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_STATUS,
            ),
            id="frameparam_status",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_ALLOWED_SCOPE,
            ),
            id="frameparam_allowed_scope",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_ATOMIC_BATCH,
            ),
            id="frameparam_atomic_batch",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_VALUE,
            ),
            id="frameparam_value",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_STATE_GAS_LIMIT,
            ),
            id="frameparam_state_gas_limit",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_EXECUTION_GAS_USED,
            ),
            id="frameparam_execution_gas_used",
        ),
        pytest.param(
            Op.FRAMEPARAM,
            sweep(
                Op.FRAMEPARAM,
                READABLE_FRAMES,
                Spec.FRAMEPARAM_STATE_GAS_USED,
            ),
            id="frameparam_state_gas_used",
        ),
        # Each selector reads only the entries it is defined for.
        pytest.param(
            Op.SIGPARAM,
            Op.POP(Op.SIGPARAM(0, Spec.SIGPARAM_RESOLVED_SIGNER)),
            id="sigparam_resolved_signer",
        ),
        pytest.param(
            Op.SIGPARAM,
            sweep(
                Op.SIGPARAM,
                READABLE_FRAMES,
                Spec.SIGPARAM_SCHEME,
            ),
            id="sigparam_scheme",
        ),
        pytest.param(
            Op.SIGPARAM,
            sweep(
                Op.SIGPARAM,
                READABLE_FRAMES,
                Spec.SIGPARAM_MSG,
            ),
            id="sigparam_msg",
        ),
        pytest.param(
            Op.SIGPARAM,
            sweep(
                Op.SIGPARAM,
                ARBITRARY_ENTRIES,
                Spec.SIGPARAM_SIGNATURE_LENGTH,
            ),
            id="sigparam_signature_length",
        ),
        pytest.param(
            Op.FRAMEDATALOAD,
            sum(
                (Op.POP(Op.FRAMEDATALOAD(0, frame)) for frame in DATA_FRAMES),
                Bytecode(),
            ),
            id="framedataload_in_range",
        ),
        pytest.param(
            Op.FRAMEDATALOAD,
            sum(
                (
                    Op.POP(Op.FRAMEDATALOAD(READABLE_LENGTH, frame))
                    for frame in DATA_FRAMES
                ),
                Bytecode(),
            ),
            id="framedataload_past_end",
        ),
        # Priced as CALLDATACOPY, so the copy size moves their cost.
        pytest.param(
            Op.FRAMEDATACOPY,
            sum(
                (Op.FRAMEDATACOPY(0, 0, 0, frame) for frame in DATA_FRAMES),
                Bytecode(),
            ),
            id="framedatacopy_size_0",
        ),
        pytest.param(
            Op.FRAMEDATACOPY,
            sum(
                (Op.FRAMEDATACOPY(0, 0, 32, frame) for frame in DATA_FRAMES),
                Bytecode(),
            ),
            id="framedatacopy_size_32",
        ),
        pytest.param(
            Op.SIGDATACOPY,
            sum(
                (
                    Op.SIGDATACOPY(0, 0, 0, entry)
                    for entry in ARBITRARY_ENTRIES
                ),
                Bytecode(),
            ),
            id="sigdatacopy_size_0",
        ),
        pytest.param(
            Op.SIGDATACOPY,
            sum(
                (
                    Op.SIGDATACOPY(0, 0, 32, entry)
                    for entry in ARBITRARY_ENTRIES
                ),
                Bytecode(),
            ),
            id="sigdatacopy_size_32",
        ),
    ],
)
def test_frame_introspection(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    opcode: Op,
    attack_block: Bytecode,
) -> None:
    """Benchmark a frame transaction introspection instruction."""
    sender = pre.fund_eoa()
    # ExtCallGenerator's stack bound does not allow for a two-input
    # instruction's extra peak, so those POP and loop in place.
    generator = (
        ExtCallGenerator
        if attack_block.pushed_stack_items > attack_block.popped_stack_items
        else JumpLoopGenerator
    )
    loop = generator(attack_block=attack_block).deploy_contracts(
        pre=pre, fork=fork
    )

    def transaction(frame_gas: int, **overrides: Any) -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=[
                verify_frame(
                    code=Bytecode(),
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                *(
                    sender_frame(
                        code=Bytecode(),
                        data=frame.to_bytes(READABLE_LENGTH, "big"),
                        gas_limit_delta=0,
                        state_gas_limit_delta=0,
                    )
                    for frame in DATA_FRAMES
                ),
                default_frame(
                    target=loop,
                    data=LOOP_FRAME.to_bytes(READABLE_LENGTH, "big"),
                    gas_limit=frame_gas,
                    state_gas_limit=0,
                    outcome=Outcome.HALT,
                ),
            ],
            signatures=[
                canonical_entry(sender),
                *(
                    FrameSignature(
                        scheme=Spec.SCHEME_ARBITRARY,
                        signature=Bytes(
                            entry.to_bytes(READABLE_LENGTH, "big")
                        ),
                    )
                    for entry in ARBITRARY_ENTRIES
                ),
            ],
            **overrides,
        )

    payload_gas = gas_benchmark_value // math.ceil(
        gas_benchmark_value / min(tx_gas_limit, gas_benchmark_value)
    )
    # Only the frame budget grows, so one probe large enough for the
    # execution dimension to bind measures the fixed overhead.
    probe_gas = payload_gas // 2
    overhead = transaction(probe_gas, nonce=0).block_gas_used() - probe_gas
    frame_gas = payload_gas - overhead

    first = transaction(frame_gas)
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [
        transaction(frame_gas) for _ in range(iteration_count - 1)
    ]

    benchmark_test(
        pre=pre,
        target_opcode=opcode,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )
