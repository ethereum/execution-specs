"""
Test SETCODEFROM inside the frames of an
[EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction.

A `VERIFY` frame is static, so `SETCODEFROM` halts in it. An adoption in a
later frame changes the code that following frames resolve, unrolls with a
failed atomic batch, and treats every frame of the transaction as the same
transaction when checking whether its source was created in it.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create_address,
)

from ..eip8141_frame_transactions.helpers import (
    default_frame,
    sender_frame,
    verify_frame,
)
from ..eip8141_frame_transactions.spec import Spec as Spec8141
from .helpers import (
    MARKER_A,
    MARKER_SLOT,
    RESULT_SLOT,
    SENTINEL,
    SSTORE_MARKER_A,
)
from .spec import ref_spec_8298

REFERENCE_SPEC_GIT_PATH = ref_spec_8298.git_path
REFERENCE_SPEC_VERSION = ref_spec_8298.version

pytestmark = pytest.mark.valid_from("EIP8298")

APPROVE_ALL = Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT)
"""Approve the transaction's execution and payment."""


def approve_then(later_frames_code: Bytecode) -> Bytecode:
    """
    Return sender code that approves in the transaction's first frame and
    runs `later_frames_code` in every later frame.
    """
    return Conditional(
        condition=Op.ISZERO(Op.TXPARAM(Spec8141.TXPARAM_CURRENT_FRAME_INDEX)),
        if_true=APPROVE_ALL,
        if_false=later_frames_code,
    )


def adopt(source: Address) -> Bytecode:
    """Return code that adopts `source` and stores the result."""
    return Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(source)) + Op.STOP


@pytest.mark.exception_test
def test_verify_frame_halts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify `SETCODEFROM` halts in a `VERIFY` frame, which runs static, so
    the sender never approves and the transaction is invalid.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    sender_code = Op.POP(Op.SETCODEFROM(template)) + APPROVE_ALL
    sender = pre.deploy_contract(sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame()],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(
        pre=pre, post={sender: Account(code=sender_code, nonce=1)}, tx=tx
    )


def test_later_frame_runs_adopted_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify the sender adopting code in a `SENDER` frame finishes that
    frame on its old code, and the next frame targeting the sender runs
    the adopted code.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    sender = pre.deploy_contract(approve_then(adopt(template)), balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame(), sender_frame(), sender_frame()],
    )

    state_test(
        pre=pre,
        post={
            sender: Account(
                code=SSTORE_MARKER_A,
                storage={RESULT_SLOT: 1, MARKER_SLOT: MARKER_A},
            )
        },
        tx=tx,
    )


@pytest.mark.parametrize(
    "batch_fails",
    [
        pytest.param(False, id="batch-succeeds"),
        pytest.param(True, id="batch-fails"),
    ],
)
def test_atomic_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    batch_fails: bool,
) -> None:
    """
    Verify an adoption in an atomic batch is kept when the batch
    succeeds, and unrolled with the rest of the batch when a later frame
    of the batch fails.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    sender_code = approve_then(adopt(template))
    sender = pre.deploy_contract(sender_code, balance=10**18)
    batch_end = pre.deploy_contract(
        Op.REVERT(0, 0) if batch_fails else Op.STOP
    )

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(),
            sender_frame(flags=Spec8141.ATOMIC_BATCH_FLAG),
            default_frame(target=batch_end),
        ],
    )

    post_sender = (
        Account(code=sender_code, storage={})
        if batch_fails
        else Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1})
    )
    state_test(pre=pre, post={sender: post_sender}, tx=tx)


@pytest.mark.parametrize(
    "created_in_earlier_frame",
    [
        pytest.param(False, id="pre-existing-source"),
        pytest.param(True, id="source-created-earlier-frame"),
    ],
)
def test_source_created_in_earlier_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    created_in_earlier_frame: bool,
) -> None:
    """
    Verify a source created by an earlier frame of the same frame
    transaction is invalid, so the adoption pushes 0, while a source that
    existed before the transaction is adopted.
    """
    initcode = Initcode(deploy_code=SSTORE_MARKER_A)
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(Op.CREATE(0, 0, Op.CALLDATASIZE))
        + Op.STOP
    )
    if created_in_earlier_frame:
        source = compute_create_address(address=factory, nonce=1)
    else:
        source = pre.deploy_contract(SSTORE_MARKER_A)
    sender_code = approve_then(adopt(source))
    sender = pre.deploy_contract(
        sender_code, balance=10**18, storage={RESULT_SLOT: SENTINEL}
    )

    post: Dict[Address, Account] = {
        sender: (
            Account(code=sender_code, storage={RESULT_SLOT: 0})
            if created_in_earlier_frame
            else Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1})
        ),
        source: Account(code=SSTORE_MARKER_A),
    }
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(),
            default_frame(target=factory, data=initcode),
            sender_frame(),
        ],
    )

    state_test(pre=pre, post=post, tx=tx)
