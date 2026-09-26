"""
Tests for [EIP-8038: State-access gas cost update](https://eips.ethereum.org/EIPS/eip-8038).

The headline mechanism of the spec is the
``SSTORE`` clear-refund *reversal*: ``refund_counter`` is decremented by
``REFUND_STORAGE_CLEAR`` when a slot's original value is non-zero, its
current value is zero and the new value is non-zero (a slot cleared
earlier in the same transaction is set to a non-zero value again). The
spec reverses the clear refund "so that clearing and then restoring a
slot within the same transaction is never net-profitable". The reversal
fires on any non-zero rewrite: ``test_sstore_clear_then_reset_nets_zero``
covers the ``x -> 0 -> y`` path and
``test_sstore_clear_then_restore_original`` the ``x -> 0 -> x`` round
trip, where the reversal coincides with the ``STORAGE_WRITE`` refund.

This module covers the EIP-8038 *execution* ``SSTORE`` refund schedule via
the transaction receipt's ``cumulative_gas_used``:

* Clearing a slot whose original value is non-zero grants
  ``REFUND_STORAGE_CLEAR`` to ``refund_counter`` (no EIP-8037
  state refund, since no state was created).
* Clearing then re-setting the same non-zero-original slot nets a zero
  refund: the clear grant is reversed (``refund -= REFUND_STORAGE_CLEAR``)
  exactly when ``original != 0 and current == 0`` and a non-zero value is
  written back.
* Restoring a non-zero-original slot to its original value refunds the
  write cost ``STORAGE_WRITE``.
* The applied refund is capped at ``gas_used // 5`` (EIP-3529 quotient).

All refunds use a non-zero original so the state-creation refund owned by
EIP-8037 is never involved; only the EIP-8038 execution dimension is
exercised.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Bytecode,
    Fork,
    GasConsumer,
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

    Mirrors the spec: gross gas is intrinsic plus the execution and state
    gas of the code; the applied refund is ``min(gross // 5, refund)``
    (EIP-3529 quotient cap); the receipt reports gross minus the applied
    refund.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork) + code.state_cost(fork)
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
    (``gas_used // 5``) does not bind, letting the full clear refund be
    observed in ``cumulative_gas_used``. The non-zero original means no
    EIP-8037 state refund participates.
    """
    clear = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )(0, 0)
    # Burn unrelated execution gas so that gas_used // 5 exceeds the
    # refund and the full grant applies.
    burn = GasConsumer(gas=clear.refund(fork) * 5, fork=fork)
    code = clear + burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # The slot's clear grants exactly one REFUND_STORAGE_CLEAR.
    refund_clear = code.refund(fork)
    expected_cumulative = _cumulative_gas_used(code, fork)
    # The cap must not bind here, so the full grant is visible.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork)
    assert gross // 5 > refund_clear
    assert expected_cumulative == gross - refund_clear

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
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

    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 2})}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # The clear and the reset net into one change holding the
                # final value, not one entry per write.
                contract: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=2
                                )
                            ],
                        )
                    ],
                    storage_reads=[],
                ),
            }
        ),
    )


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Under()
def test_sstore_clear_then_rewrite_zero_grants_refund_once(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Rewriting zero over an already-cleared slot grants no second refund.

    The first ``SSTORE`` clears the slot and grants
    ``REFUND_STORAGE_CLEAR``. The second writes zero again: the new value
    equals the current value, so every refund rule is skipped and the
    write charges only its access cost. An implementation that keyed the
    clear grant off the original and new values alone, without comparing
    the new value to the current one, would grant the refund twice. The
    receipt pins exactly one grant.

    Enough unrelated gas is burned that the EIP-3529 quotient cap stays
    clear of *two* grants; were the cap to bind at or below a single
    grant, a double grant would be capped back to the same figure and
    the test would not see it.
    """
    clear = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )(0, 0)
    rewrite_zero = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=0,
        new_value=0,
    )(0, 0)
    burn = GasConsumer(gas=clear.refund(fork) * 15, fork=fork)
    code = clear + rewrite_zero + burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # The redundant zero write adds nothing to the refund counter.
    assert code.refund(fork) == clear.refund(fork)
    expected_cumulative = _cumulative_gas_used(code, fork)

    # Keep the cap clear of two grants so a spurious one would show.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork)
    assert gross // 5 > clear.refund(fork) * 2

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 0})}
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
    original non-zero value, refunding ``STORAGE_WRITE``. Gas is
    burned so the quotient cap does not bind and the full refund is
    observable.
    """
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
    burn = GasConsumer(gas=code.refund(fork) * 5, fork=fork)
    code += burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # Restoring the non-zero original refunds STORAGE_WRITE.
    storage_write = code.refund(fork)
    expected_cumulative = _cumulative_gas_used(code, fork)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork)
    assert gross // 5 > storage_write
    assert expected_cumulative == gross - storage_write

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 1})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Under()
def test_sstore_clear_then_restore_original(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Clearing then restoring a slot's original value nets one write refund.

    The ``x -> 0 -> x`` round trip: the clear grants
    ``REFUND_STORAGE_CLEAR``; the restore both reverses that grant and
    refunds ``STORAGE_WRITE`` (the only row where the two adjustments
    coincide). The net refund equals a pure restore's write refund, so
    the round trip pays access costs plus nothing net for the write.
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
        new_value=1,
    )(0, 1)
    burn = GasConsumer(gas=code.refund(fork) * 5, fork=fork)
    code += burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # The clear grant and its reversal cancel; only the STORAGE_WRITE
    # refund of the restore survives, exactly as for a plain non-zero
    # restore (the (x, y, x) row).
    restore_refund = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=2,
        new_value=1,
    ).refund(fork)
    assert code.refund(fork) == restore_refund
    expected_cumulative = _cumulative_gas_used(code, fork)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork)
    assert gross // 5 > restore_refund
    assert expected_cumulative == gross - restore_refund

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 1})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Under()
def test_sstore_write_charged_each_move_away(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    ``STORAGE_WRITE`` is charged by each write that moves the slot away
    from its transaction-start value, not once per transaction.

    The ``x -> y -> x -> z`` sequence charges the write cost twice (the
    first and third writes each find ``current == original``) with one
    refund between them, so the net refund is exactly one write refund
    while the gross gas carries both charges.
    """
    code = (
        Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=2,
        )(0, 2)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=1,
            current_value=2,
            new_value=1,
        )(0, 1)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=1,
            current_value=1,
            new_value=3,
        )(0, 3)
    )
    burn = GasConsumer(gas=code.refund(fork) * 5, fork=fork)
    code += burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # One restore refund survives; the second move-away is charged in
    # full again with no further refund.
    restore_refund = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=2,
        new_value=1,
    ).refund(fork)
    assert code.refund(fork) == restore_refund
    expected_cumulative = _cumulative_gas_used(code, fork)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork)
    assert gross // 5 > restore_refund
    assert expected_cumulative == gross - restore_refund

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 3})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Under()
def test_sstore_clear_refund_granted_twice(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The clear refund is granted on each clear of a non-zero slot, not
    once per transaction.

    The ``x -> 0 -> y -> 0`` sequence grants ``REFUND_STORAGE_CLEAR``,
    reverses it on the non-zero rewrite, then grants it again on the
    second clear, netting exactly one grant.
    """
    code = (
        Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=0,
        )(0, 0)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=1,
            current_value=0,
            new_value=2,
        )(0, 2)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=1,
            current_value=2,
            new_value=0,
        )(0, 0)
    )
    burn = GasConsumer(gas=code.refund(fork) * 5, fork=fork)
    code += burn

    contract = pre.deploy_contract(code=code, storage={0: 1})

    # Grant, reversal, grant: the net refund is one clear grant, the
    # same as a single clear of a non-zero-original slot.
    single_clear_refund = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=1,
        new_value=0,
    ).refund(fork)
    assert code.refund(fork) == single_clear_refund
    expected_cumulative = _cumulative_gas_used(code, fork)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork)
    assert gross // 5 > single_clear_refund
    assert expected_cumulative == gross - single_clear_refund

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Over()
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

    # num_clears distinct clears accrue num_clears * REFUND_STORAGE_CLEAR.
    accrued = code.refund(fork)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork)
    # The cap binds for every parametrization (single-clear gross is far
    # below 5x a clear refund).
    cap = gross // 5
    assert cap < accrued
    applied_refund = min(cap, accrued)
    expected_cumulative = gross - applied_refund

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage=dict.fromkeys(range(num_clears), 0))}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasRefundsChanges.Test.RefundCalculation.Exact()
def test_sstore_refund_cap_exact_equality(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The applied refund equals the EIP-3529 cap at exact equality.

    A single non-zero-original clear accrues ``REFUND_STORAGE_CLEAR``.
    Unrelated execution gas is burned so the gross gas lands at
    exactly ``max_refund_quotient * accrued``; the quotient cap
    ``gross // max_refund_quotient`` then equals the accrued refund
    *exactly*, the boundary between the cap binding and not binding. The
    full refund applies and ``cumulative_gas_used`` is ``gross - accrued``.
    """
    quotient = fork.max_refund_quotient()

    clear = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )(0, 0)
    accrued = clear.refund(fork)

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    # Target the exact boundary: gross == quotient * accrued, so that
    # gross // quotient == accrued with no slack. The burn is whatever
    # is left after the intrinsic cost and the clear's execution cost.
    target_gross = quotient * accrued
    base_gross = intrinsic + clear.execution_cost(fork)
    burn_gas = target_gross - base_gross

    code = clear + GasConsumer(gas=burn_gas, fork=fork)
    contract = pre.deploy_contract(code=code, storage={0: 1})

    gross = intrinsic + code.execution_cost(fork) + code.state_cost(fork)
    # Exact equality: the cap is neither under nor over the accrued refund.
    assert gross == target_gross
    assert gross // quotient == accrued
    expected_cumulative = gross - accrued

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)
