"""
Measurement instrument: is `gasleft()` a sufficient statistic for what a
frame can afford, once a state-gas reservoir exists?

`GAS` pushes `gas_meter.gas_left` only, never the reservoir, while state
charges draw from the reservoir FIRST. So a frame can complete a 97,920
state-gas write while reporting a `gasleft()` far below it.

The child is reached by CALL with a small forwarded budget;
`drain_state_gas_reservoir` hands it the ENTIRE reservoir with no 63/64 rule.
FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

SLOT_UNDERSTATES = 0x01
SLOT_WORK = 0x02
STATE_COST = 97_920


@pytest.mark.parametrize("fwd", [30_000, 60_000])
@pytest.mark.parametrize("understates,work", [(1, 1), (1, 0), (0, 1), (0, 0)])
@pytest.mark.valid_from("EIP8037")
def test_suff(
    state_test: StateTestFiller, pre: Alloc, fwd: int, understates: int, work: int
) -> None:
    """Probe."""
    child = pre.deploy_contract(
        Op.SSTORE(SLOT_UNDERSTATES, Op.LT(Op.GAS, STATE_COST))
        + Op.SSTORE(SLOT_WORK, 1)
        + Op.STOP
    )
    caller = pre.deploy_contract(Op.POP(Op.CALL(gas=fwd, address=child)) + Op.STOP)
    tx = Transaction(
        to=caller, state_gas_reservoir=200_000, sender=pre.fund_eoa()
    )
    state_test(
        pre=pre,
        post={child: Account(storage={SLOT_UNDERSTATES: understates, SLOT_WORK: work})},
        tx=tx,
    )
