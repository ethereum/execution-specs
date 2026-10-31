# Class #16 — reservoir allocation is NOT subject to 63/64

**The invariant.** A child frame receives the parent's *entire* state-gas reservoir, so
a parent cannot hold any state gas back across a child call — asymmetrically with
execution gas, where it always retains `gas_left // 64`.

**What a failure means.** A contract that creates state after calling out can no longer
predict whether its own write will fit.

## The rule, in the spec's own words

```python
def drain_state_gas_reservoir(gas_meter: GasMeter) -> StateGas:
    """
    Empty the frame's state gas reservoir for a child frame.

    A child frame receives the parent's entire reservoir; there is no
    all-but-one-64th rule for state gas. The parent's reservoir is
    restored when the child returns.
    """
    reservoir = gas_meter.state_gas_left
    gas_meter.state_gas_left = StateGas(Uint(0))
    return reservoir
```
`amsterdam/vm/gas.py:689` (body at :707-710). Against:
```text
max_message_call_gas(g) = g - g // 64                       amsterdam/vm/gas.py:861
```

This class pins a **new** rule rather than an old one. That is the point: a later fork
that "fixed" the asymmetry by giving state gas its own 63/64 rule would change what every
Amsterdam-era contract receives, and nothing else in the corpus would notice. There is no
deployed mainnet witness because the rule does not exist on mainnet yet — the witnessed
population is the whole body of contracts that will be written against Amsterdam. Stated
plainly rather than padded.

## Two facts that shape every test here

**1. The reservoir is the part of `tx.gas` above the EIP-7825 cap.** Not a separate
field.

```python
evm_gas = tx_gas - intrinsic.execution
execution_gas_budget = GasCosts.TX_MAX_GAS_LIMIT - intrinsic.execution   # 16,777,216
execution_gas = min(execution_gas_budget, evm_gas)
state_gas_reservoir = evm_gas - execution_gas
```
`allocate_evm_gas`, amsterdam/vm/gas.py:1105. Consequence for EEST: passing **both**
`gas_limit=` and a positive `state_gas_reservoir=` silently yields a **zero** reservoir,
because `state_gas_reservoir` only steers the *implicit* gas limit
(`transaction_types.py:611`). This cost an hour and produced a probe where every param
failed for the wrong reason.

**2. A state charge the reservoir cannot cover spills into `gas_left`.**
`charge_state_gas_from_meter` (amsterdam/vm/gas.py:412) falls back to execution gas and
records the spill. So a frame with plenty of execution gas never notices an empty
reservoir. Every test here therefore forwards a **tight execution-gas literal** to the
frame doing the state-creating work. That is the only way to make the reservoir visible,
and it is also the shape deployed callers actually use.

A corollary worth recording: an **out-of-gas child returns the reservoir intact**.
`incorporate_child` asserts `child_meter.state_gas_left == child_meter.state_gas_baseline`
for a failed child, and the baseline is the full grant, so the parent gets all of it back
(`vm/__init__.py:187`). Only a *successful* child that spent the reservoir removes it —
which is why the drain contract below commits a slot rather than running out of gas.

## Measurements

Instrument: `tests/tools/test_cls16_reservoir_probe.py`. Failures *are* the measurement:
a failing param is a budget too small.

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/instruments --from Amsterdam --until Amsterdam \
    -k "cls16 and state_test" --output /tmp/p16 -q --tb=line -p no:cacheprovider
```

### How much execution gas a child needs to create one slot, by reservoir

```text
reservoir handed to the child   minimum forwarded execution literal
97,920  (= StateGasCosts.STORAGE_SET)      (12,100 , 12,110]
     0                                     (110,020 , 110,040]
difference                                 97,920 = exactly STORAGE_SET
```
The reservoir covers the state charge with nothing spilled and nothing left over, which
is only true if the child received **100%** of it. Had it received `63/64 = 96,390`, the
remaining 1,530 would spill out of the literal, pushing the requirement to ~13,636.
CHECKED.

### A reservoir a child spends is gone for the next child

One caller, one reservoir of exactly one slot, two children:

```text
first child      second child's literal   second child commits
does nothing     12,200                   yes
does nothing     13,630 / 20,000/ 110,040 yes
spends it        12,200                   no
spends it        13,630                   no
spends it        20,000                   no
spends it        110,040                  yes
```
The last row identifies the shortfall as exactly the state-gas charge, not something
else. CHECKED.

### The execution-gas half of the asymmetry, to one gas

Reservoir 0, child consumes everything it is given, parent's inline fresh `SSTORE` runs
purely on what the 63/64 rule withheld:

```text
tx.gas        retained = (tx.gas - 18,020) // 64   parent commits
6,949,784                            108,465       no    <- 63 epilogues
7,041,280                            109,738       no
7,059,683                            110,027       no
7,059,811                            110,027       no
7,059,812                            110,028       YES   <- 64 epilogues, exactly
7,060,000                            110,030       yes
```

The threshold is **7,059,812 exactly**, and every component of it is named:

```text
epilogue execution need E = 110,028
    2,100  COLD_STORAGE_ACCESS
   10,000  STORAGE_WRITE
   97,920  STORAGE_SET, spilled out of gas_left
        8  POP + two PUSH1
caller pre-call cost  c = 3,020  = 3,000 COLD_ACCOUNT_ACCESS + 18 (six PUSH) + 2 (GAS)
intrinsic                15,000  Amsterdam zero-value call (EIP-2780 decomposition)
threshold = 64*E + c + intrinsic = 7,041,792 + 3,020 + 15,000 = 7,059,812
```
Predicted and measured agree to **one gas**, so both are CHECKED rather than one inferred
from the other. The same arithmetic also confirms the Amsterdam intrinsic is 15,000 for
this shape.

## Tests

| test | params | asserts |
|---|---|---|
| `test_child_receives_the_entire_reservoir` | reservoir 97,920 at literals 12,100 / 12,110 / 20,000, plus reservoir 0 at 20,000 | the child's slot commits only from 12,110, and never without a reservoir |
| `test_a_reservoir_spent_by_a_child_is_gone_for_the_next` | `not_drained`, `drained`, `drained_but_funded` | the second child commits unless the first spent the reservoir — and commits again once given 110,040 |
| `test_execution_gas_retention_is_exactly_one_64th` | 63 epilogues, 64 epilogues − 1, 64 epilogues | the parent's epilogue commits at exactly `64 x` and not one gas below |

All `valid_from("EIP8037")`: a positive reservoir raises on earlier forks
(`transaction_types.py:697`) and there is nothing to test without one.

**What these tests do not claim.** A 63/64 rule applied to a one-slot reservoir would
leave the parent `97,920 // 64 = 1,530` — still not a slot — so the `drained` arm would
fail either way. The asymmetry only becomes *arithmetically* decisive at reservoirs of
`64 x STORAGE_SET = 6,266,880` and above, where a hypothetical retained 64th would be a
whole slot. That is stated here rather than tested, because a child cannot *spend* a
6.27M reservoir without ~775,000 execution gas of its own, and the budget that allows
that also lets the parent spill its way out — the two requirements are incompatible. A
clean negative with its cause, per SCHEMA §7.9.

The asymmetry is therefore expressed as a pair of quantitative statements rather than one
matched A/B test:

```text
execution gas:  64 x the epilogue's cost in the budget  ->  parent retains exactly 1 epilogue
state gas:      any multiple of the epilogue's cost     ->  parent retains 0
```

## Mutation results

```bash
cd /home/devops/toni/datanalysis/eip-8037/patterns
python3 tools/mutate.py -k reservoir --archetype reservoir_allocation
python3 tools/mutate.py -k retention --archetype reservoir_allocation
```

```text
mutation                            reservoir_allocation
(baseline)                          pass(30)
reservoir-6364                      DETECTED(3)
reservoir-half                      DETECTED(15)
drain-no-reservoir                  DETECTED(15)
retention-32                        DETECTED(6)
retention-128                       DETECTED(3)
retention-256                       DETECTED(3)
retention-osaka-256                 n/a    (no test selected: Amsterdam-only class)
cls9-inframe-refund-to-reservoir    survives
gas-reports-reservoir               survives
```

- **`reservoir-6364`** is my mutation and the one this class exists for: it applies the
  all-but-one-64th rule to `drain_state_gas_reservoir`, i.e. a later fork "fixes" the
  asymmetry its own docstring declares. DETECTED(3) — exactly the
  `exact_reservoir_12110` param, the tight bracket. The loose params survive it
  correctly -- 20,000 and 110,040 both absorb the 1,530-gas spill the mutation
  introduces -- so *which* params fire measures how large the change was.
- **`reservoir-half`** is the coarse version; it breaks 5 params.
- **`retention-*`** are caught by the third test, where the parent's retained execution
  gas halves (`128`) or quarters (`256`) and the zero-margin `64 epilogues` param flips.
  `retention-32` doubles the retention, so the two `no` params flip instead — DETECTED(6)
  rather than DETECTED(3), which is the signature of the opposite direction.
- **`retention-osaka-256` reads `n/a`**, not `survives`. Every test here is
  `valid_from("EIP8037")`, so an Osaka-fork mutation selects nothing and the harness
  reports `UNTRUSTWORTHY` — correctly refusing to read "no tests ran" as a pass.
- **`gas-reports-reservoir` survives** (another agent's mutation): no test here reads
  `GAS`.
- **`cls9-inframe-refund-to-reservoir` survives** (another agent's mutation): no test
  here clears a slot it created.

### Specificity: the unrestricted matrix

One unrestricted run, all 20 archetype directories in the corpus
(`python3 tools/mutate.py -k "reservoir-" --md`):

```text
mutation          detected by                     survives
reservoir-6364    reservoir_allocation only (3)   the other 19 archetypes
reservoir-half    reservoir_allocation only (15)  the other 19 archetypes
```

Both mutations are seen by **this directory alone**. That is the property that makes a
failure diagnostic: when `reservoir_allocation` goes red and nothing else does, the cause
is the state-gas allocation rule and nothing else. In particular `retained_epilogue` —
the archetype that already detects the *execution*-gas retention divisor — is blind to
both, which is the asymmetry stated as a measurement.

## Scaffolding audit

Every gas literal in this directory **is** the measurement — that is the archetype. The
bracketing pairs (12,100/12,110 and `64x`−1/`64x`) mean no literal is load-bearing
without a partner that pins it from the other side. The one literal that is merely
"comfortable" is `LITERAL_COMFORTABLE = 20,000`, used as the drain child's budget: it must
exceed 12,110 and it does, by 1.65x.
