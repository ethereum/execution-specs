"""
Tests for the introspection instructions of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`TXPARAM`, `FRAMEDATALOAD`, `FRAMEDATACOPY`, `FRAMEPARAM`, `SIGPARAM`
and `SIGDATACOPY` are exercised from a `DEFAULT` frame that stores what
it reads, so the post state pins the value each selector returns.

The instructions take full 256-bit operands. An undefined selector, an
index past the end of the frame or signature list, a receipt field of
a frame that has not completed, and a read the entry's scheme does not
allow each halt exceptionally; offsets and lengths follow the
`CALLDATALOAD`/`CALLDATACOPY` rules, zero-filling past the end of the
data. Wide operands such as `0x100` and `2**256-1` catch a client that
narrows an operand before checking it. Where a marker cannot tell a
halt from a revert, the probe runs in a `DEFAULT` frame whose receipt
pins the halt: an exceptional halt reports status `0` and consumes the
frame's whole execution budget, which neither a successful read nor a
revert does.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    DEFAULT_FRAME_GAS_LIMIT,
    DEFAULT_FRAME_STATE_GAS_LIMIT,
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

from .helpers import (
    APPROVE_ALL,
    CURRENT_FRAME_INDEX,
    FrameCase,
    FrameTransaction,
    Outcome,
    approving_contract_sender,
    default_frame,
    sender_frame,
    verify_frame,
)
from .signature_helpers import (
    DIGEST,
    P256_SIGNER,
    canonical_entry,
    signed_digest_entry,
    valid_p256_entry,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_RESULT = 0x01
"""Storage slot the probe contract writes what it read into."""

PROBE_FRAME_DATA = Bytes(bytes(range(1, 41)))
"""Data of the probe frame: 40 bytes, so a word read is truncated."""

PROBE_FRAME_GAS = 500_000
"""Execution gas budget of the probe frames."""

PROBE_FRAME_STATE_GAS = 200_000
"""
State gas budget of the probe frames, distinct from the framework
default so a probe reading its own frame's budget pins the right one.
"""

MAX_PRIORITY_FEE = 7
MAX_FEE = 1_000_000_000

ARBITRARY_WITNESS = Bytes(b"\xab" * 5)

ARBITRARY_MSG = Bytes(b"\x5a" * 32)
"""Explicit `msg` of an `ARBITRARY` signature entry."""


def probe_transaction(
    sender: EOA,
    probe: Address,
    signatures: List[FrameSignature] | None = None,
) -> Transaction:
    """
    Return a two frame transaction: a `VERIFY` frame approving through
    the sender's default code, followed by a `DEFAULT` frame calling
    the probe contract at index 1.
    """
    return Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=PROBE_FRAME_STATE_GAS,
                data=PROBE_FRAME_DATA,
            ),
        ],
        signatures=signatures,
    )


@pytest.mark.parametrize(
    "param,expected",
    [
        pytest.param(Spec.TXPARAM_TYPE, Spec.FRAME_TX_TYPE, id="type"),
        pytest.param(Spec.TXPARAM_NONCE, 0, id="nonce"),
        pytest.param(
            Spec.TXPARAM_MAX_PRIORITY_FEE_PER_GAS,
            MAX_PRIORITY_FEE,
            id="priority_fee",
        ),
        pytest.param(Spec.TXPARAM_MAX_FEE, MAX_FEE, id="max_fee"),
        pytest.param(Spec.TXPARAM_BLOB_COUNT, 0, id="blob_count"),
        pytest.param(Spec.TXPARAM_FRAME_COUNT, 2, id="frame_count"),
        pytest.param(Spec.TXPARAM_CURRENT_FRAME_INDEX, 1, id="frame_index"),
        pytest.param(Spec.TXPARAM_SIGNATURE_COUNT, 1, id="signature_count"),
    ],
)
def test_txparam(
    state_test: StateTestFiller,
    pre: Alloc,
    param: int,
    expected: int,
) -> None:
    """Read transaction scoped information through `TXPARAM`."""
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.TXPARAM(param)) + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_txparam_sender_and_sig_hash(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the sender and the canonical signature hash through `TXPARAM`.

    The canonical hash covers the raw signature bytes of the entry
    signing it, so its value is not known when the test is authored and
    the probe can only pin that it reads back nonzero. The `msg`
    readback of an explicit-digest entry, by contrast, is pinned to the
    exact digest the entry was verified over.
    """
    explicit_msg = Bytes(b"\x5a" * 32)
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.TXPARAM(Spec.TXPARAM_SENDER))
        + Op.SSTORE(
            SLOT_RESULT + 1,
            Op.ISZERO(Op.TXPARAM(Spec.TXPARAM_SIG_HASH)),
        )
        + Op.SSTORE(SLOT_RESULT + 2, Op.SIGPARAM(1, Spec.SIGPARAM_MSG))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(
            sender,
            probe,
            signatures=[
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)
                ),
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1,
                    signer=Bytes(sender),
                    msg=explicit_msg,
                ),
            ],
        ),
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: sender,
                    SLOT_RESULT + 1: 0,
                    SLOT_RESULT + 2: int.from_bytes(explicit_msg, "big"),
                }
            )
        },
    )


def test_txparam_state_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read the executing frame's remaining state gas pool through
    `TXPARAM`, before and after a write that draws from it.

    The first read happens before any state charge, so it reports the
    frame's full budget; the write storing it creates a fresh slot, so
    the second read reports the budget less that slot's creation.
    """
    sender = pre.fund_eoa()
    first_write = Op.SSTORE(
        SLOT_RESULT, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT)
    )
    probe = pre.deploy_contract(
        code=first_write
        + Op.SSTORE(SLOT_RESULT + 1, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: PROBE_FRAME_STATE_GAS,
                    SLOT_RESULT + 1: PROBE_FRAME_STATE_GAS
                    - first_write.state_cost(fork),
                }
            )
        },
    )


@pytest.mark.parametrize(
    "frame_index,param,expected",
    [
        pytest.param(0, Spec.FRAMEPARAM_MODE, Spec.MODE_VERIFY, id="mode"),
        pytest.param(
            0,
            Spec.FRAMEPARAM_FLAGS,
            Spec.APPROVE_EXECUTION_AND_PAYMENT,
            id="flags",
        ),
        pytest.param(
            0,
            Spec.FRAMEPARAM_ALLOWED_SCOPE,
            Spec.APPROVE_EXECUTION_AND_PAYMENT,
            id="allowed_scope",
        ),
        pytest.param(0, Spec.FRAMEPARAM_DATA_LENGTH, 0, id="empty_data"),
        pytest.param(
            0,
            Spec.FRAMEPARAM_EXECUTION_GAS_LIMIT,
            DEFAULT_FRAME_GAS_LIMIT,
            id="gas_limit",
        ),
        pytest.param(
            0,
            Spec.FRAMEPARAM_STATE_GAS_LIMIT,
            DEFAULT_FRAME_STATE_GAS_LIMIT,
            id="state_gas_limit",
        ),
        pytest.param(0, Spec.FRAMEPARAM_ATOMIC_BATCH, 0, id="atomic_batch"),
        pytest.param(
            0,
            Spec.FRAMEPARAM_STATUS,
            Spec.STATUS_SUCCESS,
            id="status_of_earlier_frame",
        ),
        pytest.param(
            1,
            Spec.FRAMEPARAM_DATA_LENGTH,
            len(PROBE_FRAME_DATA),
            id="data_length",
        ),
        pytest.param(1, Spec.FRAMEPARAM_VALUE, 0, id="value"),
        pytest.param(
            1,
            Spec.FRAMEPARAM_EXECUTION_GAS_LIMIT,
            PROBE_FRAME_GAS,
            id="own_gas_limit",
        ),
        pytest.param(
            1,
            Spec.FRAMEPARAM_STATE_GAS_LIMIT,
            PROBE_FRAME_STATE_GAS,
            id="own_state_gas_limit",
        ),
    ],
)
def test_frameparam(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_index: int,
    param: int,
    expected: int,
) -> None:
    """
    Read frame scoped information through `FRAMEPARAM`.

    Unlike the receipt-reported selectors, a frame's declared budgets
    are static data: reading the executing frame's own state gas
    budget is allowed.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.FRAMEPARAM(frame_index, param))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_frameparam_resolved_target(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    `FRAMEPARAM` reports the resolved target, so a frame with an empty
    target reads back as the transaction sender.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_RESULT, Op.FRAMEPARAM(0, Spec.FRAMEPARAM_RESOLVED_TARGET)
        )
        + Op.SSTORE(
            SLOT_RESULT + 1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_RESOLVED_TARGET)
        )
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={
            probe: Account(
                storage={SLOT_RESULT: sender, SLOT_RESULT + 1: probe}
            )
        },
    )


def test_frameparam_atomic_batch_set(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the atomic batch flag of a frame that carries it back as one
    through `FRAMEPARAM`, both via the dedicated selector and the raw
    flags.

    A flagged frame cannot be the transaction's last, so a `DEFAULT`
    frame targeting the sender trails the batch.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_RESULT, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_ATOMIC_BATCH)
        )
        + Op.SSTORE(SLOT_RESULT + 1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_FLAGS))
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
            ),
            default_frame(),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: 1,
                    SLOT_RESULT + 1: Spec.ATOMIC_BATCH_FLAG,
                }
            )
        },
    )


def test_frameparam_gas_used(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read a completed frame's receipt gas usage — both dimensions —
    through `FRAMEPARAM`.

    A worker frame performs one fresh storage write, so its receipt
    reports the frame entry's cold target access plus the write's
    execution gas in one dimension and the slot's creation in the
    other.
    """
    sender = pre.fund_eoa()
    worker_code = Op.SSTORE(SLOT_RESULT, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    probe_code = (
        Op.SSTORE(
            SLOT_RESULT,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_EXECUTION_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_RESULT + 1,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    worker_frame = default_frame(target=worker, code=worker_code)
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            worker_frame,
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=PROBE_FRAME_STATE_GAS,
            ),
        ],
    )

    worker_receipt = worker_frame.receipt(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            worker: Account(storage={SLOT_RESULT: 1}),
            probe: Account(
                storage={
                    SLOT_RESULT: worker_receipt.gas_used,
                    SLOT_RESULT + 1: worker_receipt.state_gas_used,
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "frame_index,param",
    [
        pytest.param(1, Spec.FRAMEPARAM_STATUS, id="status_of_current_frame"),
        pytest.param(
            1,
            Spec.FRAMEPARAM_EXECUTION_GAS_USED,
            id="execution_gas_used_of_current_frame",
        ),
        pytest.param(
            1,
            Spec.FRAMEPARAM_STATE_GAS_USED,
            id="state_gas_used_of_current_frame",
        ),
        pytest.param(2, Spec.FRAMEPARAM_MODE, id="frame_index_out_of_bounds"),
        pytest.param(0, 0x0C, id="undefined_param"),
    ],
)
def test_frameparam_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_index: int,
    param: int,
) -> None:
    """
    `FRAMEPARAM` halts exceptionally on the receipt-reported selectors
    — status and gas usage — of the current frame, an out of bounds
    frame index, and an undefined selector. The halt fails the frame
    without invalidating the transaction, because the frame does not
    run in `VERIFY` mode.

    The probe writes a marker before the halting read, so a selector
    that returned zero instead of halting would leave the marker
    behind.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 0xFF)
        + Op.POP(Op.FRAMEPARAM(frame_index, param))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: 0})},
    )


@pytest.mark.parametrize(
    "halting_read",
    [
        pytest.param(
            Op.POP(Op.TXPARAM(0x0D)),
            id="txparam_undefined_param",
        ),
        # The per-gas and per-blob-gas fee caps and the maximum cost
        # selectors were removed with the `max_fee` budget.
        pytest.param(
            Op.POP(Op.TXPARAM(0x05)),
            id="txparam_removed_max_fee_per_blob_gas",
        ),
        pytest.param(
            Op.POP(Op.TXPARAM(0x06)),
            id="txparam_removed_max_cost",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0, 0x04)),
            id="sigparam_undefined_copy_param",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0, 0x05)),
            id="sigparam_undefined_param",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0, Spec.SIGPARAM_SIGNATURE_LENGTH)),
            id="sigparam_length_of_protocol_validated_entry",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(1, Spec.SIGPARAM_SCHEME)),
            id="sigparam_signature_index_out_of_bounds",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 32, 1),
            id="sigdatacopy_signature_index_out_of_bounds",
        ),
        pytest.param(
            Op.POP(Op.FRAMEDATALOAD(0, 2)),
            id="framedataload_frame_index_out_of_bounds",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 32, 2),
            id="framedatacopy_frame_index_out_of_bounds",
        ),
    ],
)
def test_introspection_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    halting_read: Bytecode,
) -> None:
    """
    `TXPARAM`, `SIGPARAM`, `SIGDATACOPY`, `FRAMEDATALOAD` and
    `FRAMEDATACOPY` halt exceptionally on undefined selectors, out of
    bounds indices, and the signature length of a protocol-validated
    entry — the raw signature bytes the protocol validates are not
    introspectable, their length included. `SIGPARAM`'s former copy
    selector (`0x04`) is undefined. The halt fails the frame without
    invalidating the transaction, because the frame does not run in
    `VERIFY` mode.

    The probe transaction carries two frames and one protocol-validated
    signature entry, so frame index 2 and signature index 1 are the
    first indices out of bounds. The probe writes a marker before the
    halting read, so a read that returned a value instead of halting
    would leave the marker behind.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 0xFF) + halting_read + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: 0})},
    )


# Halts pinned by the probe frame's receipt. The `*_first_*` cases
# restate the boundary values of `test_introspection_halts` and
# `test_frameparam_halts` under this oracle, since their marker cannot
# tell a halt from a revert.

MAX_U256 = 2**256 - 1
"""Largest operand value."""

HALT_PROBE_GAS = 100_000
"""Execution gas budget of the probe frames whose receipt is pinned."""

LONG_ARBITRARY_WITNESS = Bytes(bytes(range(0x81, 0x81 + 40)))
"""Raw bytes of the receipt-pinned probes' `ARBITRARY` entry: 40 bytes."""

# Signature entries of the halting probe's transaction.
SIG_SECP256K1 = 0
SIG_P256 = 1
SIG_ARBITRARY = 2
SIGNATURE_COUNT = 3

# Frames of the halting probe's transaction.
PROBE_FRAME = 1
FRAME_COUNT = 2


def probe_signatures(sender: EOA) -> List[FrameSignature]:
    """
    Return the halting probe's signature entries: the sender's entry
    over the canonical hash, a valid P256 entry and an `ARBITRARY`
    entry, one per scheme.
    """
    return [
        canonical_entry(sender),
        valid_p256_entry(),
        FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY,
            msg=ARBITRARY_MSG,
            signature=LONG_ARBITRARY_WITNESS,
        ),
    ]


def run_probe(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    probe_code: Bytecode,
    outcome: Outcome,
) -> None:
    """
    Run `probe_code` in frame 1 of a two-frame transaction carrying one
    signature entry of each scheme, and pin the probe frame's receipt
    to `outcome`.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(code=probe_code)
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=HALT_PROBE_GAS,
                data=PROBE_FRAME_DATA,
                outcome=outcome,
            ),
        ],
        signatures=probe_signatures(sender),
    )
    assert tx.frames is not None and len(tx.frames) == FRAME_COUNT
    assert tx.signatures is not None
    assert len(tx.signatures) == SIGNATURE_COUNT
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(Op.TXPARAM(0x0D), id="txparam_first_undefined"),
        pytest.param(Op.TXPARAM(0x100), id="txparam_0x100"),
        pytest.param(Op.TXPARAM(MAX_U256), id="txparam_max"),
        pytest.param(
            Op.FRAMEPARAM(PROBE_FRAME, 0x0C), id="frameparam_first_undefined"
        ),
        pytest.param(Op.FRAMEPARAM(PROBE_FRAME, 0x100), id="frameparam_0x100"),
        pytest.param(
            Op.FRAMEPARAM(PROBE_FRAME, MAX_U256), id="frameparam_max"
        ),
        pytest.param(
            Op.SIGPARAM(SIG_SECP256K1, 0x04), id="sigparam_first_undefined"
        ),
        pytest.param(Op.SIGPARAM(SIG_SECP256K1, 0x101), id="sigparam_0x101"),
        pytest.param(Op.SIGPARAM(SIG_SECP256K1, MAX_U256), id="sigparam_max"),
    ],
)
def test_undefined_selector_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    read: Bytecode,
) -> None:
    """
    Halt on a selector past the defined ones, including values whose
    low byte is a defined selector (`0x100` reads as `TYPE` or
    `RESOLVED_TARGET`, `0x101` as `SCHEME` if narrowed to a byte).

    EIP-8141 §`TXPARAM`: "Undefined `param` values result in an
    exceptional halt." §`FRAMEPARAM` and §`SIGPARAM`, Notes: "Undefined
    `param` values result in an exceptional halt."
    """
    run_probe(state_test, pre, fork, Op.POP(read) + Op.STOP, Outcome.HALT)


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(
            Op.POP(Op.FRAMEPARAM(FRAME_COUNT, Spec.FRAMEPARAM_MODE)),
            id="frameparam_first_out_of_bounds",
        ),
        pytest.param(
            Op.POP(Op.FRAMEPARAM(0x100 + PROBE_FRAME, Spec.FRAMEPARAM_MODE)),
            id="frameparam_index_0x101",
        ),
        pytest.param(
            Op.POP(Op.FRAMEPARAM(MAX_U256, Spec.FRAMEPARAM_MODE)),
            id="frameparam_index_max",
        ),
        pytest.param(
            Op.POP(Op.FRAMEDATALOAD(0, 0x100 + PROBE_FRAME)),
            id="framedataload_index_0x101",
        ),
        pytest.param(
            Op.POP(Op.FRAMEDATALOAD(0, MAX_U256)),
            id="framedataload_index_max",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 32, 0x100 + PROBE_FRAME),
            id="framedatacopy_index_0x101",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 32, MAX_U256),
            id="framedatacopy_index_max",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 0, FRAME_COUNT),
            id="framedatacopy_index_out_of_bounds_zero_length",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(SIGNATURE_COUNT, Spec.SIGPARAM_SCHEME)),
            id="sigparam_first_out_of_bounds",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0x100 + SIG_SECP256K1, Spec.SIGPARAM_SCHEME)),
            id="sigparam_index_0x100",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(MAX_U256, Spec.SIGPARAM_SCHEME)),
            id="sigparam_index_max",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 32, 0x100 + SIG_ARBITRARY),
            id="sigdatacopy_index_0x102",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 0, SIGNATURE_COUNT),
            id="sigdatacopy_index_out_of_bounds_zero_length",
        ),
    ],
)
def test_out_of_bounds_index_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    read: Bytecode,
) -> None:
    """
    Halt on a frame or signature index at or past the end of its list,
    including indices whose low byte names an existing entry and copies
    of zero bytes.

    EIP-8141 §`FRAMEPARAM`, Notes: "Out-of-bounds access for
    `frameIndex` results in an exceptional halt." §`FRAMEDATALOAD` and
    §`FRAMEDATACOPY`: "When the `frameIndex` is out-of-bounds, an
    exceptional halt occurs." §`SIGPARAM`, Notes: "Out-of-bounds access
    for `signatureIndex` results in an exceptional halt."
    §`SIGDATACOPY`: "When the `signatureIndex` is out-of-bounds, an
    exceptional halt occurs." None of them exempts a zero `length`.
    """
    run_probe(state_test, pre, fork, read + Op.STOP, Outcome.HALT)


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(
            Op.POP(Op.SIGPARAM(SIG_P256, Spec.SIGPARAM_SIGNATURE_LENGTH)),
            id="sigparam_length_of_p256",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(SIG_ARBITRARY, Spec.SIGPARAM_RESOLVED_SIGNER)),
            id="sigparam_signer_of_arbitrary",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 32, SIG_P256), id="sigdatacopy_of_p256"
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 0, SIG_P256),
            id="sigdatacopy_of_p256_zero_length",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 0, SIG_SECP256K1),
            id="sigdatacopy_of_secp256k1_zero_length",
        ),
    ],
)
def test_scheme_restricted_read_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    read: Bytecode,
) -> None:
    """
    Halt on a signature read the entry's scheme does not define: the
    length or bytes of a protocol-validated entry, even zero bytes of
    them, and the resolved signer of an `ARBITRARY` entry.

    EIP-8141 §`SIGPARAM`, Notes: "For `ARBITRARY` signature entries,
    requesting `resolved_signer` results in an exceptional halt." and
    "For signature entries of any other `scheme`, requesting
    `len(signature)` results in an exceptional halt."
    §`SIGDATACOPY`: "If the referenced signature entry's `scheme` is
    not `ARBITRARY`, an exceptional halt occurs."
    """
    run_probe(state_test, pre, fork, read + Op.STOP, Outcome.HALT)


@pytest.mark.parametrize(
    "copy,outcome",
    [
        pytest.param(
            Op.FRAMEDATACOPY(MAX_U256, 0, 1, PROBE_FRAME),
            Outcome.HALT,
            id="frame",
        ),
        pytest.param(
            Op.SIGDATACOPY(MAX_U256, 0, 1, SIG_ARBITRARY),
            Outcome.HALT,
            id="signature",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(MAX_U256, 0, 0, PROBE_FRAME),
            Outcome.SUCCESS,
            id="frame_zero_length",
        ),
        pytest.param(
            Op.SIGDATACOPY(MAX_U256, 0, 0, SIG_ARBITRARY),
            Outcome.SUCCESS,
            id="signature_zero_length",
        ),
    ],
)
def test_copy_to_unreachable_memory_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    copy: Bytecode,
    outcome: Outcome,
) -> None:
    """
    Copy one byte to memory offset `2**256-1`: the memory expansion
    cannot be paid, so the copy halts out of gas. The same copy of zero
    bytes expands no memory and succeeds, the passing side of the pair.

    EIP-8141 §`FRAMEDATACOPY`: "Its gas cost is calculated exactly as
    for `CALLDATACOPY`, including [...] the standard EVM memory
    expansion cost." §`SIGDATACOPY` states the same. The end of the
    region, `2**256`, overflows a 256-bit sum, so a client wrapping it
    to zero would skip the expansion and copy instead.
    """
    run_probe(state_test, pre, fork, copy + Op.STOP, outcome)


@pytest.mark.parametrize(
    "frame_index,outcome",
    [
        pytest.param(0, Outcome.SUCCESS, id="earlier_frame"),
        # The reader's own frame: the first index whose receipt is not
        # yet defined.
        pytest.param(PROBE_FRAME, Outcome.HALT, id="current_frame"),
        pytest.param(2, Outcome.HALT, id="later_frame"),
    ],
)
@pytest.mark.parametrize(
    "param",
    [
        pytest.param(Spec.FRAMEPARAM_STATUS, id="status"),
        pytest.param(
            Spec.FRAMEPARAM_EXECUTION_GAS_USED, id="execution_gas_used"
        ),
        pytest.param(Spec.FRAMEPARAM_STATE_GAS_USED, id="state_gas_used"),
    ],
)
def test_receipt_field_of_later_frame_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_index: int,
    outcome: Outcome,
    param: int,
) -> None:
    """
    Read a receipt field of a frame that has not completed, the
    reader's own or the one after it: the read halts. The same read of
    the frame before the reader's is the passing side of the boundary
    and succeeds; the values it reads are pinned in
    `test_frameparam[status_of_earlier_frame]` and
    `test_frameparam_gas_used`.

    EIP-8141 §`FRAMEPARAM`, Notes: "Like `status`, they are defined
    only for frames that have completed; accessing them for the current
    frame or a subsequent frame results in an exceptional halt." and
    "Attempting to access the return `status` of the current frame or
    a subsequent frame results in an exceptional halt."
    """
    sender = pre.fund_eoa()
    probe_code = Op.POP(Op.FRAMEPARAM(frame_index, param)) + Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=HALT_PROBE_GAS,
                outcome=outcome,
            ),
            # The frame read, which runs codeless at the warm sender.
            default_frame(target=sender, warm=True),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_sigparam_with_no_signature_entries_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    In a transaction with no signature entry, read the scheme of entry
    0: the read halts.

    EIP-8141 §`SIGPARAM`, Notes: "Out-of-bounds access for
    `signatureIndex` results in an exceptional halt." With an empty
    list, every index is out of bounds. The sender is a contract that
    approves through its code, so the transaction needs no entry.
    """
    sender = approving_contract_sender(pre)
    probe_code = Op.POP(Op.SIGPARAM(0, Spec.SIGPARAM_SCHEME)) + Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        signatures=[],
        frames=[
            verify_frame(pin_gas=False),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=HALT_PROBE_GAS,
                outcome=Outcome.HALT,
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})


@pytest.mark.parametrize(
    "frame_index,offset,expected",
    [
        pytest.param(
            1,
            0,
            int.from_bytes(PROBE_FRAME_DATA[0:32], "big"),
            id="first_word",
        ),
        pytest.param(
            1,
            32,
            int.from_bytes(PROBE_FRAME_DATA[32:].ljust(32, b"\x00"), "big"),
            id="tail_zero_padded",
        ),
        pytest.param(1, 64, 0, id="past_the_end"),
        pytest.param(0, 0, 0, id="empty_frame_data"),
    ],
)
def test_framedataload(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_index: int,
    offset: int,
    expected: int,
) -> None:
    """
    Read a word of a frame's data through `FRAMEDATALOAD`, including
    reads that run past the end and read as zeroes.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.FRAMEDATALOAD(offset, frame_index))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_framedatacopy(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Copy a frame's data into memory through `FRAMEDATACOPY`, including
    a copy that straddles the end of the data and is zero filled.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.FRAMEDATACOPY(0, 0, 32, 1)
        + Op.SSTORE(SLOT_RESULT, Op.MLOAD(0))
        + Op.FRAMEDATACOPY(32, 32, 32, 1)
        + Op.SSTORE(SLOT_RESULT + 1, Op.MLOAD(32))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: int.from_bytes(PROBE_FRAME_DATA[0:32], "big"),
                    SLOT_RESULT + 1: int.from_bytes(
                        PROBE_FRAME_DATA[32:].ljust(32, b"\x00"), "big"
                    ),
                }
            )
        },
    )


@pytest.mark.parametrize(
    "signature_index,param,expected",
    [
        pytest.param(
            0,
            Spec.SIGPARAM_SCHEME,
            Spec.SCHEME_SECP256K1,
            id="secp256k1_scheme",
        ),
        pytest.param(0, Spec.SIGPARAM_MSG, 0, id="canonical_hash_msg"),
        pytest.param(
            1,
            Spec.SIGPARAM_SCHEME,
            Spec.SCHEME_ARBITRARY,
            id="arbitrary_scheme",
        ),
        pytest.param(
            1,
            Spec.SIGPARAM_SIGNATURE_LENGTH,
            len(ARBITRARY_WITNESS),
            id="arbitrary_length",
        ),
    ],
)
def test_sigparam(
    state_test: StateTestFiller,
    pre: Alloc,
    signature_index: int,
    param: int,
    expected: int,
) -> None:
    """Read signature scoped metadata through `SIGPARAM`."""
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.SIGPARAM(signature_index, param))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(
            sender,
            probe,
            signatures=[
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)
                ),
                FrameSignature(
                    scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_WITNESS
                ),
            ],
        ),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_sigparam_resolved_signer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the resolved signer of a protocol-validated entry through
    `SIGPARAM`, and check the same read against an `ARBITRARY` entry
    halts the frame instead: the protocol assigns no signer to bytes
    it does not validate.

    The refused probe writes a marker before the halting read, so a
    read that returned a value instead of halting would leave the
    marker behind.
    """
    sender = pre.fund_eoa()
    resolved = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_RESULT, Op.SIGPARAM(0, Spec.SIGPARAM_RESOLVED_SIGNER)
        )
        + Op.STOP
    )
    refused = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 0xFF)
        + Op.POP(Op.SIGPARAM(1, Spec.SIGPARAM_RESOLVED_SIGNER))
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                target=resolved,
                gas_limit=PROBE_FRAME_GAS,
            ),
            default_frame(
                target=refused,
                gas_limit=PROBE_FRAME_GAS,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_WITNESS
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            resolved: Account(storage={SLOT_RESULT: sender}),
            refused: Account(storage={SLOT_RESULT: 0}),
        },
    )


def test_sigdatacopy(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Copy an `ARBITRARY` entry's raw signature bytes into memory
    through `SIGDATACOPY`, including the zero fill past the end of the
    signature, and check that the same copy against a protocol
    validated entry halts the frame instead.
    """
    sender = pre.fund_eoa()
    copied = pre.deploy_contract(
        code=Op.SIGDATACOPY(0, 0, 32, 1)
        + Op.SSTORE(SLOT_RESULT, Op.MLOAD(0))
        + Op.STOP
    )
    refused = pre.deploy_contract(
        code=Op.SIGDATACOPY(0, 0, 32, 0) + Op.SSTORE(SLOT_RESULT, 1) + Op.STOP
    )

    signatures = [
        FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
        FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_WITNESS
        ),
    ]

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                target=copied,
                gas_limit=PROBE_FRAME_GAS,
            ),
            default_frame(
                target=refused,
                gas_limit=PROBE_FRAME_GAS,
            ),
        ],
        signatures=signatures,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            copied: Account(
                storage={
                    SLOT_RESULT: int.from_bytes(
                        bytes(ARBITRARY_WITNESS).ljust(32, b"\x00"), "big"
                    )
                }
            ),
            refused: Account(storage={SLOT_RESULT: 0}),
        },
    )


SLOT_ZERO_LENGTH_COPY = 0x01
SLOT_LOAD_FAR = 0x02
SLOT_COPY_FAR = 0x03
SLOT_SIG_COPY_FAR = 0x04
SLOT_STRADDLE_HEAD = 0x05
SLOT_STRADDLE_TAIL = 0x06
SLOT_ORDERED_COPY = 0x07
SLOT_ORDERED_MSIZE = 0x08
SLOT_ORDERED_SIG_COPY = 0x09

ALL_ONES = MAX_U256
"""Memory canary a zero-filling copy has to overwrite."""


def test_copy_and_load_operand_ranges(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read the probe frame's data and the `ARBITRARY` entry's bytes with
    offsets past their end and with distinct operands, in two probes
    whose writes pin each result.

    The probes check that:

    - a zero-length copy to memory offset `2**256-1` succeeds without
      expanding memory (`MSIZE` stays unchanged);
    - `FRAMEDATALOAD` at offset `2**256-1` reads zero;
    - a 32-byte copy from data offset `2**256-1` writes 32 zero bytes
      over a canary, for frame data and signature bytes alike;
    - a copy straddling the end of the data writes the tail and then
      zeroes over a second canary;
    - `FRAMEDATACOPY(memOffset=64, dataOffset=8, length=16, i)` and its
      `SIGDATACOPY` twin copy `data[8:24]` to memory offset 64; the
      first leaves `MSIZE` at `memOffset + length` rounded up to a
      whole word, read before anything else touches memory, which pins
      the operand order.

    EIP-8141 §`FRAMEDATALOAD`: "The operation semantics match
    CALLDATALOAD". §`FRAMEDATACOPY`: "The operation semantics match
    CALLDATACOPY, copying `length` bytes from the chosen frame's
    `data`, starting at the given byte `dataOffset`, into a memory
    region starting at `memOffset`." with stack `memOffset`,
    `dataOffset`, `length`, `frameIndex` from the top. §`SIGDATACOPY`:
    "Bytes beyond the end of the signature are copied as zeroes."

    Values that may be zero are stored plus one, so a zero read is told
    apart from a write that never happened.
    """
    canary = Op.MSTORE(0, ALL_ONES)
    probe_code = (
        Op.FRAMEDATACOPY(MAX_U256, 0, 0, PROBE_FRAME)
        + Op.SSTORE(SLOT_ZERO_LENGTH_COPY, Op.ADD(1, Op.MSIZE))
        + Op.SSTORE(
            SLOT_LOAD_FAR, Op.ADD(1, Op.FRAMEDATALOAD(MAX_U256, PROBE_FRAME))
        )
        + canary
        + Op.FRAMEDATACOPY(0, MAX_U256, 32, PROBE_FRAME)
        + Op.SSTORE(SLOT_COPY_FAR, Op.ADD(1, Op.MLOAD(0)))
        + canary
        + Op.SIGDATACOPY(0, MAX_U256, 32, SIG_ARBITRARY)
        + Op.SSTORE(SLOT_SIG_COPY_FAR, Op.ADD(1, Op.MLOAD(0)))
        + Op.MSTORE(32, ALL_ONES)
        + Op.FRAMEDATACOPY(0, 8, 64, PROBE_FRAME)
        + Op.SSTORE(SLOT_STRADDLE_HEAD, Op.MLOAD(0))
        + Op.SSTORE(SLOT_STRADDLE_TAIL, Op.ADD(1, Op.MLOAD(32)))
        + Op.STOP
    )
    # A fresh memory for the operand-order copies, so `MSIZE` reports
    # their expansion alone.
    ordered_code = (
        Op.FRAMEDATACOPY(64, 8, 16, PROBE_FRAME)
        + Op.SSTORE(SLOT_ORDERED_MSIZE, Op.MSIZE)
        + Op.SSTORE(SLOT_ORDERED_COPY, Op.MLOAD(64))
        + Op.SIGDATACOPY(64, 8, 16, SIG_ARBITRARY)
        + Op.SSTORE(SLOT_ORDERED_SIG_COPY, Op.MLOAD(64))
        + Op.STOP
    )
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(code=probe_code)
    ordered = pre.deploy_contract(code=ordered_code)

    def frame(target: Address, code: Bytecode) -> FrameCase:
        return default_frame(
            target=target,
            gas_limit=PROBE_FRAME_GAS,
            data=PROBE_FRAME_DATA,
            pin_gas=False,
            state_gas_limit=code.state_cost(fork),
            state_gas_used=code.state_cost(fork),
        )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            frame(probe, probe_code),
            frame(ordered, ordered_code),
        ],
        signatures=probe_signatures(sender),
    )

    def word(data: bytes) -> int:
        return int.from_bytes(data.ljust(32, b"\x00")[:32], "big")

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                storage={
                    SLOT_ZERO_LENGTH_COPY: 1,
                    SLOT_LOAD_FAR: 1,
                    SLOT_COPY_FAR: 1,
                    SLOT_SIG_COPY_FAR: 1,
                    SLOT_STRADDLE_HEAD: word(PROBE_FRAME_DATA[8:40]),
                    SLOT_STRADDLE_TAIL: 1,
                }
            ),
            ordered: Account(
                storage={
                    SLOT_ORDERED_COPY: word(PROBE_FRAME_DATA[8:24]),
                    # `memOffset + length` rounded up to a whole word.
                    SLOT_ORDERED_MSIZE: 96,
                    SLOT_ORDERED_SIG_COPY: word(LONG_ARBITRARY_WITNESS[8:24]),
                }
            ),
        },
    )


FRAME_VALUE = 123
"""Value a value-bearing `SENDER` frame carries."""

SLOT_SIGNER = 0x00
"""Base of the slots recording each entry's resolved signer."""

SLOT_SCHEME = 0x10
"""Base of the slots recording each entry's scheme, plus one."""

SLOT_MSG = 0x20
"""Base of the slots recording each entry's `msg`, plus one."""


def test_sigparam_reads_every_scheme(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read the resolved signer, scheme and `msg` of four entries: the
    sender's secp256k1 entry with an empty signer and `msg`, a
    secp256k1 entry from another key with an explicit signer and
    `msg`, a P256 entry, and an `ARBITRARY` entry with a `msg`.

    EIP-8141 §Transaction Signatures: "For `SECP256K1` and `P256`, the
    `signer` is a 20-byte Ethereum address. If absent, `tx.sender` is
    used (for introspections as well)." and "The explicit 32-byte zero
    digest is invalid. This reserves the zero stack value as the
    EVM-visible representation of the transaction signing hash case."
    §`SIGPARAM`: `SIGPARAM_RESOLVED_SIGNER` returns `resolved_signer`,
    `SIGPARAM_SCHEME` returns `scheme`, `SIGPARAM_MSG` returns `msg`.
    `ARBITRARY` entries have no resolved signer, so theirs is not read.

    Scheme and `msg` are stored plus one, since `ARBITRARY` is scheme 0
    and an empty `msg` reads as 0.
    """
    sender = pre.fund_eoa()
    other = pre.fund_eoa()
    assert other.key is not None
    signatures = [
        FrameSignature(scheme=Spec.SCHEME_SECP256K1, secret_key=sender.key),
        signed_digest_entry(other.key, signer=Bytes(other)),
        valid_p256_entry(),
        FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY,
            msg=ARBITRARY_MSG,
            signature=ARBITRARY_WITNESS,
        ),
    ]
    signers: List[Address | Bytes] = [sender, other, P256_SIGNER]
    schemes = [
        Spec.SCHEME_SECP256K1,
        Spec.SCHEME_SECP256K1,
        Spec.SCHEME_P256,
        Spec.SCHEME_ARBITRARY,
    ]
    msgs = [0, int.from_bytes(DIGEST, "big"), int.from_bytes(DIGEST, "big")]
    msgs.append(int.from_bytes(ARBITRARY_MSG, "big"))

    probe_code = Bytecode()
    expected: Dict[int, int] = {}
    for index in range(len(signatures)):
        if index < len(signers):
            probe_code += Op.SSTORE(
                SLOT_SIGNER + index,
                Op.SIGPARAM(index, Spec.SIGPARAM_RESOLVED_SIGNER),
            )
            expected[SLOT_SIGNER + index] = int.from_bytes(
                bytes(signers[index]), "big"
            )
        probe_code += Op.SSTORE(
            SLOT_SCHEME + index,
            Op.ADD(1, Op.SIGPARAM(index, Spec.SIGPARAM_SCHEME)),
        ) + Op.SSTORE(
            SLOT_MSG + index, Op.ADD(1, Op.SIGPARAM(index, Spec.SIGPARAM_MSG))
        )
        expected[SLOT_SCHEME + index] = int(schemes[index]) + 1
        expected[SLOT_MSG + index] = msgs[index] + 1
    probe_code += Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit_delta=fork.call_value_stipend() + 1,
                state_gas_limit_delta=0,
            ),
        ],
        signatures=signatures,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={probe: Account(storage=expected)},
    )


# Funding an EOA with a custom nonce mutates the shared pre-alloc.
@pytest.mark.pre_alloc_mutable
def test_txparam_nonce_is_the_transaction_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    After the sender's approval incremented its account nonce, read
    `TXPARAM_NONCE`: it still reports the transaction's nonce.

    EIP-8141 §`TXPARAM`: `TXPARAM_NONCE` returns `nonce`, the
    transaction field. §`APPROVE` Behavior increments "the sender's
    nonce" in the state, which is one higher by the time the probe
    runs.
    """
    tx_nonce = 5
    sender = pre.fund_eoa(nonce=tx_nonce)
    probe_code = (
        Op.SSTORE(SLOT_SIGNER, Op.TXPARAM(Spec.TXPARAM_NONCE)) + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=tx_nonce,
        frames=[
            verify_frame(),
            default_frame(target=probe, code=probe_code),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=tx_nonce + 1),
            probe: Account(storage={SLOT_SIGNER: tx_nonce}),
        },
    )


def test_frameparam_allowed_scope_masks_batch_flag(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A probe in an atomic batch frame reads its own allowed scope and
    flags, and the first frame's: the allowed scope drops the batch
    flag, which the flags keep.

    EIP-8141 §`FRAMEPARAM`: `FRAMEPARAM_ALLOWED_SCOPE` returns
    "`allowed_scope` (`frame.flags & APPROVE_SCOPE_MASK`)" and
    `FRAMEPARAM_FLAGS` returns `flags`. The probe's flags are
    `ATOMIC_BATCH_FLAG` alone, so its allowed scope is 0; values are
    stored plus one.
    """
    sender = pre.fund_eoa()
    probe_code = Bytecode()
    for index in (0, 1):
        probe_code += Op.SSTORE(
            index,
            Op.ADD(1, Op.FRAMEPARAM(index, Spec.FRAMEPARAM_ALLOWED_SCOPE)),
        ) + Op.SSTORE(
            0x10 + index,
            Op.ADD(1, Op.FRAMEPARAM(index, Spec.FRAMEPARAM_FLAGS)),
        )
    probe_code += Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=probe,
                code=probe_code,
                gas_limit_delta=fork.call_value_stipend() + 1,
            ),
            # The batch terminator, codeless at the warm sender.
            default_frame(target=sender, warm=True),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                storage={
                    0: Spec.APPROVE_EXECUTION_AND_PAYMENT + 1,
                    1: 1,
                    0x10: Spec.APPROVE_EXECUTION_AND_PAYMENT + 1,
                    0x11: Spec.ATOMIC_BATCH_FLAG + 1,
                }
            )
        },
    )


SLOT_MODE = 0x00
"""Base of the slots recording each frame's mode, plus one."""

SLOT_VALUE = 0x10
"""Base of the slots recording each frame's value, plus one."""


def test_frameparam_mode_and_value_of_own_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    One probe runs in a `SENDER` frame carrying value and in a
    `DEFAULT` frame, and each time records its own frame's mode and
    value, keyed by its frame index.

    EIP-8141 §`FRAMEPARAM`: `FRAMEPARAM_MODE` returns `mode` and
    `FRAMEPARAM_VALUE` returns `value`. §Mode: mode 0 is `DEFAULT`, 2
    is `SENDER`. Values are stored plus one, since the
    `DEFAULT` frame's mode and value are both 0.
    """
    sender = pre.fund_eoa()
    probe_code = (
        Op.SSTORE(
            Op.ADD(SLOT_MODE, CURRENT_FRAME_INDEX),
            Op.ADD(
                1, Op.FRAMEPARAM(CURRENT_FRAME_INDEX, Spec.FRAMEPARAM_MODE)
            ),
        )
        + Op.SSTORE(
            Op.ADD(SLOT_VALUE, CURRENT_FRAME_INDEX),
            Op.ADD(
                1, Op.FRAMEPARAM(CURRENT_FRAME_INDEX, Spec.FRAMEPARAM_VALUE)
            ),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                target=probe,
                value=FRAME_VALUE,
                code=probe_code,
                logs=[transfer_log(sender, probe, FRAME_VALUE)],
            ),
            default_frame(target=probe, code=probe_code, warm=True),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                balance=FRAME_VALUE,
                storage={
                    SLOT_MODE + 1: Spec.MODE_SENDER + 1,
                    SLOT_VALUE + 1: FRAME_VALUE + 1,
                    SLOT_MODE + 2: Spec.MODE_DEFAULT + 1,
                    SLOT_VALUE + 2: 1,
                },
            )
        },
    )


LATER_FRAME_DATA = Bytes(b"\x42" * 32)
"""Data the later `SENDER` frame carries."""


def test_verify_frame_reads_later_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A contract sender's `VERIFY` frame approves only after checking the
    `SENDER` frame that follows it: its resolved target, mode, value,
    data length and data. Every read succeeds, so the transaction is
    valid.

    EIP-8141 §`FRAMEPARAM`: only the receipt fields `status`,
    `gas_used.execution` and `gas_used.state` halt for "the current
    frame or a subsequent frame"; the frame's other fields are not
    restricted. §Security Considerations, Cross-frame Data Visibility
    During Validation: "`FRAMEPARAM`, `FRAMEDATALOAD`, and
    `FRAMEDATACOPY` allow validation code to inspect other frames,
    including later `SENDER` frames and their `value`s."
    """
    recipient = pre.fund_eoa(amount=1)
    later = 1
    checks = [
        Op.EQ(
            Op.FRAMEPARAM(later, Spec.FRAMEPARAM_RESOLVED_TARGET), recipient
        ),
        Op.EQ(Op.FRAMEPARAM(later, Spec.FRAMEPARAM_MODE), Spec.MODE_SENDER),
        Op.EQ(Op.FRAMEPARAM(later, Spec.FRAMEPARAM_VALUE), FRAME_VALUE),
        Op.EQ(
            Op.FRAMEPARAM(later, Spec.FRAMEPARAM_DATA_LENGTH),
            len(LATER_FRAME_DATA),
        ),
        Op.EQ(
            Op.FRAMEDATALOAD(0, later),
            int.from_bytes(LATER_FRAME_DATA, "big"),
        ),
    ]
    condition = checks[0]
    for check in checks[1:]:
        condition = Op.AND(condition, check)
    sender_code = Conditional(
        condition=condition,
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(pin_gas=False),
            sender_frame(
                target=recipient,
                value=FRAME_VALUE,
                data=LATER_FRAME_DATA,
                logs=[transfer_log(sender, recipient, FRAME_VALUE)],
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            recipient: Account(balance=1 + FRAME_VALUE),
        },
    )


SLOT_REFILLED = 0x05
"""Storage slot the first frame creates and the second clears."""

SLOT_BEFORE_REFILL = 0x10
"""Slot recording the first frame's state gas before the refill."""

SLOT_AFTER_REFILL = 0x11
"""Slot recording the first frame's state gas after the refill."""


def test_frameparam_state_gas_used_is_live(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Frame 1 creates a storage slot; frame 2 reads frame 1's state gas,
    clears the slot, and reads it again; frame 3 reads both frames'
    state gas. The refill lowers frame 1's reported state gas at once,
    inside frame 2, not at the end of frame 2.

    EIP-8141 §`FRAMEPARAM`, Notes: "The `gas_used.execution` (0x0A)
    and `gas_used.state` (0x0B) fields return the current values
    recorded in the frame's receipt. [...] A completed frame's
    `gas_used.state` may subsequently decrease when another frame
    refills state gas attributed to it". §Receipt Encoding: "A later
    frame may therefore reduce an earlier frame's `gas_used.state`."

    Frame 2's two records create two slots of its own, which frame 3
    reads back as frame 2's state gas. Values are stored plus one.
    """
    sender = pre.fund_eoa()
    read_first = Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED))
    create = Op.SSTORE(SLOT_REFILLED, 1)
    record_before = Op.SSTORE(SLOT_BEFORE_REFILL, read_first)
    record_after = Op.SSTORE(SLOT_AFTER_REFILL, read_first)
    clearer = record_before + Op.SSTORE(SLOT_REFILLED, 0) + record_after
    # The first frame supplies no calldata, the second one byte.
    worker_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=clearer + Op.STOP,
        if_false=create + Op.STOP,
    )
    # Frame 1 is charged its creation; frame 2 its two records.
    created_gas = create.state_cost(fork)
    records_gas = (record_before + record_after).state_cost(fork)
    worker = pre.deploy_contract(code=worker_code)
    probe_code = (
        Op.SSTORE(1, read_first)
        + Op.SSTORE(
            2, Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATE_GAS_USED))
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            # Frame 2's refill leaves frame 1 with no state gas.
            default_frame(target=worker, pin_gas=False, state_gas_used=0),
            default_frame(
                target=worker,
                data=Bytes(b"\x01"),
                pin_gas=False,
                state_gas_used=records_gas,
            ),
            default_frame(
                target=probe,
                pin_gas=False,
                state_gas_used=probe_code.state_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            worker: Account(
                storage={
                    SLOT_REFILLED: 0,
                    SLOT_BEFORE_REFILL: created_gas + 1,
                    SLOT_AFTER_REFILL: 1,
                }
            ),
            probe: Account(storage={1: 1, 2: records_gas + 1}),
        },
    )


def test_txparam_current_frame_index_in_every_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read `TXPARAM_CURRENT_FRAME_INDEX` in a `VERIFY` frame and in three
    `DEFAULT` frames running the same probe: each read is the index of
    the frame running it.

    EIP-8141 §`TXPARAM`: `TXPARAM_CURRENT_FRAME_INDEX` returns the
    "currently executing frame index". The contract sender's `VERIFY`
    frame approves only if it reads 0; the probe records, under its
    frame's index, that index plus one.
    """
    sender_code = Conditional(
        condition=Op.ISZERO(CURRENT_FRAME_INDEX),
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)
    probe_code = (
        Op.SSTORE(CURRENT_FRAME_INDEX, Op.ADD(1, CURRENT_FRAME_INDEX))
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)
    probe_frames = [1, 2, 3]

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(pin_gas=False),
            *(
                default_frame(
                    target=probe,
                    pin_gas=False,
                    state_gas_used=probe_code.state_cost(fork),
                )
                for _ in probe_frames
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            probe: Account(
                storage={index: index + 1 for index in probe_frames}
            ),
        },
    )
