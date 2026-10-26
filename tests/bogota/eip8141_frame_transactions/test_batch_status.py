"""
Atomic batch status tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

An atomic batch is "a maximal contiguous sequence of frames `[i, j]`
where `j > i`, frames `i` through `j - 1` have `ATOMIC_BATCH_FLAG` set,
and frame `j` does not" (§Behavior). When one of its frames fails, the
state rolls back to before the batch, its remaining frames are skipped
with status `2`, and its executed frames keep their status and
execution gas with empty logs and zero state gas.

These tests pin where a batch ends, which failures unroll it, and the
statuses a later frame reads back through `FRAMEPARAM`.
"""

from typing import Any, Dict, List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
)

from .helpers import (
    CURRENT_FRAME_INDEX,
    FrameCase,
    FrameTransaction,
    Outcome,
    account_creation_cost,
    default_frame,
    sender_frame,
    sponsored_signatures,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

WRITER_CODE = Op.SSTORE(CURRENT_FRAME_INDEX, 1) + Op.STOP
"""Mark the frame running it: write one into the slot of its index."""

REVERTER_CODE = Op.REVERT(0, 0)
"""Fail the frame running it, without consuming its whole budget."""

SLOT_WRITTEN = 0x01
"""Storage slot a single-slot worker writes."""


@pytest.mark.parametrize(
    "frame_mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="default_frames"),
        pytest.param(Spec.MODE_SENDER, id="sender_frames"),
    ],
)
def test_failed_batch_skips_only_its_own_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_mode: int,
) -> None:
    """
    Run two adjacent atomic batches of three and two frames. The first
    batch's first frame reverts, so its flagged second frame and its
    unflagged terminator are both skipped; the second batch, which
    starts right after that terminator, runs in full.

    EIP-8141 §Behavior: "If a frame's execution reverts, [...] if this
    frame has the atomic batch flag set, mark all subsequent frames in
    the same atomic group as skipped." and "An **atomic batch** is a
    maximal contiguous sequence of frames `[i, j]` where `j > i`,
    frames `i` through `j - 1` have `ATOMIC_BATCH_FLAG` set, and frame
    `j` does not have `ATOMIC_BATCH_FLAG` set." §Receipt Encoding: "A
    new code `0x2` is introduced for frames which are skipped due to
    failed atomic batch."

    Every worker frame writes the slot of its own frame index, so the
    post-state shows which frames ran. A client that ends the skip at
    the first frame, or carries it into the next batch, fails both the
    receipts and the storage.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=WRITER_CODE)
    reverter = pre.deploy_contract(code=REVERTER_CODE)

    def frame(**overrides: Any) -> FrameCase:
        return FrameCase(mode=frame_mode, **overrides)

    frames: List[FrameCase] = [
        verify_frame(),
        # First batch: frames 1 to 3.
        frame(
            flags=Spec.ATOMIC_BATCH_FLAG,
            target=reverter,
            code=REVERTER_CODE,
            outcome=Outcome.REVERT,
        ),
        frame(
            flags=Spec.ATOMIC_BATCH_FLAG,
            target=writer,
            outcome=Outcome.SKIPPED,
        ),
        frame(target=writer, outcome=Outcome.SKIPPED),
        # Second batch: frames 4 and 5, the writer still cold.
        frame(
            flags=Spec.ATOMIC_BATCH_FLAG,
            target=writer,
            code=WRITER_CODE,
        ),
        frame(target=writer, code=WRITER_CODE, warm=True),
    ]
    tx = FrameTransaction.build(fork=fork, sender=sender, frames=frames)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            writer: Account(storage={2: 0, 3: 0, 4: 1, 5: 1}),
        },
    )


def test_batch_before_any_approval_unrolls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Run an atomic batch at the start of the transaction, before any
    frame approved anything: its terminator reverts, so its first
    frame's write is unrolled, and the `VERIFY` frame after the batch
    still approves.

    EIP-8141 §Behavior: "When a frame in the batch fails, the state
    must be rolled back to the condition it was immediately before the
    atomic batch began." and "`APPROVE` is not possible within a batch,
    so it is not necessary to rollback anything related to `payer` or
    `sender_approved`." The unroll restores the state from before the
    first frame of the transaction, and leaves the approval context,
    still empty, for the `VERIFY` frame to fill.
    """
    sender = pre.fund_eoa()
    worker_code = Op.SSTORE(SLOT_WRITTEN, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    reverter = pre.deploy_contract(code=REVERTER_CODE)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=worker,
                code=worker_code,
                outcome=Outcome.UNROLLED,
            ),
            default_frame(
                target=reverter, code=REVERTER_CODE, outcome=Outcome.REVERT
            ),
            verify_frame(),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_WRITTEN: 0}),
        },
    )


def test_value_shortfall_unrolls_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    End an atomic batch with a `SENDER` frame carrying one wei more
    than the sender holds: the frame reverts on the balance check,
    which unrolls the batch frame before it.

    EIP-8141 §Behavior: "As with an ordinary `CALL`, if the caller does
    not have sufficient balance to transfer `frame.value`, the frame
    reverts, consuming the gas charged so far." and "If a frame is
    part of an atomic batch and it fails, unroll the associated atomic
    batch." The failing frame's receipt reports its target's entry
    access, the only gas charged before the check.

    A sponsor pays, so the sender's balance, and with it the
    shortfall, is fixed by the pre-state alone.
    """
    sender_balance = 10**15
    sender = pre.fund_eoa(amount=sender_balance)
    payer = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)
    worker_code = Op.SSTORE(SLOT_WRITTEN, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            sender_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=worker,
                code=worker_code,
                outcome=Outcome.UNROLLED,
            ),
            sender_frame(
                target=recipient,
                value=sender_balance + 1,
                outcome=Outcome.REVERT,
            ),
        ],
        signatures=sponsored_signatures(sender, payer),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=sender_balance),
            recipient: Account(balance=1),
            worker: Account(storage={SLOT_WRITTEN: 0}),
        },
    )


def test_new_account_charge_halt_unrolls_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    End an atomic batch with a `SENDER` frame sending value to an
    address with no account, budgeted one state gas less than the
    account creation: the frame halts exceptionally, which unrolls the
    batch frame before it.

    EIP-8141 §Behavior: "If `frame.value > 0` and `resolved_target`
    does not exist, `STATE_BYTES_PER_NEW_ACCOUNT * CPSB` state gas is
    charged after the balance check and before the frame's code
    executes [...]. If `state_gas_left` cannot cover the charge, the
    frame halts exceptionally." and "If a frame is part of an atomic
    batch and it fails, unroll the associated atomic batch." The
    halting frame forfeits its whole execution budget and the new
    account is never created.
    """
    sender = pre.fund_eoa()
    absent = pre.nonexistent_account()
    worker_code = Op.SSTORE(SLOT_WRITTEN, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=worker,
                code=worker_code,
                outcome=Outcome.UNROLLED,
            ),
            sender_frame(
                target=absent,
                value=1,
                state_gas_limit=account_creation_cost(fork) - 1,
                outcome=Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            absent: Account.NONEXISTENT,
            worker: Account(storage={SLOT_WRITTEN: 0}),
        },
    )


SLOT_STATUS = 0x10
"""Base of the slots recording each frame's status, plus one."""

SLOT_EXECUTION_GAS_USED = 0x20
"""Base of the slots recording each frame's execution gas, plus one."""

SLOT_STATE_GAS_USED = 0x30
"""Base of the slots recording each frame's state gas, plus one."""


def test_frameparam_reads_batch_outcomes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    After an atomic batch whose second frame reverts, a probe frame
    reads back through `FRAMEPARAM` each batch frame's status and gas:
    the unrolled frame reports success with its execution gas and zero
    state gas, the reverted frame failure, and the skipped terminator
    status `2` with no gas.

    EIP-8141 §Behavior: "Executed frame receipts retain their
    execution status and execution gas used, with empty logs and zero
    state gas used." and "All remaining frames in the atomic batch are
    skipped." §`FRAMEPARAM`: "The `status` field (0x05) returns `0`
    for failure, `1` for success, or `2` for a frame skipped due to a
    failed atomic batch." and "The `gas_used.execution` (0x0A) and
    `gas_used.state` (0x0B) fields return the current values recorded
    in the frame's receipt."

    The probe records each value plus one, so a read of zero is told
    apart from a slot never written.
    """
    sender = pre.fund_eoa()
    worker_code = Op.SSTORE(SLOT_WRITTEN, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    reverter = pre.deploy_contract(code=REVERTER_CODE)

    batch = [1, 2, 3]
    probe_code = Bytecode()
    for index in batch:
        probe_code += (
            Op.SSTORE(
                SLOT_STATUS + index,
                Op.ADD(1, Op.FRAMEPARAM(index, Spec.FRAMEPARAM_STATUS)),
            )
            + Op.SSTORE(
                SLOT_EXECUTION_GAS_USED + index,
                Op.ADD(
                    1,
                    Op.FRAMEPARAM(index, Spec.FRAMEPARAM_EXECUTION_GAS_USED),
                ),
            )
            + Op.SSTORE(
                SLOT_STATE_GAS_USED + index,
                Op.ADD(
                    1, Op.FRAMEPARAM(index, Spec.FRAMEPARAM_STATE_GAS_USED)
                ),
            )
        )
    probe_code += Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    unrolled = default_frame(
        flags=Spec.ATOMIC_BATCH_FLAG,
        target=worker,
        code=worker_code,
        outcome=Outcome.UNROLLED,
    )
    reverted = default_frame(
        flags=Spec.ATOMIC_BATCH_FLAG,
        target=reverter,
        code=REVERTER_CODE,
        outcome=Outcome.REVERT,
    )
    skipped = default_frame(target=worker, outcome=Outcome.SKIPPED)
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            unrolled,
            reverted,
            skipped,
            default_frame(
                target=probe,
                code=probe_code,
                # Headroom keeps the last write clear of the call
                # stipend check, which an exact budget would trip.
                gas_limit_delta=fork.gas_costs().CALL_STIPEND + 1,
                state_gas_limit_delta=0,
            ),
        ],
    )

    storage: Dict[int, int] = {}
    for index, case in zip(batch, [unrolled, reverted, skipped], strict=True):
        receipt = case.receipt(fork)
        assert receipt.status is not None and receipt.gas_used is not None
        storage[SLOT_STATUS + index] = int(receipt.status) + 1
        storage[SLOT_EXECUTION_GAS_USED + index] = int(receipt.gas_used) + 1
        storage[SLOT_STATE_GAS_USED + index] = 1
    # The premises the reads pin: success, failure and skip, and a
    # write whose state gas the unroll zeroed.
    assert [storage[SLOT_STATUS + index] for index in batch] == [2, 1, 3]
    assert worker_code.state_cost(fork) > 0

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_WRITTEN: 0}),
            probe: Account(storage=storage),
        },
    )
