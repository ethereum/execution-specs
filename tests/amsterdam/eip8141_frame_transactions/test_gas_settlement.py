"""
Transaction-level gas settlement tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame transaction's payer-facing `gas_used` is the post-refund execution
usage held to the EIP-7623 calldata floor plus final attributed state gas.
Block accounting keeps the same state dimension but counts execution before
storage refunds, as required by EIP-7778.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    FrameReceipt,
    Header,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import (
    default_code_frame_gas,
    default_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT = 0x01
"""Storage slot the worker contract writes or clears."""

FLOOR_WORKER_GAS = 30_000
"""
Execution gas budget of the floor-bound worker frame, kept small so
the calldata floor dominates the settlement anchor.
"""

FLOOR_PADDING_DATA = b"\x00" * 30_000
"""Frame data driving the calldata floor above the settlement anchor."""

REFUND_WORKER_GAS = 100_000
"""Execution gas budget of the refund test's worker frame."""


@pytest.mark.parametrize(
    "with_state_write",
    [
        pytest.param(True, id="state_write"),
        pytest.param(False, id="no_state_write"),
    ],
)
def test_calldata_floor_with_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    with_state_write: bool,
) -> None:
    """
    Bind the calldata floor on a transaction that also grows state.

    The floor is compared against the execution dimension alone, so a
    floor-bound transaction pays the floor plus its state gas in full:
    state growth never rides free under the data floor.
    """
    sender = pre.fund_eoa()
    write = Op.SSTORE(SLOT, 1)
    worker_code = (write if with_state_write else Bytecode()) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    state_used = write.state_cost(fork) if with_state_write else 0

    tx = Transaction(
        sender=sender,
        frames=[
            # The floor must dominate the settlement anchor, so every
            # budget the anchor sums is kept to what execution needs.
            # The verifying frame needs its entry access and nothing
            # more: the default code itself draws no execution gas.
            verify_frame(
                gas_limit=default_code_frame_gas(fork, target_warm=True),
                state_gas_limit=0,
            ),
            default_frame(
                target=worker,
                gas_limit=FLOOR_WORKER_GAS,
                state_gas_limit=state_used,
                data=FLOOR_PADDING_DATA,
            ),
        ],
    )
    # Materialize the signature bytes the calldata floor charges for.
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    calldata_floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames, signatures=tx.signatures
    )
    standard_gas_limit = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        return_cost_deducted_prior_execution=True,
    ) + sum(frame.gas_limit + frame.state_gas_limit for frame in tx.frames)
    # The premise of the test: the floor binds.
    assert calldata_floor > standard_gas_limit

    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=calldata_floor + state_used,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT: 1 if with_state_write else 0}),
        },
    )


def test_storage_refund_settlement(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Settle a frame transaction that clears a pre-existing storage slot.

    The EIP-3529 refund reduces the payer's charge, while EIP-7778 keeps
    the refunded execution gas counted toward the block gas limit. The
    receipt therefore reports post-refund cumulative gas and the block
    header reports pre-refund gas. Clearing durable state consumes no
    state gas, so the frame declares none.
    """
    sender = pre.fund_eoa()
    clear = Op.SSTORE(
        SLOT,
        0,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )
    # Pad execution so the refund cap — a fifth of the pre-refund
    # usage — stays above the clearing refund and the refund applies
    # in full. The sender seeds the warm set, so its repeated balance
    # reads are warm accesses.
    padding = Op.POP(Op.BALANCE(address=sender, address_warm=True)) * 400
    worker_code = padding + clear + Op.STOP
    worker = pre.deploy_contract(code=worker_code, storage={SLOT: 1})

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                gas_limit=REFUND_WORKER_GAS,
                state_gas_limit=0,
            ),
        ],
    )
    # Materialize the signature bytes the intrinsic cost charges for.
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    verify_gas = default_code_frame_gas(fork, target_warm=True)
    frame_execution_gas = fork.frame_entry_gas_calculator()() + (
        worker_code.execution_cost(fork)
    )
    gas_used_before_refund = (
        fork.frame_transaction_intrinsic_cost_calculator()(
            frames=tx.frames,
            signatures=tx.signatures,
            return_cost_deducted_prior_execution=True,
        )
        + verify_gas
        + frame_execution_gas
    )
    refund = worker_code.refund(fork)
    # The premise of the test: the refund applies uncapped.
    assert 0 < refund <= gas_used_before_refund // 5
    gas_used = gas_used_before_refund - refund

    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=gas_used,
        frame_receipts=[
            FrameReceipt(
                status=Spec.STATUS_SUCCESS,
                gas_used=verify_gas,
                state_gas_used=0,
            ),
            # The receipt reports pre-refund execution gas; the refund
            # applies only at transaction settlement.
            FrameReceipt(
                status=Spec.STATUS_SUCCESS,
                gas_used=frame_execution_gas,
                state_gas_used=0,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT: 0}),
        },
        blockchain_test_header_verify=Header(gas_used=gas_used_before_refund),
    )
