"""
Measurement instrument: the EXECUTION-gas component of one fresh SSTORE at
Amsterdam, isolated by paying its state charge from a reservoir.

The child does exactly one fresh store. With a reservoir large enough to
cover the 97,920 state charge, whatever the child still needs from its
forwarded budget is the execution component. FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Storage, Transaction


@pytest.mark.parametrize(
    "fwd", [5000, 8000, 10000, 12000, 12200, 14000, 16000, 20000, 24000]
)
@pytest.mark.valid_from("EIP8037")
def test_exec(state_test: StateTestFiller, pre: Alloc, fwd: int) -> None:
    """Probe."""
    cs = Storage()
    child = pre.deploy_contract(Op.SSTORE(cs.store_next(1, "w"), 1) + Op.STOP)
    caller = pre.deploy_contract(Op.POP(Op.CALL(gas=fwd, address=child)) + Op.STOP)
    tx = Transaction(
        to=caller, state_gas_reservoir=200_000, sender=pre.fund_eoa()
    )
    state_test(pre=pre, post={child: Account(storage=cs)}, tx=tx)
