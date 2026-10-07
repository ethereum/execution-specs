"""
Tests for [EIP-3298: Remove storage-clear refund and refund cap](https://eips.ethereum.org/EIPS/eip-3298).

Clearing a slot no longer grants a refund, and the refund a transaction
accrues is no longer capped at a fraction of its gas used. The only
surviving rule is the net-metered reversal that refunds `STORAGE_WRITE`
when a slot ends the transaction at its original value.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_3298

REFERENCE_SPEC_GIT_PATH = ref_spec_3298.git_path
REFERENCE_SPEC_VERSION = ref_spec_3298.version

pytestmark = pytest.mark.valid_from("Bogota")


def _gross_gas(code: Bytecode, fork: Fork) -> int:
    """
    Return the gas a transaction running exactly `code` uses before any
    refund is applied.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    return intrinsic + code.execution_cost(fork) + code.state_cost(fork)


@pytest.mark.parametrize("slots", [1, 8])
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
def test_storage_clear_grants_no_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    slots: int,
) -> None:
    """
    Clearing non-zero-original slots grants no refund at all.

    Several slots are cleared so that a surviving per-clear grant would
    show up multiplied, well clear of rounding.
    """
    code = Bytecode()
    for slot in range(slots):
        code += Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=0,
        )(slot, 0)

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(range(slots), 1)
    )

    # No refund rule fires: the clear grant is removed and the slots do
    # not end at their original values.
    assert code.refund(fork) == 0
    gross = _gross_gas(code, fork)

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gross),
    )

    post = {contract: Account(storage=dict.fromkeys(range(slots), 0))}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("slots", [1, 8])
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Over()
def test_restore_refund_applied_uncapped(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    slots: int,
) -> None:
    """
    A write reversal refund larger than the removed cap applies in full.

    Each slot is moved off its non-zero original and then restored,
    refunding `STORAGE_WRITE` per slot. The accrued refund is asserted
    to exceed the quotient the EIP removes, so the receipt distinguishes
    the uncapped refund from the capped one, while the block header still
    reports the pre-refund gas.
    """
    code = Bytecode()
    for slot in range(slots):
        code += Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=2,
        )(slot, 2)
    for slot in range(slots):
        code += Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=1,
            current_value=2,
            new_value=1,
        )(slot, 1)

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(range(slots), 1)
    )

    refund = code.refund(fork)
    gross = _gross_gas(code, fork)
    # The refund the EIP-3529 quotient would have allowed, so the
    # expectation below only holds once the cap is gone.
    assert refund > gross // 5
    # Keep the calldata floor clear of the post-refund usage, so the
    # receipt reflects the refund and not the floor.
    data_floor = fork.transaction_data_floor_cost_calculator()(data=b"")
    assert gross - refund > data_floor

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gross - refund
        ),
    )

    post = {contract: Account(storage=dict.fromkeys(range(slots), 1))}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=gross),
    )
