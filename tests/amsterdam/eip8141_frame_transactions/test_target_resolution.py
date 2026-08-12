"""
Target resolution tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Only a `VERIFY` frame's codeless target runs the default code; every
other frame runs a top-level call, which dispatches a precompile by
address and follows an EIP-7702 designation. Each case pins the
resolution through the frame receipt's `gas_used`.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from .helpers import AMPLE_FRAME_GAS, default_frame, sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

# EIP-8141 is slated for the fork after Amsterdam, so fixtures are
# labeled with the pseudo `Bogota` fork (Amsterdam + EIP-8141), even
# though the spec prototypes the EIP inside the Amsterdam fork module.
# Fill these tests with `--fork Bogota`.
pytestmark = pytest.mark.valid_from("Bogota")

IDENTITY = Address(0x04)
"""The `IDENTITY` precompile, whose gas is a function of its input."""

BN254_ADD = Address(0x06)
"""The `BN254_ADD` precompile, which rejects a point off the curve."""

OFF_THE_CURVE = b"\xff" * 128
"""`BN254_ADD` input that is not a pair of curve points."""


def identity_gas(fork: Fork, data: bytes) -> int:
    """
    Return the gas a frame targeting `IDENTITY` with `data` uses, whose
    entry access is warm because the precompiles seed the warm set.
    """
    gas_costs = fork.gas_costs()
    words = (len(data) + 31) // 32
    return (
        fork.frame_entry_gas_calculator()(target_warm=True)
        + gas_costs.PRECOMPILE_IDENTITY_BASE
        + gas_costs.PRECOMPILE_IDENTITY_PER_WORD * words
    )


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="default_mode"),
        pytest.param(Spec.MODE_SENDER, id="sender_mode"),
    ],
)
@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"", id="no_input"),
        pytest.param(b"\x01" * 32, id="one_word"),
        pytest.param(b"\x01" * 33, id="two_words"),
    ],
)
def test_precompile_target(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: int,
    data: bytes,
) -> None:
    """
    Execute the precompile a frame targets, charging the frame its
    input-dependent gas on top of the warm frame-entry access.
    """
    sender = pre.fund_eoa()
    frame = default_frame if mode == Spec.MODE_DEFAULT else sender_frame

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            frame(target=IDENTITY, data=data),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=identity_gas(fork, data),
                ),
            ],
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_precompile_target_rejecting_its_input(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Fail the frame whose targeted precompile rejects its input: the
    rejection halts the frame, which forfeits its whole gas limit.
    """
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(target=BN254_ADD, data=OFF_THE_CURVE),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(
                    status=Spec.STATUS_FAILURE, gas_used=AMPLE_FRAME_GAS
                ),
            ],
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.exception_test
def test_verify_frame_precompile_target(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction whose `VERIFY` frame targets a
    precompile: the target's empty code hash routes the frame to the
    default code, which reverts because no signature entry can resolve
    to a precompile address.

    The first frame approves both execution and payment, so the
    approvals do not depend on the frame under test. Dispatching the
    precompile instead would leave every approval in place and make the
    transaction valid, rather than rejecting it for a missing approval.
    """
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            verify_frame(flags=Spec.APPROVE_NONE, target=IDENTITY),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    # The rejected transaction leaves the sender's nonce untouched.
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


@pytest.mark.parametrize(
    "warm_delegate",
    [
        pytest.param(False, id="cold_delegate"),
        pytest.param(True, id="warm_delegate"),
    ],
)
def test_delegated_target_entry_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    warm_delegate: bool,
) -> None:
    """
    Charge the access of a frame target's designated address at frame
    entry, on top of the target's own access, warm or cold.
    """
    entry_gas = fork.frame_entry_gas_calculator()
    sender = pre.fund_eoa()
    delegate = pre.deploy_contract(code=Op.STOP)
    authority = pre.fund_eoa(delegation=delegate)

    if warm_delegate:
        # The warming frame accesses the designated address itself, so
        # it pays for the cold access the frame under test then avoids.
        warming_frames = [default_frame(target=delegate)]
        warming_receipts = [
            FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=entry_gas())
        ]
    else:
        warming_frames = []
        warming_receipts = []

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            *warming_frames,
            default_frame(target=authority),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                *warming_receipts,
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=entry_gas(
                        delegated=True, delegation_warm=warm_delegate
                    ),
                ),
            ],
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_delegated_to_precompile_target(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Run no precompile for a frame whose target designates one:
    following a designation disables precompile dispatch, leaving the
    frame to execute the designated address's empty code.
    """
    entry_gas = fork.frame_entry_gas_calculator()
    sender = pre.fund_eoa()
    authority = pre.fund_eoa(delegation=IDENTITY)

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(target=authority, data=b"\x01" * 32),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=entry_gas(delegated=True, delegation_warm=True),
                ),
            ],
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_verify_frame_delegated_to_precompile_target(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Follow the designation of a `VERIFY` frame's delegated target
    rather than running the default code: the resolved code is empty,
    as it is for the codeless target that does route to the default
    code, but the target itself holds a designation and so is not
    codeless.

    Deciding the default code from the resolved code hash instead would
    run it here, revert for want of a signature entry resolving to the
    target, and reject the transaction.
    """
    entry_gas = fork.frame_entry_gas_calculator()
    sender = pre.fund_eoa()
    authority = pre.fund_eoa(delegation=IDENTITY)

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            verify_frame(flags=Spec.APPROVE_NONE, target=authority),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=entry_gas(delegated=True, delegation_warm=True),
                ),
            ],
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})
