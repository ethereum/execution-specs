"""
Verify the EIP-2200 (EIP-1706) minimum-gas rule for SSTORE: a non-mutating
store fails unless the gas left exceeds the call stipend, across CALL,
CALLCODE and DELEGATECALL entry into the storing frame.

Ported from:
state_tests/stSStoreTest/sstore_gasLeftFiller.json

@manually-enhanced: Do not overwrite. The stored-to slot is warmed
before the boundary call, so the stipend check - not the cold-access
charge EIP-8037/8038 reprice - binds on every fork. Boundary gas is
stipend + the store's own operand pushes +/- 1; the indicator's budget
is its full composite cost. Success is signalled by
`flag * indicator_gas`, not the ported hardcoded-pc JUMPI, and the
canary slot proves the caller ran to completion.
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
    # The storing frame: push the operands, then a no-op SSTORE. Gas left
    # when it executes is the forwarded amount less these pushes, and
    # EIP-2200 requires that to exceed the stipend.
    store_operands = Op.PUSH1[0x1] * 2
    store_code = store_operands + Op.SSTORE
    storer = pre.deploy_contract(code=store_code + Op.STOP, storage={1: 1})
    boundary_gas = (
        fork.gas_costs().CALL_STIPEND
        + store_operands.gas_cost(fork)
        + gas_offset
    )

    # Written only if the boundary call succeeded. Forward its full
    # composite cost so EIP-8037 state gas is covered outright.
    indicator_code = Op.SSTORE(
        key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    indicator = pre.deploy_contract(code=indicator_code)
    indicator_gas = indicator_code.gas_cost(fork)

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

    # The indicator gets gas only if the boundary call succeeded, so no
    # jump destinations are needed. Without the canary a failure arm
    # would also pass if the caller never reached the indicator.
    canary_slot = 0xC0DE
    caller = pre.deploy_contract(
        code=prelude
        + Op.POP(
            Op.CALL(
                gas=Op.MUL(indicator_gas, boundary_call),
                address=indicator,
            )
        )
        + Op.SSTORE(key=canary_slot, value=0x1)
        + Op.STOP,
    )

    # CALLCODE / DELEGATECALL store into the caller's own slot 1.
    caller_storage = {canary_slot: 1}
    if opcode != Op.CALL:
        caller_storage[1] = 1

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
    )

    post = {
        indicator: Account(storage={1: 1 if store_succeeds else 0}),
        caller: Account(storage=caller_storage),
    }

    state_test(pre=pre, post=post, tx=tx)
