# Pattern registry schema and discovery brief

Read this before producing anything. Every lens writes to the same schema so the
results merge without rework.

## 0. What we are building and why

A **regression corpus for the Ethereum execution specs**, derived from code that is
actually deployed. Each entry is a code idiom whose observable behaviour depends on an
execution rule a fork could change. Each idiom becomes an EEST state test that asserts
the *invariant the deployed code relies on*. A future spec change that breaks a real
on-chain idiom then fails a test instead of shipping.

This is not a vulnerability hunt. A pattern is in scope whether or not it is currently
broken. "Widely relied on and would break if rule X changed" is the bar.

## 1. What counts as a pattern

A pattern is in scope only if **both** hold:

1. **Rule-dependent.** Its observable behaviour changes if some execution rule changes
   (an opcode's gas cost, a refund rule, the 63/64 retention, warm/cold accounting,
   return-data semantics, address derivation, code-size limits, transient storage
   lifetime, account-existence semantics, ...). If no rule change alters its behaviour,
   it is out of scope.
2. **Witnessed.** At least one deployed instance exists in the corpus, with an address.
   Rarity is fine - a pattern with 3 instances is in scope. Zero instances is not.

Out of scope: style conventions, pure-logic bugs, anything whose behaviour is identical
under every conceivable rule change.

## 2. Completeness is defined over the RULE space, not the contract space

"All patterns across 7.9M contracts" is unbounded and not a stopping rule. The finite
object is the set of execution rules. So:

- enumerate the rule axes (see `docs/RULE-AXES.md`, lens L4 owns it),
- for each axis, ask "which deployed idioms depend on this axis?",
- a lens is complete for an axis when it can state the idioms found and the search it ran.

Report coverage per axis, not per contract. An axis with no deployed dependents is a
valid, reportable result.

## 3. Registry record (one JSON object per line, `registry/<lens>.jsonl`)

```json
{
  "pattern_id": "",                     // leave empty; the merge assigns PAT-NNNN
  "lens": "L2-bytecode",                // your lens id
  "name": "gas-delta meter across an external call",
  "summary": "Caller snapshots gasleft(), calls out, subtracts to bill or branch.",
  "rule_axes": ["gas-introspection", "refund-accounting", "63-64-retention"],
  "invariant": "gasleft() after the call is <= gasleft() before it, so the subtraction cannot underflow.",
  "why_rule_dependent": "Any rule that returns gas to a frame after a call inverts the inequality.",
  "detector": {
    "kind": "bytecode",                 // bytecode | source-regex | source-ast | abi | dynamic
    "spec": "GAS ... SUB whose result reaches JUMPI or SSTORE, with a CALL between the two GAS reads",
    "script": "lenses/L2/gasmeter.py",  // runnable, committed; required
    "false_positive_notes": "call(gas(),..) forwarding is NOT this pattern"
  },
  "prevalence": {"instances": 0, "distinct_runtimes": 0, "method": "how counted"},
  "exemplars": [
    {"address": "0x...", "why": "clearest instance", "source_available": true,
     "lines_or_pcs": "Foo.sol:120-140 | pc 852/1119/1173"}
  ],
  "test_sketch": {
    "archetype": "minimal",             // minimal | production-witness
    "assert_what": "the committed effect that encodes the invariant",
    "must_not_assert": "exact gas numbers, unless the gas number IS the invariant"
  },
  "confidence": "CHECKED|INFERRED",
  "notes": ""
}
```

Rules for the record:

- `invariant` must be a falsifiable statement about behaviour, not a description of the
  code. "The callee receives enough gas to complete" is an invariant. "Uses gasleft()"
  is not.
- `detector.script` must exist and run. A pattern without a runnable detector cannot be
  counted, re-found, or regression-tested.
- `prevalence.method` must say exactly what was counted (files? addresses? distinct
  runtime code hashes?) - these differ by an order of magnitude.
- Label every claim `CHECKED` (ran it, read it) or `INFERRED` (reasoned). Never assert
  prevalence you did not measure.

## 4. Test design rules (phase 4 depends on these; get them right now)

1. **Assert the invariant, not the cost.** A test asserting `gasUsed == 45038` breaks on
   every repricing and protects nothing. Assert committed effects: storage, logs,
   balances, status.
2. **The test must be able to fail.** Every test is validated by *mutation*: perturb the
   rule it claims to depend on and the test must fail. A test that passes under every
   mutation protects nothing and is rejected. Record which mutations it detects.
3. **Prefer `minimal`.** Hand-built bytecode or a small Solidity source that isolates the
   idiom: portable, fast, no prestate, survives contract redeployment.
4. **Use `production-witness` only when realism is the point** - when the idiom's
   interaction with real state is what makes it interesting. Pin the block and the slots.
5. **Multi-fork by default.** Tests fill `--until Amsterdam` and should express the
   invariant on every fork where the idiom is valid, so the corpus keeps working for the
   fork after this one.
6. One pattern may need several tests (the invariant holding, the boundary, the negative).

## 5. Corpus and tools available

```text
Sourcify v2 export   /home/devops/toni/datanalysis/eip-8037/sourcify/v2
                     7,911,914 distinct mainnet addresses; 6,582,425 source files;
                     5,913,457 compilations with ABI + storageLayout; 38 GiB of code.
                     Join: contract_deployments -> verified_contracts -> compiled_contracts
                                                -> compiled_contracts_sources -> sources
                     duckdb/pyarrow/polars installed. Counts ~1 s; targeted joins ~11 s.
EELS                 /home/devops/toni/datanalysis/eip-8037/engine/eels  pinned 16898000
                     ./.venv/bin/fill <dir> --until Amsterdam --output <dir>   (works; 1,340 tests/20 s)
XATU ClickHouse      traces, logs, storage diffs, per-frame opcode aggregates (structlog_agg)
Archive + tracer     ethpandaops teku-erigon (archive state + prestateTracer)
Existing detector    8037-coordination/tools/setcallclear-bc/  (CFG, symbolic slot keys)
Prior art            8037-coordination/{findings,results}  - 56 findings; read before
                     claiming a pattern is new, and cite overlap rather than ignoring it.
```

## 6. What a lens returns

- `registry/<lens>.jsonl` - the records
- `lenses/<lens>/` - the runnable detectors
- `lenses/<lens>/REPORT.md` - what you searched, coverage per rule axis, what you did
  **not** cover, and your prevalence numbers with their method

Do **not** write EEST tests in the discovery phase. Duplicate patterns across lenses are
expected and fine; the merge dedupes. Over-reporting a candidate is cheaper than missing
one, but every record still needs a detector and an exemplar address.

## 7. Correctness gate (binding, added after the first lens round)

The standard is "100% correct". A record or a test that does not meet all of these is not
accepted; it is reworked.

1. **Runnable detector.** No detector, no record. A pattern that cannot be re-found
   cannot be defended or regression-tested.
2. **Two-sided calibration.** Every detector is run against known positives *and* known
   negatives, and the result is stated. Ready-made positives: the 56 findings in
   `8037-coordination/findings/` (a deployed randomness coordinator callback limits, a deployed staking-pod module, OP
   messengers, a major DEX LBP try/catch, a deployed cross-chain router, a deployed sidechain WithdrawManager). Ready-made
   negatives: plain ERC-20s, a canonical batch-call helper, a canonical permit helper. Prior reference points: the bytecode
   detector flags 4/4 known positives and is clean on those negatives; `finalfilter.py`
   scored 0/6 miscalibrations.
3. **Measured false-positive rate.** Hand-validate a random sample of each detector's
   own hits by reading the source or disassembling the bytecode, and report the measured
   rate. An assumed rate is not accepted. This is the step that catches things like
   solc's division guard colliding with the `g - g/64` shape, or a regex matching
   commented-out code. A false-*negative* bound is a different quantity and does not
   substitute for this.

   **Enforce it in code, not by discipline (required).** L4's registry builder is the
   reference: it drops any probe whose `measured.json` `fp_measured` is null, so an
   unvalidated count cannot reach a record even by accident. Every lens's registry builder
   must do the same. Rationale: four of five lenses initially shipped records with no
   measured FP rate, so this gate does not survive on good intentions.

   **Do not gate on a confirm rate; gate on measured precision (L1, CHECKED).** These are
   different quantities and confusing them inverts the decision. A *confirm rate* is
   `confirmed hits / candidate hits` — how aggressively a detector filters. *Precision* is
   `true positives / confirmed hits` — whether what it kept is real. Tightening a broken
   detector **lowers** its confirm rate while **raising** its correctness, measured:
   P13 0.585→0.130, P60 0.905→0.132, P25 0.911→0.432, P23 0.097→0.002, each after hand
   reads showed the loose version was counting unbounded proxies, a deployed multisig
   `SENTINEL_OWNERS`, or `21000 * 10**6` token amounts. So a confirm-rate gate would have
   **kept the broken detectors and rejected the repaired ones**. The main session asserted
   that detectors near 0.05 confirm rate were "~95% noise" and was wrong: P30, P26, P23,
   P11 and P47 each hand-read 3/3 true positive. Only P27 was genuinely noise (`codesize()`
   in deployed source is a widely used assembly library cheap non-zero trick, not a code read) and was dropped.
   Record both numbers per detector; gate on the hand-measured one.

   When a sample's hits are **not independent**, say so — L4 found one dividend template
   accounting for 6 of 18 sampled `gas-delta` hits and a burn loop for 3 more. A 0/18 FP
   rate over 4 distinct templates is a weaker result than over 18, and ranking must use
   the distinct-template count.
4. **Reproducible claims.** Every `CHECKED` claim carries the exact command or query
   that produced it, plus the block window for anything dynamic. Never assert a count
   that was not run.
5. **Stated counting unit.** Source files vs addresses vs distinct runtime code hashes vs
   distinct ABIs differ by an order of magnitude. Say which, every time.
6. **Declared vs invoked.** For interface-level patterns, report both implementer count
   and real call volume. A convention in 50,000 ABIs that is never called ranks far
   below one called constantly.
7. **Document false-positive sources.** A detection pitfall is itself a finding about
   detection. Write it down with the discriminator used, rather than silently filtering.
8. **Validate arithmetic fingerprints before relying on them.** Example: `gas_refund/100`
   being odd proves an odd number of fresh set-then-clears *because* `48a + 28b` is
   always even — but that proof must be re-checked against every refund component the
   fork can produce (EIP-7702 authorization refunds in particular) before it is used.
   **Resolved, and the caution was justified (L5, CHECKED):** on a 7702-enabled fork the
   fingerprint is *not* exact. Measured over blocks 26,250,000–26,259,999, 20,291 of
   199,108 odd-refund transactions (**10.19%**) are type-4 false positives. Treat the
   fingerprint as a ~90%-precision filter, never as a proof, and state the rate wherever
   it is used for ranking.
9. **No padding.** An axis with no deployed dependents, a detector that could not be
   built, a search not run, a count the data cannot support: all are results. State them.
   A clean negative with a stated population is worth more than a padded list.

## 8. Alarm semantics (binding, added after the corpus went green)

1. **Every fixture a client runs on the newest supported fork must pass today.** A test
   that is red on the newest fork is rejected — re-scope it with `valid_until` so it runs
   only where its invariant holds, or re-pin it to what the fork actually does. The gate is
   `tools/verify_corpus.py --only-fork <newest>`; the signal this corpus exists to give is
   a test going from **green to red** after a future change, which is impossible if it is
   already red.
2. **An invariant that changed is written as two arms, never one failing test:** a CANARY
   scoped to the forks where it held, and a PIN asserting what the fork now does. Both
   green.
3. **Declare the role** on the last docstring line — `Role: CANARY` (a failure means
   deployed code stopped working) or `Role: PIN` (a failure means a semantic moved, which
   may be a *fix*). Unlabelled defaults to CANARY, the stricter reading. Name heuristics are
   not sufficient: one test in the corpus reads as a PIN by name and is a CANARY on review.
   See `docs/ALARM-SEMANTICS.md`.
