# Archetype 20: `gasleft()` as a sufficient statistic for affordability

**Invariant.** If `gasleft()` is below the cost of some work, the frame genuinely cannot
perform that work. Equivalently: `gasleft()` tells a frame what it can afford.

**Why it matters.** Affordability gates are everywhere on mainnet — batch processors,
keeper and automation contracts, liquidation loops, relayers — in the shape
`if (gasleft() < THRESHOLD) { skip or break }`. All of them rest on this invariant.

**Why it is rule-dependent.** `GAS` pushes `gas_meter.gas_left` only and never the
reservoir (`vm/instructions/control_flow.py:143`), while state charges draw from the
**reservoir first** and from `gas_left` only on spill. `drain_state_gas_reservoir` hands a
child the *entire* reservoir with no 63/64 rule. So a frame can complete a
97,920-state-gas write while truthfully reporting a `gasleft()` far below it.

**The failure direction is the one no other archetype covers.** This is not an
out-of-gas; it is an **unnecessary refusal**. The gate declines work the frame could have
done, the batch silently processes fewer items, and nothing reverts. Every other
archetype in this corpus detects work that stops fitting. This one detects work that
still fits but is no longer attempted.

**Three arms, same forwarded budget**, so the only thing that varies is the rule:

```text
fork          reservoir   forwarded   fresh store   asserted
<= Osaka      0           26,000      FAILS         gasleft is sound
Amsterdam     0           26,000      FAILS         control: not the fork alone
Amsterdam     200,000     26,000      SUCCEEDS      gasleft understates capacity
```

The middle arm is load-bearing: without it, the third arm's behaviour could be attributed
to being on a later fork rather than to the reservoir.

**Measurements that set the budget** (CHECKED, `tests/tools/`):

```text
execution component of one fresh SSTORE, Amsterdam   (12,000 , 12,200]
   -- isolated by paying the state charge from a reservoir
   (test_exec_component_probe.py)
   This reconciles exactly with the independently measured floor of
   (110,020 , 110,040]: 97,920 state + ~12,106 execution.
working window for FORWARDED                          (24,000 , ~27,100)
   -- above Amsterdam's execution need for the two stores in this child,
      below the pre-8037 total cost of the same two stores
   (measured by sweeping FORWARDED; 26,000 satisfies all three arms)
```

The marker slot is pre-seeded non-zero so writing it is a reset rather than a creation.
Without that, the marker itself creates a second fresh slot, doubling both the reservoir
draw and the execution cost and masking the mechanism under test. I hit exactly that and
the first two budget choices failed because of it.

**Reproduce**

```bash
cd engine/eels
./.venv/bin/fill ../../wave1/gasleft_sufficiency --until Amsterdam \
    --output /tmp/gs -q -p no:cacheprovider          # 25 passed
cd ../../patterns && python3 tools/mutate.py -k reservoir
```

**Mutation result** (CHECKED), with perfect specificity — no other archetype moves:

```text
mutation                gasleft_sufficiency   every other archetype
drain-no-reservoir      DETECTED(3)           survives
gas-reports-reservoir   DETECTED(3)           survives
```

`gas-reports-reservoir` is the direct test of the rule: make `GAS` report
`gas_left + reservoir` and the gate stops understating, so the test fails.

**What a failure means.** Either the reservoir no longer reaches child frames, or `GAS`
has started reporting it. In the second case every deployed affordability gate silently
changes behaviour.
