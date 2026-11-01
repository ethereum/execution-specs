"""
Measurement instrument, not a corpus test: locate the minimum frozen gas
budget in which a callee can create one storage slot, per fork.

Its FAILURES ARE THE MEASUREMENT. A param that fails is a budget too small
on that fork. Do not add this directory to a corpus pass/fail gate.

Reproduce (from engine/eels):
  ./.venv/bin/fill ../../wave1/instruments --from <Fork> --until <Fork> \
      -k "floor and state_test" --output /tmp/fl -q --tb=no
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Storage, Transaction


@pytest.mark.parametrize("g", [20000, 22100, 22200, 50000, 110020, 110040, 200000, 250000])
@pytest.mark.valid_from("Berlin")
def test_floor(state_test: StateTestFiller, pre: Alloc, g: int) -> None:
    """Probe."""
    cs = Storage()
    callee = pre.deploy_contract(Op.SSTORE(cs.store_next(1, "w"), 1) + Op.STOP)
    caller = pre.deploy_contract(Op.POP(Op.CALL(gas=g, address=callee)) + Op.STOP)
    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={callee: Account(storage=cs)}, tx=tx)
