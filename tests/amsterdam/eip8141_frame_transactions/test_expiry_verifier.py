"""
Tests for the expiry verifier frames of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A `VERIFY` frame targeting the expiry verifier predeploy carries an
unsigned big-endian expiry timestamp in its data. The predeploy's code
returns successfully while the block timestamp is at or before that
expiry, and reverts once the block timestamp exceeds it — invalidating
the whole transaction.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    Frame,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

BLOCK_TIMESTAMP = 1_000
"""Timestamp of the block executing the frame transaction."""


@pytest.mark.parametrize(
    "expiry,error",
    [
        pytest.param(BLOCK_TIMESTAMP + 1, None, id="future_expiry"),
        pytest.param(BLOCK_TIMESTAMP, None, id="expiry_at_block_timestamp"),
        pytest.param(
            BLOCK_TIMESTAMP - 1,
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
            id="expired",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_expiry_verifier_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    expiry: int,
    error: TransactionException | None,
) -> None:
    """
    Execute a frame transaction carrying an expiry verifier frame.

    While the block timestamp is at or before the expiry — including
    exactly at it — the frame succeeds and the transaction executes.
    Once the block timestamp exceeds the expiry, the predeploy
    reverts, which for a `VERIFY` frame invalidates the whole
    transaction.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)

    expected_receipt = None
    if error is None:
        expected_receipt = TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
            ],
        )

    tx = Transaction(
        sender=sender,
        frames=[
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                gas_limit=100_000,
            ),
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_NONE,
                target=Spec.EXPIRY_VERIFIER,
                gas_limit=100_000,
                data=Bytes(expiry.to_bytes(Spec.EXPIRY_DATA_LENGTH, "big")),
            ),
            Frame(
                mode=Spec.MODE_SENDER,
                target=target,
                gas_limit=200_000,
            ),
        ],
        error=error,
        expected_receipt=expected_receipt,
    )

    state_test(
        env=Environment(timestamp=BLOCK_TIMESTAMP),
        pre=pre,
        tx=tx,
        post={
            # The predeploy is injected into the genesis allocation by
            # the testing framework; pin its account here so a missing
            # predeploy fails loudly instead of silently exercising the
            # default verify code.
            Spec.EXPIRY_VERIFIER: Account(
                nonce=0,
                code=Spec.EXPIRY_VERIFIER_CODE,
            ),
            target: Account(
                storage={SLOT_EXECUTED: 0 if error else 1},
            ),
        },
    )
