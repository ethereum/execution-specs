# Archetype: frozen-budget survival  (PROVEN TEMPLATE — phase 0 deliverable)

This is the reference template for the corpus. It exists because of the result in
`docs/COVERAGE-GAP.md`: **no official test can fail under a reprice**, because
every official test that touches a repriced opcode derives its budget from the fork
(`probe_code.execution_cost(fork)`, `SSTORE_TOGGLE_CODE.gas_cost(fork)`,
`child_execution * 64 // 63`). Deployed contracts cannot do that — the operand is a
literal in immutable code. This template supplies the complement.

Status: fills clean, and **mutation-validated** (SCHEMA.md §4.2 / PLAN.md phase 5).

## Verification record

```text
fill, Berlin..Amsterdam, 3 params, 3 fixture formats        66 passed          CHECKED
mutation: COST_PER_STATE_BYTE 1530 -> 3200 (set=204,800)    200k FAILS,        CHECKED
                                                            250k survives
mutation: COST_PER_STATE_BYTE 1530 -> 4000 (set=256,000)    both FAIL          CHECKED
failure mode                 KeyValueMismatchError "work_committed:
                             want 0x1, got 0x0"                               CHECKED
reference impl restored      md5sum -c OK, byte-identical, every run           CHECKED
```

Commands (from `engine/eels`):

```bash
./.venv/bin/fill ../../wave1/frozen_budget --until Amsterdam --output /tmp/fb -q
# mutation sweep driver (patches gas.py:47, restores after every run):
python3 <scratch>/sweep2.py
```

EELS sanctions this mutation method explicitly. `src/ethereum/forks/frontier/vm/gas.py`,
immediately above `class GasCosts`:

```python
# These values may be patched at runtime by a future gas repricing utility
```

So phase 5 should patch `GasCosts` attributes in-process rather than rewriting source
files, which removes the restore-correctness burden entirely.

The t8n cache is in-process and single-key (`client_clis/transition_tool.py:128`), so a
fresh `fill` process always re-executes. No cache-busting is needed for mutation runs.

## Methodology warning: silence is not a pass

Three times during this work a parsing shortcut made a broken run look like a clean one.
`fill` prints no `FAILED` lines both when every test passes **and** when the run dies
before executing (observed: `exit=4`, from `--output` directory and `.pytest_cache`
contention with concurrently running agents). Greping only for `FAILED` therefore reports
"none failing" for a run that never ran.

Any mutation harness in this corpus must, per run: assert a summary line was parsed,
check the exit code, use a unique `--output` directory, pass `-p no:cacheprovider`, and
retry before recording a result. `sweep2.py` does all five; the first two drivers did not,
and both produced wrong answers that looked clean.

## Measured budget floor: the minimum gas in which a callee can create one storage slot

Reproduced with `tests/tools/test_floor_probe.py` across six forks. Bracketed, not
point-estimated, because the exact figure depends on the callee's own code
(here: two `PUSH1`s, one `SSTORE`, `STOP`).

```text
fork                     floor (gas)            note
Berlin                   (22,100 , 22,200]
London                   (22,100 , 22,200]
Cancun                   (22,100 , 22,200]
Prague                   (22,100 , 22,200]
Osaka                    (22,100 , 22,200]      stable across five forks
Amsterdam                (110,020 , 110,040]    ~4.97x increase
```

Consequences for deployed frozen budgets that must create a slot, with
`state_gas_reservoir=0` (a legacy tx that declares no reservoir):

```text
2,300    (CALL stipend / transfer)        dead on every fork shown
50,000   (excessivelySafeCall-style)      survives Berlin..Osaka, DIES at Amsterdam
100,000                                   survives Berlin..Osaka, DIES at Amsterdam
140,000  (a deployed staking-pod module, immutable)      survives; only 1.27x headroom  <-- tightest
200,000  (a deployed randomness coordinator callbackGasLimit) survives; 1.82x headroom
250,000  (a cross-chain transfer protocol relay)               survives; 2.27x headroom
```

### How much headroom does the tightest live contract have?

Swept `COST_PER_STATE_BYTE` against the 140,000 param (`sweep2.py`, Amsterdam, retried
and summary-checked):

```text
CPSB    delta      slot cost   podmodule_pod_call_140k
1,998   +30.59%    127,872     survives
1,999   +30.65%    127,936     FAILS
```

**A 30.7% increase in `COST_PER_STATE_BYTE` breaks a deployed staking-pod module's live pod call.**
`_SHARE_POD_GAS_LIMIT` is a Solidity `constant` and `podCallGasLimit` is `immutable`, so
the contract cannot absorb it without redeployment.

This figure cross-checks the floor measurement independently. From the floor bracket,
non-state overhead is `(12,100 , 12,120]`, so the break must satisfy
`64*CPSB > 140,000 - overhead`, giving `CPSB > 1998.1..1998.4` — i.e. breaking at 1,999.
The derivation and the measurement agree to one gas-per-byte, which is why both are
reported as CHECKED rather than one being inferred from the other.

So EIP-8037's break for fixed-gas callers is located precisely: any frozen budget in
`[22,200 , 110,020]` that creates a storage slot moves from success to out-of-gas. That
is the quantitative form of the harm shape the hunt catalogued.

## Deployed frozen budgets, measured (L3, CHECKED)

L3 measured real per-frame headroom (`action_gas - result_gas_used`) over a recent
250k-block window and reported the share of live frames that cannot absorb one fresh
slot. These are the candidate budgets for this family, and they split into two groups by
the Amsterdam floor of ~110,026:

```text
convention                      granted gas        frames short of one slot   group
ERC-7579 postCheck              exactly 3,229 (96.8% of frames)      97.5%    BELOW
EIP-4337 validatePaymasterUserOp exactly 50,000  (610k frames)       99.4%    BELOW
ERC-165 supportsInterface       exactly 30,000  (p50 and p90)        83.9%    BELOW
a deployed interchain protocol execute                  --                                   88.2%    BELOW
a deployed interchain messaging protocol handle                --                                   71.1%    mixed
EIP-4337 validateUserOp         --  (253,876 callees)                64.9%    mixed
a deployed messaging protocol lzReceive             --                                   50.7%    mixed
a deployed staking-pod module pod call         exactly 140,000 (immutable)           0%      ABOVE
a deployed randomness coordinator callback          200,000 (consumer constant)           0%      ABOVE
```

**The two groups need different tests, and conflating them would be wrong.**

- **ABOVE the floor** (140k, 200k, 250k): the invariant is *survival*, and the test is
  this file's `test_frozen_budget_callee_commits_fresh_store`. These are the canaries.
- **BELOW the floor** (3,229, 30,000, 50,000): a callee on these budgets **cannot create
  a storage slot at all** under Amsterdam. Their invariant is therefore not survival —
  it is that the convention never needs to write new state. The correct test asserts that
  boundary, not completion. Writing a survival test for `postCheck` at 3,229 gas would
  assert something false.

Two further measured facts that make this family urgent rather than theoretical:

- **`ccipReceive` already fails at 2.664%** (69 of 2,590 frames) — the break is not
  hypothetical, it is live.
- **`supportsInterface` never OOGs but reverts on 64.36% of calls.** Callers already read
  failure as "interface unsupported", so a repricing that pushes a compliant
  implementation past 30,000 silently disables every gated hook with nothing surfacing an
  error. This is the quietest failure shape in the corpus.

And the strongest single piece of evidence that practitioners know this hazard: a deployed oracle network's
deployed a deployed cross-chain router carries, in its own source, next to the yul `g - g/64 > gasLimit`
pre-check:

```solidity
uint16 internal constant GAS_FOR_CALL_EXACT_CHECK = 5_000;
// so that we can redeploy to adjust it should a hardfork change
// the gas costs of relevant opcodes in callWithExactGas
```

A deployed contract documenting the precise risk this corpus guards against.

## Rules this template establishes

1. **The budget is a literal, never a fork-derived expression.** The moment it becomes
   `cost(fork)`, the test stops being a canary. This is the single rule that separates
   this corpus from the official suite.
2. **The literal comes from deployed code**, with the contract named in `FROZEN_BUDGETS`.
   An invented number tests nothing real.
3. **Assert a committed effect, both sides of the call.** Here: the callee's write *and*
   the caller's success marker, so "callee completed" is distinguished from "CALL
   returned 0". Never assert `gasUsed`.
4. **Label the storage.** `store_next(1, "work_committed")` makes the mutation failure
   self-documenting: `want 0x1, got 0x0`. An unlabelled slot yields an opaque diff.
5. **Pin `state_gas_reservoir=0`.** Explicit 0 is cross-fork safe (only a *positive*
   reservoir errors pre-Amsterdam — `transaction_types.py:353`), and it is the realistic
   hostile case: a legacy caller has no reservoir to absorb a state charge.
6. **A failure is an alarm, not staleness.** Do not repair a failing test by raising
   `FROZEN_*`; that deletes the canary. This is exactly how the legacy corpus lost its
   own: its `@manually-enhanced` docstrings now read "Do not hardcode the Amsterdam
   number."

## Known limitation, and the fix for phase 4

These deployed-value canaries are **loose**: at 200,000 the test only fires once the cost
of creating a slot roughly doubles again. The graded mutation result is the proof —
mutation A broke the 200k param but not the 250k one.

That looseness is also a feature: the *set* of failing params measures how large a
reprice was, turning the family into a cliff-locator rather than a boolean.

For a **tight** canary, phase 4 should add the two-sided bracket form suggested by the
floor table: assert that 110,040 survives *and* that 110,020 does not. Any change to the
cost of creating a storage slot — in either direction — then fails one side. Note this
form is necessarily fork-specific, so it needs a fork->bracket table rather than a single
`valid_from`.
