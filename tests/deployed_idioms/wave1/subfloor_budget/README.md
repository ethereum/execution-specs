# Archetype 2: frozen budget *below* the storage-slot floor

## The invariant

A deployed convention is reached with a gas literal far under the cost of creating one
storage slot. Its invariant is **not** survival-with-a-write — asserting that would
assert something false. It is two-sided:

1. the convention's **read-only work fits** the budget, and
2. the budget is **genuinely insufficient to create new state**, so "this hook never
   writes" is enforced by the gas schedule rather than by its implementers' manners.

A failure means either a sub-floor convention's read-only work no longer fits the budget
deployed callers forward, or a budget that provably could not create state now can.

## Deployed witnesses

All three budgets are measured values from lens L3 over a recent 250k-block mainnet
window, with the share of live frames unable to absorb one fresh slot
(`registry/L3-abi.jsonl`, `wave1/frozen_budget/README.md`; CHECKED by L3, not re-derived
here):

| convention | granted gas | share of frames | L3 record |
|---|---|---|---|
| ERC-7579 `postCheck` | exactly **3,229** (96.8% of frames) | 97.5% short | "ERC-7579 module lifecycle hooks, including a 3,229-gas postCheck", 167 instances |
| ERC-165 `supportsInterface` | exactly **30,000** (p50 and p90) | 83.9% short | "ERC-165 interface probe capped at 30,000 gas whose failure reads as 'false'", 163,050 instances |
| EIP-4337 `validatePaymasterUserOp` | exactly **50,000** (610k frames) | 99.4% short | "ERC-4337 paymaster validation and postOp on reserved sub-budgets", 173 instances |

The 30,000 figure is not one contract's choice: EIP-165 states `supportsInterface` "must
use less than 30,000 gas" and its reference caller does `staticcall(30000, ...)`.

## Measurement

Instrument: `tests/tools/test_subfloor_probe.py`. Its failures are the measurement; for
the write probe the **passing** param names the real answer.

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
# arm 1 -- does the read-only hook body fit?   (ran for all six forks)
for F in Berlin London Cancun Prague Osaka Amsterdam; do
  ./.venv/bin/fill ../../wave1/instruments --from $F --until $F \
      -k "subfloor_readonly and state_test" --output /tmp/p2b-$F -q --tb=no \
      -p no:cacheprovider
done
# arm 2 -- can the callee create one slot?
for F in Berlin London Cancun Prague Osaka Amsterdam; do for B in 3229 30000 50000; do
  ./.venv/bin/fill ../../wave1/instruments --from $F --until $F \
      -k "subfloor_write and state_test and budget_$B and expect_1" \
      --output /tmp/p2c-$F-$B -q --tb=no -p no:cacheprovider
done; done
```

Result (CHECKED, all six forks):

```text
budget    read-only hook fits?       callee can create one slot?
          Berlin..Amsterdam          Berlin..Osaka    Amsterdam
 3,229    yes                        NO               NO
30,000    yes                        yes              NO
50,000    yes                        yes              NO
```

The middle column is the finding that shaped the test file. For 30,000 and 50,000 the
"never needs to write" guarantee is **new at EIP-8037**: on Berlin through Osaka a
`supportsInterface` or `validatePaymasterUserOp` implementation given its standard budget
had 22,100 of its 30,000 available to create a slot, and an ERC-165 caller's
static-call context was the only thing preventing it. ERC-7579's 3,229 is the only one of
the three that was always sub-floor.

Arithmetic behind the two floors, read out of EELS at the pinned commit (CHECKED):

```text
Berlin..Osaka   COLD_STORAGE_ACCESS 2,100 + STORAGE_SET  20,000              =  22,100
Amsterdam       COLD_STORAGE_ACCESS 2,100 + STORAGE_WRITE 10,000
                  + STATE_BYTES_PER_STORAGE_SET 64 * COST_PER_STATE_BYTE 1,530 = 110,020
                osaka/vm/gas.py:45,48;  amsterdam/vm/gas.py:47-53,78,81
```

## Fill

```bash
./.venv/bin/fill ../../wave1/subfloor_budget --until Amsterdam \
    --output /tmp/c2 -q --tb=no -p no:cacheprovider
```

**132 passed**, exit 0 (CHECKED). Berlin through Amsterdam, four tests, 36 fixtures across
3 formats. Re-verified after restoring the shared EELS tree (see "Incident" below).

## Mutation result

`python3 tools/mutate.py -k cls2-` and `-k cls12-` (full 20-archetype matrix, CHECKED).
Baseline `pass(18)` at Amsterdam, `pass(18)` at Osaka.

| mutation | verdict | which test it kills |
|---|---|---|
| `cls12-cold-read-5000` (COLD_STORAGE_ACCESS 2100→5000) | **DETECTED(6)** | test 1 *and* test 2, both via the 3,229 param: the read-only body no longer fits |
| `cls2-cpsb-250` (COST_PER_STATE_BYTE 1530→250) | **DETECTED(6)** | test 2 — a fresh slot falls to 28,100, so 30,000 and 50,000 become write-capable |
| `cls2-storage-set-osaka-1000` (Osaka STORAGE_SET 20000→1000) | **DETECTED(3)** | test 3 — the pre-8037 floor falls to 3,100, under ERC-7579's 3,229 |
| `cls2-storage-set-osaka-60000` (Osaka STORAGE_SET 20000→60000) | **DETECTED(6)** | test 4 — the pre-8037 floor rises to 62,100, so 30,000 and 50,000 lose the write capability this archetype pins them as having |
| `cls12-cold-read-700` (COLD_STORAGE_ACCESS 2100→700) | survives | correctly: see below |

**All four tests in this directory are killed by at least one mutation**, and the failure
counts match the arithmetic exactly (test 2 and test 4 are 2 params × 3 fixture formats =
6; test 3 is 1 × 3 = 3), which is the cross-check that the right test died rather than
merely some test.

`cls12-cold-read-700` survives **correctly, not through a coverage hole.** Cheaper reads
reduce a fresh slot's cost only by the access term: `700 + 10,000 + 97,920 = 108,620`,
still 2.2x above the largest budget in the table, so arm 2 is unchanged; and arm 1 only
gets easier. Two of this archetype's three budgets are therefore insensitive to read
pricing in the cheaper direction *by construction* — `COST_PER_STATE_BYTE` dominates the
Amsterdam floor at 89% of it.

Note also what `cls2-cpsb-250` does **not** do: it leaves the 3,229 param passing, because
`2,100 + 10,000 = 12,100` of execution gas exceeds 3,229 before any state gas is counted.
No state-gas repricing of any size can make ERC-7579's budget write-capable at Amsterdam.
That graded outcome is the useful part — the *set* of failing params measures how large a
reprice was.

## Design notes

- **`CALL`, not `STATICCALL`, for both arms.** ERC-165 probes are static calls, under which
  a write is impossible by *context* rather than by *gas*; using `CALL` means what is
  measured is the gas boundary. ERC-7579 `postCheck` and EIP-4337
  `validatePaymasterUserOp` are ordinary calls, and for them gas is the only thing between
  the budget and a state write.
- **Both arms in one transaction** (tests 2–4). That is what distinguishes "the budget is
  too small to run at all" from "large enough to run, too small to write". Neither arm
  establishes the boundary alone.
- **No literal gas operand anywhere in the scaffolding** except the three budgets under
  test. The transaction uses the default limit (the `TX_MAX_GAS_LIMIT` cap) with
  `state_gas_reservoir=0`, so a sub-floor literal cannot leak into the support code — a
  hazard the coordinator hit with a `100_000` control that silently sat below the
  Amsterdam floor.
- **`Op.X(a, b)` emits `b` first.** Folding a `CALL` into an `AND` with an `MLOAD` reads
  the return buffer before the call fills it. This cost one wrong measurement: the first
  read-only probe reported "fails at every budget on every fork" when the real problem was
  evaluation order.

## Incident: the shared EELS tree was found corrupted

Mid-task, `tools/mutate.py` refused to start: `osaka/vm/instructions/storage.py` carried a
`# MUTATION` marker from a run that died mid-mutation. `git status` showed two files
modified in the pinned tree — `osaka/vm/gas.py` (`max_message_call_gas` 64→**256**) and
`osaka/vm/instructions/storage.py` (an in-frame refund credited to `gas_left`). Neither is
one of mine. Restored with `git checkout --` on both files; tree verified clean (no
modified files under `src/`, no `# MUTATION` markers anywhere).

Every measurement in this README was then **re-taken** against the restored reference and
is byte-identical to the pre-incident reading, so nothing here was contaminated. The
literal-forwarding budgets in this archetype are far below 255/256 of available gas, which
is why the retention mutation could not have reached them.
