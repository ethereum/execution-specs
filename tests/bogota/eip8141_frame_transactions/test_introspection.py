"""
Tests for the introspection instructions of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`TXPARAM`, `FRAMEDATALOAD`, `FRAMEDATACOPY` and `FRAMEPARAM` are
exercised from a `DEFAULT` frame that stores what it reads, so the post
state pins the value each selector returns. `HASCLAIM` is covered in
`test_claims.py`.
"""

from typing import List

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
    Claim,
    Fork,
    Frame,
    Op,
    Signer,
    StateTestFiller,
    Transaction,
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


def probe_transaction(
    sender: EOA,
    probe: Address,
    claims: List[Claim | Signer] | None = None,
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
            Frame.verify(),
            Frame.default(
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=PROBE_FRAME_STATE_GAS,
                data=PROBE_FRAME_DATA,
            ),
        ],
        claims=claims,
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

    The transaction carries no witness bytes, so the canonical hash is
    known before any claim is signed: `keccak(0x06 || 0x00 || rlp(tx))`,
    which differs from the transaction hash by the `0x00` byte.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.TXPARAM(Spec.TXPARAM_SENDER))
        + Op.SSTORE(SLOT_RESULT + 1, Op.TXPARAM(Spec.TXPARAM_SIG_HASH))
        + Op.STOP
    )
    tx = probe_transaction(sender, probe)
    sig_hash = Bytes(
        bytes([Spec.FRAME_TX_TYPE, 0x00]) + tx.rlp()[1:]
    ).keccak256()
    assert sig_hash != tx.hash

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: sender,
                    SLOT_RESULT + 1: int.from_bytes(sig_hash, "big"),
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
            Frame.verify(),
            Frame.default(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
            ),
            Frame.default(),
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

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            Frame.verify(),
            Frame.default(target=worker, code=worker_code),
            Frame.default(
                target=probe,
                code=probe_code,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=PROBE_FRAME_STATE_GAS,
            ),
        ],
    ).resolve_frames(fork)

    assert tx.expected_receipt is not None
    assert tx.expected_receipt.frame_receipts is not None
    worker_receipt = tx.expected_receipt.frame_receipts[1]

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
        # The signature count selector was removed with the signature
        # list.
        pytest.param(
            Op.POP(Op.TXPARAM(0x0B)),
            id="txparam_removed_signature_count",
        ),
        # `SIGDATACOPY` was removed with the signature list, and no
        # instruction took its opcode.
        pytest.param(
            Bytecode(b"\xb5", popped_stack_items=0, pushed_stack_items=0),
            id="removed_sigdatacopy",
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
    `TXPARAM`, `FRAMEDATALOAD` and `FRAMEDATACOPY` halt exceptionally on
    undefined selectors and out of bounds indices, and the opcode of the
    removed `SIGDATACOPY` is undefined. The halt fails the frame without
    invalidating the transaction, because the frame does not run in
    `VERIFY` mode.

    The probe transaction carries two frames, so frame index 2 is the
    first index out of bounds. The probe writes a marker before the
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
