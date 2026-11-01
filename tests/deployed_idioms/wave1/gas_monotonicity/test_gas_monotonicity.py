"""
Archetype 10: gas monotonicity across an external call.

Every gas meter and every gas-refunding relayer on mainnet relies on
`gasleft()` after a call being no larger than before it, so that
`before - after` is the gas consumed and cannot underflow. Safe's
`gasUsed.sub(gasleft())` is the canonical instance.

Witnessed by L4's `gas-delta` probe at **252,006 mainnet addresses from
2,499 source files**, FP 0/18 hand-validated.

**Severity splits by compiler, and the quieter case is the worse one.**
Under solc >= 0.8 or SafeMath the underflow reverts: a liveness failure.
Under a plain `-` with solc < 0.8 it wraps to a value near 2**256, and the
relayer is reimbursed an astronomically wrong amount: a correctness and
funds failure that surfaces nothing. The second marker below pins exactly
that case.

EIP-8037 inverts the invariant: a child's clear credits the parent's
`gas_left` (`credit_state_gas_refund`, LIFO -- `gas_left` up to the spill,
then the reservoir; amsterdam/vm/gas.py:594), so the later reading can be
the larger one. L4 established that **no existing test asserts monotonicity
on the forks where it still holds** -- only its Amsterdam violation is
covered. The first test here closes that.

Measured, not assumed (see `tests/tools/test_monotonicity_probe.py`):
Berlin 1, Osaka 1, Amsterdam 0.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SLOT_X = 0x01
SLOT_DECREASING = 0x02
SLOT_NO_WRAP = 0x03

# A meter's delta is a few thousand gas. An underflow wraps to ~2**256, so
# any bound far above a real delta and far below the wrap separates them.
# The bound is a discriminator, not an assertion about cost.
WRAP_DISCRIMINATOR = 1 << 128


def _metered_caller(clearer: object) -> object:
    """Build a caller that meters a call the way a deployed relayer does."""
    return (
        # Create a slot, so the frame carries an outstanding state-gas
        # spill that the child's clear can repay into `gas_left`.
        Op.SSTORE(SLOT_X, 1)
        + Op.MSTORE(0, Op.GAS)
        # DELEGATECALL so the child clears *this* frame's slot.
        + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=clearer))
        + Op.MSTORE(0x20, Op.GAS)
        # Marker 1: did the readings strictly decrease?
        + Op.SSTORE(SLOT_DECREASING, Op.GT(Op.MLOAD(0), Op.MLOAD(0x20)))
        # Marker 2: does the deployed subtraction stay un-wrapped?
        + Op.SSTORE(
            SLOT_NO_WRAP,
            Op.LT(Op.SUB(Op.MLOAD(0), Op.MLOAD(0x20)), WRAP_DISCRIMINATOR),
        )
        + Op.STOP
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_gas_readings_strictly_decrease_across_a_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test `GAS` readings strictly decrease across a call that clears a slot.

    This is the invariant deployed gas meters are built on, asserted on the
    forks where it holds. A child clears a slot the parent just created --
    the strongest available attempt to return gas to the parent mid-frame --
    and the parent's later reading must still be the smaller one, with the
    meter's subtraction not wrapping.
    """
    clearer = pre.deploy_contract(Op.SSTORE(SLOT_X, 0) + Op.STOP)
    caller = pre.deploy_contract(_metered_caller(clearer))

    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            caller: Account(
                storage={SLOT_X: 0, SLOT_DECREASING: 1, SLOT_NO_WRAP: 1}
            )
        },
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_gas_readings_invert_from_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the same meter sees a non-decreasing pair once state gas refills.

    The identical bytecode now records `0` for both markers: the second
    reading is not smaller, and the deployed subtraction wraps. Pinning the
    violation alongside the invariant keeps the pair honest -- if a later
    fork restores monotonicity, this test fails and the one above starts
    applying again, which is the signal we want rather than silence.
    """
    clearer = pre.deploy_contract(Op.SSTORE(SLOT_X, 0) + Op.STOP)
    caller = pre.deploy_contract(_metered_caller(clearer))

    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            caller: Account(
                storage={SLOT_X: 0, SLOT_DECREASING: 0, SLOT_NO_WRAP: 0}
            )
        },
        tx=tx,
    )


def _inframe_meter() -> object:
    """Meter a set/clear pair in one frame, with no call between them."""
    return (
        # Create the slot, so the frame carries an outstanding spill.
        Op.SSTORE(SLOT_X, 1)
        + Op.MSTORE(0, Op.GAS)
        # Clear it in the SAME frame: `credit_state_gas_refund` returns the
        # charge to this frame's own `gas_left` (storage.py:151), with no
        # child merge involved.
        + Op.SSTORE(SLOT_X, 0)
        + Op.MSTORE(0x20, Op.GAS)
        + Op.SSTORE(SLOT_DECREASING, Op.GT(Op.MLOAD(0), Op.MLOAD(0x20)))
        + Op.SSTORE(
            SLOT_NO_WRAP,
            Op.LT(Op.SUB(Op.MLOAD(0), Op.MLOAD(0x20)), WRAP_DISCRIMINATOR),
        )
        + Op.STOP
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_gas_readings_decrease_across_an_inframe_clear(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test `GAS` readings strictly decrease across a same-frame set/clear pair.

    This covers EIP-8037's in-frame mechanic, which the cross-frame test
    above structurally cannot reach: there is no call here, so the refund
    path is `credit_state_gas_refund` rather than `repay_state_gas_spill`.
    The mutation matrix found this path unprotected.
    """
    caller = pre.deploy_contract(_inframe_meter())
    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            caller: Account(
                storage={SLOT_X: 0, SLOT_DECREASING: 1, SLOT_NO_WRAP: 1}
            )
        },
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_gas_readings_invert_across_an_inframe_clear(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the same-frame pair also inverts once a clear refills `gas_left`.

    The clear repays this frame's own spill directly, so the second reading
    is the larger one and the deployed subtraction wraps.
    """
    caller = pre.deploy_contract(_inframe_meter())
    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            caller: Account(
                storage={SLOT_X: 0, SLOT_DECREASING: 0, SLOT_NO_WRAP: 0}
            )
        },
        tx=tx,
    )
