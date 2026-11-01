"""
Archetype 20: `gasleft()` as a sufficient statistic for affordability.

Affordability gates are everywhere on mainnet -- batch processors, keeper and
automation contracts, liquidation loops, relayers -- in the shape
`if (gasleft() < THRESHOLD) { skip or break }`. They all rest on one
assumption: **`gasleft()` tells the frame what it can afford.**

EIP-8037 breaks that assumption, and breaks it in the direction the rest of
this corpus does not cover. `GAS` pushes `gas_meter.gas_left` only and never
the reservoir, while state charges draw from the **reservoir first** and from
`gas_left` only on spill. So a frame can complete a 97,920-state-gas write
while truthfully reporting a `gasleft()` far below 97,920.

The resulting failure is not an out-of-gas. It is an **unnecessary refusal**:
the gate declines work the frame could have performed, the batch silently
processes fewer items, and nothing reverts. Every other archetype here
detects work that stops fitting; this one detects work that still fits but is
no longer attempted.

Measured (`tests/tools/test_gasleft_sufficiency_probe.py`, CHECKED): with a
200,000 reservoir and 30,000 forwarded execution gas, `LT(GAS, 97920)` is 1
and the fresh store still commits.

The three arms below use the **same forwarded budget** so the only thing that
varies is the rule:

```
fork        reservoir   forwarded   fresh store
<= Osaka    0           15,000      FAILS     -- the whole cost comes from gas_left
Amsterdam   0           15,000      FAILS     -- spill: same as above
Amsterdam   200,000     15,000      SUCCEEDS  -- state charge drawn from the reservoir
```

The middle arm matters: it proves the third arm's behaviour comes from the
reservoir and not merely from being on a later fork.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SLOT_GATE_WOULD_REFUSE = 0x01
SLOT_WORK = 0x02

# State-gas cost of creating one slot: COST_PER_STATE_BYTE 1530 x 64 bytes.
# Used only as the gate's threshold, i.e. the number a real contract would
# compare against -- not as an assertion about cost.
STATE_COST = 97_920

# Deliberately below the ~110,026 a fresh slot needs from `gas_left` alone,
# and far above the few thousand its execution component needs.
FORWARDED = 26000


# The marker slot is pre-seeded non-zero so that writing it is a RESET, not a
# creation. Without this the marker itself creates a second fresh slot, which
# doubles the reservoir draw and the execution cost and masks the mechanism
# under test.
MARKER_SEED = 9


def _gated_worker(pre: Alloc) -> object:
    """A frame that records what a gate would decide, then does the work."""
    return pre.deploy_contract(
        storage={SLOT_GATE_WOULD_REFUSE: MARKER_SEED},
        code=(
            # What a deployed affordability gate would conclude from `gasleft()`.
            Op.SSTORE(SLOT_GATE_WOULD_REFUSE, Op.LT(Op.GAS, STATE_COST))
            # The work the gate was guarding. Reached unconditionally, so the
            # test observes what the frame could *actually* afford rather
            # than what the gate decided.
            + Op.SSTORE(SLOT_WORK, 1)
            + Op.STOP
        ),
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_gasleft_is_sufficient_before_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a frame cannot afford a store its `gasleft()` does not cover.

    With no state-gas reservoir, the store's entire cost is drawn from
    `gas_left`, so a frame reporting less than the cost genuinely cannot do
    it. The frame runs out of gas and neither marker commits -- which is
    exactly what makes `gasleft()` a sound basis for a gate on these forks.
    """
    worker = _gated_worker(pre)
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=FORWARDED, address=worker)) + Op.STOP
    )
    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={worker: Account(storage={SLOT_GATE_WOULD_REFUSE: MARKER_SEED})},
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_gasleft_still_sufficient_without_a_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the pre-8037 behaviour survives when no reservoir is declared.

    This is the control for the next test. The state charge spills onto
    `gas_left`, so the frame fails exactly as it did before EIP-8037, and the
    divergence below cannot be attributed to the fork alone.
    """
    worker = _gated_worker(pre)
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=FORWARDED, address=worker)) + Op.STOP
    )
    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={worker: Account(storage={SLOT_GATE_WOULD_REFUSE: MARKER_SEED})},
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_gasleft_understates_capacity_with_a_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a frame completes a store whose cost exceeds its own `gasleft()`.

    `drain_state_gas_reservoir` hands the child the entire reservoir with no
    63/64 rule, and the state charge draws from it before touching
    `gas_left`. So the frame reports a `gasleft()` below the store's state
    cost -- a deployed gate would refuse here -- and the store commits
    anyway. Both markers are asserted, because the finding is precisely the
    conjunction: the gate would have said no, and the work would have
    succeeded.
    """
    worker = _gated_worker(pre)
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=FORWARDED, address=worker)) + Op.STOP
    )
    tx = Transaction(
        to=caller, state_gas_reservoir=200_000, sender=pre.fund_eoa()
    )
    state_test(
        pre=pre,
        post={
            worker: Account(
                storage={SLOT_GATE_WOULD_REFUSE: 1, SLOT_WORK: 1}
            )
        },
        tx=tx,
    )
