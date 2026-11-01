# Pattern-corpus project — state log and resume instructions

Written at a hard stop on **2026-10-29**. Everything below is on disk; nothing
load-bearing lives only in a conversation. Labels follow SCHEMA.md: **CHECKED** = ran it
or read it, **INFERRED** = reasoned.

Goal (unchanged): for every deployed code idiom whose behaviour depends on a changeable
execution rule, produce an EEST test asserting the invariant the idiom relies on, so a
spec change that breaks a real on-chain idiom fails a test. `PLAN.md` has the phases;
`SCHEMA.md` is binding.

---

## 1. Phase status

| # | Phase | State |
|---|---|---|
| 0 | Foundations | **DONE** — schema, 60 rule axes, coverage-gap analysis, proven test template |
| 1 | Discovery (5 lenses) | **DONE** — all five gate-passing: **217 records**, 5/5 REPORTs |
| 2 | Merge / dedupe / `PAT-NNNN` | **DONE** — 217 `PAT-NNNN`, zero duplicates (a *verified* no-op), ranked in bands. `docs/MERGE-REPORT.md` |
| 3 | Formalise invariants | **DONE** for all built classes — each archetype README states its invariant |
| 4 | Generate EEST tests | **DONE for 24 of 26 classes** — `2,683 tests, 0 failures` |
| 5 | Mutation validation | **DONE for all 24** — 83 mutations |
| 6 | Package | not started — the remaining work |

```text
corpus          2,683 tests passing, 0 failing   (python3 tools/verify_corpus.py)
archetypes      24 directories, 24 READMEs
mutations       83, in tools/mutations/*.json (one file per contributor)
registry        217 records + 217 merged PAT-NNNN entries
EELS tree       clean, verified against git HEAD
```

**Invariant classes: 26 plus 1 candidate; 24 have proven mutation-validated archetypes**
(`#1–#18`, `#20–#25`). **Nothing is silently unaddressed** — every class is built, covered
elsewhere, or explicitly deferred with a reason:
- **#19** collapses into #1 (its budget invariant *is* #1 with the threshold as the budget;
  its distinct content became #20).
- **#26** is already covered by 5,103 lines in `tests/cancun/eip6780_selfdestruct/`.
- **#27** (environment-field semantics — `BALANCE`/`CHAINID`/`BLOCKHASH`/`BLOBHASH`/
  `PREVRANDAO`/`basefee` in a branch) is a **candidate**, surfaced by the phase-2 merge and
  recorded rather than force-fitted into #18.

Read `docs/TEST-INDEX.md` for a one-line-per-test map of what asserts what,
`docs/INVARIANT-CLASSES.md` for the classes, `docs/MUTATION-MATRIX.md` for the
validation *and the hygiene rules*, `docs/MERGE-REPORT.md` for phase 2,
`docs/COVERAGE-GAP.md` for why the corpus exists, and each `tests/<archetype>/README.md`
for one class.

### Archetype coverage of the ranked patterns

From `docs/MERGE-REPORT.md`, over the 136 patterns whose lens counted mainnet addresses:

```text
built archetype                 104 patterns     95.9% of the band's address-weight
covered by the official suite     2               1.3%
in flight at the time             17               2.6%
unmapped                         13               0.2%
top 25 by addresses: 21 built, 2 official suite, 2 then-in-flight — all accounted for
```

Addresses are double-counted across patterns, because one contract exhibits many idioms.
**That percentage is a coverage indicator, not a population fraction** — do not report it as
"95.9% of mainnet".

## 1a. Incidents and hygiene — read before running anything

**The pinned EELS tree was corrupted once.** Two leftover mutations were found in it
(`osaka/vm/gas.py` with `max_message_call_gas` 64→256, and `osaka/vm/instructions/storage.py`
with an in-frame refund credited to `gas_left`), from runs that died mid-mutation. It was
restored with `git checkout --` and is clean now. All measurements taken in that window are
suspect; every affected party re-took theirs, and the main session re-verified its three
Osaka-dependent results byte-identically on the clean tree.

**Never `fill` while a `mutate.py` run holds the lock.** Discovered independently three
times, each after a measurement that looked clean: a corpus run that reported 6 phantom
failures, an agent that got 9 spurious failures on exactly its tight params, and another
that measured +2,900 gas on a shape that is 27,212 pristine and nearly pinned it. Use
`tools/verify_corpus.py` or `tools/locked_fill.py`, or wrap with
`flock tools/.mutate.lock -c '<fill …>'`. Both guards are needed: the lock misses a tree
left dirty by a killed run, and the git check misses a run legitimately mid-mutation.

**`fill` has four summary forms and three lack the word "passed"** —
`"9 failed, 6 passed in 1.2s"`, `"9 failed in 0.8s"`, `"30 failed, 30 deselected"` (with
`-k`), `"44 passed in 2.0s"`. A form that is not parsed must never read as a pass. Silence
is not a pass.

**`Transaction(gas_limit=X, state_gas_reservoir=R>0)` silently yields a ZERO reservoir.**
EIP-8037 defines the reservoir as `tx.gas` above `TX_MAX_GAS_LIMIT` (16,777,216), and the
field only steers the *implicit* limit (`transaction_types.py:611`). Omit `gas_limit`.

**Do not gate detectors on a confirm rate; gate on measured precision.** Tightening a
broken detector *lowers* its confirm rate while *raising* correctness (measured:
0.585→0.130, 0.905→0.132, 0.097→0.002). A confirm-rate gate keeps the broken detectors and
rejects the repaired ones. See SCHEMA §7.3.

## 2. The keystone result (this justifies the whole project)

`docs/COVERAGE-GAP.md`, 299 lines. **CHECKED**, 12 of 12 sampled claims independently
re-verified by the main session against the EELS tree.

> **No official test can fail under a gas reprice, by construction.** Every official test
> touching a repriced opcode derives its budget from the fork —
> `probe_code.execution_cost(fork)`, `SSTORE_TOGGLE_CODE.gas_cost(fork)`,
> `child_execution * 64 // 63`, and even the test *named* "fixed-gas probe" uses
> `Op.SSTORE(0,1).gas_cost(fork) - 1`. The legacy frozen-budget corpus was either retired
> (109 `ported_static` files `valid_until("Prague")`) or deliberately rebased, with
> `@manually-enhanced` docstrings reading *"Do not hardcode the Amsterdam number."* The
> only frozen operands still active (`stPreCompiledContracts{,2}/`, `gas=0xBB8`) target
> operations that were never repriced, so they are structurally incapable of firing.

That the design is deliberate rather than an oversight is **INFERRED** (docstrings read,
referenced PRs not read).

Verified samples: no `istanbul/eip1884*` exists; `grep -rl 1884 tests/` → 19 files, all
`stRandom`/`stWalletTest`; `generators.py:524` raises
`ValueError("Gas tests before Berlin are not supported due to CALL gas changes")`;
`CODE_DEPOSIT_PER_BYTE=200` at `forks/forks.py:119` with no per-fork override; exactly
**109** `valid_until("Prague")` files in `ported_static/`.

---

## 3. Measured results (all CHECKED, all reproducible)

### 3.1 Minimum frozen budget in which a callee can create one storage slot

Bisected against the filler. Bracketed, not point-estimated, because the figure includes
the callee's own code (here `PUSH1 1, PUSH1 0, SSTORE, STOP`).

```text
Berlin / London / Cancun / Prague / Osaka    (22,100 , 22,200]   stable across 5 forks
Amsterdam                                    (110,020 , 110,040]  ~4.97x increase
```

**Independently cross-validated.** L3 derived the bare fresh-slot cost from the EELS
constants as 22,100 → 110,020 (`COST_PER_STATE_BYTE=1530` x
`STATE_BYTES_PER_STORAGE_SET=64` = 97,920 state gas; delta +87,920). My callee adds 6 gas
of pushes: 110,020 + 6 = 110,026, inside the measured bracket. A derivation from the
constants and a bisection against the execution engine agreeing to single-digit gas.

Consequence: **any deployed frozen budget in `[22,200 , 110,020]` that must create a
storage slot moves from success to out-of-gas at Amsterdam.**

### 3.2 How much headroom the tightest live contract has

a deployed staking-pod module: `_SHARE_POD_GAS_LIMIT = 140_000` is a Solidity `constant` and
`DelegatedShare.podCallGasLimit` is `immutable`, so neither can change without
redeployment. Confirmed live by `eth_call` at block ~26,245,933.

```text
COST_PER_STATE_BYTE = 1,998  (+30.59%)   survives
COST_PER_STATE_BYTE = 1,999  (+30.65%)   FAILS
```

**A 30.7% increase in `COST_PER_STATE_BYTE` breaks a live, immutable a deployed DEX aggregator contract.**
This also cross-checks §3.1: from the floor bracket, non-state overhead is
`(12,100 , 12,120]`, so the break must satisfy `64*CPSB > 140,000 - overhead`, giving
`CPSB > 1998.1..1998.4` — breaking at 1,999 exactly as measured.

### 3.3 Deployed budgets split into two groups by the floor (L3, CHECKED)

Measured per-frame headroom (`action_gas - result_gas_used`) over a 250k-block window;
the percentage is the share of live frames that cannot absorb one fresh slot.

```text
ERC-7579 postCheck               exactly 3,229 gas (96.8% of frames)   97.5%   BELOW floor
EIP-4337 validatePaymasterUserOp exactly 50,000   (610k frames)        99.4%   BELOW
ERC-165 supportsInterface        exactly 30,000   (p50 and p90)        83.9%   BELOW
a deployed interchain protocol execute                   --                                    88.2%   BELOW
a deployed interchain messaging protocol handle                 --                                    71.1%   mixed
EIP-4337 validateUserOp          --  (253,876 callees)                 64.9%   mixed
a deployed messaging protocol lzReceive              --                                    50.7%   mixed
a deployed staking-pod module pod call          exactly 140,000 (immutable)            0%     ABOVE
a deployed randomness coordinator callback           200,000 (consumer constant)            0%     ABOVE
```

**These two groups need different tests.** Above the floor, the invariant is *survival*.
Below it, the callee cannot create a slot at all under Amsterdam, so the invariant is
"this convention never needs to write new state" and the test must assert that boundary.
Writing a survival test for `postCheck` at 3,229 gas would assert something false.

Two facts that make this live rather than theoretical: **`ccipReceive` already OOGs at
2.664%** (69/2,590 frames); and **`supportsInterface` never OOGs but reverts on 64.36%**
of calls, so callers already read failure as "unsupported" — a reprice past 30,000
silently disables every gated hook with nothing surfacing an error. Quietest failure
shape in the corpus.

### 3.4 A deployed contract that documents this exact hazard

a deployed cross-chain router, in its own source, beside the yul `g - g/64 > gasLimit` check:

```solidity
uint16 internal constant GAS_FOR_CALL_EXACT_CHECK = 5_000;
// so that we can redeploy to adjust it should a hardfork change
// the gas costs of relevant opcodes in callWithExactGas
```

### 3.5 Corrections to earlier claims of my own

- **The refund-parity fingerprint is not a proof.** I had treated `gas_refund/100` being
  odd as exact evidence of an odd number of fresh set-then-clears (because `48a+28b` is
  always even). L5 measured it against EIP-7702: **20,291 of 199,108 odd-refund
  transactions (10.19%) are type-4 false positives.** It is a ~90%-precision filter.
  Recorded in `SCHEMA.md` §7.8.
- **Do not generalise the survival archetype to budgets below the floor** (see §3.3).

---

## 3.6 Invariant classes and archetypes

`docs/INVARIANT-CLASSES.md` enumerates **26 invariant classes** a repricing or semantic
change can break, each with the verified EELS mechanism, whether a mainnet fork has already
broken it, the witnessed population from our lenses, and the archetype it requires.

The central structural point: the archetypes have **incompatible shapes**, so phase 4 is
not one generator but ~20. A frozen-budget test cannot express a monotonicity invariant;
neither can express a forwarding-prediction invariant; and none of them can express a
*semantic* invariant like "code presence identifies a contract".

Two corrections the catalogue absorbed as it grew, both worth keeping in mind:

1. **It was gas-shaped, and that was a blind spot.** Classes #1–#20 all ask "what happens
   when a price moves". L2's sweep surfaced 24 high-prevalence records that map to none of
   them — a coherent *semantic* family (classes #21–#26) whose invariants are about meaning,
   not cost. **A fork can change semantics without changing any price**, and EIP-7702 is the
   proof: it broke `isContract` for 2,417,615 addresses while repricing nothing.
2. **It assumed costs rise.** Five of the fifteen gas constants that changed across the
   fifteen mainnet forks moved **down** (`TX_BASE` 21,000→12,000, `TX_DATA_PER_NON_ZERO`
   68→16, and four EIP-1108 precompiles — `PRECOMPILE_ECMUL` 40,000→6,000). A reduction
   breaks a *different* population: frozen-budget survival is blind to it, a two-sided probe
   inverts, and class #17 over-pays instead of reverting. Confirmed empirically — the
   `cls12-cold-read-700` mutation is survived by **all six** budget-sufficiency archetypes
   and detected only by exact-value or two-sided-bracket ones.

**20 of 26 classes built and mutation-validated.** One line each, with the fill count:

```text
#1  frozen-budget survival          wave1/frozen_budget/              66
#2  sub-floor "never writes"        tests/subfloor_budget/           132
#3  hardcoded cost-equality         tests/hardcoded_cost_equality/    44
#4  retained-gas epilogue (63/64)   wave1/retained_epilogue/          22
#5  forwarding-prediction           tests/forwarding_prediction/     210
#6  compounded depth forwarding     tests/depth_forwarding/          308
#7  stipend-funded fallback         tests/stipend_fallback/           22
#8  refund-cap dependence           tests/refund_cap/                 28
#9  refunds don't fund execution    tests/refund_not_spendable/       63
#10 gas monotonicity (M2 + M4)      wave1/gas_monotonicity/           44
#11 halt-versus-revert gas return   tests/halt_vs_revert/            138
#12 two-sided OOG-as-signal         tests/oog_as_signal/              44
#13 block-vs-sender accounting      tests/block_vs_sender_accounting/ 22
#14 net state gas is clamped        tests/state_gas_clamp/            15
#15 calldata-floor binding          tests/calldata_floor_refund/      12
#16 reservoir not subject to 63/64  tests/reservoir_allocation/       30
#17 hardcoded intrinsic tx cost     tests/intrinsic_cost/             44
#18 dynamic-cost prediction         tests/dynamic_cost_prediction/   869
#20 gasleft() sufficiency           tests/gasleft_sufficiency/        25
#21 return-data fidelity            tests/returndata_fidelity/        88
#22 code-presence identity          tests/code_presence_identity/     31
#23 counterfactual address          tests/counterfactual_address/    179
#24 transient lifetime + immunity   tests/transient_storage_lifetime/141
#25 EOA caller identity             tests/eoa_caller_identity/       106
```

All four formerly-unassigned classes are now built. The only open taxonomy item is
candidate **#27**, environment-field semantics.

## 4. The test template (phase 0 deliverable, PROVEN)

`wave1/frozen_budget/` — `test_frozen_budget_survival.py` + a 195-line `README.md` that
is the authoritative spec for this family. `tests/tools/test_floor_probe.py` is the
measurement instrument (its *failures are the measurement*; keep it out of any pass/fail
gate).

```text
fill --until Amsterdam, 3 params x 3 fixture formats          66 passed        CHECKED
mutation COST_PER_STATE_BYTE 1530->3200 (set=204,800)         200k FAILS,      CHECKED
                                                              250k survives
mutation 1530->4000 (set=256,000)                             both FAIL        CHECKED
mutation 1530->1999                                           140k FAILS       CHECKED
failure mode   KeyValueMismatchError "work_committed: want 0x1, got 0x0"       CHECKED
pinned reference implementation restored byte-identical every run (md5sum -c)  CHECKED
```

Graded sensitivity is a feature: *which* params fail measures how large the reprice was,
so the family is a cliff-locator rather than a boolean.

**EELS sanctions this method.** `src/ethereum/forks/frontier/vm/gas.py:28`, verbatim:

```python
# These values may be patched at runtime by a future gas repricing utility
```

So phase 5 should patch `GasCosts` attributes **in-process** rather than rewriting source
files, which removes the restore-correctness burden entirely. This is the single highest-
value change to make before generalising the harness.

### Rules this template establishes (full text in its README)

1. The budget is a **literal**, never a fork-derived expression — the moment it becomes
   `cost(fork)` it stops being a canary. This is the one rule separating this corpus from
   the official suite.
2. The literal comes from **deployed code**, with the contract named.
3. Assert committed effects on **both sides** of the call, never `gasUsed`.
4. **Label the storage** so a mutation failure is self-documenting.
5. Pin `state_gas_reservoir=0` — explicit 0 is cross-fork safe (only a *positive*
   reservoir errors pre-Amsterdam, `transaction_types.py:353`), and it is the realistic
   hostile case: a legacy caller has no reservoir to absorb a state charge.
6. **A failure is an alarm, not staleness.** Never repair one by raising the budget; that
   is exactly how the legacy corpus lost its canaries.

---

## 5. Methodology warning that cost real time

**`fill` prints no `FAILED` lines both when every test passes and when the run dies
before executing** (observed `exit=4`, from `--output` directory and `.pytest_cache`
contention with concurrently running agents). Greping only for `FAILED` reports "none
failing" for a run that never ran. **Three of my intermediate readings were wrong this
way and looked clean.**

Any mutation harness here must, per run: assert a summary line was parsed, check the exit
code, use a unique `--output` directory, pass `-p no:cacheprovider`, and retry before
recording a result. The working driver is `sweep2.py` (pattern preserved in the
`wave1/frozen_budget/README.md` methodology section); the two earlier drivers lacked
these checks and produced confidently wrong numbers.

---

## 6. Lens-by-lens state, including known defects

### L3 ABI + signatures — DELIVERED, 2 gates open
`registry/L3-abi.jsonl` (20 records, 65 exemplar addresses, 0 missing fields, all
detectors resolve), `lenses/L3/REPORT.md` (523 lines), 11 scripts, `rerun.sh` reproduces
every number.

Best execution of **§7.6 declared-vs-invoked** in the project: ranked all **4,929,932**
distinct signatures (not a guess list), and the two rankings disagree sharply —
`validateUserOp` has 331 verified ABIs vs **253,879** addresses actually called (767x),
and `univ3-swap-callback` is 11th by declaration but **1st by volume** (10.8M, 7x the
runner-up). 9 conventions have measured **zero** calls; 2 have zero mainnet implementers.

Open: **§7.2 two-sided calibration absent**; **§7.3 FP rate absent** (the reported 0.14%
is a false-*negative* bound, a different quantity). Three records are prior-art-free at
high volume and most need FP rates: ERC-165 probe, V4 hooks/`unlockCallback`, ERC-7579
`postCheck`. One claim to soften: "cannot fit 2300 gas under *any* schedule" for 769,609
proxy addresses — state the schedules actually checked.

At kill time it was quantifying whether signatures leak from interfaces in the same
compilation unit (a real FP source).

### L4 rule axes + fork history — DELIVERED
`registry/L4-rule-axes.jsonl` (60 records), `lenses/L4/REPORT.md` (338 lines),
`docs/RULE-AXES.md` (729 lines), `docs/COVERAGE-GAP.md`, 6 scripts.
60 axes in 7 families, built from adjacent-fork diffs across all 15 semantically distinct
mainnet forks. `l4_axis_registry.py --verify` runs and reports **0 mismatches over 60
axes** (CHECKED by main session).

Honest and unpadded: **49 of 60 coverage verdicts are INFERRED** (directory/grep
evidence; assertions not read), **57 of 60 axes have no exemplar**, and only **2 of 21
probes have a measured FP rate** (`retention-6364` and `gas-delta`, both 0/18
hand-judged). Two clean negatives reported as records: `block-level-access-lists`,
`block-size-limit`.

Caveat it raised that phase 3 must honour: the 0/18 samples are **not independent** — one
dividend template is 6 of 18 `gas-delta` hits and a burn loop 3 more, so rank by distinct
template count. And **severity splits by compiler**: SafeMath/solc>=0.8 reverts
(liveness) while a plain `-` under solc<0.8 wraps and silently overpays relayers
(correctness, worse). Split that record.

**Contributed the enforcement mechanism now standard project-wide:** its builder drops any
probe whose `measured.json` `fp_measured` is null, so an unvalidated count cannot reach a
record even by accident. Codified into `SCHEMA.md` §7.3.

Three data losses, documented in its REPORT §6: the opcode census OOM-killed at
650k/994k codes, a 13-probe batch killed, and one self-inflicted (its own cleanup step
deleted a completed run's output while the process held it open). Consequence: **no
opcode-prevalence figure is reported anywhere** — earlier `--limit` sampling was biased
toward recent contracts. Scripts now flush per probe, checkpoint, and sample uniformly.

### L5 dynamic execution — DELIVERED, gates CLOSED (verified post-kill)
`registry/L5-dynamic.jsonl` (19 records, **19/19 parseable after the kill**, 0 missing
fields, all detectors exist, every record has an exemplar), `lenses/L5/REPORT.md` (862
lines), **37** SQL detectors. Window: mainnet blocks **26,250,000–26,259,999** (10,000
blocks; 2,571,532 txs), stated on every record. Correctly includes an `instances: 0`
record for axes with no mainnet exposure (§7.9).

It closed both outstanding gates in its final minutes, so **do not re-request them**:
- **§7.2 two-sided calibration** — REPORT §4.4, negatives a canonical batch-call helper, a canonical permit helper, a major stablecoin,
  a major stablecoin, a major stablecoin, a canonical wrapped-ether contract (`sql/29-calibration-fixed-gas.sql`, `sql/30`).
- **§7.3 measured FP rate** — now per record, via `sql/32`–`sql/36`.

**The measured FP rates change the ranking substantially, which is exactly why the gate
exists. Phase 3 must rank on the corrected figures, not the raw counts:**

```text
pattern                            raw count     MEASURED FP rate    corrected
tolerated child failure              116,823     94.12%  (sql/35)    ~6,870
2,300-gas stipend recipient          265,056     63.50%  (sql/32)    ~96,865
  (168,191 of them target a CODELESS address, where the stipend is irrelevant)
recurring round fixed-gas budget     132,214     62.21% naive;       ~301,895 true
  (100% at PAIR level on known-clean callers -- see sql/29, sql/30)   round-gas calls
                                                                      from 11,504 callers
per-item sibling fan-out             435,998     23.11% precompile
                                                 loops + 3.26%       ~325,000
proxy trampoline                   6,921,859      3.45%  (sql/33)    ~6,683,000
ERC-165 supportsInterface probe       27,561      0.10%  (sql/32)    ~27,533
self-STATICCALL at 900 gas             5,584      0       (sql/32)
SELFDESTRUCT balance sweep            18,360      0.098% cross-pipeline bound
metamorphic / ephemeral / NEW-ACCOUNT / BLOBHASH / depth:  0 by construction,
  each with its trap named explicitly in `false_positive_notes`
```

Two of its own notes worth preserving: the round-literal classifier **already failed once**
(the first version used only `% 1000 = 0`), and it delivered the EIP-7702 correction in
§3.5 above (`PER_EMPTY_ACCOUNT_COST - PER_AUTH_BASE_COST = 25,000 - 12,500 = 12,500` per
authorization is what contaminates the refund-parity fingerprint).

Minor items still open: the `exact-refund fingerprint` record has `instances: 178,985`
with `distinct_runtimes: 0` — if that is because summary rows carry no code hash, say so,
since a bare 0 reads as "measured zero". And its single record-level `confidence` (19/19
CHECKED) is coarser than §3 wants: the prevalence numbers are measured, but the
`why_rule_dependent` harm narrative is reasoned. At kill time it was mid-way through
correcting REPORT §3 claims that its own FP measurements had retracted — **so treat
REPORT §3 as possibly stale where it disagrees with the per-record
`false_positive_notes`, which are newer.**

### L1 source-text — STOPPED, no records, but valuable partial state
`lenses/L1/` 1.2 GB. On disk: `out/calibration.json`, `out/tests/deployed_idioms/` (**57** pattern
JSONs), `out/scan/` (**84** shards), `out/detect-all.log`, `out/srcmap.parquet`,
`out/srcagg.parquet`, 7 scripts. Scan covered 128 rules over 106,530,401,470 chars in
1,882 s.

**It is the only lens that actually ran §7.2 two-sided calibration, and the result is a
real defect, not a formality:**

```text
positives: 28 rows   HIT=15  MISS=13   <-- 46% recall miss on KNOWN positives
negatives:  8 rows   HIT=0   MISS=8    <-- clean on negatives
P01 (fixed-gas budget): 0 HIT / 3 MISS  <-- ALL MISS
   missed: a deployed DEX aggregator DelegatedShare _SHARE_POD_GAS_LIMIT=140k
           a deployed restaking protocol BurnerRouter BURNER_GAS_LIMIT=150k
           a deployed bridge gateway
11 patterns in total are 0-HIT: P01 P05 P07 P09 P12 P13 P16 P20 P35 P39 (+P33 1/2)
```

P01 matters most: it is the pattern my proven template depends on, and L1 cannot find it.
Confirmation rates from `detect-all.log` also show several detectors are mostly noise —
P30 0.046, P26 0.046, P23 0.051, P27 0.104, P11 0.117, P20 0.313, P17 0.415 (confirmation
= fraction of sampled hits that are real, so 0.046 is ~95% false positives).

**Verdict: L1 must not emit records until P01 and the other 0-HIT patterns are fixed and
the low-confirmation detectors are repaired or dropped.** Shipping now would fill the
registry with mostly-false records. At kill time it was mid-diamultisig of the three P01
misses and reported "diagnostics are conclusive for most".

### L2 bytecode / CFG — STOPPED, no records, substantial partial state
`lenses/L2/` 3.9 GB. On disk: `REPORT_prose.md` (**350 lines, real measured content**),
12 scripts including `mkregistry.py` and `mkreport.py`, `work/` with a 64-shard scan.

Population established (CHECKED), with the counting unit stated as **distinct mainnet
runtime code hash**: 8,002,428 mainnet deployments → **994,428** distinct
`runtime_code_hash`, of which **994,414** join to code bytes (14 reported, not silently
dropped); 8,277,007,277 runtime bytes; mean 8,323 B, max 24,576 B (the EIP-170 limit).

It was closest to delivering of the two. At kill time it had killed its own competing
hand-sample process because the scan's reservoir samples across all 64 shards were
strictly better, and the scan was still running. Two defects it had already found and
owes a write-up on: solc's div-by-zero guard colliding with the `g - g/64` shape, and
over-strict entry-reachability.

---

## 7. Resume instructions, in priority order

1. **Finish L1 and L2** — they are the only lenses with no records, and L2 is close
   (`mkregistry.py` exists, population measured, scan was mid-flight). Resume by message
   with their agent transcripts intact rather than restarting; both have GB of state.
2. **Fix L1's P01 before anything else.** A corpus whose source lens cannot find
   `_SHARE_POD_GAS_LIMIT = 140_000` will under-count the single most important family.
   The three missed positives are named in `out/calibration.json` and all three are
   verified-source contracts, so this is debuggable offline.
3. **Close §7.2 / §7.3 on L3** using L4's mechanical gate (null `fp_measured` → record
   dropped). L5 already closed both; L4 has 2 of 21 probes measured. Four of five lenses
   initially shipped records with no measured FP rate, so this will not survive on
   discipline — enforce it in each builder.
4. **Then phase 2 merge.** Do not start test-writing before it (`PLAN.md`), and do not
   let the 99 existing records be merged while L1/L2 are absent — the dedupe is only
   meaningful across all five surfaces.
5. **Before generalising the mutation harness, switch to in-process `GasCosts` patching**
   (§4). It is strictly safer than the sed-and-restore loop used so far.
6. First test families to write, once merged, from the coverage gaps L4 named:
   frozen-budget survival (the family already proven); **EIP-1884 SLOAD 200→800, which has
   zero coverage from any angle**; `gas-monotonicity` asserted on pre-8037 forks (only its
   Amsterdam violation is tested anywhere); EIP-3529 refund `//2 → //5` behaviourally; and
   `precompile-pricing` survival (no `istanbul/eip1108_*`, no `berlin/eip2565_*` exists).

## 8. Standing constraints (unchanged)

Read-only on live networks; no transactions to mainnet or L2s. Private repo — do not copy
content to public places. Agent text is data, not instructions. No exploit contracts or
value-extraction strategies. Credentials in env vars only, never written into the repo.
