# Archetype 8: refund-cap dependence

## The invariant

A transaction that clears storage receives
`min(gas_used_before_refund // D, refund_counter)` back, and both terms of that `min`
are frozen rules a fork can move:

- **`D`, the divisor.** 2 at Berlin, **5 from London (EIP-3529)**.
  `berlin/fork.py:698` → `london/fork.py:810` → `amsterdam/vm/gas.py:1213`. CHECKED.
- **`REFUND_STORAGE_CLEAR`, the per-clear counter contribution.** 15,000 at Berlin,
  **4,800 from London (EIP-3529)**, and 11,616 at Amsterdam, where it is derived as
  `(STORAGE_WRITE + COLD_STORAGE_ACCESS) * 4800 // 5000` from the new 12,100 write price
  (`amsterdam/vm/gas.py:98`). CHECKED.

The tests pin each term with the *other* term deliberately out of the way, so a failure
says which one moved.

## Why this is a real gap — and exactly how large a gap, CHECKED

L4's claim was "the `//2 → //5` change is never tested behaviourally, only for
conformance". Verified against the pinned tree, with one correction to it:

| finding | evidence | status |
|---|---|---|
| No test directory for EIP-3529 exists. `tests/london/` holds only `eip1559_fee_market_change` and `validation` (a header test). | `ls tests/london/` | CHECKED |
| The quotient is read back out of the fork wherever a test touches it: `max_refund_quotient()` returns 2 at Genesis (`forks/forks/forks.py:1275`) and 5 from London (`forks/eips/london/eip_3529.py:31`). Eleven test files use it. | `grep -rln max_refund_quotient tests/` | CHECKED |
| **Correction to L4:** `tests/amsterdam/eip8038_state_access_gas_cost_increase/test_sstore_refunds.py` *does* hardcode `gross // 5`. | `grep -n "// 5" …/test_sstore_refunds.py` | CHECKED |
| …but it is `valid_from("Amsterdam")`, so it is blind to the quotient on Berlin..Osaka; and it takes the clear-refund *amount* from the fork (`code.refund(fork)`), leaving that term fork-derived everywhere. | same file, line 59 and 103 | CHECKED |

So the uncovered region is **the quotient on Berlin, London and Osaka** and **the
per-clear refund amount on every fork** — which is what this directory supplies. The
Amsterdam divisor test here overlaps with the EIP-8038 file above and is kept for the
pair's symmetry rather than claimed as new; `cls8-refund-div-10` will light up both.

A deployed contract reads neither number from a fork: it budgeted against fixed values at
deploy time. That asymmetry is the whole reason this corpus exists.

## Deployed witness

| source | population | counting unit |
|---|---|---|
| `registry/L2-bytecode.jsonl` — *bulk storage clearing inside a loop*, axes include `refund-cap` | **406,604 addresses / 298,869 distinct runtime code hashes** (30.05% of the 994,414 mainnet runtimes scanned) | distinct mainnet runtime code hashes, and the addresses they back |
| `registry/L2-bytecode.jsonl` — *storage slot cleared after a state-creating call*, axes include `refund-cap` | 265,217 addresses / 208,712 runtimes (20.99%) | as above |
| `registry/L5-dynamic.jsonl` — refund fingerprint, mainnet blocks 26,250,000–26,259,999 | **792,199 of 2,571,532 transactions (30.81%) receive a refund**; 365,238 refund exactly 4,800 (one plain clear), 77,109 exactly 2,800, 60,324 exactly 19,900 | distinct transactions |

Exemplar addresses (L2, highest deployed-address count for the shape):
`<address withheld>`,
`<address withheld>`.

The L2 record's own stated invariant is this class: *"the number of slots a batch can
clear within a given transaction gas limit is determined by the per-slot cost net of
refund, and the batch completes the count it was asked for."*

**On gas tokens.** a gas-token contract/a gas-token contract are the historically-killed population and the reason
EIP-3529 names the problem, but L4's `refund-cap` axis records `instances: 0` with
`method: "NOT CITED by L4 ... Zero here means unmeasured, NOT absent"`. So the gas-token
story is cited here as history, **not** as a measured count. INFERRED, and labelled as
such in the test docstring too.

## How a refund is made observable

A refund is settled after execution, so the only thing it can change is the ether
returned to the sender — it can never make a transaction complete that would otherwise
run out of gas (that is archetype 9's invariant). So:

1. Two senders start with **exactly** `gas_limit * gas_price` wei and run bytecode of
   *identical gas cost* over identical storage. One clears its slots (`1 → 0`, refund
   granted); the twin moves them to another non-zero value (`1 → 2`, same charge, **no**
   refund — `amsterdam/vm/instructions/storage.py:122-139`). `PUSH1 v; PUSH1 k; SSTORE`
   has the same width and price for every `v`, so the two runs cost the same to the gas.
2. A third transaction in the same block reads both balances with `BALANCE`, divides by
   the gas price, and commits the derived quantity to storage.
3. The twin received no refund, so `gas_limit - BALANCE/price` is literally
   `gas_used_before_refund`; the *difference* between the two balances is the refund.
   Every price the two share cancels.

So `refund` is read out in gas units, and `gas_used_before_refund // refund` is the
divisor `D` itself — a dimensionless number that is the rule, not a cost. That is the
only assertion in this directory that could look like "asserting a gas number", and
SCHEMA §4.1 permits it for exactly this case: the number **is** the invariant.

### `state_gas_reservoir`, stated explicitly

Every transaction here sets an explicit `gas_limit` of 1,000,000. On Amsterdam
`allocate_evm_gas` (`amsterdam/vm/gas.py:1104`) splits the limit into execution gas and
reservoir, and the reservoir is `max(0, gas_limit - TX_MAX_GAS_LIMIT)` — **0** for any
limit below 16,777,216. So `state_gas_left` is 0 at settlement and
`gas_used_before_refund = tx_gas - gas_left` with no reservoir term. No slot is created
either (every slot starts non-zero), so no state gas is charged at all. CHECKED by the
measurement below: Amsterdam's `used` of 620,300 equals
`15,000 (EIP-2780 intrinsic, zero-value call) + 50 × 12,100 + 300` exactly.

## Measurement

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
for F in Berlin London Cancun Osaka Amsterdam; do
  ./.venv/bin/fill ../../wave1/instruments/test_refund_probe.py \
      --from $F --until $F -k "cap_bound" --output /tmp/p8-$F -q --tb=line \
      -p no:cacheprovider
done
```

The probe's expectation is `0`, so each failure prints the real value. CHECKED:

```text
fork       gas_used_before_refund   refund    used // refund
Berlin                    271,300   135,650                2
London                    271,300    54,260                5
Cancun                    271,300    54,260                5
Osaka                     271,300    54,260                5
Amsterdam                 620,300   124,060                5
```

and with one clear inside a ~138,000-gas memory expansion, so the counter is the smaller
term (`-k "counter_bound"`):

```text
fork       refund (= REFUND_STORAGE_CLEAR)
Berlin                              15,000
London                               4,800
Osaka                                4,800
Amsterdam                           11,616
```

`271,300 // 5 = 54,260` and `620,300 // 5 = 124,060` to the gas, and the Amsterdam
constant reproduces `(10,000 + 2,100) * 4800 // 5000 = 11,616` to the gas. Derivation and
measurement agree, which is why both are reported CHECKED rather than one inferred from
the other.

## Fill

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/refund_cap --until Amsterdam \
    --output /tmp/rc -q --tb=no -p no:cacheprovider
# 28 passed    CHECKED  (tree verified pristine before and after)
```

## Mutation result

```bash
cd tests/deployed_idioms
python3 tools/mutate.py -k cls8 --archetype refund          # scoped, seconds
python3 tools/mutate.py -k cls8-refund-div-10-london        # specificity row
```

### Inventory: 9 mutations, **2 distinct rules** — stated per SCHEMA §7.9

They are deliberately not 9 independent results. They are two rules crossed with the
fork each is implemented in and the direction it is moved:

| rule | mutations | why the variants are not padding |
|---|---|---|
| **R1 — the cap divisor** | `cls8-refund-div-10`, `cls8-refund-div-2-amsterdam`, `cls8-refund-div-{10,2}-london`, `cls8-refund-div-{5,1}-berlin` | **three independent code sites** (`berlin/fork.py:698`, `london/fork.py:810`, `amsterdam/vm/gas.py:1213`), so a fork can move one without the others — and only the Amsterdam site has any existing behavioural coverage. Two directions per site because the harm inverts with direction. |
| **R2 — the per-clear counter contribution** | `cls8-clear-refund-halved-amsterdam`, `cls8-clear-refund-2400-london`, `cls8-clear-refund-30000-berlin` | the same: three independent constants, and the value differs per fork (11,616 / 4,800 / 15,000), so one mutation cannot cover all three. |

Within a site the two directions *do* fire on the same test. That is the point, not a
duplication: it demonstrates the assertion is a two-sided equality rather than a
one-sided bound. Reported as "one test, both arms", not as two findings.

```text
mutation                             refund_cap   refund_not_spendable  calldata_floor_refund
(baseline)                           pass(4)      pass(6)               pass(4)
cls8-refund-div-10        (tighter)  DETECTED(2)  survives              survives
cls8-refund-div-2-amsterdam (looser) DETECTED(2)  survives              survives
cls8-refund-div-10-london (tighter)  DETECTED(1)  survives              n/a
cls8-refund-div-2-london  (looser)   DETECTED(1)  survives              n/a
cls8-refund-div-5-berlin  (tighter)  DETECTED(1)  survives              n/a
cls8-refund-div-1-berlin  (looser)   DETECTED(1)  survives              n/a
cls8-clear-refund-halved-amsterdam   DETECTED(2)  survives              survives
cls8-clear-refund-2400-london        DETECTED(1)  survives              n/a
cls8-clear-refund-30000-berlin       DETECTED(1)  survives              n/a
every cls9-* and cls11-* mutation    survives     --                    --
```

**9 of 9 DETECTED, both directions at all three fork sites.** The baseline row
is green (`pass(4)`), so no cell is a masked baseline failure.

### Specificity across all 19 archetypes, measured — and the divisor is NOT exclusive

`python3 tools/mutate.py -k cls8-refund-div-10` (unrestricted, 19 archetypes,
baselines green everywhere):

```text
mutation                     refund_cap   block_vs_sender_accounting  state_gas_clamp  other 16
cls8-refund-div-10           DETECTED(2)  DETECTED(3)                 DETECTED(12)     survives
cls8-refund-div-10-london    DETECTED(1)  DETECTED(2)                 n/a              survives
```

This **corrects an earlier claim in this file**, which said the cls8 mutations
survive everywhere else. They do survive on the 16 archetypes outside the
settlement family, but the refund divisor is genuinely shared with the
**EIP-7778 block-versus-sender** family (class 13) and the **net-state-gas
clamp** family (class 14) — which is correct and expected, because the divisor
feeds the sender-facing `gas_used` those archetypes assert on.

So the honest specificity statement is: *the refund divisor is a shared rule
across three archetype families, and this directory is the only one that
asserts the divisor itself rather than a quantity derived from it.* Diagnostic
value is retained because the **signature** differs — when `refund_cap` goes red
alone the clear refund moved; when all three go red the divisor moved.

`n/a` is the harness's `UNTRUSTWORTHY`: at a Berlin/London mutation fork,
`calldata_floor_refund` has no tests, so `fill` produces no pytest summary at
all and the harness refuses to read silence as a pass. It is an absence of a
result, not a result.

Counts: `DETECTED(2)` at Amsterdam is both Amsterdam-valid tests failing (the
`//5` ratio test and the 11,616 clear-refund test, one fixture format each
counted per param); `DETECTED(1)` at Berlin or London is the single test valid
there. Failure text is self-documenting, e.g.
`refund_divisor: want 0x5 (dec:5), got 0xa (dec:10)`.

**Cross-detection worth recording:** another agent's `refund-divisor-4`
(5 -> 4, in `cls-13-14-15.json`) will also fire here, because the ratio
assertion is an equality on the divisor rather than a bound. Two agents'
mutations landing on one assertion is one rule, not two findings.


## What a failure means

**The refund a clearing transaction gets back is no longer the fraction, or no longer the
per-clear amount, that 406,604 deployed addresses' clearing loops were sized against** —
and because the pair of tests brackets the London boundary from both sides, a failure also
says which direction the rule moved.

## Direction matters, and this pair covers both

Five of the fifteen gas constants that changed across mainnet forks moved **down**, and
the refund cap is the sharpest case because the direction inverts who is hurt.
*Tightening* the divisor (2 → 5) shrinks the refund and breaks anything that needed the
larger one — the EIP-3529 break. *Loosening* it breaks anything treating post-refund
`gas_used` as stable, a relayer reimbursing from it being the obvious case. The
`cls8-*` mutations are therefore parametrised in both directions
(`// Uint(10)` tighter, `// Uint(2)`/`// Uint(1)` looser; clear refund 4,800 → 2,400
tighter and 15,000 → 30,000 looser), and the ratio assertion is a two-sided equality, so
it detects both. A test that only detects tightening covers half the rule.
