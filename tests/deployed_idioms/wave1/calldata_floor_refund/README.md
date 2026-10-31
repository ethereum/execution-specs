# Archetype 15 — the calldata floor makes a refund invisible (EIP-7623 / EIP-7976)

## The invariant

A calldata-heavy, execution-light transaction pays the floor regardless of refunds. Two
transactions with identical calldata, gas limits, fees and value cost their senders
**exactly the same** even when one earns a large storage-clear refund and the other earns
none. A relayer, paymaster, or sequencer that prices a call as "execution minus expected
refund" is computing a number the protocol will not charge; a gas-token-style scheme that
monetises refunds earns nothing at all on this transaction shape.

**What a failure means in one sentence:** the floor has stopped binding for this calldata
size — either the `max` is gone, or the per-token floor cost fell far enough that refunds
are visible again — and anything that assumed a fixed data-cost floor is now mispricing.

## Mechanism citation (CHECKED)

```python
gas_used = max(gas_used_after_refund, calldata_floor)      # amsterdam/vm/gas.py:1214
                                                           # prague/fork.py:922 (EIP-7623 original)
```

and the floor itself (`amsterdam/transactions.py:772-784`):

```python
floor_tokens_in_calldata = ulen(tx.data) * GasCosts.TX_DATA_TOKEN_STANDARD   # 4 per BYTE
base_execution_gas  = GasCosts.TX_BASE + recipient_execution_gas
data_floor_gas_cost = (base_execution_gas
                       + floor_tokens_in_calldata * GasCosts.TX_DATA_TOKEN_FLOOR
                       + access_list_data_cost)
```

EIP-7976 changed two things at once: `TX_DATA_TOKEN_FLOOR` 10 → 16, and the token count
became `4 × len(data)` uniformly instead of `zeros + 4 × non-zeros`. Verified per-token
cost, by hand against the measurement rather than from the fork object:

```text
fork         floor(len)              per byte   derivation
Prague       21,000 + 40 x len             40   TX_DATA_TOKEN_FLOOR 10 x 4 tokens/byte
Osaka        21,000 + 40 x len             40   unchanged
Amsterdam    15,000 + 64 x len             64   TX_DATA_TOKEN_FLOOR 16 x 4 tokens/byte
```

Measured floors (CHECKED, read straight off `settle_transaction_gas`'s `calldata_floor`
argument for Amsterdam, and off the receipts for Prague/Osaka), all-non-zero calldata:

```text
len     Amsterdam   Prague / Osaka
  0        15,000           21,000
128        23,192           26,120
512        47,768           41,480
2048      146,072          102,920
4096      277,144          184,840
```

Every figure matches the formula exactly. The Amsterdam base is 15,000 rather than 21,000
because EIP-2780 decomposed the intrinsic base into
`TX_BASE 12,000 + COLD_ACCOUNT_ACCESS 3,000`, and the floor is anchored on that sum.
**Consequence this test controls for:** `recipient_execution_gas` adds `TX_VALUE_COST`
6,000 when `tx.value > 0`, so a value-bearing transaction's floor is 6,000 higher than an
otherwise identical zero-value one. Every transaction here is `value=0`. (Intrinsic-side
facts cross-checked against `tests/intrinsic_cost/`.)

## Why this is not the official EIP-7976 suite

`tests/amsterdam/eip7976_increase_calldata_floor_cost/` has
`test_floor_cost_not_reduced_by_refunds` and a whole `test_refunds.py` with three
refund-versus-floor regimes. Two gaps remain.

1. **Fork coverage.** Both are `pytestmark = valid_from("EIP7976")`, i.e. Amsterdam only.
   The floor shipped at **Prague** with EIP-7623 and deployed code has depended on it
   since. Nothing asserts the refund interaction on Prague or Osaka. This test runs
   `valid_from("Prague")`.
2. **Self-derivation.** Every expectation comes from the fork under test —
   `fork.transaction_data_floor_cost_calculator()`, `code.gas_cost(fork)`,
   `fork.max_refund_quotient()` — so the test recomputes both sides of its own equality
   (`docs/COVERAGE-GAP.md`).

**This file asserts no gas number at all.** Two senders start with equal balances and send
transactions differing only in whether the callee's slots were already non-zero; a third
transaction has a contract commit `EQ(BALANCE(quiet), BALANCE(refunding))` to storage. The
assertion is a committed effect, so it survives any repricing that keeps the floor
binding.

## Measurement

Same instrument as the sibling archetypes (`tests/tools/settlement_probe/`). The exact
test shape was measured by copying the test file into the probe directory so the
logging conftest instruments it:

```bash
cd /home/devops/toni/datanalysis/eip-8037
cp wave1/calldata_floor_refund/test_calldata_floor_refund.py \
   wave1/instruments/settlement_probe/test_zz_c15_shapes.py
cd engine/eels
SETTLEMENT_PROBE_LOG=/tmp/sp15.jsonl ./.venv/bin/fill \
    ../../wave1/instruments/settlement_probe --until Amsterdam \
    -k "zz_c15 and blockchain_test and not engine" \
    --output /tmp/sp15 -q --tb=no -p no:cacheprovider
rm ../../wave1/instruments/settlement_probe/test_zz_c15_shapes.py
```

Per-transaction settlement, Amsterdam (CHECKED):

```text
floor_binds (4,096 bytes of calldata)
  tx0 quiet      before=  97,384  refund=      0  floor= 277,144  gas_used= 277,144
  tx1 refunding  before= 177,384  refund= 35,476  floor= 277,144  gas_used= 277,144
  tx2 comparator before= 131,032  refund=      0  floor=  15,000  gas_used= 131,032

floor_has_slack (128 bytes)
  tx0 quiet      before=  33,896  refund=      0  floor=  23,192  gas_used=  33,896
  tx1 refunding  before= 113,896  refund= 22,779  floor=  23,192  gas_used=  91,117
  tx2 comparator before=  23,112  refund=      0  floor=  15,000  gas_used=  23,112
```

Prague and Osaka, receipt cumulative figures: `floor_binds` → `184,840 / 369,680 / 417,992`
(so both senders paid exactly 184,840); `floor_has_slack` → `40,696 / 91,173 / 119,585`
(so 40,696 against 50,477).

`tx1` earns a 35,476-gas refund and pays the same 277,144 as `tx0`, which earns none.
That is the invariant, read directly.

## A bug this measurement caught, worth repeating

The first version gave the comparator a 100,000 gas limit. On Amsterdam its single fresh
`SSTORE` needs ~110,026 once EIP-8037's 97,920 state gas spills into `gas_left`
(`wave1/frozen_budget/README.md`), so the comparator **ran out of gas and committed 0** —
which is indistinguishable from "the senders paid different amounts". The probe showed it
immediately: `tx2 before = 100,000`, exactly its limit. The positive arm is now the only
one that creates a slot, and its limit is 400,000.

The general lesson: **a comparator contract inside a corpus test is itself a frozen-budget
caller.** Give it headroom over the Amsterdam slot floor, and verify from the measurement
that it did not consume its whole limit.

## Fill

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/calldata_floor_refund \
    --until Amsterdam --output /tmp/c15 -q --tb=no -p no:cacheprovider
# 12 passed  CHECKED   (2 params x 3 forks (Prague, Osaka, Amsterdam) x 2 blockchain formats)
```

`blockchain_test` rather than `state_test`: three transactions must land in one block in a
fixed order, which a state test cannot express.

## Mutation result (CHECKED, `python3 tools/mutate.py`)

```text
mutation                        calldata_floor_refund
(baseline)                      pass(4)
floor-not-a-max                 DETECTED(2)
floor-token-7                   DETECTED(2)
floor-token-8                   survives    <-- correctly; the cliff is between 7 and 8
everything else (7 mutations)   survives
```

**`floor-not-a-max`** replaces `max(gas_used_after_refund, calldata_floor)` with
`gas_used_after_refund`, i.e. the floor stops being a floor on the sender-facing charge.
The refunding sender then pays 141,908 against the quiet sender's 97,384, the balances
diverge, and the committed answer flips to 0. **DETECTED** — both failures are the
`floor_binds` param, and the `floor_has_slack` param correctly keeps passing because its
refund was already visible.

**`floor-token-7` / `floor-token-8` locate a cliff.** The floor stops binding when it
falls below the refunding transaction's *post-refund* figure, 141,908 — not below its
pre-refund 177,384, which is the mistake this measurement corrected:

```text
TX_DATA_TOKEN_FLOOR   floor at 4,096 bytes      vs 141,908   verdict
                 16   15,000 + 16,384x16 = 277,144   binds    (reference)
                  8   15,000 + 16,384x 8 = 146,072   binds    survives, correctly
                  7   15,000 + 16,384x 7 = 129,688   does not DETECTED(2)
```

So EIP-7976's increase could be reverted entirely (16 → 10, the EIP-7623 value) and *more*
besides, and this shape would still pay the floor. The cliff sits at
`TX_DATA_TOKEN_FLOOR = 7.74`, and which side of it a mutation lands on measures how large
the reprice was — the same graded-sensitivity property the `retention-128` /
`retention-256` pair has in `docs/MUTATION-MATRIX.md`, and a reason to read a `survives`
cell as a magnitude rather than a hole.

**Specificity.** No mutation from any other agent's file touches this archetype, and none
of this archetype's own class-13 or class-14 mutations do either. The floor is the only
rule it depends on.

## Rules this archetype adds to the corpus

1. **Prefer a differential committed effect to a pinned gas number.** Two senders, equal
   starting balances, an on-chain `EQ(BALANCE, BALANCE)` committed to storage: the test
   asserts "these two cost the same" without ever naming the cost, so it covers three
   forks with one body and survives repricing.
2. **Always ship the arm where the invariant does *not* hold.** The `floor_has_slack`
   param commits 0. Without it, a broken comparator, a mis-specified pair, or a
   transaction that silently reverted would all commit 1 and the test would pass
   vacuously.
3. **Compare the floor against the post-refund figure, not the pre-refund one.** This is
   the arithmetic error that made a predicted-detecting mutation survive; the floor's
   competitor in the `max` is `gas_used_after_refund`.
4. **Control `value`.** From Amsterdam the floor is anchored on `base_execution_gas`, so a
   value-bearing transaction has a floor 6,000 higher. Comparing a value-bearing
   transaction with a zero-value one compares two different floors.
