# Archetype 24: transient-storage lifetime, and its state-gas immunity

**Invariant, two-sided.**

1. **Lifetime.** A transient slot is visible for the whole transaction and gone at its
   end: a nested frame sees its caller's write, a *reverted* frame's write is discarded,
   and a *successful* write survives to the end of the transaction.
2. **State-gas immunity.** Transient storage carries **no state gas**, so it is
   structurally immune to every state-gas repricing in this catalogue.

Half (2) is the load-bearing one and nothing asserted it before this archetype. A fork
that gave transient storage a state cost would break the whole population at once,
silently.

**Mechanism** (CHECKED, pinned EELS Amsterdam):

```text
tstore:  charge_gas(evm, GasCosts.OPCODE_TSTORE)        amsterdam/.../storage.py:207
         -- and nothing else. No charge_state_gas call anywhere in the function.
sstore:  charge_gas(evm, gas_cost)                      amsterdam/.../storage.py:156
         charge_state_gas(evm, state_gas)               amsterdam/.../storage.py:157
         where state_gas = StateGasCosts.STORAGE_SET only inside
             if original_value == 0                     amsterdam/.../storage.py:145
transient lifetime:
         copy_tx_state     deep-copies transient_storage         state_tracker.py:763
         restore_tx_state  restores it on rollback               state_tracker.py:787
         incorporate_tx_into_block  clears it per transaction    state_tracker.py:843
```

The `original_value == 0` gate is why the negative control works: a *persistent* 1/2 lock
is state-gas immune too, because its slot never holds zero, while a 0/1 lock is not.

## Deployed witness

| shape | runtimes | addresses | FP | lens |
|---|---|---|---|---|
| transient reentrancy lock | 2,315 | 4,528 | 0.0 | L2 |
| transient storage written before an external call | 4,091 | 14,167 | 0.0 | L2 |
| transient slot written and never cleared | 2,005 | 5,478 | 0.125 | L2 |
| `sto.lock12` — persistent 1/2 lock (the negative control) | 6,785 | — | 0/8 | L2 |

L5 separately measured `TSTORE` at **3,938,758 occurrences across 12,603 runtimes** in a
10,000-block window; the window is mainnet 26,250,000–26,259,999, which L5's REPORT
states on every record (INFERRED for this figure specifically). Counting units are
distinct runtime code hashes and distinct addresses, as stated by L2.

Prior art cited rather than duplicated: a widely used reentrancy guard uses 1/2 rather
than 0/1 so its slot never holds zero and no zero-boundary refund rule touches it. That
result is reused here as the negative control instead of writing a new one. What is new is
that the same property also buys **state-gas** immunity — measured below. No claim is made
about intent; the 1/2 convention predates EIP-8037 by years.

## What is new here, and what is not

`tests/cancun/eip1153_tstore/` is **11 files and 2,698 lines** and already covers half (1)
thoroughly: `test_tstore_clear_after_tx` and `test_tstore_clear_after_deployment_tx` (the
transaction boundary), `test_tstore_rollback_on_callcode_revert` (revert rollback),
`test_tload_calls`, `test_tload_reentrancy`, `test_tstore_reentrancy`, 430 lines of
execution contexts, 364 of create contexts and 284 of selfdestruct interaction. **Per
SCHEMA's prior-art rule the lifetime semantics are not rebuilt here.**

Half (2) has **zero** coverage there, and structurally so (CHECKED): that suite derives
every gas expectation from the fork — `Op.TLOAD.gas_cost(fork)`
(`test_basic_tload.py:244-245`), `bytecode.gas_cost(fork)` (`test_tstorage.py:212`),
`callee_bytecode.gas_cost(fork) - 1` (`test_tstorage_execution_contexts.py:203`) — and
`grep -c "state_gas\|reservoir"` over it returns **0**. That is `docs/COVERAGE-GAP.md`'s
keystone result applied to this class: no test in it can fail under a reprice.

So this archetype contributes:

* the **immunity** itself, from both observables (zero-reservoir gas delta, and
  reservoir exhaustion with a positive reservoir);
* the **negative control** that gives the immunity meaning — the same lock in three
  flavours, two immune and one not, measured across the fork that broke the third;
* the lifetime facts the deployed idiom needs, asserted inside a **frozen deployed
  budget** rather than a fork-derived one, which is the one thing the official suite
  cannot express.

## Tests — 141 fill, Cancun → Amsterdam

```text
test_a_transient_lock_round_trips_inside_a_frozen_budget            3 params
test_a_reverted_attempt_does_not_brick_an_unreleased_transient_lock 1
test_a_transient_write_costs_no_state_gas                           4 params
test_a_transient_write_does_not_draw_on_the_state_gas_reservoir      3 params  (EIP8037+)
test_lock_flavours_that_carry_no_state_gas                          2 params
test_a_fresh_zero_one_lock_still_fitted_50000_before_eip8037        1         (..Osaka)
test_a_fresh_zero_one_lock_no_longer_fits_50000_at_eip8037          1         (EIP8037+)
```

## Measurements (all CHECKED)

Instrument: `tests/tools/test_cls24_tstore_probe.py`. Its **failures are the
measurement** — every param asserts 0 so the mismatch prints the real value.

```bash
cd tests/deployed_idioms
for F in Cancun Prague Osaka Amsterdam; do
  python3 tools/locked_fill.py tests/tools --from $F --until $F \
      -k "cls24_gas_delta and state_test" --output /tmp/gd-$F -q --tb=line \
      -p no:cacheprovider
done
```

**1. In-frame gas delta, zero reservoir.** With an empty reservoir every state charge
spills out of `gas_left` (`charge_state_gas_from_meter`, `gas.py:413`), so the `GAS`
difference is the whole cost. The apparatus itself costs 11 gas (measured with a bare
`JUMPDEST`: 12).

| operation | Cancun | Prague | Osaka | Amsterdam |
|---|---|---|---|---|
| `TSTORE` | 117 | 117 | 117 | **117** |
| `TLOAD` | 116 | 116 | 116 | **116** |
| `TSTORE` + `TLOAD` | 222 | 222 | 222 | **222** |
| `SSTORE` update (slot already non-zero) | 5,017 | 5,017 | 5,017 | **12,117** |
| `SSTORE` fresh slot | 22,117 | 22,117 | 22,117 | **110,037** |

The transient numbers do not move across the fork that multiplies a fresh slot by
**4.97x**. That is the immunity, measured rather than argued. The persistent rows
independently reproduce two of the corpus's other results. Subtracting the 17 gas of
apparatus (11 for the `GAS`/`MSTORE` harness, 6 for two `PUSH1` operands) gives 5,000,
12,100, 22,100 and **110,020** exactly: the first is archetype 3's equality that EIP-2929
deliberately preserved (held on the three pre-8037 forks measured here), the last sits
dead on the lower end of HANDOFF §3.1's independently bisected fresh-slot bracket of
(110,020 , 110,040].

**2. Reservoir exhaustion.** Reservoir of exactly one slot (97,920), child does two
TSTOREs and then one fresh `SSTORE`, on a tight forwarded literal.

```text
floor for (2 TSTOREs + 1 fresh SSTORE | reservoir 97,920)   (12,315 , 12,318]
chosen literal                                              13,320  (slack ~1,002)

reservoir 97,920, 0 TSTOREs, literal 13,320    write commits
reservoir 97,920, 2 TSTOREs, literal 13,320    write commits   <- nothing was drained
reservoir 96,390, 2 TSTOREs, literal 13,320    write FAILS     <- sensitivity calibration
          (97,920 - 1,530: one single state byte short)
```

The third row is what makes the first two trustworthy: a reservoir shortfall of **1.6%**
is enough to make the identical child fail, so the arm is sensitive to a per-TSTORE state
charge above roughly half a state byte. A doubling of TSTORE's *execution* price costs 200
gas against 1,002 of slack and would **not** trip it.

**3. Frozen-budget floor for the lock round-trip** (TLOAD guard → TSTORE set → external
call that re-enters → TSTORE clear, re-entry rejected, then a second successful entry):

```text
Cancun / Prague / Osaka      (3,250 , 3,260]
Amsterdam                    (3,640 , 3,660]      +400
```

The +400 is one `COLD_ACCOUNT_ACCESS` increase (2,600 → 3,000, EIP-8038) on the single
cold account access inside the budget — derivation INFERRED, brackets CHECKED. Consequence
measured on all four forks: **ERC-7579's 3,229-gas `postCheck` convention cannot host a
transient reentrancy guard that makes an external call, on any fork.** That is the lower
side of the two-sided bracket and it is a finding, not a construction.

**4. Lock flavours in EIP-4337's frozen 50,000-gas budget**, reservoir 0:

| flavour | why | Cancun..Osaka | Amsterdam |
|---|---|---|---|
| transient `TSTORE` 0/1 | `tstore` never calls `charge_state_gas` | fits | **fits** |
| persistent `SSTORE` 1/2 | `original_value != 0`, so `STORAGE_SET` unreachable | fits | **fits** |
| persistent `SSTORE` 0/1 | genuine `0 -> 1`: 22,100 then 110,020 | fits | **does not fit** |

Two unrelated mechanisms produce the same immunity, and the third flavour is the control
that already moved from working to out-of-gas at EIP-8037.

## Mutation result

```bash
cd tests/deployed_idioms
python3 tools/mutate.py -k cls24 --archetype transient_storage_lifetime
python3 tools/mutate.py -k cls24-          # the specificity column
```

```text
(baseline)                              pass(42)
cls24-tstore-charges-state-gas          DETECTED(18)   6 params
cls24-tstore-charges-one-state-byte     DETECTED(9)    3 params
cls24-transient-revert-not-rolled-back  DETECTED(3)    1 param
cls24-tload-always-zero                 DETECTED(9)    3 params
```

Which arms each one fires, measured per test:

```text
cls24-tstore-charges-state-gas (97,920)
    lock_round_trips: erc165_30000, erc4337_50000
    costs_no_state_gas: tstore, tstore_then_tload
    does_not_draw_on_the_reservoir: exact_reservoir_two_tstores
    lock_flavours: transient
cls24-tstore-charges-one-state-byte (1,530)
    costs_no_state_gas: tstore, tstore_then_tload
    does_not_draw_on_the_reservoir: exact_reservoir_two_tstores
cls24-transient-revert-not-rolled-back
    reverted_attempt_does_not_brick_the_lock
cls24-tload-always-zero
    reverted_attempt_does_not_brick_the_lock
    lock_round_trips: erc165_30000, erc4337_50000
```

**The graded pair behaves exactly as MUTATION-MATRIX.md §4 wants, and the arithmetic is
stated.** The fine mutation (one state byte) is *not* detected by the frozen-budget
survival arms, correctly: two TSTOREs charged 1,530 each spill 3,060 into a 30,000 or
50,000 budget, which absorbs it. It *is* detected by the exact-threshold arm and by the
reservoir arm, whose slack is 1,002. So the pair brackets the archetype's sensitivity
between ~500 gas per TSTORE (threshold and reservoir arms) and ~15,000 (survival arms),
which is the cliff-locating behaviour the corpus is built for rather than a boolean.

Also correct and worth recording: neither state-gas mutation touches the `tload` param,
because only `tstore` was given a cost; and `cls24-tload-always-zero` leaves the
`lock_flavours: transient` arm alone, because that lock never reads its slot. A mutation
firing on a *subset* of an archetype's arms is a sign the arms are independent.

## Specificity, and which direction this archetype detects

**All four `cls24-` mutations have exactly one detector**, over all 24 archetypes
(`python3 tools/mutate.py -k cls24- --md`; 48 baseline cells across the two column runs,
every one `pass`). That is the property that makes a failure diagnostic: when this row
alone goes red, the cause is transient storage, not a state-gas change elsewhere.

Run the other way — `python3 tools/mutate.py --archetype transient_storage_lifetime`,
all 61 mutations registered at the time of the run (the file count rises as other
contributors land theirs) — this archetype **detects 15**:

```text
cls24-tstore-charges-state-gas          18   mine, DEARER (state gas appears)
cls24-tstore-charges-one-state-byte      9   mine, DEARER (the smallest step)
cls24-tload-always-zero                  9   mine, semantic
cls24-transient-revert-not-rolled-back   3   mine, semantic
cpsb-x2.6                                6   DEARER state gas
cls2-storage-set-osaka-60000             3   DEARER state gas, pre-8037
cls3-storage-write-9000                  3   DEARER
cls12-cold-read-5000                     6   DEARER access
cls2-cpsb-250                            6   CHEAPER state gas
cls12-cold-read-700                      3   CHEAPER access
reservoir-6364                           6
reservoir-half                           6
drain-no-reservoir                       6
cls11-no-child-gas-return                6
```

**Both directions, measured, which INVARIANT-CLASSES.md's "repricing downward" section
requires.** The dearer direction is caught by the immunity arms; the cheaper direction is
caught by the three control arms, because they assert that something *fails* and a
reduction makes it succeed. Most notably `cls12-cold-read-700` — the EIP-1108-scale
reduction that **all six budget-sufficiency archetypes survive**, and which
MUTATION-MATRIX.md records as detectable only by exact-value or two-sided-bracket
archetypes — is **detected here** (3 failures = one param across the three fixture
formats). *Which* param is INFERRED, not measured: the arithmetic points at the reservoir
arm's `one_state_byte_short` calibration, because a cold read 2,100 -> 700 cuts the
child's execution floor by 1,400 and widens the forwarded literal's slack past the 1,530
it has to be unable to absorb, so the write it asserts must fail can suddenly be funded.
If so, that arm is tied to the access price as well as to the reservoir — a real
sensitivity, recorded rather than tuned away.

## What a failure means

Either transient storage has acquired a state cost — in which case 14,167 deployed
addresses that write a transient slot before an external call are running on a budget
that no longer covers them — or its lifetime boundary moved, and 4,528 addresses'
reentrancy guards either stop excluding re-entry or brick themselves after one tolerated
failure.
