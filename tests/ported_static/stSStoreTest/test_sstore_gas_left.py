"""
Verify the EIP-2200 (EIP-1706) minimum-gas rule for SSTORE: a non-mutating
store fails unless the gas left exceeds the call stipend, across CALL,
CALLCODE and DELEGATECALL entry into the storing frame.

Ported from:
state_tests/stSStoreTest/sstore_gasLeftFiller.json

@manually-enhanced: Do not overwrite. The stored-to slot is warmed before
the boundary call so the stipend check (not the cold-access charge, which
EIP-8037/8038 reprice) is the binding constraint on every fork; the
boundary gas is derived as stipend + push cost +/- 1; the success
indicator forwards gas via `flag * INDICATOR_GAS` instead of the ported
hardcoded-pc JUMPI; the tx gas is maxed so the indicator's storage write
is not budget-bound.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Gas forwarded to the success indicator; only needs to cover its regular
# costs (state gas rides on the transaction's implicit reservoir).
INDICATOR_GAS = 30_000


@pytest.mark.ported_from(
    ["state_tests/stSStoreTest/sstore_gasLeftFiller.json"],
)
@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
    ],
)
@pytest.mark.parametrize(
    "gas_offset, store_succeeds",
    [
        pytest.param(-1, False, id="below_boundary"),
        pytest.param(0, False, id="at_boundary"),
        pytest.param(1, True, id="above_boundary"),
    ],
)
def test_sstore_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    gas_offset: int,
    store_succeeds: bool,
) -> None:
    """A non-mutating SSTORE needs gas left above the call stipend."""
    gas_costs = fork.gas_costs()

    # The storing contract: a no-op SSTORE (slot 1 already holds 1 for the
    # CALL arm; the CALLCODE/DELEGATECALL arms pre-set the caller's own
    # slot 1). At the SSTORE, gas left = forwarded - two pushes; EIP-2200
    # requires it to exceed the stipend.
    store_code = Op.SSTORE(key=0x1, value=0x1)
    storer = pre.deploy_contract(code=store_code + Op.STOP, storage={1: 1})
    push_cost = 2 * gas_costs.VERY_LOW
    boundary_gas = gas_costs.CALL_STIPEND + push_cost + gas_offset

    # Written by the success indicator call.
    indicator = pre.deploy_contract(code=Op.SSTORE(key=0x1, value=0x1))

    if opcode == Op.CALL:
        # Warm the storer's slot (and pre-write it back to 1) with an
        # unbounded call, so the boundary call's SSTORE is a warm no-op
        # and only the stipend check can fail it.
        prelude = Op.POP(Op.CALL(address=storer))
        boundary_call = opcode(gas=boundary_gas, address=storer)
    else:
        # CALLCODE/DELEGATECALL store into the caller's own slot 1: the
        # pre-write makes the boundary store a warm no-op.
        prelude = Op.SSTORE(key=0x1, value=0x1)
        if opcode == Op.CALLCODE:
            boundary_call = opcode(gas=boundary_gas, address=storer, value=0)
        else:
            boundary_call = opcode(gas=boundary_gas, address=storer)

    # The indicator receives gas only if the boundary call succeeded
    # (flag * INDICATOR_GAS), so no jump destinations are needed.
    caller = pre.deploy_contract(
        code=prelude
        + Op.POP(
            Op.CALL(
                gas=Op.MUL(INDICATOR_GAS, boundary_call),
                address=indicator,
            )
        )
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
    )

    post = {
        indicator: Account(storage={1: 1 if store_succeeds else 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
