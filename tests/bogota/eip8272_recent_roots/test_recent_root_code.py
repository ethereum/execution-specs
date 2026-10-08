"""
Tests pinning the recent root code and the EIP's reference vector for
[EIP-8272: Recent Roots for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8272).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from ..eip8141_frame_transactions.helpers import sender_frame, verify_frame
from ..eip8141_frame_transactions.spec import Spec as FrameSpec
from .helpers import recent_root_frame, validation_gas
from .spec import Spec, ref_spec_8272, validation_tuple

REFERENCE_SPEC_GIT_PATH = ref_spec_8272.git_path
REFERENCE_SPEC_VERSION = ref_spec_8272.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "root,error",
    [
        pytest.param(Spec.VECTOR_ROOT, None, id="reference_vector"),
        pytest.param(
            (3).to_bytes(32, "big"),
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
            id="reference_vector_wrong_root",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_reference_vector(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    root: bytes,
    error: TransactionException | None,
) -> None:
    """
    Verify the EIP's reference vector through a recent root verifier
    frame.

    The code the testing framework pre-allocates must be the runtime
    code the EIP's deployment transaction creates. With the
    vector's entry hash stored under its storage key, the 72-byte tuple
    validates at `current_slot = 2`; any other root reverts, which for a
    `VERIFY` frame invalidates the transaction.
    """
    installed = fork.pre_allocation()[Spec.RECENT_ROOT_ADDRESS_INT]
    assert bytes(installed["code"]) == Spec.RECENT_ROOT_CODE

    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    pre[Spec.RECENT_ROOT_ADDRESS] = Account(
        nonce=Spec.RECENT_ROOT_NONCE,
        code=Spec.RECENT_ROOT_CODE,
        storage={
            int.from_bytes(Spec.VECTOR_STORAGE_KEY, "big"): int.from_bytes(
                Spec.VECTOR_ENTRY_HASH, "big"
            )
        },
    )
    verifier = recent_root_frame(
        validation_tuple(Spec.VECTOR_SOURCE_ID, Spec.VECTOR_SLOT, root)
    )

    expected_receipt = None
    if error is None:
        expected_receipt = TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=FrameSpec.STATUS_SUCCESS,
                    gas_used=validation_gas(fork, tuples=1, cold_keys=1),
                    state_gas_used=0,
                ),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
            ],
        )

    state_test(
        env=Environment(slot_number=Spec.VECTOR_CURRENT_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[verifier, verify_frame(), sender_frame(target=target)],
            error=error,
            expected_receipt=expected_receipt,
        ),
        post={
            target: Account(storage={SLOT_EXECUTED: 0 if error else 1}),
        },
    )
