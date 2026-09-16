"""
Tests for [EIP-8038: State-access gas cost update](https://eips.ethereum.org/EIPS/eip-8038).

Covers ``SSTORE`` refund and charge accounting across frames that fail.
A frame's refund-counter adjustments are discarded when the frame
reverts or exceptionally halts, while the gas it consumed stays
consumed; and a rollback restores ``current == original``, so a later
write to the same slot is priced as a first change again. These
semantics are inherited from EIP-2200/EIP-3529 but become far more
consequential under EIP-8038's repriced ``STORAGE_WRITE`` and
``REFUND_STORAGE_CLEAR``.

All failing frames run under ``DELEGATECALL`` so every touched slot
belongs to the outer contract and rollback is observable in its
post-state. All slots have non-zero originals so the EIP-8037
state-creation dimension never participates; every expectation is an
exact receipt ``cumulative_gas_used`` pin.
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
from execution_testing import Macros as Om
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")

# Alias for the deep checklist path so decorator lines stay within
# the line limit; the marks are applied at runtime, so the checklist
# scanner resolves them identically.
_REVERTABLE = EIPChecklist.GasRefundsChanges.Test.ExceptionalAbort.Revertable

DATA_SLOT = 0x42

# Gas forwarded to a child frame that exceptionally halts: the child
# consumes exactly this grant, making the receipt exact by construction.
# Sized to comfortably cover a cold first-change SSTORE.
CHILD_GAS = 30_000

# Headroom on top of the expected consumption so the 63/64 withhold
# never truncates the requested child grant.
GAS_LIMIT_MARGIN = 50_000


def _intrinsic(fork: Fork) -> int:
    """Return the intrinsic gas deducted prior to execution."""
    return fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )


def _clear_refund(fork: Fork) -> int:
    """Return the refund granted by clearing a non-zero-original slot."""
    return Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    ).refund(fork)


@_REVERTABLE()
@_REVERTABLE.Revert()
@_REVERTABLE.OutOfGas()
@_REVERTABLE.InvalidOpcode()
@pytest.mark.parametrize(
    "failure,returns_unused_gas",
    [
        pytest.param(Op.REVERT(0, 0), True, id="revert"),
        pytest.param(Om.OOG, False, id="out_of_gas"),
        pytest.param(Op.INVALID, False, id="invalid_opcode"),
    ],
)
def test_sstore_clear_refund_discarded_on_frame_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure: Bytecode,
    returns_unused_gas: bool,
) -> None:
    """
    A clear refund accrued in a failing frame is discarded.

    The child clears a non-zero-original slot (accruing
    ``REFUND_STORAGE_CLEAR``) and then fails; the receipt shows the full
    gross gas with no refund applied, and the slot rolls back.
    """
    child_code = Op.SSTORE(DATA_SLOT, 0) + failure
    child = pre.deploy_contract(code=child_code)

    caller_code = Op.POP(Op.DELEGATECALL(gas=CHILD_GAS, address=child))
    caller = pre.deploy_contract(code=caller_code, storage={DATA_SLOT: 1})

    # A REVERT returns the child's unused gas, so the child consumes
    # only what it executed; an exceptional halt consumes the whole
    # grant.
    child_consumed = (
        child_code.execution_cost(fork) if returns_unused_gas else CHILD_GAS
    )

    # The discarded refund must be non-trivial for the pin to have
    # teeth: kept erroneously, it would lower the receipt.
    assert _clear_refund(fork) > 0
    expected_cumulative = (
        _intrinsic(fork) + caller_code.execution_cost(fork) + child_consumed
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        gas_limit=expected_cumulative + GAS_LIMIT_MARGIN,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    # The clear rolls back with the failing frame.
    post = {caller: Account(storage={DATA_SLOT: 1})}
    state_test(pre=pre, post=post, tx=tx)


@_REVERTABLE()
@_REVERTABLE.UpperRevert()
def test_sstore_clear_refund_discarded_on_upper_frame_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A refund merged from a successful child dies with a reverting parent.

    The inner frame clears the slot and returns successfully, merging
    its clear refund into the middle frame; the middle frame then
    reverts, discarding the merged refund along with the state change.
    """
    inner_code = Op.SSTORE(DATA_SLOT, 0) + Op.STOP
    inner = pre.deploy_contract(code=inner_code)

    middle_code = Op.POP(
        Op.DELEGATECALL(gas=Op.GAS, address=inner)
    ) + Op.REVERT(0, 0)
    middle = pre.deploy_contract(code=middle_code)

    outer_code = Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=middle))
    outer = pre.deploy_contract(code=outer_code, storage={DATA_SLOT: 1})

    # Both inner (STOP) and middle (REVERT) return their unused gas, so
    # each frame consumes exactly its executed cost.
    assert _clear_refund(fork) > 0
    expected_cumulative = (
        _intrinsic(fork)
        + outer_code.execution_cost(fork)
        + middle_code.execution_cost(fork)
        + inner_code.execution_cost(fork)
    )

    tx = Transaction(
        to=outer,
        sender=pre.fund_eoa(),
        gas_limit=expected_cumulative + GAS_LIMIT_MARGIN,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {outer: Account(storage={DATA_SLOT: 1})}
    state_test(pre=pre, post=post, tx=tx)


@_REVERTABLE()
@_REVERTABLE.Revert()
def test_sstore_restore_refund_discarded_on_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The write-restore refund is discarded with its reverting frame.

    The child changes the slot and restores its original value
    (accruing the ``STORAGE_WRITE`` refund of refund rule 3), then
    reverts. The slot ends the transaction at its original value, yet
    the write cost burned in the child stays consumed and the refund is
    gone — the receipt shows the full gross gas.
    """
    # Metadata on both writes: the first is a cold first change, the
    # second a warm restore, so the child's modeled execution cost and
    # net refund match what actually runs.
    child_code = (
        Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=2,
        )(DATA_SLOT, 2)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=1,
            current_value=2,
            new_value=1,
        )(DATA_SLOT, 1)
        + Op.REVERT(0, 0)
    )
    child = pre.deploy_contract(code=child_code)

    caller_code = Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=child))
    caller = pre.deploy_contract(code=caller_code, storage={DATA_SLOT: 1})

    # The child's own accounting nets a STORAGE_WRITE refund; it must
    # be non-trivial, and none of it may survive the revert.
    assert child_code.refund(fork) > 0

    expected_cumulative = (
        _intrinsic(fork)
        + caller_code.execution_cost(fork)
        + child_code.execution_cost(fork)
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        gas_limit=expected_cumulative + GAS_LIMIT_MARGIN,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {caller: Account(storage={DATA_SLOT: 1})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@_REVERTABLE.InvalidOpcode()
def test_sstore_write_recharged_after_frame_rollback(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A rollback re-arms the first-change ``STORAGE_WRITE`` charge.

    The child pays cold access plus ``STORAGE_WRITE`` moving the slot
    away from its original, then exceptionally halts: the write and the
    slot's warmth roll back, but the gas stays consumed. The outer
    frame's own write to the same slot then finds ``current ==
    original`` on a cold slot again and pays the full first-change
    price a second time.
    """
    child_code = Op.SSTORE(DATA_SLOT, 2) + Op.INVALID
    child = pre.deploy_contract(code=child_code)

    # The outer write is priced as a cold first change even though the
    # child already wrote (and warmed) the slot: both rolled back.
    caller_code = Op.POP(
        Op.DELEGATECALL(gas=CHILD_GAS, address=child)
    ) + Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=2,
    )(DATA_SLOT, 2)
    caller = pre.deploy_contract(code=caller_code, storage={DATA_SLOT: 1})

    expected_cumulative = (
        _intrinsic(fork) + caller_code.execution_cost(fork) + CHILD_GAS
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        gas_limit=expected_cumulative + GAS_LIMIT_MARGIN,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative
        ),
    )

    post = {caller: Account(storage={DATA_SLOT: 2})}
    state_test(pre=pre, post=post, tx=tx)
