# Execution-semantics regression corpus

For every code idiom in deployed Ethereum contracts whose behaviour depends on a
changeable execution rule, an EEST test that asserts the invariant the idiom relies on.
Outcome: **a spec change that breaks a real on-chain idiom fails a test.**

## Why this exists

Measured, not assumed (`docs/COVERAGE-GAP.md`): **no official EEST test can fail under a
gas reprice.** Every official test that touches a repriced opcode derives its budget from
the fork — `probe_code.execution_cost(fork)`, `SSTORE_TOGGLE_CODE.gas_cost(fork)`,
`child_execution * 64 // 63`, and even the test *named* "fixed-gas probe" uses
`Op.SSTORE(0,1).gas_cost(fork) - 1`. The legacy frozen-budget corpus was either retired
(109 `ported_static` files `valid_until("Prague")`) or deliberately rebased, with
`@manually-enhanced` docstrings reading *"Do not hardcode the Amsterdam number."* The gap
is a **design property** of the official suite, not an oversight — which is why it cannot
be found by looking for missing files, only by reading how the budgets are computed.

Deployed contracts do the opposite: the operand is a constant compiled into immutable code
and cannot be rebased. This corpus supplies that complement.

## State

```text
test functions      77   written, across 24 archetype directories
filled fixtures  2,683   (functions x params x applicable forks x 3 fixture formats)
failures             0   Berlin -> Amsterdam
mutations       83, across 11 contributor-owned files
registry        217 records (5 lenses) + 217 merged PAT-NNNN
classes         26 identified + 1 candidate; 24 proven, 2 deferred with reasons
```

## Verify from a clean checkout

Point the tools at your execution-spec checkout. `$EELS_ROOT` is the portable way; a few
conventional sibling layouts are auto-discovered as a convenience.

```bash
cd tests/deployed_idioms
export EELS_ROOT=/path/to/execution-spec-tests         # or rely on auto-discovery
python3 tools/check_tree.py                            # is the tree safe to measure against?
python3 tools/verify_corpus.py --only-fork Amsterdam    # THE GATE: 464 passed, 0 failed
python3 tools/verify_corpus.py --wave expansion --only-fork Amsterdam   # 147 passed
python3 tools/verify_corpus.py     # all forks, under the lock -> 2,683 passed
python3 tools/mutate.py --md       # the full mutation matrix (~2,000 fills)
python3 tools/merge_registry.py    # rebuild registry/merged.jsonl
```

**Never run a fill or a lock-holding script under `timeout`.** SIGTERM kills Python
without running `finally`, which leaves a mutation applied in the shared tree and the lock
held — and a later fill against it looks like an ordinary pass. See the hygiene section of
`docs/MUTATION-MATRIX.md`; that section exists because this went wrong repeatedly.

## Documents

| file | what it holds |
|---|---|
| `SCHEMA.md` | **binding** — record schema, test-design rules (§4), correctness gate (§7) |
| `PLAN.md` | the six phases and their exit gates |
| `HANDOFF.md` | current state, incidents, prioritised resume list — **read this first** |
| `expansion/README.md` | the **separate second wave**: unexplored rule surfaces, and the fork-scoping convention |
| `docs/ALARM-SEMANTICS.md` | **what a failing test means** — the green-on-newest-fork gate, and CANARY vs PIN |
| `docs/TEST-INDEX.md` | **every test function and the pattern it tests** — generated, do not hand-edit |
| `docs/INVARIANT-CLASSES.md` | the 26 classes + candidate #27, each with its verified EELS mechanism |
| `docs/MUTATION-MATRIX.md` | phase-5 validation, and the measurement-hygiene rules |
| `docs/COVERAGE-GAP.md` | the official-suite analysis this corpus answers |
| `docs/MERGE-REPORT.md` | phase 2: why the dedupe step is a *verified* no-op |
| `docs/RULE-AXES.md` | the 60 rule axes, built by diffing adjacent forks |

## Archetypes

One directory per invariant class; each has a README stating its invariant, deployed
witness, measurement commands, mutation result, and what a failure means.

| class | directory | tests |
|---|---|---|
| **#1** | `frozen_budget/` | 66 |
| **#2** | `subfloor_budget/` | 132 |
| **#3** | `hardcoded_cost_equality/` | 44 |
| **#4** | `retained_epilogue/` | 22 |
| **#5** | `forwarding_prediction/` | 210 |
| **#6** | `depth_forwarding/` | 308 |
| **#7** | `stipend_fallback/` | 22 |
| **#8** | `refund_cap/` | 28 |
| **#9** | `refund_not_spendable/` | 63 |
| **#10** | `gas_monotonicity/` | 44 |
| **#11** | `halt_vs_revert/` | 138 |
| **#12** | `oog_as_signal/` | 44 |
| **#13** | `block_vs_sender_accounting/` | 22 |
| **#14** | `state_gas_clamp/` | 15 |
| **#15** | `calldata_floor_refund/` | 12 |
| **#16** | `reservoir_allocation/` | 30 |
| **#17** | `intrinsic_cost/` | 44 |
| **#18** | `dynamic_cost_prediction/` | 869 |
| **#20** | `gasleft_sufficiency/` | 25 |
| **#21** | `returndata_fidelity/` | 88 |
| **#22** | `code_presence_identity/` | 31 |
| **#23** | `counterfactual_address/` | 179 |
| **#24** | `transient_storage_lifetime/` | 141 |
| **#25** | `eoa_caller_identity/` | 106 |

The `tests` column counts **filled fixtures**, not functions: 77 functions expand to 2,683
executable fixtures across parametrisations, applicable forks and the three fixture
formats. Sums to 2,683, reconciling exactly with the corpus gate. Per-function detail is
in `docs/TEST-INDEX.md`.

`tests/tools/` holds **measurement instruments, not corpus tests** — their *failures are
the measurement* (a failing param reports the real value). Keep them out of any pass/fail
gate; `verify_corpus.py` excludes them.

Deliberately not built, and each is a result rather than a gap: **#19** collapses into #1
(its budget invariant *is* #1 with the threshold as the budget; its distinct content became
#20), **#26** is already covered by 5,103 lines in `tests/cancun/eip6780_selfdestruct/`,
and **#27** (environment-field semantics) is a candidate recorded rather than force-fitted.

## Three rules that cost the most to learn

1. **Silence is not a pass.** `fill` has four summary forms and three lack the word
   "passed": `"9 failed, 6 passed in 1.2s"`, `"9 failed in 0.8s"`,
   `"30 failed, 30 deselected"` (with `-k`), `"44 passed in 2.0s"`. An unparsed summary is
   UNTRUSTWORTHY, never a pass.
2. **Measure before you pin.** Every number in this corpus was bisected with a probe
   first. Predictions were wrong repeatedly — an off-by-2 because `GAS` executes before
   the subtraction, a marker slot that silently created a second fresh slot, and an
   assumption that EIP-2780 merely lowered the intrinsic cost when it actually
   *decomposed* it.
3. **A mutation that survives for a stated arithmetic reason is a result; one that
   survives unexplained is a coverage gap.** Keep the distinction explicit — the matrix is
   only worth reading if "survives" has been earned.

## What is deliberately not published here

The **discovery output is omitted**: the per-pattern registry and the five lenses that
produced it. Those carry prevalence counts and roughly 910 deployed witness addresses —
i.e. which specific applications exhibit each pattern. That is findings data, it belongs in
the disclosure process rather than in a test corpus, and none of it is needed to run or
review the tests.

What remains is the part that is useful to a client: the invariant, the mechanism, the gas
arithmetic, and the tests. Where a doc previously named an application it now names the
*role* instead ("a deployed cross-chain router"), and witness addresses read
`<address withheld>`. Prevalence figures are kept in aggregate, because "this shape occurs
at N addresses" is a property of the pattern, not a claim about anyone.
