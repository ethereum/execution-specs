# Real-world execution-semantics regression corpus — plan

Goal: for every code idiom in deployed contracts whose behaviour depends on a changeable
execution rule, produce an EEST state test that asserts the invariant the idiom relies
on. Outcome: a spec change that breaks a real on-chain idiom fails a test.

Definitions, scope and test-design rules: `SCHEMA.md`. That file is binding.

## Why this is tractable

Completeness is defined over the **rule space** (finite: the set of execution rules a
fork can change), not the **contract space** (7.9M addresses, unbounded). For each rule
axis we ask which deployed idioms depend on it and report coverage per axis. An axis with
no deployed dependents is a valid result.

## Feasibility, established before planning

```text
EEST filler       ./.venv/bin/fill tests/amsterdam/... --until Amsterdam   -> 1,340 tests / 20 s  CHECKED
Test artefact     fixtures, executable against any client, not just EELS                          CHECKED
Corpus            7,911,914 mainnet addresses; 6.58M sources; 5.91M compilations w/ layouts       CHECKED
Query cost        row counts ~1 s; 219-address join over 128 GiB ~11 s; full JSON scan ~73 s      CHECKED
```

## Phases

| # | Phase | Parallel | Gate to exit |
|---|---|---|---|
| 0 | Foundations: schema, rule axes, test template | no | **DONE** — `SCHEMA.md`, `docs/RULE-AXES.md` (60 axes, 12/12 claims verified), `docs/COVERAGE-GAP.md`, and a mutation-validated template at `wave1/frozen_budget/` |
| 1 | Discovery: 5 independent lenses over the corpus | **yes, 5 agents** | **DONE** — 217 records, 5/5 REPORTs, every record with a runnable detector, an exemplar address and a non-null measured FP rate |
| 2 | Merge: dedupe, assign `PAT-NNNN`, rank | no | **DONE** — 217 `PAT-NNNN` in `registry/merged.jsonl`; the dedupe step is a *verified* no-op (zero duplicates, see `docs/MERGE-REPORT.md`), ranked within commensurable bands |
| 3 | Formalise: exact invariant + prevalence per pattern | **yes, by family** | **DONE** for every built class — each `tests/<archetype>/README.md` states a falsifiable invariant, its deployed witness and its measurement commands |
| 4 | Generate EEST tests | **yes, by family** | **DONE for 24 of 26 classes** — 2,683 tests, 0 failures, `--until Amsterdam`; #19 and #26 deliberately not built, with reasons |
| 5 | **Mutation validation** | **yes, by family** | **DONE** — 24x83 matrix, 1,992 cells: 24/24 baselines green, 81/83 mutations detected, 43 with a single detector, 0 untrustworthy cells, no archetype detecting nothing. The 2 survivors are explained arithmetically |
| 6 | Package: docs, index, mutation matrix | no | **DONE** — `README.md` is the entry point; 5 committed tools; `python3 tools/verify_corpus.py` reproduces the gate from a clean checkout |

Phase 5 is the quality gate that makes this real. A test that passes under every
mutation protects nothing; it is rejected and rewritten. The harness is
`tools/mutate.py`, generalised from the prototype that patched
`credit_state_gas_refund` to separate refill-caused from repricing-caused divergence.

**One refinement the matrix forced, worth stating in the plan itself:** a mutation that
survives *for a stated arithmetic reason* is a result, while one that survives unexplained
is a coverage gap. The gate is not "nothing survives" but "every survival is accounted
for". On its first run the matrix found `m2-no-inframe-refill` detected by nothing, which
was a real hole in an otherwise-passing archetype; it closed only after adding a test of a
different *shape*, not by loosening the existing one.

## Phase 1 lenses (independent by construction, so they cross-check each other)

| Lens | Surface | Finds what the others cannot |
|---|---|---|
| L1 source-text | 6.58M source files | named idioms, comments stating intent, fixed constants |
| L2 bytecode/CFG | 38 GiB runtime code | unverified contracts, Vyper/Yul, compiler-generated slots |
| L3 ABI + signatures | 5.91M ABIs, 10.6M signatures | callback/hook conventions implying gas contracts |
| L4 rule axes + fork history | EIP/spec history | the taxonomy itself; rules nobody has a detector for yet |
| L5 dynamic | XATU traces, structlog_agg | which idioms actually execute, and in which frames |

L4 also owns `docs/RULE-AXES.md`, the axis list every other lens reports coverage against.

## Non-negotiables

1. Every claim labelled `CHECKED` or `INFERRED`; prevalence never asserted unmeasured.
2. Every pattern has a runnable detector; otherwise it cannot be re-found or defended.
3. Tests assert committed effects, never raw gas numbers, unless the number is the
   invariant.
4. Every test survives mutation validation or is rewritten.
5. Prior art in `8037-coordination/{findings,results}` is read and cited, not re-derived.
6. No shortcuts: a rare pattern is in scope; "too rare to matter" is not a reason to drop
   one, only to rank it lower.
