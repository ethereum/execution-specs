"""
Static validity of frame transactions carrying `ASSERT` frames
(EIP-7906): the mode's suffix rule, its value restriction, and its
place outside atomic batches.

The first mode value beyond `ASSERT` is rejected by the EIP-8141
suite's `test_first_undefined_frame_mode`, which reads the boundary
from the fork.

As in the EIP-8141 static validity suite, each rejected case fills as
a state test, which checks the verdict against the reference
implementation, and as a transaction test, which pins the verdict
itself.
"""

from typing import Callable, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    Frame,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    TransactionTestFiller,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    default_frame,
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .helpers import assert_frame, success_receipts
from .spec import ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")

FrameList = Callable[[Fork, Address, Address], List[Frame]]
"""Build a case's frames from a no-op contract and a reverting one."""

INVALID_FRAME_LISTS = [
    pytest.param(
        lambda fork, noop, _: [
            verify_frame(),
            assert_frame(fork, target=noop),
            sender_frame(target=noop),
        ],
        id="sender_after_assert",
    ),
    pytest.param(
        lambda fork, noop, _: [
            verify_frame(),
            assert_frame(fork, target=noop),
            default_frame(target=noop),
        ],
        id="default_after_assert",
    ),
    pytest.param(
        lambda fork, noop, _: [
            verify_frame(),
            assert_frame(fork, target=noop),
            verify_frame(target=noop, flags=Spec8141.APPROVE_PAYMENT),
        ],
        id="verify_after_assert",
    ),
    pytest.param(
        lambda fork, noop, _: [
            verify_frame(),
            assert_frame(fork, target=noop, value=1),
        ],
        id="assert_with_value",
    ),
    pytest.param(
        lambda fork, noop, _: [
            verify_frame(),
            assert_frame(fork, target=noop, flags=Spec8141.ATOMIC_BATCH_FLAG),
            assert_frame(fork, target=noop),
        ],
        id="assert_with_atomic_batch_flag",
    ),
    pytest.param(
        lambda fork, noop, failure: [
            verify_frame(),
            sender_frame(target=failure, flags=Spec8141.ATOMIC_BATCH_FLAG),
            assert_frame(fork, target=noop),
        ],
        id="batch_ends_on_assert",
    ),
    pytest.param(
        lambda fork, noop, failure: [
            verify_frame(),
            sender_frame(target=noop),
            sender_frame(target=failure, flags=Spec8141.ATOMIC_BATCH_FLAG),
            assert_frame(fork, target=noop),
        ],
        id="failing_batch_skips_assertion",
    ),
]
"""
Frame lists breaking one `ASSERT` static rule each: only `ASSERT`
frames may follow one, an `ASSERT` frame carries no value and no atomic
batch flag, and no atomic batch may end on an `ASSERT` frame.

The `VERIFY` frame after an `ASSERT` frame carries only the payment
scope, so no rule but the suffix rule rejects it. A failing batch
before an `ASSERT` frame would skip the assertion and keep the frame
before the batch.
"""


def invalid_assert_transaction(
    pre: Alloc, fork: Fork, frame_list: FrameList
) -> Transaction:
    """Return a frame transaction built from one invalid frame list."""
    noop = pre.deploy_contract(code=Op.STOP)
    failure = pre.deploy_contract(code=Op.REVERT(0, 0))
    return Transaction(
        sender=pre.fund_eoa(),
        frames=frame_list(fork, noop, failure),
        error=TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
    )


@pytest.mark.exception_test
@pytest.mark.parametrize("frame_list", INVALID_FRAME_LISTS)
def test_assert_frame_static_rules(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_list: FrameList,
) -> None:
    """Reject a frame transaction breaking one `ASSERT` static rule."""
    tx = invalid_assert_transaction(pre, fork, frame_list)
    state_test(pre=pre, tx=tx, post={tx.sender: Account(nonce=0)})


@pytest.mark.exception_test
@pytest.mark.parametrize("frame_list", INVALID_FRAME_LISTS)
def test_assert_frame_static_rules_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_list: FrameList,
) -> None:
    """
    Assert `test_assert_frame_static_rules` on the transaction itself rather
    than on a block containing it.
    """
    transaction_test(
        pre=pre, tx=invalid_assert_transaction(pre, fork, frame_list)
    )


def test_assert_frame_suffix_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Accept several `ASSERT` frames as the trailing suffix of a
    transaction with an execution body.
    """
    sender = pre.fund_eoa()
    noop = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(target=noop),
            assert_frame(fork, target=noop),
            assert_frame(fork, target=noop),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender, frame_receipts=success_receipts(4)
        ),
    )
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})
