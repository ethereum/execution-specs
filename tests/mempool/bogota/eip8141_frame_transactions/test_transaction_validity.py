"""
Transaction validity tests for the mempool admission of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame transaction that is invalid for the next block must never be
broadcast. The execution specification decides these cases.
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    Frame,
    MempoolTestFiller,
    Transaction,
    TransactionException,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    APPROVE_ALL,
)

from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SENDER_NONCE = 1
"""Nonce of the deployed sender contract."""


@pytest.mark.parametrize(
    "nonce,error",
    [
        pytest.param(
            SENDER_NONCE - 1,
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="nonce_too_low",
        ),
        pytest.param(SENDER_NONCE, None, id="nonce_current"),
        pytest.param(
            SENDER_NONCE + 1,
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="nonce_gap",
        ),
    ],
)
def test_frame_transaction_nonce(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce: int,
    error: TransactionException | None,
) -> None:
    """
    Broadcast a frame transaction only when its nonce equals the sender's.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    assert pre[sender].nonce == SENDER_NONCE  # type: ignore[union-attr]

    tx = Transaction(
        sender=sender,
        nonce=nonce,
        frames=[Frame.verify()],
        error=error,
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=error is None,
    )
