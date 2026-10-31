"""
Transient storage tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The EIP discards the `TSTORE`/`TLOAD` transient storage between frames
(§Cross-frame interactions: "Discard the `TSTORE` and `TLOAD` transient
storage between frames"), with no exception for the frames of an atomic
batch. Each frame therefore starts with empty transient storage,
whatever an earlier frame wrote, whether the two frames belong to one
atomic batch, and whether a frame in between failed. Within one frame,
transient storage behaves as in any other transaction: a `TLOAD` after
a `TSTORE` returns the stored value.

Most tests run a recorder contract in several frames. In each frame it
reads its transient slot at entry, writes it, and reads it back,
recording both reads in storage slots keyed by the frame's index.
"""

from typing import Any, Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Fork,
    Op,
    StateTestFiller,
)

from .helpers import (
    APPROVE_ALL,
    CURRENT_FRAME_INDEX,
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

TRANSIENT_KEY = 0x01
"""Transient storage key every test writes and reads."""

TRANSIENT_VALUE = 0x2A
"""Value the recorder writes into its transient slot."""

FAILED_FRAME_TRANSIENT_VALUE = 0x99
"""Value a failing frame writes into the slot before it fails."""

CALLING_FRAME_GAS = 200_000
"""Execution gas budget of the frames whose target calls another account."""

SLOT_SEEN_AT_ENTRY = 0x00
"""
Base of the storage slots recording the transient value a frame reads
at entry; frame `i` records into `SLOT_SEEN_AT_ENTRY + i`.
"""

SLOT_SEEN_AFTER_TSTORE = 0x100
"""
Base of the storage slots recording the transient value a frame reads
after writing it; frame `i` records into `SLOT_SEEN_AFTER_TSTORE + i`.
"""

RECORDER_CODE = (
    # The entry read is expected to find the slot empty, so this write
    # stores zero into an empty storage slot.
    Op.SSTORE(
        Op.ADD(SLOT_SEEN_AT_ENTRY, CURRENT_FRAME_INDEX),
        Op.TLOAD(TRANSIENT_KEY),
        new_value=0,
    )
    + Op.TSTORE(TRANSIENT_KEY, TRANSIENT_VALUE)
    + Op.SSTORE(
        Op.ADD(SLOT_SEEN_AFTER_TSTORE, CURRENT_FRAME_INDEX),
        Op.TLOAD(TRANSIENT_KEY),
    )
    + Op.STOP
)
"""
Record the transient value at frame entry, write the transient slot,
and record the value read back within the same frame.
"""


def recorded(*frame_indices: int) -> Dict[int, int]:
    """
    Return the storage the recorder holds after running in each of
    `frame_indices`: every frame found its transient slot empty at
    entry, and read its own write back.
    """
    storage: Dict[int, int] = {}
    for index in frame_indices:
        storage[SLOT_SEEN_AT_ENTRY + index] = 0
        storage[SLOT_SEEN_AFTER_TSTORE + index] = TRANSIENT_VALUE
    return storage


def recorder_frame(
    mode: int, recorder: Address, **overrides: Any
) -> FrameCase:
    """Return a frame of `mode` running the recorder at `recorder`."""
    return FrameCase(
        mode=mode, target=recorder, code=RECORDER_CODE, **overrides
    )


@pytest.mark.parametrize(
    "first_mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="from_default"),
        pytest.param(Spec.MODE_SENDER, id="from_sender"),
    ],
)
@pytest.mark.parametrize(
    "second_mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="to_default"),
        pytest.param(Spec.MODE_SENDER, id="to_sender"),
    ],
)
def test_transient_storage_discarded_between_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    first_mode: int,
    second_mode: int,
) -> None:
    """
    Run the recorder in two consecutive frames: the second frame finds
    empty the transient slot the first frame wrote.

    EIP-8141 §Cross-frame interactions: "Discard the `TSTORE` and
    `TLOAD` transient storage between frames." Both frames also read
    their own write back within the frame, which the readback slots pin
    to `TRANSIENT_VALUE`: discarding happens between frames, not within
    one.
    """
    sender = pre.fund_eoa()
    recorder = pre.deploy_contract(code=RECORDER_CODE)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            recorder_frame(first_mode, recorder),
            # The first frame's success leaves the recorder warm.
            recorder_frame(second_mode, recorder, warm=True),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            recorder: Account(storage=recorded(1, 2)),
        },
    )


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="default_batch"),
        pytest.param(Spec.MODE_SENDER, id="sender_batch"),
    ],
)
def test_transient_storage_discarded_between_atomic_batch_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: int,
) -> None:
    """
    Run the recorder in the three frames of one successful atomic
    batch: each batch frame finds empty the transient slot the previous
    batch frame wrote.

    EIP-8141 §Cross-frame interactions discards transient storage
    "between frames", and its atomic-batch rules (§Behavior: "If a frame
    is part of an atomic batch and it fails, unroll the associated
    atomic batch") only add an unroll on failure; nothing exempts the
    frames of one batch from the discard.
    """
    sender = pre.fund_eoa()
    recorder = pre.deploy_contract(code=RECORDER_CODE)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            recorder_frame(mode, recorder, flags=Spec.ATOMIC_BATCH_FLAG),
            recorder_frame(
                mode, recorder, flags=Spec.ATOMIC_BATCH_FLAG, warm=True
            ),
            recorder_frame(mode, recorder, warm=True),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            recorder: Account(storage=recorded(1, 2, 3)),
        },
    )


@pytest.mark.parametrize(
    "failure,failed_outcome,in_batch",
    [
        pytest.param(
            Op.REVERT(0, 0), Outcome.REVERT, False, id="frame_reverts"
        ),
        pytest.param(Op.INVALID, Outcome.HALT, False, id="frame_halts"),
        pytest.param(
            Op.REVERT(0, 0), Outcome.REVERT, True, id="atomic_batch_unrolls"
        ),
    ],
)
def test_transient_storage_discarded_after_failed_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure: Bytecode,
    failed_outcome: Outcome,
    in_batch: bool,
) -> None:
    """
    Fail a frame after the recorder's first frame wrote the transient
    slot, and check that the recorder's last frame finds it empty.

    The last frame's entry read is zero only if transient storage is
    discarded between frames (EIP-8141 §Cross-frame interactions:
    "Discard the `TSTORE` and `TLOAD` transient storage between
    frames"); `TRANSIENT_VALUE` there means the first frame's write
    survived. The failing frame also writes the slot, with
    `FAILED_FRAME_TRANSIENT_VALUE`, but its own failure already undoes
    that write under EIP-1153's journaling, so reading it back would
    expose a client that does not journal transient storage, not one
    that skips the discard.
    """
    # Frames supplying calldata fail, the others record.
    code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=Op.TSTORE(TRANSIENT_KEY, FAILED_FRAME_TRANSIENT_VALUE)
        + failure,
        if_false=RECORDER_CODE,
    )
    sender = pre.fund_eoa()
    recorder = pre.deploy_contract(code=code)
    record_state_gas = RECORDER_CODE.state_cost(fork)

    def record(**overrides: Any) -> FrameCase:
        overrides.setdefault("state_gas_used", record_state_gas)
        return default_frame(target=recorder, pin_gas=False, **overrides)

    batch = []
    # The unroll restores the pre-batch state. A client whose unroll also
    # restored transient storage as it stood when the first frame ended
    # would bring its write back, so this case pins the discard after an
    # unroll too.
    if in_batch:
        batch.append(
            record(
                flags=Spec.ATOMIC_BATCH_FLAG,
                outcome=Outcome.UNROLLED,
                state_gas_used=0,
            )
        )
    batch.append(
        default_frame(
            target=recorder,
            data=Bytes(b"\x01"),
            outcome=failed_outcome,
            pin_gas=False,
        )
    )

    frames = [verify_frame(), record(), *batch, record()]
    tx = FrameTransaction.build(fork=fork, sender=sender, frames=frames)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            recorder: Account(storage=recorded(1, len(frames) - 1)),
        },
    )


def test_transient_storage_discarded_before_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Write the sender's transient slot in a `DEFAULT` frame; the
    following `VERIFY` frame of the same account approves only if it
    finds the slot empty.

    EIP-8141 §Cross-frame interactions: "Discard the `TSTORE` and
    `TLOAD` transient storage between frames." A `VERIFY` frame runs as
    a `STATICCALL` (§Behavior: "Execute the frame as a `STATICCALL`"),
    which allows `TLOAD` but not `TSTORE`, so the write comes from an
    earlier frame of another mode targeting the sender. If the write
    survived, the `VERIFY` frame would revert and the transaction would
    be invalid.
    """
    writer = Op.TSTORE(TRANSIENT_KEY, TRANSIENT_VALUE) + Op.STOP
    verifier = Conditional(
        condition=Op.ISZERO(Op.TLOAD(TRANSIENT_KEY)),
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    # The `DEFAULT` frame supplies calldata, the `VERIFY` frame none.
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=writer,
        if_false=verifier,
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            default_frame(target=sender, data=Bytes(b"\x01"), pin_gas=False),
            verify_frame(pin_gas=False),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})


SLOT_SEEN_BY_CALLEE = 0x200
"""
Base of the storage slots recording the transient value a called
account reads; frame `i` records into `SLOT_SEEN_BY_CALLEE + i`.
"""


def test_transient_storage_discarded_for_called_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A frame's target calls a second account, which writes its own
    transient slot, then calls it again to read the slot back. In the
    next frame another target calls the same account to read the slot:
    it is empty, although the account was never a frame's target.

    EIP-8141 §Cross-frame interactions: "Discard the `TSTORE` and
    `TLOAD` transient storage between frames." The discard covers all
    transient storage, not only the frame target's. The read within
    the first frame shows the write was made and survived its call.

    The called account records each read plus one, so an empty slot
    reads as 1.
    """
    record = Op.SSTORE(
        Op.ADD(SLOT_SEEN_BY_CALLEE, CURRENT_FRAME_INDEX),
        Op.ADD(1, Op.TLOAD(TRANSIENT_KEY)),
    )
    callee_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=Op.TSTORE(TRANSIENT_KEY, TRANSIENT_VALUE),
        if_false=record,
    )
    callee = pre.deploy_contract(code=callee_code)
    writer_code = (
        Op.POP(Op.CALL(gas=Op.GAS, address=callee, args_size=1))
        + Op.POP(Op.CALL(gas=Op.GAS, address=callee))
        + Op.STOP
    )
    writer = pre.deploy_contract(code=writer_code)
    reader = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=callee)) + Op.STOP
    )
    # Each frame is charged the callee's record of its read.
    slot_gas = record.state_cost(fork)
    sender = pre.fund_eoa()

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=writer,
                gas_limit=CALLING_FRAME_GAS,
                pin_gas=False,
                state_gas_used=slot_gas,
            ),
            default_frame(
                target=reader,
                gas_limit=CALLING_FRAME_GAS,
                pin_gas=False,
                state_gas_used=slot_gas,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            callee: Account(
                storage={
                    SLOT_SEEN_BY_CALLEE + 1: TRANSIENT_VALUE + 1,
                    SLOT_SEEN_BY_CALLEE + 2: 1,
                }
            ),
        },
    )
