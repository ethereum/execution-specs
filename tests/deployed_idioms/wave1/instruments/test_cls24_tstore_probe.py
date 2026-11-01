"""
Measurement instrument for class #24 (transient-storage lifetime and its
state-gas immunity). **ITS FAILURES ARE THE MEASUREMENT.** Every param
asserts 0, so the mismatch message prints the real value as
`want 0x0, got 0x...`. Do not add this directory to a corpus gate.

Three questions:

1. `gas_delta` -- what does a frame actually get charged, from inside the
   EVM, for one TSTORE / TLOAD, with a ZERO reservoir? With no reservoir
   any state charge has to spill out of `gas_left`
   (`charge_state_gas_from_meter`, amsterdam/vm/gas.py:412), so the
   `GAS`-difference is the whole cost, state gas included.

2. `lock_budget` -- the smallest frozen literal in which the deployed
   reentrancy-lock shape (TLOAD guard, TSTORE set, external call, TSTORE
   clear) completes, and whether reentry is actually blocked.

3. `reservoir_intact` -- with a reservoir of exactly one slot
   (`StateGasCosts.STORAGE_SET` = 97,920) and a tight forwarded literal,
   does a frame still afford one fresh SSTORE after N TSTOREs? If TSTORE
   drew on the reservoir, the SSTORE's shortfall would spill into the
   tight literal and out-of-gas.

Reproduce (from tests/deployed_idioms/):
  python3 tools/locked_fill.py tests/tools --from <Fork> --until <Fork> \
      -k cls24 --output /tmp/cls24probe -q --tb=line -p no:cacheprovider
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Op,
    StateTestFiller,
    Transaction,
)

SLOT_MEASURED = 0x09
SLOT_EXISTING = 0x02
SLOT_RESULT = 0x0A
SLOT_OUTER = 0x20
SLOT_REENTRY = 0x21
SLOT_SECOND = 0x22
LOCK = 0x11

ONE_SLOT_STATE_GAS = 97_920

MEASURED_OPS = {
    # 1 gas, to price the measurement harness itself
    "jumpdest": Op.JUMPDEST,
    "tstore": Op.TSTORE(LOCK, 1),
    "tload": Op.POP(Op.TLOAD(LOCK)),
    "tstore_then_tload": Op.TSTORE(LOCK, 1) + Op.POP(Op.TLOAD(LOCK)),
    # reference: a slot that already holds a non-zero value, so no state
    # gas is charged (storage.py:148 gates on `original_value == 0`)
    "sstore_update": Op.SSTORE(SLOT_EXISTING, 2),
    "fresh_sstore": Op.SSTORE(0x7F, 1),
}


@pytest.mark.parametrize("op", list(MEASURED_OPS))
@pytest.mark.valid_from("Cancun")
def test_cls24_gas_delta(
    state_test: StateTestFiller, pre: Alloc, op: str
) -> None:
    """Probe: the in-frame gas delta across one transient-storage op."""
    subject = pre.deploy_contract(
        Op.MSTORE(0, Op.GAS)
        + MEASURED_OPS[op]
        + Op.MSTORE(0x20, Op.GAS)
        + Op.SSTORE(SLOT_MEASURED, Op.SUB(Op.MLOAD(0), Op.MLOAD(0x20)))
        + Op.STOP,
        storage={SLOT_EXISTING: 1},
    )
    tx = Transaction(to=subject, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre, post={subject: Account(storage={SLOT_MEASURED: 0})}, tx=tx
    )


# --------------------------------------------------------------------------
# 2. the deployed lock shape inside a frozen literal
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "budget",
    [3_229, 3_250, 3_260, 3_640, 3_660, 30_000, 50_000],
)
@pytest.mark.valid_from("Cancun")
def test_cls24_lock_budget(
    state_test: StateTestFiller, pre: Alloc, budget: int
) -> None:
    """
    Probe: does the transient lock round-trip inside `budget`.

    `attacker` takes the address to re-enter from calldata, so the two
    contracts need no deployment cycle. `guarded` hands it its own
    ADDRESS, so the re-entry hits the live lock.
    """
    # returns 1 | (reentry_succeeded << 1), so "the attacker ran" and "the
    # re-entry got through" are distinguishable from a zero word.
    attacker = pre.deploy_contract(
        Op.MSTORE(
            0x40,
            Op.OR(
                1,
                Op.SHL(
                    1, Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(0))
                ),
            ),
        )
        + Op.RETURN(0x40, 0x20)
    )
    guarded = pre.deploy_contract(
        Conditional(
            condition=Op.TLOAD(LOCK),
            if_true=Op.REVERT(0, 0),
            if_false=(
                Op.TSTORE(LOCK, 1)
                + Op.MSTORE(0, Op.ADDRESS)
                + Op.POP(
                    Op.CALL(
                        gas=Op.GAS,
                        address=attacker,
                        args_offset=0,
                        args_size=0x20,
                        ret_offset=0x20,
                        ret_size=0x20,
                    )
                )
                + Op.TSTORE(LOCK, 0)
                + Op.RETURN(0x20, 0x20)
            ),
        )
    )
    parent = pre.deploy_contract(
        Op.MSTORE(
            0x40,
            Op.CALL(
                gas=budget, address=guarded, ret_offset=0, ret_size=0x20
            ),
        )
        + Op.SSTORE(
            SLOT_OUTER,
            Op.OR(
                Op.OR(
                    Op.MLOAD(0x40),  # bit 0  outer call succeeded
                    Op.SHL(8, Op.MLOAD(0)),  # bit 8  re-entry succeeded
                ),
                # bit 16  a second outer call succeeds -> lock released
                Op.SHL(16, Op.CALL(gas=budget, address=guarded)),
            ),
        )
        + Op.STOP
    )
    tx = Transaction(to=parent, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={parent: Account(storage={SLOT_OUTER: 0})},
        tx=tx,
    )


# --------------------------------------------------------------------------
# 3. does a TSTORE consume state gas out of the reservoir?
# --------------------------------------------------------------------------


@pytest.mark.parametrize("tstores", [2])
@pytest.mark.parametrize(
    "literal", [12_315, 12_318, 13_320]
)
@pytest.mark.parametrize(
    "reservoir", [ONE_SLOT_STATE_GAS, ONE_SLOT_STATE_GAS - 1_530]
)
@pytest.mark.valid_from("EIP8037")
def test_cls24_reservoir_intact(
    state_test: StateTestFiller,
    pre: Alloc,
    tstores: int,
    literal: int,
    reservoir: int,
) -> None:
    """
    Probe: N TSTOREs, then one fresh SSTORE, on a reservoir of exactly one
    slot and a tight forwarded literal. Asserts 0, so a `got 0x1` means
    the write happened.
    """
    body = Bytecode()
    for i in range(tstores):
        body += Op.TSTORE(LOCK + i, 1)
    child = pre.deploy_contract(body + Op.SSTORE(SLOT_RESULT, 1) + Op.STOP)
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=literal, address=child)) + Op.STOP
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre, post={child: Account(storage={SLOT_RESULT: 0})}, tx=tx
    )
