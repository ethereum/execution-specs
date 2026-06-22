"""
Tests for [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Covers the EIP-8038 *regular* ``SSTORE`` refund schedule via the
transaction receipt's ``cumulative_gas_used``:

* Clearing a slot whose original value is non-zero grants
  ``REFUND_STORAGE_CLEAR`` (12480) to ``refund_counter`` (no EIP-8037
  state refund, since no state was created).
* Clearing then re-setting the same non-zero-original slot nets a zero
  refund (the clear grant is reversed).
* Restoring a non-zero-original slot to its original value refunds the
  write cost ``STORAGE_WRITE`` (10000).
* The applied refund is capped at ``gas_used // 5`` (EIP-3529 quotient).

All refunds use a non-zero original so the state-creation refund owned by
EIP-8037 is never involved; only the EIP-8038 regular dimension is
exercised.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _cumulative_gas_used(code: Bytecode, fork: Fork) -> int:
    """
    Return the receipt ``cumulative_gas_used`` for a single transaction
    whose execution is exactly ``code``.

    Mirrors the spec: gross gas is intrinsic plus the regular and state
    gas of the code; the applied refund is ``min(gross // 5, refund)``
    (EIP-3529 quotient cap); the receipt reports gross minus the applied
    refund.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.regular_cost(fork) + code.state_cost(fork)
    applied_refund = min(gross // 5, code.refund(fork))
    return gross - applied_refund


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Under()
def test_sstore_clear_grants_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Clearing a non-zero-original slot grants ``REFUND_STORAGE_CLEAR``.

    Enough unrelated gas is burned so the EIP-3529 quotient cap
    (``gas_used // 5``) does not bind, letting the full 12480 refund be
    observed in ``cumulative_gas_used``. The non-zero original means no
    EIP-8037 state refund participates.
    """
    gas_costs = fork.gas_costs()
    refund_clear = gas_costs.REFUND_STORAGE_CLEAR

    clear = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )(0, 0)
    # Burn cheap gas (JUMPDEST = 1 gas, no stack effect) so that
    # gas_used // 5 exceeds the refund and the full grant applies.
    burn = Op.JUMPDEST * 60_000
    code = clear + burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # Sanity: the slot's refund counter accrues exactly one clear grant.
    assert code.refund(fork) == refund_clear
    expected_cumulative = _cumulative_gas_used(code, fork)
    # The cap must not bind here, so the full grant is visible.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.regular_cost(fork)
    assert gross // 5 > refund_clear
    assert expected_cumulative == gross - refund_clear

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
def test_sstore_clear_then_reset_nets_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Clearing then re-setting a non-zero-original slot nets zero refund.

    The clear grants ``REFUND_STORAGE_CLEAR``; re-setting the slot to a
    non-zero value reverses it. ``refund_counter`` ends at zero, so
    ``cumulative_gas_used`` equals the gross gas with no refund applied.
    """
    code = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )(0, 0) + Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=0,
        new_value=2,
    )(0, 2)

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # The grant and its reversal cancel exactly.
    assert code.refund(fork) == 0
    expected_cumulative = _cumulative_gas_used(code, fork)

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 2})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Under()
def test_sstore_restore_nonzero_refunds_write(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Restoring a non-zero-original slot refunds the write cost.

    The slot is changed (charging ``STORAGE_WRITE``) then restored to its
    original non-zero value, refunding ``STORAGE_WRITE`` (10000). Gas is
    burned so the quotient cap does not bind and the full refund is
    observable.
    """
    gas_costs = fork.gas_costs()
    storage_write = (
        gas_costs.COLD_STORAGE_WRITE - gas_costs.COLD_STORAGE_ACCESS
    )

    code = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=2,
    )(0, 2) + Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=2,
        new_value=1,
    )(0, 1)
    burn = Op.JUMPDEST * 60_000
    code += burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    assert code.refund(fork) == storage_write
    expected_cumulative = _cumulative_gas_used(code, fork)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.regular_cost(fork)
    assert gross // 5 > storage_write
    assert expected_cumulative == gross - storage_write

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 1})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Exact()
@pytest.mark.parametrize("num_clears", [1, 8, 32])
def test_sstore_refund_quotient_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    num_clears: int,
) -> None:
    """
    The applied refund saturates at the EIP-3529 quotient cap.

    ``num_clears`` distinct non-zero-original slots are each cleared,
    accruing ``num_clears * REFUND_STORAGE_CLEAR`` into ``refund_counter``.
    A single clear's gross gas is small enough that ``gas_used // 5`` is
    always below the accrued refund, so the applied refund is the cap and
    ``cumulative_gas_used`` reflects ``min(gas_used // 5, accrued)``.
    """
    gas_costs = fork.gas_costs()
    accrued = num_clears * gas_costs.REFUND_STORAGE_CLEAR

    code = Bytecode()
    for slot in range(num_clears):
        code += Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=0,
        )(slot, 0)

    contract = pre.deploy_contract(
        code=code,
        storage=dict.fromkeys(range(num_clears), 1),
    )

    assert code.refund(fork) == accrued
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.regular_cost(fork)
    # The cap binds for every parametrization (single-clear gross is far
    # below 5x a clear refund).
    cap = gross // 5
    assert cap < accrued
    applied_refund = min(cap, accrued)
    expected_cumulative = gross - applied_refund

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=2_000_000,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage=dict.fromkeys(range(num_clears), 0))}
    state_test(pre=pre, post=post, tx=tx)
