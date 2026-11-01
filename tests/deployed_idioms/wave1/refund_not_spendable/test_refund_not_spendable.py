"""
Archetype 9: refunds do not fund in-frame execution.

On every fork before EIP-8037 this is absolute. A storage refund accrues
to `evm.refund_counter` and is settled after the transaction finishes
(`osaka/vm/instructions/storage.py:98-116`; settlement in
`osaka/fork.py`), so **clearing a slot never raises the gas available to
the frame that cleared it**. From EIP-8037 it is false for state gas:
`credit_state_gas_refund` puts the refund straight back into `gas_left`
(LIFO -- `gas_left` up to the spill, then the reservoir;
`amsterdam/vm/gas.py:594`, called from
`amsterdam/vm/instructions/storage.py:151`).

The corpus already has EIP-8037-specific tests asserting the *new*
behaviour. Nothing pinned the *old* invariant on the forks where it still
holds, and that asymmetry is what this file closes.

This is adjacent to archetype 10 but distinct. Archetype 10 asserts what
`GAS` *reports*; this file asserts what the frame can *afford*. A fork
could in principle change one without the other, and only this shape
would notice.

Witnessed (CHECKED, `registry/L2-bytecode.jsonl`): *storage slot cleared
after a state-creating call (set/call/clear)* -- **265,217 mainnet
addresses from 208,712 distinct runtime code hashes**, 20.99% of the
994,414 mainnet runtimes scanned; exemplar
`<address withheld>`. The record's own invariant
is this class verbatim: *"clearing a slot after a sub-call does not
increase the gas the frame has available for its remaining work, so
whether the frame's epilogue commits is decided by the budget it was
given and not by how many slots it happened to clear."*

**Shape.** A caller forwards a literal budget to a child, tolerates the
child's failure, and records `CALL + 1` -- so 2 means the child
completed and 1 means it did not, and *both* outcomes are a committed
non-zero effect rather than an absent write. The child sets a slot,
clears it, then does a fixed 15,000 gas of further work as a `JUMPDEST`
sled (`JUMPDEST` costs 1 gas on every fork from Frontier through
Amsterdam, `amsterdam/vm/gas.py:197`), so the sled is a literal, not a
fork-derived expression.

`state_gas_reservoir=0` on the transaction: explicit 0 pins the gas limit
to the fork's cap with no reservoir (cross-fork safe -- only a *positive*
reservoir raises pre-Amsterdam), so the child's state charge spills out
of its own `gas_left` and the clear's credit returns there. That is the
hostile and realistic case: a legacy caller has no reservoir to absorb a
state charge.

Measured, not assumed (`tests/tools/test_refund_probe.py`, budget ladder
of 26 points, three fixture formats):

```text
fork             smallest budget in which set + clear + 15,000 completes
Berlin                                              (37,200 , 37,300]
London                                              (37,200 , 37,300]
Osaka                                               (37,200 , 37,300]
Amsterdam                                          (112,000 , 115,000]
```

Berlin..Osaka: `22,100` set + `100` clear + `15,000` sled + pushes.
Amsterdam: the `110,026` peak of the set *plus* the 2,301 EIP-2200
stipend sentry the clear must satisfy **before** its own credit arrives
(`amsterdam/vm/instructions/storage.py:103`) -- the refill cannot pay for
the clear that produces it.

A second measured surprise, found the same way: Berlin..Osaka the clear
needs `gas_left > 2,300` on entry (`osaka/.../storage.py:73`), so a
budget of 23,000 cannot even reach past the clear although the set and
the clear together only cost 22,212. The control point below uses 25,000
for that reason, and the shortfall it leaves is 12,200 rather than the
14,300 a naive subtraction gives.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SLOT_X = 0x01

# 15,000 JUMPDESTs = 15,000 gas, and the same number on every fork.
SLED = 15_000

# Measured floor Berlin..Osaka is in (37,200 , 37,300]. 25,000 covers the
# set, the clear, and the clear's own 2,300 stipend sentry (~24,413
# together -- measured: 23,000 is NOT enough, the sentry is checked before
# the clear's 100-gas charge), and leaves the frame ~12,200 short of
# finishing -- less than the 19,900 the clear just put in the refund
# counter (STORAGE_SET 20,000 - WARM_ACCESS 100).
PRE_8037_SHORT_BUDGET = 25_000
PRE_8037_AMPLE_BUDGET = 38_000

# Measured floor at Amsterdam is in (112,000 , 115,000].
EIP8037_BUDGET = 115_000
EIP8037_SHORT_BUDGET = 112_000


def _child(sled: int) -> Bytecode:
    """Create a slot, clear it, then do `sled` gas of further work."""
    return (
        Op.SSTORE(SLOT_X, 1)
        + Op.SSTORE(SLOT_X, 0)
        + Op.JUMPDEST * sled
        + Op.STOP
    )


def _tolerant_caller(child: object, budget: int, slot: int) -> Bytecode:
    """Call `child` on a literal budget; commit 2 on success, 1 on failure."""
    return (
        Op.SSTORE(slot, Op.ADD(Op.CALL(gas=budget, address=child), 1))
        + Op.STOP
    )


def _run(
    state_test: StateTestFiller,
    pre: Alloc,
    *,
    sled: int,
    budget: int,
    expected: int,
) -> None:
    """Fill one (sled, budget) point and assert the caller's record."""
    child = pre.deploy_contract(_child(sled))
    committed = Storage()
    slot = committed.store_next(expected, "child_ok")
    caller = pre.deploy_contract(_tolerant_caller(child, budget, slot))
    state_test(
        pre=pre,
        post={caller: Account(storage=committed)},
        tx=Transaction(
            to=caller, sender=pre.fund_eoa(), state_gas_reservoir=0
        ),
    )


@pytest.mark.parametrize(
    "sled,budget,expected",
    [
        pytest.param(
            SLED, PRE_8037_AMPLE_BUDGET, 2, id="ample_budget_completes"
        ),
        pytest.param(
            0, PRE_8037_SHORT_BUDGET, 2, id="short_budget_reaches_the_clear"
        ),
        pytest.param(
            SLED, PRE_8037_SHORT_BUDGET, 1, id="refund_is_not_spendable"
        ),
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_a_frames_own_clear_does_not_fund_its_execution(
    state_test: StateTestFiller,
    pre: Alloc,
    sled: int,
    budget: int,
    expected: int,
) -> None:
    """
    Test a clear's 19,900-gas refund buys the clearing frame nothing.

    Three points, and all three are needed. The first shows the
    construction completes when the budget covers it, so a failure
    elsewhere is not an artefact of the shape. The second, with the sled
    removed, shows 25,000 gas is enough to reach *past* the clear -- so
    in the third point the refund has demonstrably accrued at the moment
    the frame starves. The third is the invariant: holding 19,900 in the
    refund counter and needing ~12,200 more gas, the frame still dies.

    A fork that routed storage refunds into `gas_left` the way EIP-8037
    routes state gas would turn the third point green, and 265,217
    deployed addresses whose epilogues are budgeted on the old rule would
    start seeing gas they were never written to expect.
    """
    _run(state_test, pre, sled=sled, budget=budget, expected=expected)


@pytest.mark.parametrize(
    "budget,expected",
    [
        pytest.param(EIP8037_BUDGET, 2, id="refill_makes_the_budget_enough"),
        pytest.param(
            EIP8037_SHORT_BUDGET, 1, id="below_the_set_plus_sentry_peak"
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_a_frames_own_clear_does_fund_its_execution_from_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
    budget: int,
    expected: int,
) -> None:
    """
    Test the same shape now completes on a budget that cannot cover it.

    At 115,000 the child pays 110,026 to create the slot and is left with
    under 5,000 -- not enough for the 15,000-gas sled. It finishes anyway,
    because the clear returns the 97,920 state-gas spill to its own
    `gas_left`. Without that refill the child needs ~125,100, so this
    test is exactly the in-frame M2 refund and nothing else.

    The 112,000 point is the floor's other side: below the set's peak
    plus the clear's 2,301 stipend sentry, the refill never happens.
    Pinning both keeps the test at the cliff rather than somewhere
    comfortably above it.
    """
    _run(state_test, pre, sled=SLED, budget=budget, expected=expected)
