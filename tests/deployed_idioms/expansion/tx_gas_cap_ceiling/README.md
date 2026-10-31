# tx_gas_cap_ceiling — the per-transaction gas cap as a *work ceiling*

**Invariant.** The amount of execution work a single transaction can perform is
`min(2²⁴, tx.gas) − intrinsic.execution`. Deployed relayers, batchers and
multicalls size a batch against the *block* gas limit and assume "the gas I buy
is the gas I get"; a per-transaction cap is a different constraint, and from
EIP-8037 it truncates them **silently**.

Three claims, all CHECKED, all pinned here:

1. **The ceiling exists and is 2²⁴.** The number IS the invariant (SCHEMA §4.1).
2. **The cap and EIP-8037's state-gas reservoir are the same boundary.**
   `reservoir == max(0, tx.gas − 2²⁴)`, with the intrinsic cost cancelling out.
3. **The block gas limit still bounds the whole `tx.gas`,** reservoir included —
   the cap does *not* let a transaction oversubscribe a block.

## Why it is rule-dependent, and why it is quiet

```
Osaka      tx.gas > TX_MAX_GAS_LIMIT          -> INVALID      osaka/transactions.py:582
Amsterdam  tx.gas > TX_MAX_TOTAL_GAS_LIMIT    -> INVALID      amsterdam/transactions.py:638
           TX_MAX_GAS_LIMIT bounds only the execution grant:
             evm_gas   = tx.gas - intrinsic
             budget    = TX_MAX_GAS_LIMIT - intrinsic
             execution = min(budget, evm_gas)
             reservoir = evm_gas - execution                   amsterdam/vm/gas.py:1133-1136
```

The same constant changed job: a **validity** bound became an **allocation**
bound. So the hazard has three stages and the last one is the dangerous one:

| fork | ask for 17,777,216 gas | outcome |
| --- | --- | --- |
| Prague | granted 17,756,214 | works |
| Osaka | transaction rejected | **loud** failure, nothing is mined |
| Amsterdam | granted 16,762,214 | **silent** truncation, nothing reverts |

## Measured (CHECKED)

`GAS` as the first instruction, so the figure is the grant minus 2.
Instruments: `expansion/tests/tools/test_exp_txcaps_{ceiling,accesslist,reservoir,blockcap}_probe.py`.

```text
execution grant, no access list
fork            tx.gas = 2**24      tx.gas = 2**24 + 1,000,000
Berlin..Prague  16,756,214          17,756,214        1:1 with tx.gas
Osaka           16,756,214          transaction INVALID
Amsterdam       16,762,214          16,762,214        identical

reservoir threshold, child frame handed exactly 12,106 execution gas
tx.gas = 2**24               fresh slot does NOT land
tx.gas = 2**24 + 97,919      does NOT land
tx.gas = 2**24 + 97,920      LANDS          <- reservoir origin, to one gas
tx.gas = 2**24 + 97,921      LANDS

access-list cost against the ceiling
                        Prague/Osaka   Amsterdam   delta
one address entry       2,400          4,180       +74.17%
one storage key         1,900          4,048       +113.05%

block dimension, 20,000,000-gas block
tx.gas = 20,000,000          included
tx.gas = 20,000,001          GAS_ALLOWANCE_EXCEEDED
```

Three numbers worth keeping:

- **12,106** is the measured execution cost of one fresh `SSTORE`
  (`COLD_STORAGE_ACCESS` 2,100 + `STORAGE_WRITE` 10,000 + two `PUSH1`s).
  Handing the child exactly that leaves zero slack for the 97,920 state gas to
  spill into, which is what makes the reservoir threshold measurable to a single
  gas. With a 94-gas slack (forward 12,200) the threshold moves to
  `2²⁴ + 97,826` — measured, and the reason the probe was re-run.
- The intrinsic cost **cancels out** of `evm_gas − execution`, so the reservoir
  boundary is the one number in this file immune to EIP-2780's decomposition.
- The EIP-7981 floor-token surcharge is **30.62%** of an address entry
  (1,280 of 4,180) and **50.59%** of a storage key (2,048 of 4,048) — more than
  half the charge for a key is the piece that is *also* counted in the calldata
  floor.

## Deployed witness

**Protocol constants, with an idiom witness rather than an address witness for
the cap itself.** 2²⁴ is nine months old and no deployed contract can contain
it as a learned constant yet, so claiming an address count for it would be
dishonest. What is witnessed is the *idiom the cap breaks* — gas-budget sizing
against a block limit:

- L4 `gas-delta` — **252,006 addresses from 2,499 source files**, FP 0/18
  (`registry/L4-rule-axes.jsonl`), the meter shape relayers wrap around a batch.
- L1 measures the EIP-170/3860 size constants at 338 addresses (see
  `code_size_gate`), which is the directly comparable case of a protocol limit
  hardcoded in deployed code; the same practice applied to a gas cap is
  INFERRED, not measured.

The access-list half has **no deployed contract witness and that is a result**:
`docs/INVARIANT-CLASSES.md` #18 already records that an access list is sized by
the sender off chain, so no contract predicts its cost. This archetype does not
contradict that — it pins the access-list cost from the *other* end, as lost
execution capacity inside the transaction, which is a property of the
transaction rather than of any contract.

## Non-duplicative with the official suite (CHECKED)

`tests/osaka/eip7825_transaction_gas_limit_cap/` (747 + 129 lines) is a
**validity** suite: it tests which gas limits are accepted or rejected. Its one
non-fork-restricted execution test, `test_tx_gas_limit_cap_subcall_context`,
passes `tx_gas_limit_cap + 1` as a `*CALL` gas argument and asserts the call
succeeded — it never measures what the top frame was granted. Four of its tests
carry `valid_before("EIP8037")` with the file docstring explaining why, so the
suite deliberately stops where this archetype starts.

Nothing in it states:

- the grant at the cap (16,756,214 / 16,762,214) — the batcher's actual ceiling;
- that above the cap at Amsterdam the grant **stops moving**;
- that `reservoir == tx.gas − 2²⁴` exactly;
- that the block's *state* dimension still measures the full `tx.gas`.

For EIP-7981, every official test is `valid_at("EIP7981")` or
`valid_at_transition_to("EIP7981")` (grep over all six files, CHECKED) and every
expectation comes from `fork.transaction_intrinsic_cost_calculator()` /
`fork.transaction_data_floor_cost_calculator()`, which **re-implement the same
formula** (`packages/testing/.../forks/eips/amsterdam/eip_7981.py`:
`total_bytes * 4 * TX_DATA_TOKEN_FLOOR`). A literal `2400`, `1900`, `4180`,
`4048`, `1280` or `2048` appears in none of them. So the cross-fork delta is
asserted nowhere, and a reprice that lands in the EIP and the framework fork
definition together — which is how a reprice actually ships — moves both sides
of every official assertion at once. This archetype holds the absolute numbers,
so it cannot.

The transaction gas limit cap is **not** an invariant class in
`docs/INVARIANT-CLASSES.md`; the nearest neighbours are #13 (block-vs-sender
accounting, which is about settlement rather than allocation), #15 (the calldata
floor) and #17 (intrinsic cost), and none of them can express a work ceiling.

## Reproduce

```bash
cd tests/deployed_idioms
python3 tools/locked_fill.py \
    expansion/tests/tx_gas_cap_ceiling --until Amsterdam \
    --output /tmp/txcap --clean -q -p no:cacheprovider      # 106 passed

# the measurements behind every pinned number
python3 tools/locked_fill.py \
    expansion/tests/tools/test_exp_txcaps_ceiling_probe.py \
    expansion/tests/tools/test_exp_txcaps_reservoir_probe.py \
    expansion/tests/tools/test_exp_txcaps_accesslist_probe.py \
    expansion/tests/tools/test_exp_txcaps_blockcap_probe.py \
    --from Prague --until Amsterdam --output /tmp/txprobe --clean -q --tb=no \
    -p no:cacheprovider      # failures ARE the measurement

python3 tools/mutate.py --wave expansion -k exp-tx --archetype tx_gas_cap
```

## Mutation result (CHECKED)

`python3 tools/mutate.py --wave expansion -k exp-tx`, run over all **9**
expansion archetypes. Baseline `pass(33)` at Amsterdam (the full Berlin→Amsterdam
fill is 106). Failure counts in brackets.

| mutation | this archetype | elsewhere in the expansion wave |
| --- | --- | --- |
| `exp-tx-cap-halved` | DETECTED(21) | all 8 survive |
| `exp-tx-cap-doubled` | DETECTED(12) | all 8 survive |
| `exp-tx-cap-not-applied-to-execution` | DETECTED(12) | all 8 survive |
| `exp-tx-budget-ignores-intrinsic` | DETECTED(12) | all 8 survive |
| `exp-tx-reservoir-gets-all-evm-gas` | DETECTED(30) | detected by all 8 as well |
| `exp-tx-block-state-dim-capped` | DETECTED(3) | all 8 survive |
| `exp-tx-al-address-2400` | DETECTED(6) | all 8 survive |
| `exp-tx-al-key-1900` | DETECTED(3) | all 8 survive |
| `exp-tx-al-address-floor-tokens-40` | DETECTED(6) | all 8 survive |
| `exp-tx-al-key-floor-tokens-256` | DETECTED(3) | all 8 survive |
| `exp-tx-al-surcharge-not-in-execution` | DETECTED(6) | all 8 survive |
| `exp-tx-osaka-cap-halved` | DETECTED(9) | also 4 others (see note) |
| `exp-tx-osaka-tx-base-20000` | DETECTED(9) | all 8 survive |
| `exp-tx-osaka-al-address-2000` | DETECTED(6) | all 8 survive |

**14 mutations detected, 12 of them with perfect specificity** — nothing else in
the wave can see the transaction gas cap, the reservoir origin, the execution
budget's intrinsic subtraction, the block's state dimension, or any access-list
coefficient.

**Both directions, as `docs/INVARIANT-CLASSES.md` requires.** Dearer/tighter:
`cap-halved`, `al-key-floor-tokens-256`, `block-state-dim-capped`. Cheaper/looser:
`cap-doubled`, `cap-not-applied-to-execution`, `budget-ignores-intrinsic`,
`al-address-2400`, `al-key-1900`, `al-address-floor-tokens-40`,
`al-surcharge-not-in-execution`, `osaka-tx-base-20000`, `osaka-al-address-2000`.
Four of the cheaper ones restore the **exact** pre-fork values (2,400 / 1,900 /
21,000 reduced / 2**25) rather than inventing a number, so they model the real
historical reprice run backwards.

**Graded counts, each predicted before the run:** `cap-halved` fails 21 of 33
because the four reservoir params and the two access-list params move together
with the three ceiling params, while the block-dimension pair is unaffected;
`block-state-dim-capped` fails exactly **3** — the single
`one_gas_over_the_block_gas_limit` param, since it is the only assertion in the
file that depends on the state dimension rather than on the cap. The access-list
mutations split 6/3 exactly as the parametrisation predicts: an address-side
change moves both params, a key-side change moves only the `one_key` param.

**Two blunt rows, flagged rather than claimed as strength.**
`exp-tx-reservoir-gets-all-evm-gas` and `exp-tx-osaka-cap-halved` fire on most of
the wave, because handing every transaction a vast reservoir, or halving the
Osaka validity bound, perturbs gas accounting for every test that uses the
implicit gas limit. They are valid detections with **low diagnostic value**; the
12 single-detector rows are what locate a regression.

**Fork coverage.** `mutate.py` perturbs one fork per mutation and fills only that
fork, so the Amsterdam rows cannot reach the `valid_until("Prague")` and
`valid_until("Osaka")` arms. The three `exp-tx-osaka-*` mutations exist for
exactly that reason and close it: they falsify the Osaka ceiling test
(16,756,214) and the pre-EIP-7981 access-list arm. The
`valid_until("Prague")` arm (`a_million_above_it`) is **not** reached by any
mutation here, because `mutate.py` has no Prague-fork mutation registered in this
wave — a stated gap, not a silent one.

## What a failure means

The per-transaction work ceiling moved, or the reservoir stopped being the gas
above it. Every relayer, batcher and multicall that sizes a batch by gas is now
sizing it against the wrong number — and on the Amsterdam side of the boundary
that produces no exception at all, just a batch that quietly did less than it
was paid for.
