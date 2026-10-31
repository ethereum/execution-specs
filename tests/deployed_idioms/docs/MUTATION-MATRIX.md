# Mutation matrix (PLAN.md phase 5)

Reproduce: `python3 tools/mutate.py` (list targets with `--list`). Each cell is a real
`fill` of that archetype against the pinned EELS Amsterdam fork with one rule perturbed.
The reference implementation is restored after every run and md5-verified at the end.

A test that survives every mutation of the rule it claims to depend on protects nothing
and is rejected (SCHEMA.md §4.2).

## Current scale

```text
archetype directories          24
registered mutations           83   (tools/mutations/*.json, one file per contributor)
corpus tests, Berlin..Amsterdam  2,683 passed, 0 failed
   ./.venv/bin/fill tests/deployed_idioms/tests --ignore wave1/instruments --until Amsterdam
```

**All 19 baselines are green.** The harness prints the baseline row first for a
reason: if an archetype's baseline is red, every mutation cell in its row is meaningless.
`subfloor_budget` was red mid-development and is now `pass(18)`.

## Concurrency

The harness edits files in the shared EELS tree, so it takes an exclusive `flock` and
refuses to start if it finds a leftover `# MUTATION` marker (the signature of a run killed
mid-mutation). Without the lock, a second instance would read the first's mutation as its
own "pristine" baseline and restore *that* at exit, leaving the pinned reference
implementation permanently corrupted. Seven contributors share it; use
`--archetype <dir>` while iterating so a run costs one fill per mutation instead of 19.

## Verified archetype/mutation pairs (main session)

```text
archetype                 detected by                              specificity
frozen_budget             cpsb-x2.6                                sole detector w/ A4
retained_epilogue         retention-256, cpsb-x2.6                 sole detector of retention
stipend_fallback          sload-cold-2300, stipend-2000            perfect
gas_monotonicity          m2-no-inframe-refill, m4-no-merge-repay  perfect
intrinsic_cost            tx-base-11000 (both arms),               perfect
                          tx-value-cost-5000 (value arm only)
gasleft_sufficiency       drain-no-reservoir, gas-reports-reservoir  perfect
code_presence_identity    extcodesize-hides-delegation             perfect (16 others survive)
```

`intrinsic_cost` is the sharpest result: `tx-base-11000` breaks both arms (6 tests) while
`tx-value-cost-5000` breaks only the value-bearing arm (3 tests), so the test
discriminates the *components* of EIP-2780's decomposition rather than just its total.

Mutations, and the exact edit each makes to
`src/ethereum/forks/amsterdam/vm/gas.py`:

```text
cpsb-x2.6             COST_PER_STATE_BYTE 1530 -> 4000; a fresh slot 97,920 -> 256,000
sload-cold-2300       COLD_STORAGE_ACCESS 2100 -> 2300; an EIP-1884-shaped access reprice
stipend-2000          CALL_STIPEND 2300 -> 2000
retention-128         max_message_call_gas: gas // 64 -> gas // 128
retention-256         max_message_call_gas: gas // 64 -> gas // 256
m2-no-inframe-refill  credit_state_gas_refund no longer adds to gas_left  (in-frame clear)
m4-no-merge-repay     repay_state_gas_spill no longer adds to gas_left    (child merge)
```

## What the matrix establishes

**1. Specificity, not just sensitivity.** Each mutation is detected only by the
archetype(s) that actually depend on it. That is the property that makes a failure
diagnostic: when `A7` alone goes red, the cause is an access or stipend reprice, not a
state-gas change.

**2. `A4` is the only archetype that can see the retention divisor.** Nothing else
detects `retention-256`. This confirms the reason archetype 4 had to exist: the 63/64
shape contains **no gas literal**, so no frozen-budget test can cover it. 245,595
mainnet addresses depend on it (L4, FP 0/18).

**3. `A10` detects the merge path and *not* the in-frame path**, which pins the M2/M4
distinction mechanically rather than by argument. `credit_state_gas_refund` is called
from `instructions/storage.py:151` (in-frame, M2); `repay_state_gas_spill` from
`vm/__init__.py:240` (child merge, M4). The monotonicity test uses `DELEGATECALL`, so the
child's clear credits the child's reservoir — in the child `from_gas_left` is already 0 —
and the parent's `gas_left` only grows on merge. An earlier version of this matrix
mutated M2 and wrongly read "survives" as a weak test; it was a wrong mutation, not a
weak test.

**4. Graded sensitivity is real and useful — and `retention-128` is no longer
undetected.** Against `retained_epilogue` it survives, correctly: keeping back
`avail // 128` of a 2**24 budget is ~131,072, above the measured ~110,026 needed to create
one slot, while `retention-256` (~65,536) is below it and bites. But classes #5, #6 and
#16 *do* detect `retention-128` (and `retention-32`), and **only** those three — the other
seventeen archetypes survive it. So the earlier "undetected" row was a genuine coverage
gap, now closed by a different test shape rather than by loosening the first one. As with
the `COST_PER_STATE_BYTE` sweep, *which* mutations fire measures how large a change was,
so the corpus locates a cliff rather than returning a boolean.

**5. A mutation can be legitimately shared without losing diagnostic value.**
`cls8-refund-div-10` fires `refund_cap`, `block_vs_sender_accounting` and
`state_gas_clamp`, because the divisor genuinely feeds the sender-facing `gas_used` that
the settlement classes assert on. Specificity is not the only useful property: the
*signature* discriminates. `refund_cap` red alone means the clear-refund amount moved; all
three red means the divisor moved.

**6. Some rules are structurally invisible to a given test shape, and that is worth
recording rather than fixing.** `gas-reports-reservoir` survives class #5 for a provable
reason: if `GAS` returned `gas_left + reservoir`, the parent's prediction would inflate by
`reservoir × 63/64` while the child's own `GAS` inflates by the *whole* reservoir, so the
two cancel to within `reservoir / 64`. **Any** cross-boundary agreement test is blind to
it; catching it needs a single-frame test comparing `GAS` against something outside the
gas system, which is what `gasleft_sufficiency` does.

## Gap the matrix exposed, and how it was closed

On its first run, **`m2-no-inframe-refill` was detected by nothing.** No archetype
exercised the in-frame refill: a frame that creates a slot, spills, and then clears *that
same slot with no child call*, so `credit_state_gas_refund` returns the gas to its own
`gas_left`. EIP-8037's M2 mechanic was unprotected.

Closed by adding `test_gas_readings_{decrease,invert}_across_an_inframe_clear` to
`wave1/gas_monotonicity/`: one frame, `SSTORE(x,1)` then `SSTORE(x,0)`, a `GAS` reading
on each side and no call between. Measured: strictly decreasing through Osaka, inverted
from EIP-8037 — the same invariant as the cross-frame test, on a path it structurally
cannot reach. `m2-no-inframe-refill` is now DETECTED.

This is the loop the matrix exists to drive: **a mutation that no test detects is a
finding about coverage.** Run it after every archetype is added, and treat any
all-`survives` row as unprotected until a test is written for it.


## Full matrix — the authoritative phase-5 deliverable

Reproduce: `python3 tools/mutate.py --md`. **Do not wrap it in `timeout`** (see hygiene
below). It takes the lock, so nothing else may fill concurrently.

```text
archetypes                      24
registered mutations            83
cells                           1,992
baselines green                 24/24
mutations detected by >=1       81/83
mutations with ONE detector     43   (perfect specificity)
archetypes detecting nothing    0            (every archetype protects something)
UNTRUSTWORTHY cells             0            (the `n/a` verdict removed all of them)
n/a cells                       40           (fork-restricted archetype vs fork-specific mutation)
```

**Both undetected mutations are explained, and neither is a coverage gap.**
`state-clamp-off` survives because `max(0, x) == x` for every `x` the reference rules can
produce — the clamp is unreachable, since `sstore` credits state gas only inside
`if original_value == 0` (`storage.py:148-151`); ten adversarial shapes were measured and
all came out 0 or +97,920. `floor-token-8` survives correctly, and paired with the
detected `floor-token-7` it locates the cliff at `TX_DATA_TOKEN_FLOOR = 7.74`.

A mutation that survives *for a stated arithmetic reason* is a result. One that survives
unexplained is a coverage gap. Keep that distinction explicit, or the matrix is not worth
reading.

### Detections per archetype

A low count is not a weakness — `frozen_budget` detects one mutation and it is the right
one. What would be a defect is an archetype detecting **nothing**, and none does.

```text
state_gas_clamp                 18
block_vs_sender_accounting      17
reservoir_allocation            16
dynamic_cost_prediction         15
refund_cap                      15
transient_storage_lifetime      14
hardcoded_cost_equality         11
halt_vs_revert                  10
refund_not_spendable            10
counterfactual_address           9
forwarding_prediction            9
depth_forwarding                 6
eoa_caller_identity              5
gas_monotonicity                 5
gasleft_sufficiency              5
intrinsic_cost                   4
subfloor_budget                  4
oog_as_signal                    3
stipend_fallback                 3
calldata_floor_refund            2
retained_epilogue                2
returndata_fidelity              2
code_presence_identity           1
frozen_budget                    1
```

### Breadth distribution

```text
detected by  0 archetype(s):   2 mutation(s)
detected by  1 archetype(s):  43 mutation(s)
detected by  2 archetype(s):  15 mutation(s)
detected by  3 archetype(s):   9 mutation(s)
detected by  4 archetype(s):   5 mutation(s)
detected by  5 archetype(s):   2 mutation(s)
detected by  6 archetype(s):   1 mutation(s)
detected by  7 archetype(s):   2 mutation(s)
detected by  8 archetype(s):   2 mutation(s)
detected by 10 archetype(s):   1 mutation(s)
detected by 11 archetype(s):   1 mutation(s)
```

43 of 83 mutations hit exactly one archetype. The widest is detected by 11, and those are
**shared rules**, not weak tests: a cold-read or state-byte reprice moves the cost of
almost everything. Diagnostic power lives in the *signature* — which set goes red
identifies which rule moved.

```text
cls12-cold-read-5000               11 archetypes
cpsb-x2.6                          10 archetypes
cls2-cpsb-250                       8 archetypes
cls12-cold-read-700                 8 archetypes
cls3-storage-write-9000             7 archetypes
sload-cold-2300                     7 archetypes
```

## Measurement hygiene, learned three times independently

**`fill` must not run while any `mutate.py` holds the lock.** This was discovered
separately by the main session and two agents, each time after a measurement that looked
clean:

- the main session filled the whole corpus during a live mutation and reported
  "6 failed" that did not reproduce;
- one agent's verification fill landed inside another's mutation window and reported
  **9 spurious failures on exactly its tight params**;
- another measured **+2,900 execution gas** on a shape that is 27,212 pristine, and nearly
  pinned it as a constant.

**`timeout <n> python3 <lock-holding script>` is itself a corruption mode, and the main
session used it repeatedly before this was understood.** SIGTERM terminates Python
**without running `finally`**, so a mutation run killed that way leaves the perturbed file
in place *and* the lock held. One such run was killed by a 2-minute tool limit mid-flight.
Run lock-holding scripts in the background and let them finish; never wrap them in
`timeout`.

**Before restoring a dirty tree, run `python3 tools/check_tree.py`.** It makes the rule
below executable rather than a habit, and exits `0` clean / `10` live-mutation-wait /
`20` stale-leftover-restore.

**Before restoring a dirty tree, check whether it is someone else's live mutation.** An
agent found `src/ethereum/forks/` dirty three separate times, and each time it was another
contributor's **in-flight** mutation (`cls18-copy-per-word-6`, `retention-osaka-256`,
`extcodesize-hides-delegation`), identified by matching the diff against the registered
mutation set *before* touching anything. Reflexively running `git checkout --` would have
silently corrupted a neighbour's measurement mid-run. The check is: is a `mutate.py`
process alive, and does the diff match a mutation in `tools/mutations/*.json`? If yes,
wait. Only a diff matching no registered mutation, with no live process, is a genuine
stale leftover.

Two guards exist, both acceptable; use one for every measurement run:

```bash
# simplest: borrow the same lock for a read-only fill
flock tools/.mutate.lock -c './.venv/bin/fill … '

# or the wrappers, which ALSO refuse to run against a dirty src/ethereum/forks/
python3 tools/verify_corpus.py        # whole corpus, one summary
python3 tools/locked_fill.py <args>   # arbitrary fill
```

Both guards are needed, not either: the lock misses a tree left dirty by a killed run, and
the git check misses a run that is legitimately mid-mutation right now.

## Two harness gotchas worth knowing

**`Transaction(gas_limit=X, state_gas_reservoir=R>0)` silently yields a ZERO reservoir.**
EIP-8037 defines the reservoir as `tx.gas` above `TX_MAX_GAS_LIMIT` (16,777,216), and
`state_gas_reservoir` only steers the *implicit* gas limit
(`transaction_types.py:611`). To get a real reservoir, **omit `gas_limit` entirely**. This
cost an agent an hour of uniformly-failing probes.

**`fill` has four summary forms and three lack the word "passed":**
`"9 failed, 6 passed in 1.2s"`, `"9 failed in 0.8s"`, `"30 failed, 30 deselected"` (with
`-k`), and `"44 passed in 2.0s"`. A form that is not parsed must never be read as a pass.
Separately, `mutate.py` currently reports `UNTRUSTWORTHY` when a fork-specific mutation
selects *nothing* in a fork-restricted archetype — a correct refusal, but it should be
distinguished from a genuinely unparseable run.

## Per-mutation detail: classes #24 and #25

**Reconciliation complete.** This section was written as an addendum while #18, #23, #24
and #25 were being built concurrently, because four racing edits to the same tables would
have lost data. The tables above have since been rebuilt from the full 24x83 run and are
authoritative. Every claim below was then **re-verified against that run**: all eight
`cls24-`/`cls25-` mutations are detected, each by exactly one archetype, with the counts
shown — an exact match, no discrepancies.

Kept because it carries per-mutation attribution the aggregate tables do not show.

```text
cls24-tstore-charges-state-gas          -> transient_storage_lifetime (18)
cls24-tstore-charges-one-state-byte     -> transient_storage_lifetime (9)
cls24-tload-always-zero                 -> transient_storage_lifetime (9)
cls24-transient-revert-not-rolled-back  -> transient_storage_lifetime (3)
cls25-origin-is-the-current-caller      -> eoa_caller_identity (9)
cls25-caller-is-the-tx-origin           -> eoa_caller_identity (9)
cls25-delegation-length-24              -> eoa_caller_identity (6)
cls25-delegatecall-rewrites-the-caller  -> eoa_caller_identity (3)
```

Three results that change statements elsewhere in this file:

**1. `extcodesize-hides-delegation` no longer has exactly one detector.** The list of 19
above needs it moved: `eoa_caller_identity` detects it too (6), because its EIP-7702 arms
assert `EXTCODESIZE(CALLER) == 23`. The 23-byte designator is now pinned from both sides
of a call — `code_presence_identity` on the callee side, `eoa_caller_identity` on the
caller side.

**2. `cls12-cold-read-700` is detected by a seventh archetype.** §"Mutations that
legitimately light up many archetypes" lists it at 7; `transient_storage_lifetime` makes
8 (CHECKED: 3 failures). The route is INFERRED, not measured: the reservoir arm's
calibration param (`one_state_byte_short`) asserts that a write *fails*, and a cold read
2,100 -> 700 widens the forwarded literal's slack past the one state byte it must be
unable to absorb. Recorded rather than tuned away: on that reading the arm is genuinely
sensitive to the access price as well as the reservoir.

**3. `eoa_caller_identity` is detected by no gas mutation at all.** `code_presence_identity`
was the first archetype with that signature; this is the second. The overwhelming majority
of registered mutations perturb a gas rule and none of them can change what `ORIGIN` or
`CALLER` reports — which is the cleanest available argument for the semantic-identity
family existing. (Measured as of this run: 61 mutations registered, of which 54 live in a
`vm/gas.py` or a fork-level refund divisor.)

Detection coverage for the two new rows: `transient_storage_lifetime` detects **15**
mutations out of the 61 registered at the time of the run (both reprice directions: `cpsb-x2.6`, `cls2-storage-set-osaka-60000`,
`cls3-storage-write-9000`, `cls12-cold-read-5000` dearer; `cls2-cpsb-250`,
`cls12-cold-read-700` cheaper; plus `reservoir-6364`, `reservoir-half`,
`drain-no-reservoir`, `cls11-no-child-gas-return`). `eoa_caller_identity` detects **5**.

## Validity caveat: EEST keeps its own gas table

`execution_testing` carries a **second, independent** gas table
(`packages/testing/.../forks/forks/eips/istanbul/eip_1108.py:21` sets
`PRECOMPILE_ECADD=150`; `src/ethereum/forks/istanbul/vm/gas.py:72` sets the same value
separately — both CHECKED). `tools/mutate.py` edits only the `src/ethereum/` side.

So for any constant mirrored in both tables, a single-table mutation makes the framework's
expectation disagree with the engine, and **every fork-derived test goes red for that
reason alone** — a `DETECTED` there would prove nothing about the test.

Why this corpus is largely insulated, and where it is not: our archetypes assert **frozen**
values and committed effects, so their assertions never consult the framework table. But
scaffolding that calls `.gas_cost(fork)`, `.execution_cost(fork)` or
`GasConsumer(gas=None, fork=fork)` does, and those cells carry the caveat.

The discriminator, measured: editing **both** tables to simulate a real reprice
(`PRECOMPILE_ECADD` 150→50) leaves the official `byzantium/eip196_ec_add_mul/test_gas.py`
**green at 24 passed — blind to the reprice** — while `precompile_price_bracket` goes
**3 failed, detected**. That is the first measured demonstration of the COVERAGE-GAP
argument on the precompile axis, and the method to use for any future mirrored constant.
