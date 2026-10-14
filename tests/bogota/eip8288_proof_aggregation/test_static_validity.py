"""
Static validity of dependency verification frames (EIP-8288): the
encoding of their claims, the claim count, the accepted scheme, the
frame's target, flags, value and gas budgets, and its place outside
atomic batches.

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
    Bytes,
    Fork,
    Frame,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    TransactionTestFiller,
)

from tests.bogota.eip7906_transaction_assertions.helpers import post_tx_frame
from tests.bogota.eip8141_frame_transactions.helpers import (
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .helpers import (
    claim,
    dependency_frame,
    dependency_receipt,
    encode_dependencies,
    verification_gas,
)
from .spec import Spec, ref_spec_8288

REFERENCE_SPEC_GIT_PATH = ref_spec_8288.git_path
REFERENCE_SPEC_VERSION = ref_spec_8288.version

pytestmark = pytest.mark.valid_from("EIP8288")

FrameList = Callable[[Fork, Address, Address], List[Frame]]
"""Build a case's frames from the sender and a no-op contract."""


def with_byte(data: Bytes, index: int, value: int) -> Bytes:
    """Return `data` with the byte at `index` replaced by `value`."""
    return Bytes(data[:index] + bytes([value]) + data[index + 1 :])


ONE_CLAIM = encode_dependencies([claim(1)])

INVALID_FRAME_LISTS = [
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, []),
            verify_frame(),
        ],
        id="no_claims",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(
                fork,
                [claim(1)],
                data=ONE_CLAIM[: Spec.DEPENDENCY_LENGTH - 1],
            ),
            verify_frame(),
        ],
        id="truncated_claim",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, [claim(1)], data=ONE_CLAIM + b"\x00"),
            verify_frame(),
        ],
        id="trailing_byte",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(
                fork, [claim(1)], data=with_byte(ONE_CLAIM, 0, 1)
            ),
            verify_frame(),
        ],
        id="nonzero_first_padding_byte",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(
                fork, [claim(1)], data=with_byte(ONE_CLAIM, 30, 1)
            ),
            verify_frame(),
        ],
        id="nonzero_last_padding_byte",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(
                fork, [claim(1), claim(2, scheme=Spec.LEANSTARK_SCHEME)]
            ),
            verify_frame(),
        ],
        id="reserved_leanstark_scheme",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, [claim(1, scheme=0x00)]),
            verify_frame(),
        ],
        id="zero_scheme",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, [claim(1, scheme=0x12)]),
            verify_frame(),
        ],
        id="undefined_scheme",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(
                fork,
                [
                    claim(index)
                    for index in range(Spec.MAX_DEPENDENCIES_PER_FRAME + 1)
                ],
            ),
            verify_frame(),
        ],
        id="claims_above_max",
    ),
    pytest.param(
        lambda fork, sender, _noop: [
            dependency_frame(fork, [claim(1)], target=sender),
            verify_frame(),
        ],
        id="explicit_sender_target",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, [claim(1)], target=Address(0)),
            verify_frame(),
        ],
        id="zero_address_target",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, [claim(1)], flags=Spec8141.APPROVE_PAYMENT),
            verify_frame(),
        ],
        id="approval_flag",
    ),
    pytest.param(
        lambda fork, _sender, noop: [
            verify_frame(),
            dependency_frame(
                fork, [claim(1)], flags=Spec8141.ATOMIC_BATCH_FLAG
            ),
            sender_frame(target=noop),
        ],
        id="opens_atomic_batch",
    ),
    pytest.param(
        lambda fork, _sender, noop: [
            verify_frame(),
            sender_frame(target=noop, flags=Spec8141.ATOMIC_BATCH_FLAG),
            dependency_frame(fork, [claim(1)]),
        ],
        id="terminates_atomic_batch",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, [claim(1)], value=1),
            verify_frame(),
        ],
        id="value",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(
                fork, [claim(1)], gas_limit=verification_gas(fork, 1) - 1
            ),
            verify_frame(),
        ],
        id="execution_gas_below_verification_gas",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(
                fork, [claim(1)], gas_limit=verification_gas(fork, 1) + 1
            ),
            verify_frame(),
        ],
        id="execution_gas_above_verification_gas",
    ),
    pytest.param(
        lambda fork, _sender, _noop: [
            dependency_frame(fork, [claim(1)], state_gas_limit=1),
            verify_frame(),
        ],
        id="state_gas",
    ),
    pytest.param(
        lambda fork, _sender, noop: [
            verify_frame(),
            post_tx_frame(fork, target=noop),
            dependency_frame(fork, [claim(1)]),
        ],
        id="after_post_tx",
    ),
]
"""
Frame lists breaking one dependency frame rule each. The explicit
sender target names the account an absent target resolves to, so only
the absent-target rule rejects it. A batch flag on the frame before a
dependency frame makes it the batch's terminator. A dependency frame
cannot follow a `POST_TX` frame, which only `POST_TX` frames may
follow.
"""


def invalid_dependency_transaction(
    pre: Alloc, fork: Fork, frame_list: FrameList
) -> Transaction:
    """Return a frame transaction built from one invalid frame list."""
    sender = pre.fund_eoa()
    noop = pre.deploy_contract(code=Op.STOP)
    return Transaction(
        sender=sender,
        frames=frame_list(fork, sender, noop),
        error=TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
    )


@pytest.mark.exception_test
@pytest.mark.parametrize("frame_list", INVALID_FRAME_LISTS)
def test_dependency_frame_static_rules(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_list: FrameList,
) -> None:
    """Reject a frame transaction breaking one dependency frame rule."""
    tx = invalid_dependency_transaction(pre, fork, frame_list)
    state_test(pre=pre, tx=tx, post={tx.sender: Account(nonce=0)})


@pytest.mark.exception_test
@pytest.mark.parametrize("frame_list", INVALID_FRAME_LISTS)
def test_dependency_frame_static_rules_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_list: FrameList,
) -> None:
    """
    Assert `test_dependency_frame_static_rules` on the transaction
    itself rather than on a block containing it.
    """
    transaction_test(
        pre=pre, tx=invalid_dependency_transaction(pre, fork, frame_list)
    )


@pytest.mark.parametrize(
    "claim_counts",
    [
        pytest.param([1], id="one_claim"),
        pytest.param([Spec.MAX_DEPENDENCIES_PER_FRAME], id="max_claims"),
        pytest.param([1, 1], id="two_frames"),
    ],
)
@pytest.mark.parametrize("before_verify", [True, False])
def test_dependency_frame_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    claim_counts: List[int],
    before_verify: bool,
) -> None:
    """
    Accept dependency frames at the claim count boundaries, before or
    after the frame approving the transaction.
    """
    sender = pre.fund_eoa()
    dependency_frames = [
        dependency_frame(
            fork,
            [claim(position * 1000 + index) for index in range(count)],
        )
        for position, count in enumerate(claim_counts)
    ]
    dependency_receipts = [
        dependency_receipt(fork, count) for count in claim_counts
    ]
    verify_receipts = [FrameReceipt(status=Spec8141.STATUS_SUCCESS)]
    if before_verify:
        frames = [*dependency_frames, verify_frame()]
        receipts = [*dependency_receipts, *verify_receipts]
    else:
        frames = [verify_frame(), *dependency_frames]
        receipts = [*verify_receipts, *dependency_receipts]
    tx = Transaction(
        sender=sender,
        frames=frames,
        expected_receipt=TransactionReceipt(
            payer=sender, frame_receipts=receipts
        ),
    )
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})
