# Archetype 9: refunds do not fund in-frame execution

## The invariant

**On every fork before EIP-8037: a frame's available gas is unchanged by its own clears.**
A storage refund accrues to `evm.refund_counter` and is settled after the transaction
finishes (`osaka/vm/instructions/storage.py:98-116`), so the gas it represents is never
spendable by the frame that earned it. CHECKED.

From EIP-8037 this is **false for state gas**. `credit_state_gas_refund` puts the refund
straight back into `gas_left` — LIFO, `gas_left` up to the spill and then the reservoir
(`amsterdam/vm/gas.py:594`), called from
`amsterdam/vm/instructions/storage.py:151`. CHECKED.

The corpus already had EIP-8037-specific tests asserting the *new* behaviour, and nothing
pinning the *old* invariant on the forks where it still holds. That asymmetry is what
this directory closes.

**Distinct from archetype 10.** Archetype 10 asserts what `GAS` *reports*; this asserts
what the frame can *afford*. A fork could change one without the other, and only this
shape would notice. The mutation matrix shows the two archetypes are in fact detected by
overlapping but not identical mutation sets.

## Deployed witness

`registry/L2-bytecode.jsonl` — *storage slot cleared after a state-creating call
(set/call/clear)*, rule axes `storage-refunds`, `state-gas-reservoir`,
`gas-monotonicity`, `refund-cap`:

- **265,217 mainnet addresses from 208,712 distinct runtime code hashes**, 20.99% of the
  994,414 mainnet runtimes scanned (counting unit: distinct runtime code hashes behind a
  chain-1 deployment in the Sourcify v2 export, and the addresses they back). CHECKED.
- Exemplar `<address withheld>` (highest deployed-address count
  for the shape); further witnesses `<address withheld>`,
  `<address withheld>`.
- The record's own invariant **is this class verbatim**: *"Clearing a slot after a
  sub-call does not increase the gas the frame has available for its remaining work, so
  whether the frame's epilogue commits is decided by the budget it was given and not by
  how many slots it happened to clear."*
- The record's own false-positive note is quoted here rather than hidden: it is
  deliberately the broad form, and the prior art's precision pipeline (prune → order →
  guardclass → finalfilter, 0/6 miscalibrations) should be applied before any single
  instance is called a *harm*. The population above is therefore the **idiom** count, not
  a harm count.

Dynamically (`registry/L5-dynamic.jsonl`, mainnet blocks 26,250,000–26,259,999):
**60,324 transactions refund exactly 19,900** — one fresh set-then-clear, which is
precisely the shape the child in these tests performs. CHECKED.

## Shape

A caller forwards a **literal** budget to a child, tolerates the child's failure, and
commits `CALL + 1`: **2** means the child completed, **1** means it did not. Both are a
non-zero committed effect, so neither arm can pass by writing nothing.

The child sets a slot, clears it, then does a fixed 15,000 gas of further work as a
`JUMPDEST` sled (`JUMPDEST` = 1 gas on every fork Frontier→Amsterdam,
`amsterdam/vm/gas.py:197`), so the post-clear work is a literal, not a fork-derived
expression.

`state_gas_reservoir=0` on the transaction: explicit 0 pins the gas limit to the fork's
cap with no reservoir, and is cross-fork safe (only a *positive* reservoir raises
pre-Amsterdam, `transaction_types.py:353`). That makes the child's state charge spill out
of its own `gas_left`, so the clear's credit returns there — the hostile and realistic
case, since a legacy caller has no reservoir to absorb a state charge.

## Measurement

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
for F in Berlin London Osaka Amsterdam; do
  ./.venv/bin/fill ../../wave1/instruments/test_refund_probe.py \
      --from $F --until $F -k "set_clear_budget and state_test" \
      --output /tmp/p9-$F -q --tb=no -p no:cacheprovider
done
```

A 26-point budget ladder whose failing params *are* the measurement. CHECKED:

```text
fork        smallest literal budget in which set + clear + 15,000 gas completes
Berlin                                                   (37,200 , 37,300]
London                                                   (37,200 , 37,300]
Osaka                                                    (37,200 , 37,300]
Amsterdam                                               (112,000 , 115,000]
```

Berlin..Osaka decomposes as `22,100` set + `100` clear + `15,000` sled + pushes ≈ 37,212.
Amsterdam is **not** `12,100 + 100 + 15,000`: the binding constraint is the `110,026`
*peak* of the set plus the `2,301` EIP-2200 stipend sentry the clear must satisfy
**before** its own credit arrives (`amsterdam/vm/instructions/storage.py:103-105`) ≈
112,333. The refill cannot pay for the clear that produces it.

### Two things the measurement corrected

1. **The in-frame refill is peak-limited, not total-limited.** A first guess of
   "`12,200 + sled`" is wrong by ~100,000 gas. The frame must be able to afford the whole
   spill before any of it comes back.
2. **A 23,000-gas budget cannot reach past the clear**, although the set and the clear
   together only cost 22,212 — because Berlin..Osaka's sstore refuses to start unless
   `gas_left > 2,300` (`osaka/vm/instructions/storage.py:73`). The control point uses
   25,000 for that reason, and the shortfall it leaves is 12,200 rather than the 14,300 a
   naive subtraction gives. Caught by a failing param, not by arithmetic.

## Tests

**Berlin..Osaka — three points, all three needed:**

| point | sled | budget | child | why it is in the test |
|---|---|---|---|---|
| `ample_budget_completes` | 15,000 | 38,000 | **2** | the construction works when the budget covers it |
| `short_budget_reaches_the_clear` | 0 | 25,000 | **2** | 25,000 is enough to execute *past* the clear, so in the next row the refund has demonstrably accrued |
| `refund_is_not_spendable` | 15,000 | 25,000 | **1** | **the invariant**: holding 19,900 in the refund counter and needing ~12,200 more gas, the frame still dies |

**From EIP-8037 — two points:**

| point | budget | child | why |
|---|---|---|---|
| `refill_makes_the_budget_enough` | 115,000 | **2** | completes on a budget ~10,100 short of what it needs without the refill; the clear's 97,920 covers the gap |
| `below_the_set_plus_sentry_peak` | 112,000 | **1** | the other side of the measured floor, so the test sits at the cliff |

A note on honesty about the cross-fork comparison: the pre-8037 arm's shortfall is
*purely* about the refund (same fork, same prices, budget 12,200 short of a 19,900
refund). The Amsterdam arm's success is pinned to the M2 mechanic by mutation rather than
by cross-fork subtraction, because Amsterdam also reprices `STORAGE_WRITE` 20,000 →
10,000 and a bare pre-vs-post budget comparison would be over-determined by that.

## Fill

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/refund_not_spendable --until Amsterdam \
    --output /tmp/rn -q --tb=no -p no:cacheprovider
# 63 passed    CHECKED  (tree verified pristine before and after)
```

## Mutation result

```bash
cd tests/deployed_idioms
python3 tools/mutate.py -k cls9 --archetype refund     # scoped, seconds
python3 tools/mutate.py -k cls9-inframe                # specificity row
python3 tools/mutate.py -k m2-no-inframe --archetype refund   # cross-check
```

### Inventory: 2 mutations, **2 distinct rules**

| rule | mutation | which arm it targets |
|---|---|---|
| **R3** — the pre-8037 refund counter does not reach `gas_left` | `cls9-refund-funds-gas-left-osaka`: the set-then-clear's 19,900 also credits `evm.gas_left` (`osaka/.../storage.py:108`), fork Osaka | the Berlin..Osaka `refund_is_not_spendable` point. This is the hypothetical 8037-style inversion applied to a fork where the invariant still holds, which is the only mutation that can falsify the old rule. |
| **R4** — the EIP-8037 state refund *does* reach `gas_left` | `cls9-inframe-refund-to-reservoir`: `credit_state_gas_refund`'s `from_gas_left` forced to 0, so the refund lands wholly in the reservoir (`amsterdam/vm/gas.py:594`) | the EIP8037 `refill_makes_the_budget_enough` point |

`core-gas.json`'s `m2-no-inframe-refill` (not mine) targets R4 as well by dropping the
gas entirely rather than re-routing it, and is cross-checked above. Two mutations of one
rule by different means is one result about the rule and two about the code path, and is
reported that way.

```text
mutation                          refund_not_spendable  refund_cap  halt_vs_revert  calldata_floor_refund
(baseline)                        pass(6)               pass(4)     pass(24)        pass(4)
cls9-refund-funds-gas-left-osaka  DETECTED(3)           survives    DETECTED(3)     survives
cls9-inframe-refund-to-reservoir  DETECTED(3)           survives    survives        survives
m2-no-inframe-refill (core-gas)   DETECTED(3)           survives    --              survives
every cls8-* and cls11-* mutation survives              --          --              --
```

**Both arms independently DETECTED, and the two arms are detected by
*different* mutations** -- which is the property that makes the pair
meaningful rather than redundant:

* `cls9-refund-funds-gas-left-osaka` fires the Berlin..Osaka
  `refund_is_not_spendable` point (3 fixture formats). This is the only kind
  of mutation that *can* falsify the old invariant: the rule's content is that
  nothing happens, so it has to be tested by making something happen.
* `cls9-inframe-refund-to-reservoir` fires the EIP8037
  `refill_makes_the_budget_enough` point. `core-gas.json`'s
  `m2-no-inframe-refill` fires the same point by a different edit, which
  cross-validates the path rather than adding a second finding.

Baselines green on all four archetypes. The Osaka mutation also fires
`halt_vs_revert`'s drained-child revert arm, which is correct and expected --
that test's pre-8037 arm depends on the same rule.


## What a failure means

**Gas that a frame earned by clearing storage has become spendable by that frame (or, on
Amsterdam, stopped being spendable), so the post-clear epilogue of 265,217 deployed
addresses is now running on a different budget than the one it was written against.**
