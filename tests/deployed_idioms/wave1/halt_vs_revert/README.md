# Archetype 11: halt-versus-revert gas return

## The invariant

**A caller that tolerates child failure recovers gas on `REVERT` but not on an
exceptional halt, and its own completion depends on which.**

- A reverting frame keeps its unspent `gas_left`, which the parent absorbs
  (`amsterdam/vm/interpreter.py:460-463` → `amsterdam/vm/__init__.py:231-241`). CHECKED.
- A halted frame runs `forfeit_remaining_gas`, which zeroes `gas_left`
  (`amsterdam/vm/interpreter.py:450-458`, `amsterdam/vm/gas.py:647`), so the parent
  absorbs nothing. CHECKED.
- **From EIP-8037 the reverting frame hands back more than its unspent execution gas.**
  `restore_state_gas` refills the state-gas spill into `gas_left` before the parent
  absorbs the meter (`amsterdam/vm/gas.py:493`); the halting frame reaches the same
  refill and then forfeits it, so the halt destroys state gas the child was charged for.
  CHECKED.

The asymmetry is invisible to the caller's control flow: `CALL` returns `0` in both
cases. Only the gas tells them apart, and only indirectly — by whether the caller's own
epilogue can still run.

## Deployed witness

`registry/L5-dynamic.jsonl` — *tolerated child failure inside a committing transaction*,
mainnet blocks 26,250,000–26,259,999, axes `revert-propagation`,
`exceptional-halt-gas-burn`, `gas-forwarding-6364`, `fixed-gas-budget`:

- Raw 116,823 frames, **measured false-positive rate 94.12% (`sql/35`)**: 109,953 of them
  are reverts that consumed under half their grant — business-logic failures no repricing
  can flip. The discriminator is `result_gas_used / action_gas`.
- The record's post-filter population is **6,281 frames across 270 distinct runtime code
  hashes** (counting unit: call frames, and the distinct runtime code hashes behind them).
  The brief's ~6,870 is the bare subtraction residual `116,823 − 109,953`; **6,281** is
  the filtered count and is the figure used here. CHECKED, with the discrepancy stated
  rather than silently reconciled.
- Exemplars:
  - `<address withheld>` — KyberSwap executor, 10,029 self-call
    frames in 3,981 transactions, 40% failing and tolerated;
  - `<address withheld>` — 5,413 of 6,852 frames (79%) fail and
    are tolerated (Sourcify: ERC1967Proxy, solc 0.8.35);
  - `<address withheld>` — a deployed AMM, where **the
    `StateChangeDuringStaticCall` and out-of-gas arms are both tolerated**. That is this
    exact discriminator in deployed code: one arm returns its gas and the other burns it,
    and the same `catch` handles both.

Statically (`registry/L2-bytecode.jsonl`) — *best-effort sub-call inside a loop*, axes
including `exceptional-halt-gas-burn` and `revert-propagation`: **17,435 mainnet
addresses from 15,296 distinct runtime code hashes** (1.54% of 994,414 scanned);
exemplar `<address withheld>`. Its recorded invariant: *"every
iteration's call is attempted and the loop completes ... regardless of how any individual
recipient behaves."* CHECKED.

## Shape

Three frames, so that *both* outcomes are a committed non-zero effect:

```
outer      SSTORE(status, CALL(gas=200_000, tolerant) + 1)     2 = survived, 1 = died
tolerant   POP(CALL(gas=GAS, child))                           tolerates the failure
           SSTORE(s0,1) SSTORE(s1,1) SSTORE(s2,1)              the epilogue
child       STOP | REVERT | INVALID | out-of-gas
```

`tolerant` forwards `GAS` — the deployed `call(gas(), ...)` idiom — so it retains exactly
the 63/64 remainder and nothing else. The epilogue overwrites three **pre-existing**
slots (`0xFF → 1`), which costs 15,000 on Berlin..Osaka and 36,300 on Amsterdam: more
than the retained remainder, far less than a returned grant. So the epilogue commits
**iff** the child gave its gas back, and the three slots keep `0xFF` otherwise because
the whole frame rolls back.

The grant is a literal (200,000). A deployed caller's forwarding ceiling is in its
immutable code; the moment it becomes `cost(fork)` the test stops being a canary
(`wave1/frozen_budget/README.md`, rule 1).

## Measurement

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
for F in Berlin London Osaka Amsterdam; do
  ./.venv/bin/fill ../../wave1/instruments/test_refund_probe.py --from $F --until $F \
      -k "retained_after and state_test" --output /tmp/p11-$F -q --tb=line \
      -p no:cacheprovider
done
```

Gas held by `tolerant` after the child ends, on a 200,000 grant. CHECKED:

```text
fork               STOP      REVERT   INVALID      OOG
Berlin            197,376   197,370     3,080    3,080
London            197,376   197,370     3,080    3,080
Osaka             197,376   197,370     3,080    3,080
Amsterdam         196,976   196,970     3,073    3,073
```

A factor of 64 between the returning and the burning column, stable across every fork in
range, and one epilogue cost (15,000 / 36,300) sits inside every bracket — which is why a
single construction discriminates on all six forks.

And after a child that creates a slot and burns itself down to ~4,000 gas with `WhileGas`
before ending — once **clearing** the slot first (`-k "drained_child"`) and once leaving
the spill **outstanding** (`-k "unrepaid_child"`):

```text
                    clears the slot        keeps the spill
fork               REVERT   INVALID      REVERT   INVALID
Berlin              6,990     3,080       7,096     3,080
Osaka               6,990     3,080       7,096     3,080
Amsterdam         104,902     3,073     105,008     3,073
```

Both Amsterdam revert figures are ~105,000, but **they arrive by different routes**, and
the mutation matrix is what proved it rather than inspection. With the clear,
`credit_state_gas_refund` has already moved the spill into `gas_left`, so the revert
merely returns it; without the clear the spill is still outstanding and
`restore_state_gas` on the revert path is the only thing that can return it. Only the
second shape can detect a change to that refill — see the gap section below.

## Tests

| test | forks | points | assertion |
|---|---|---|---|
| `test_a_tolerant_caller_recovers_gas_on_revert_but_not_on_a_halt` | Berlin → Amsterdam | `stop`, `revert`, `invalid`, `oog` | epilogue commits on the first two (`status` 2), rolls back on the last two (`status` 1) |
| `test_a_drained_child_returns_nothing_either_way_before_eip8037` | Berlin → Osaka | `revert`, `halt` | both kill the caller: a drained child's revert is worth no more than its halt |
| `test_a_drained_child_returns_its_restored_spill_on_revert_from_eip8037` | EIP8037 → | `revert`, `halt` | the revert now returns ~104,900 and the epilogue commits; the halt still returns nothing |
| `test_a_revert_returns_an_outstanding_spill_and_a_halt_destroys_it` | EIP8037 → | `revert`, `halt` | the same, with **no clear**, so `restore_state_gas` is isolated: ~105,000 back on `REVERT`, nothing on a halt |

The four-point first test is deliberately not split: without the halting pair it would not
distinguish *"gas came back"* from *"the epilogue was affordable anyway"*, and without the
returning pair it would not distinguish *"gas was burnt"* from *"the construction never
worked"*.

The second and third tests are the fork-split pair. Keeping the pre-fork half is what
makes the EIP-8037 result a *change* rather than an isolated observation: if a later fork
removed the spill restore, the third test fails and the second starts applying again,
which is the signal we want rather than silence.

## Fill

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/halt_vs_revert --until Amsterdam \
    --output /tmp/hv -q --tb=no -p no:cacheprovider
# 138 passed    CHECKED  (tree verified pristine before and after)
```

## Mutation result

```bash
cd tests/deployed_idioms
python3 tools/mutate.py -k cls11 --archetype halt_vs_revert   # scoped, seconds
python3 tools/mutate.py -k cls11-revert-no-spill              # specificity row
```

### Inventory: 6 mutations, **4 distinct rules**, 8 test points

| rule | mutations | which arm it targets |
|---|---|---|
| **R5** — an exceptional halt burns the frame's gas | `cls11-halt-returns-gas` (Amsterdam `forfeit_remaining_gas`), `cls11-halt-returns-gas-osaka` (Osaka interpreter) | the `invalid` and `oog` points of the main test; **two independent code sites**, Amsterdam's being a named helper and Osaka's an inline assignment |
| **R6** — a revert returns the frame's gas | `cls11-revert-burns-gas`, `cls11-revert-burns-gas-osaka` | the `revert` point of the main test; same two sites, opposite direction to R5 |
| **R7** — a revert restores the state-gas spill into `gas_left` | `cls11-revert-no-spill-restore` (`restore_state_gas`, Amsterdam only — the rule does not exist pre-8037) | the EIP8037 drained-child `revert` point |
| **R8** — a returning child's gas is absorbed by the parent | `cls11-no-child-gas-return` | the `stop` point, which R5 and R6 structurally cannot reach |

The two-site pairs in R5/R6 are one rule each. They are kept separate because the fork
implementations differ in shape, so a `find` string for one cannot apply to the other, and
a fork could plausibly change one. Reported as four rules, not six findings.

R8 is expected to be detected broadly, not specifically — it is near the root of the call
protocol, so many archetypes should see it. It is included only because the `stop` point
depends on it and nothing else does.

```text
mutation                       halt_vs_revert  refund_cap  refund_not_spendable  calldata_floor_refund
(baseline)                     pass(24)        pass(4)     pass(6)               pass(4)
cls11-halt-returns-gas         DETECTED(12)    survives    survives              survives
cls11-halt-returns-gas-osaka   DETECTED(6)     survives    survives              n/a
cls11-revert-burns-gas         DETECTED(9)     survives    survives              survives
cls11-revert-burns-gas-osaka   DETECTED(3)     survives    survives              n/a
cls11-revert-no-spill-restore  DETECTED(3)     survives    survives              survives
cls11-no-child-gas-return      DETECTED(12)    survives    survives              survives
cls9-refund-funds-gas-left-osaka DETECTED(3)   --          DETECTED(3)           --
cls9-inframe-refund-to-reservoir survives      --          DETECTED(3)           --
every cls8-* mutation          survives        --          --                    --
m4-no-merge-repay (core-gas)   survives        --          --                    --
```

**6 of 6 DETECTED, all four rules covered, and every one survives on the three
neighbouring archetypes.** Baseline green (`pass(24)` = 8 Amsterdam-valid test
points x 3 fixture formats).

Confirmed unrestricted across all 19 archetypes
(`python3 tools/mutate.py -k cls11-revert-no-spill`, baselines green
everywhere): `cls11-revert-no-spill-restore` is **DETECTED(3) by
`halt_vs_revert` and survives on all eighteen others**. The revert path's spill
refill has exactly one test in the corpus, and it is the one added below.

Which arm each mutation reaches, read off the counts:

| mutation | arms it fires | reading |
|---|---|---|
| `cls11-halt-returns-gas` | 12 = main `invalid`+`oog` (6) + both drained `halt` arms (6) | every halting point depends on the forfeit |
| `cls11-halt-returns-gas-osaka` | 6 = main `invalid`+`oog` only | correct: at Osaka the drained child holds only ~3,900 gas, so returning it still leaves the caller short of the 15,000 epilogue. A *graded* result, not a gap |
| `cls11-revert-burns-gas` | 9 = main `revert` + both drained `revert` arms | |
| `cls11-revert-burns-gas-osaka` | 3 = main `revert` only | the Osaka drained arm already expects failure, so burning its gas changes nothing |
| `cls11-revert-no-spill-restore` | **3 = the unrepaid-spill `revert` arm alone** | perfect isolation of `restore_state_gas` |
| `cls11-no-child-gas-return` | 12 = every arm where the caller survives | broad by nature; included only because the `stop` point depends on it and nothing else does |

### The gap the matrix found, and how it was closed

On its first run **`cls11-revert-no-spill-restore` was detected by nothing**,
including by the drained-child test written for it. The reason is mechanical and
was not visible by reading the code: the drained child *clears* its slot before
reverting, and the clear's `credit_state_gas_refund` has already moved the
97,920 spill into `gas_left`. By the time `REVERT` is reached the spill is zero,
so deleting the revert path's refill changes nothing -- the two mechanisms are
interchangeable in that construction, and it isolates neither.

Closed by adding `test_a_revert_returns_an_outstanding_spill_and_a_halt_
destroys_it`, whose child creates a slot, drains, and reverts **without
clearing**, so the spill is still outstanding and `restore_state_gas` is the
only thing that can return it. Measured: 105,008 returned on `REVERT` against
3,073 on a halt (Amsterdam), 7,096 / 3,080 pre-8037. `cls11-revert-no-spill-
restore` is now DETECTED(3) and is detected by *nothing else*.

This is the loop the matrix exists to drive: a mutation that no test detects is
a finding about the test, not about the rule. It also corrected a claim this
README previously made -- that the drained-child pair tested the spill restore.
It did not.


## What a failure means

**An exceptional halt has started returning gas, or a revert has stopped returning it (or
stopped returning the state gas it restores), so the 6,281 live frames that tolerate a
child's failure and then do more work are now deciding their own survival on a different
rule than the one they were written against.**
