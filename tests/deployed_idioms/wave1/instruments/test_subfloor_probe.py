"""
Measurement instrument, not a corpus test: for each sub-floor convention
budget, (a) does realistic read-only hook work complete inside it, and
(b) can a callee create one storage slot inside it?

Its FAILURES ARE THE MEASUREMENT. For probe B the PASSING param names the
real answer on that fork. Do not add this directory to a corpus gate.

Reproduce (from engine/eels):
  ./.venv/bin/fill ../../wave1/instruments --from <Fork> --until <Fork> \
      -k "subfloor and state_test" --output /tmp/sf -q --tb=no \
      -p no:cacheprovider
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

BUDGETS = [3229, 30000, 50000]

SLOT_RO = 0x11
SLOT_W = 0x12

# Read-only hook body: one cold SLOAD, a comparison, a 32-byte return.
READ_ONLY = Op.MSTORE(0, Op.ISZERO(Op.SLOAD(0))) + Op.RETURN(0, 32)
WRITER = Op.SSTORE(0, 1) + Op.STOP


@pytest.mark.parametrize("budget", BUDGETS)
@pytest.mark.valid_from("Berlin")
def test_subfloor_readonly(
    state_test: StateTestFiller, pre: Alloc, budget: int
) -> None:
    """Probe A: does the read-only body fit `budget`?"""
    callee = pre.deploy_contract(READ_ONLY)
    prober = pre.deploy_contract(
        # The CALL must run before either MLOAD: `Op.X(a, b)` emits `b`
        # first, so putting the CALL inside an AND reads memory too early.
        Op.MSTORE(
            0x20,
            Op.CALL(gas=budget, address=callee, ret_offset=0, ret_size=32),
        )
        + Op.SSTORE(SLOT_RO, Op.AND(Op.MLOAD(0x20), Op.MLOAD(0)))
        + Op.STOP
    )
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage={SLOT_RO: 1})}, tx=tx)


@pytest.mark.parametrize("expect", [0, 1])
@pytest.mark.parametrize("budget", BUDGETS)
@pytest.mark.valid_from("Berlin")
def test_subfloor_write(
    state_test: StateTestFiller, pre: Alloc, budget: int, expect: int
) -> None:
    """Probe B: can a callee create one storage slot inside `budget`?"""
    callee = pre.deploy_contract(WRITER)
    prober = pre.deploy_contract(
        Op.SSTORE(SLOT_W, Op.CALL(gas=budget, address=callee)) + Op.STOP
    )
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            prober: Account(storage={SLOT_W: expect}),
            callee: Account(storage={0: expect}),
        },
        tx=tx,
    )
