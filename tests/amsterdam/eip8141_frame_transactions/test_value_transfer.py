"""
Value transfer tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Only `SENDER` frames carry value. A frame paying an account other than
the sender is charged the value transfer cost — in the intrinsic cost
and the calldata floor alike — covering the recipient balance write
and the transfer log of [EIP-7708]; a frame paying the sender itself
is exempt and emits no log.

[EIP-7708]: https://eips.ethereum.org/EIPS/eip-7708
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    FrameReceipt,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    keccak256,
)

from .helpers import sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

TRANSFER_LOG_ADDRESS = Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)
"""System address EIP-7708 transfer logs are emitted from."""

TRANSFER_TOPIC = Hash(keccak256(b"Transfer(address,address,uint256)"))
"""Topic of an EIP-7708 transfer log."""

TRANSFER_VALUE = 10**15
"""Value the frame under test transfers."""


def transfer_log(
    sender: Address, recipient: Address, amount: int
) -> TransactionLog:
    """Create an expected EIP-7708 transfer log."""
    return TransactionLog(
        address=TRANSFER_LOG_ADDRESS,
        topics=[
            TRANSFER_TOPIC,
            Hash(bytes(sender).rjust(32, b"\x00")),
            Hash(bytes(recipient).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )


@pytest.mark.parametrize(
    "target_kind",
    [
        pytest.param("other", id="target_other_account"),
        pytest.param("self_explicit", id="target_sender_explicitly"),
        pytest.param("self_empty", id="target_sender_via_empty_target"),
    ],
)
def test_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    target_kind: str,
) -> None:
    """
    Transfer value from a `SENDER` frame, pinning the transaction's
    cost and the frame receipt's logs.

    A frame whose explicit target differs from the sender is charged
    the value transfer cost — the pinned cost carries it in both
    settlement anchors — and its receipt holds the EIP-7708 transfer
    log. A frame paying the sender itself, explicitly or through an
    empty target resolving to it, is exempt and emits no log.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)

    if target_kind == "other":
        value_frame = sender_frame(target=recipient, value=TRANSFER_VALUE)
        entry_gas = fork.frame_entry_gas_calculator()()
        logs = [transfer_log(sender, recipient, TRANSFER_VALUE)]
    elif target_kind == "self_explicit":
        # The sender seeds the warm set, so its own entry access is
        # warm.
        value_frame = sender_frame(target=sender, value=TRANSFER_VALUE)
        entry_gas = fork.frame_entry_gas_calculator()(target_warm=True)
        logs = []
    else:
        value_frame = sender_frame(value=TRANSFER_VALUE)
        entry_gas = fork.frame_entry_gas_calculator()(target_warm=True)
        logs = []

    tx = Transaction(
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: transfer the value to the resolved target.
            value_frame,
        ],
    )
    # Materialize the signature bytes the intrinsic cost charges for.
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        sender=sender,
        return_cost_deducted_prior_execution=True,
    )
    calldata_floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        sender=sender,
    )
    # The frames run no code beyond the target's entry access, so the
    # floor may bind; both anchors carry the value transfer cost, so
    # the pin exercises it either way.
    gas_used = max(intrinsic + entry_gas, calldata_floor)

    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=gas_used,
        frame_receipts=[
            FrameReceipt(
                status=Spec.STATUS_SUCCESS, gas_used=0, state_gas_used=0
            ),
            FrameReceipt(
                status=Spec.STATUS_SUCCESS,
                gas_used=entry_gas,
                state_gas_used=0,
                logs=logs,
            ),
        ],
    )

    post = {sender: Account(nonce=1)}
    if target_kind == "other":
        post[recipient] = Account(balance=1 + TRANSFER_VALUE)

    state_test(pre=pre, tx=tx, post=post)
