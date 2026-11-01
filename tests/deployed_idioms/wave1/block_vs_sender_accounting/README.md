# Archetype 13 — block-versus-sender gas accounting divergence (EIP-7778)

## The invariant

Through Osaka, a transaction's receipt `gasUsed` **is** its contribution to the block's
`gasUsed`. From EIP-7778 they are two different numbers and the gap is exactly the
refund, so any deployed code that infers block fullness, an L1 data charge, or a fee from
a receipt is reading the wrong counter and nothing in the receipt says so.

**What a failure means in one sentence:** either a fork changed which gas figure the
block counts (the alarm), or an execution cost moved and the pinned literals need
re-measuring with the probe (staleness) — the module-level assertion on the Amsterdam
pair tells you which.

## Mechanism citation (CHECKED, read at the pinned Amsterdam commit)

Pre-Amsterdam the receipt field and the block counter are literally the same variable:

```python
block_output.block_gas_used += tx_gas_used_after_refund              # prague/fork.py:941
receipt = make_receipt(tx, tx_output.error,
                       block_output.block_gas_used, tx_output.logs)  # prague/fork.py:944
```

EIP-7778 splits them into three counters, and `settle_transaction_gas` makes the
block-facing one ignore refunds:

```python
block_output.block_gas_used       += settlement.execution_gas_used   # amsterdam/fork.py:1068
block_output.block_state_gas_used += settlement.state_gas_used       # amsterdam/fork.py:1069
block_output.cumulative_gas_used  += settlement.gas_used             # amsterdam/fork.py:1072

gas_used_before_refund = tx_gas - gas_left - state_gas_left          # amsterdam/vm/gas.py:1210
gas_refund = min(gas_used_before_refund // Uint(5), Uint(refund_counter))  #        :1212
gas_used   = max(gas_used_before_refund - gas_refund, calldata_floor)      #        :1213-1214
execution_gas_used = ExecutionGas(max(gas_used_before_refund
                                      - settled_state_gas_used, calldata_floor))  # :1217-1222
```

The header carries `max(block_gas_used, block_state_gas_used)`
(`amsterdam/fork.py:335-338`), and the testing side derives the fixture's header the same
way (`evm_tools/t8n/result.py:102-106`), so `Header(gas_used=...)` observes exactly that
maximum.

The settlement docstring states the intent: *"Unlike the sender-facing `gas_used`, it
ignores refunds: block accounting counts pre-refund gas ([EIP-7778])."*

## Why this is not the official EIP-7778 suite

`tests/amsterdam/eip7778_block_gas_accounting_without_refunds/` is thorough on the
Amsterdam side but derives **every** expectation from the fork under test —
`code.execution_cost(fork)`, `max_refund_quotient`, `data_floor_calc` in `helpers.py` —
so it recomputes both sides of its own equality and cannot fail when a cost or a rule
moves (`docs/COVERAGE-GAP.md`). And nothing anywhere asserts the **pre-7778 identity** on
the six forks where deployed receipt consumers still rely on it. The first two tests here
close that; the third pins the violation beside it so the pair stays honest.

## Measurement

Measured with `tests/tools/settlement_probe/`, which wraps
`ethereum.forks.amsterdam.fork.settle_transaction_gas` and
`execution_testing.evm_tools.t8n.build_result` with **logging-only** side effects and
emits every settlement quantity per transaction as JSON. It edits nothing in the EELS
tree, so it never contends with `tools/mutate.py`. `fill` runs t8n in-process, which is
what makes patching the importing module's namespace reach the code that executes.

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
rm -f /tmp/sp.jsonl
for F in Berlin London Cancun Prague Osaka Amsterdam; do
  SETTLEMENT_PROBE_LOG=/tmp/sp-$F.jsonl ./.venv/bin/fill \
    ../../wave1/instruments/settlement_probe --from $F --until $F \
    --output /tmp/sp-out-$F -q --tb=no -p no:cacheprovider
done
```

Witness shape: four pre-existing non-zero slots zeroed, zero value, no calldata,
`state_gas_reservoir=0`, `gas_limit=1_000_000`.

All figures below are measured; nothing in this table is derived.

```text
fork        receipt gasUsed   header gasUsed   divergence
Berlin               20,512           20,512            0
London               32,820           32,820            0
Cancun               32,820           32,820            0
Prague               32,820           32,820            0
Osaka                32,820           32,820            0
Amsterdam            50,740           63,424       12,684
```

Amsterdam, additionally measured straight off the settlement (the probe's wrapper reports
the arguments and the result, so these are not reconstructed):
`gas_used_before_refund = 63,424`, `refund_counter = 46,464`, `gas_refund = 12,684`,
`calldata_floor = 15,000`, `settled_state_gas_used = 0`. The cap binds
(`46,464 > 63,424 // 5`).

Side result worth recording, measured on the same probe with one clear instead of four:
on **Berlin** the refund drives the whole block figure *below* the intrinsic cost —
21,000 with no clears, **13,003** with one — because the pre-EIP-3529 divisor is 2 and the
clear refund is 15,000. That is one of the things EIP-3529 was for, and it is why Berlin
is split into its own test rather than sharing a literal: EIP-3529 moved both the clear
refund (15,000 → 4,800) and the cap divisor (2 → 5). London through Osaka share **one**
literal, which is why a single test covers six forks.

The Amsterdam pair is self-checking at import time: the refund counter
(4 × 11,616 = 46,464) exceeds the cap, so the cap binds and

```text
63,424 - 50,740 == 12,684 == 63,424 // 5
```

A re-measurement after a repricing must preserve that relation. If it cannot, the *rule*
changed rather than the cost, and the test is doing its job.

## Fill

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/block_vs_sender_accounting \
    --until Amsterdam --output /tmp/c13 -q --tb=no -p no:cacheprovider
# 22 passed  (24 collected, 2 deselected)  CHECKED
```

Forks covered: Berlin (1 test), London / Paris / Shanghai / Cancun / Prague / Osaka
(1 test, one literal), Amsterdam (1 test).

## Mutation result (CHECKED, `python3 tools/mutate.py`)

```text
mutation                        block_vs_sender_accounting
(baseline)                      pass(3)
exec-gas-applies-refund         DETECTED(2)
refund-divisor-4                DETECTED(3)
state-free-credit               DETECTED(3)
exec-gas-no-state-subtraction   survives
state-clamp-min / -off          survives
floor-not-a-max                 survives
floor-token-8 / -7              survives
```

`exec-gas-applies-refund` is the mutation of the rule this archetype claims to depend on:
it makes `execution_gas_used` subtract the refund, i.e. reverts EIP-7778, and the receipt
and the block merge again. **DETECTED.**

`refund-divisor-4` moves the sender-facing figure (the EIP-3529 lever) and therefore the
size of the gap. **DETECTED** in all three fixture formats, because the receipt pin is
checked in every format.

`exec-gas-applies-refund` reads DETECTED(**2**) of 3 rather than 3, and the reason is a
real limitation worth stating: **the pure `state_test` fixture format has no block header,
so it cannot carry the block-gas assertion.** Verified directly by perturbing each pin by
hand (CHECKED):

```text
pin perturbed                     state_test   blockchain_test_from_state_test
expected_receipt.gas_used + 7     FAILS        FAILS
Header(gas_used) + 7              passes       FAILS
```

So `blockchain_test_header_verify` is the right mechanism, it *is* verified
(`specs/blockchain.py:1059-1062`), and the archetype's block-side assertion lives only in
the two blockchain-derived formats. A `state_test` alone cannot reach class 13.

## Rules this archetype adds to the corpus

1. **When the invariant is a relation between two gas numbers, pin both and make the
   relation an import-time assertion.** SCHEMA §4.1's "unless the gas number IS the
   invariant" exception applies here as it does to class 3, but a bare pair of literals is
   indistinguishable from a stale pair. `BLOCK - RECEIPT == BLOCK // 5` is not.
2. **Encode an equality by sharing the symbol.** The pre-7778 tests pin one literal to
   both the receipt and the header, so the equality cannot be satisfied by tuning one side.
3. **Serialise measurement runs against `tools/mutate.py`.** An early `fill` here landed
   inside another agent's mutation window and reported +2,900 execution gas on a shape
   that is 27,212 on a pristine tree — it looked like a clean measurement and would have
   been pinned as one. The lock in `mutate.py` protects mutation runs from each other; it
   does not protect *measurements* unless the measurer also takes it. `tools/locked_fill.py`
   (added with this archetype) takes the same `flock` and additionally refuses to run
   against a dirty `src/ethereum/forks/` tree:

   ```bash
   python3 tools/locked_fill.py <any fill arguments>
   ```
