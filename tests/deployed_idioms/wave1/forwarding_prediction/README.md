# Class #5 — forwarding-prediction agreement

**The invariant.** A contract that reimplements the forwarding formula to predict what
its callee will receive must get the same answer the EVM does. Concretely, for the
deployed pre-check shape: *if the contract's own check says it can afford to forward
`gasLimit`, the callee actually observes `gasLimit`.*

**What a failure means.** A deployed contract that asks itself "can I afford this
exact-gas call?" now gets the wrong answer, and nothing reverts — the callee is quietly
starved.

## Deployed witness

a deployed oracle network CCIP's `CallWithExactGas` library (`_callWithExactGas`, used by the OffRamp to
deliver cross-chain messages):

```solidity
uint16 internal constant GAS_FOR_CALL_EXACT_CHECK = 5_000;
// so that we can redeploy to adjust it should a hardfork change
// the gas costs of relevant opcodes in callWithExactGas
```

```yul
g := gas()
if lt(g, GAS_FOR_CALL_EXACT_CHECK) { revert(0, 0) }
g := sub(g, GAS_FOR_CALL_EXACT_CHECK)
if iszero(gt(sub(g, div(g, 64)), gasLimit)) { revert(0, 0) }
success := call(gasLimit, target, 0, add(payload, 0x20), mload(payload), 0, 0)
```

A deployed contract that documents, in its own source, the exact risk this corpus
guards against — and names redeployment as its only remedy. `GAS_FOR_CALL_EXACT_CHECK`
is a Solidity `constant`, so it is a literal in immutable bytecode.

The library also exposes `callWithExactGasSafeReturnData(payload, target, gasLimit,
maxReturnBytes)`, which copies up to `maxReturnBytes` of return data — so a return
buffer, and therefore a `memory_cost` term, is part of the deployed idiom. The specific
buffer sizes below are measured boundaries, **not** witnessed OffRamp configurations
(INFERRED that some deployment uses a buffer that large; the threshold itself is
CHECKED).

## Why the 5,000 is the whole invariant

`calculate_message_call_gas` (amsterdam/vm/gas.py:801-843) computes the child's grant as

```text
gas = min(requested, max_message_call_gas(gas_left - memory_cost - extra_gas))
max_message_call_gas(g) = g - g // 64                      amsterdam/vm/gas.py:861
```

Write `c` for everything the frame spends between its `gas()` reading and the moment the
grant is computed: the prediction arithmetic itself, plus `extra_gas` (account access,
value transfer, EIP-7702 delegation resolution), plus `memory_cost`. Then

```text
clamp         = (g - c) * 63/64
pre-check     = gasLimit < (g - S) * 63/64         with S = GAS_FOR_CALL_EXACT_CHECK
full delivery <=> gasLimit <= clamp
              <=> S >= c
```

So **the pre-check is sound exactly when `c <= 5,000`**, and `c` is not a constant — it
is composed per call shape, the same way EIP-2780 decomposes the intrinsic cost. That is
why both test groups parametrise over shape rather than asserting one number.

## Measurements

Instrument: `tests/tools/test_cls5_prediction_probe.py`. Its failures *are* the
measurement; each probe stores one quantity and asserts the slot is `0`, so the failure
prints the value. `gas_limit = 3,000,000`, `state_gas_reservoir = 0`.

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/instruments --from Amsterdam --until Amsterdam \
    -k "cls5 and state_test and delta and cold_zero_value" \
    --output /tmp/p5 -q --tb=line -p no:cacheprovider
```

### `delta` — the raw prediction gap, with the clamp binding

`delta = (g - g/64) - child_reported_gas`, the child forwarded `2**32` so the clamp
always binds. `delta ≈ floor(c * 63/64) + 2`. CHECKED.

```text
shape                   Berlin   London   Cancun   Prague   Osaka   Amsterdam
warm_zero_value            164      164      164      164     164         164
cold_zero_value          2,626    2,626    2,626    2,626   2,626       3,019
cold_retbuf_4kb          3,029        -        -    3,029   3,029       3,423
cold_retbuf_16kb         4,638        -        -    4,638   4,638       5,031
cold_with_value          9,185    9,185    9,185    9,185   9,185      11,843
delegated_zero_value       n/a      n/a      n/a    5,185   5,185       5,972
                              threshold the deployed constant sets: 5,000
```

`n/a` = EIP-7702 does not exist on that fork. `-` = not measured (the two return-buffer
shapes were swept on Berlin, Prague, Osaka and Amsterdam only).

### `shortfall` — the deployed pre-check, measured directly

`shortfall = gasLimit - child_reported_gas` where `gasLimit` is the largest value
passing `(g-5000) - (g-5000)/64 > gasLimit`. **`2` means full delivery** — the 2 is the
child's own `GAS` opcode.

```text
shape                   Berlin   Prague   Osaka   Amsterdam   verdict
warm_zero_value              2        2       2           2   sound on every fork
cold_zero_value              2        2       2           2   sound on every fork
cold_retbuf_4kb              2        2       2           2   sound on every fork
cold_retbuf_16kb             2        2       2         135   SOUND to Osaka, BREAKS at Amsterdam
cold_with_value          4,289    4,289   4,289       6,946   unsound on every fork
delegated_zero_value       n/a      289     289       1,076   unsound wherever EIP-7702 exists
```

The two probes are independent and agree in every measured cell: each shape with
`delta < 5,000` delivers in full, each shape with `delta > 5,000` is short. CHECKED.

### Three findings this produced

1. **The 5,000 is exactly sufficient for the shape a deployed oracle network actually calls.** Zero
   value, no delegation, no return buffer: sound Berlin → Amsterdam, with the cold
   account access consuming the largest single share of the slack (3,019 of 5,000 at
   Amsterdam, 2,626 before it).

2. **It is insufficient for a value-bearing call (4,287 gas short, 6,944 at Amsterdam)
   and for an EIP-7702 delegated target (287 gas short, 1,074 at Amsterdam).** The
   delegated case is the interesting one: resolving the delegation adds a *second* cold
   account access to `extra_gas`, a call shape that did not exist when the 5,000 was
   chosen. Both gaps widened at Amsterdam — the value case because
   `CALL_VALUE = ACCOUNT_WRITE + CALL_STIPEND` folded the stipend into the charge
   (gas.py:86), the delegated case because EIP-8038 raised `COLD_ACCOUNT_ACCESS`.

3. **Amsterdam is the first fork on which the deployed constant is insufficient for a
   16 KiB return buffer.** `5,031 - 4,638 = 393 = floor(400 * 63/64)` — precisely the
   EIP-8038 `COLD_ACCOUNT_ACCESS` rise of 400 propagated through the clamp. The derived
   figure and the measured figure agree to the gas, which is why both are CHECKED rather
   than one inferred from the other. Measured crossing points for the buffer size:
   ~16.1 KiB at Amsterdam, ~18.6 KiB before it (INFERRED from the quadratic memory
   term; the 16 KiB bracket itself is CHECKED).

## Tests

| test | shapes | asserts |
|---|---|---|
| `test_exact_gas_precheck_honours_the_promised_limit` | warm, cold, 4 KiB buffer | `limit_honoured = 1`, Berlin→Amsterdam |
| `test_exact_gas_precheck_is_short_on_a_value_bearing_call` | value | `limit_honoured = 0` |
| `test_exact_gas_precheck_is_short_on_a_delegated_target` | EIP-7702 | `limit_honoured = 0`, from Prague |
| `test_exact_gas_precheck_survives_a_16kb_return_buffer` | 16 KiB | `limit_honoured = 1`, Berlin→Osaka |
| `test_exact_gas_precheck_is_short_on_a_16kb_return_buffer` | 16 KiB | `limit_honoured = 0`, from Amsterdam |
| `test_forwarding_prediction_agrees_with_delivery` | warm, cold, 4 KiB, value | `not_over_delivered = 1`; `within_deployed_slack` per shape |
| `test_forwarding_prediction_ignores_the_state_gas_reservoir` | cold + one-slot reservoir | both markers = 1, from Amsterdam |

The two groups are sensitive in **opposite** directions, which is why both exist:

- `limit_honoured` fails when the retention fraction *tightens* or when
  `extra_gas` / `memory_cost` *grows*.
- `not_over_delivered` is a sign test on `prediction >= delivered`, so it fails when the
  retention fraction *loosens* — including `63/64 -> 127/128`, which no previously proven
  archetype in this corpus could see.

Expectations of `0` are pinned violations, not staleness. Each is half of a measured
pair: if a later fork restores the headroom, the `0` test fails and its partner starts
applying again, which is the signal we want rather than silence.

## Mutation results

```bash
cd /home/devops/toni/datanalysis/eip-8037/patterns
python3 tools/mutate.py -k "retention-" --md          # unrestricted
python3 tools/mutate.py -k "reservoir-" --md          # unrestricted
python3 tools/mutate.py -k cold-account --archetype forwarding
```

Counts are fixtures: test cases x 3 fixture formats. `forwarding_prediction` has 11 test
cases at Amsterdam, so `DET(21)` is 7 of them.

```text
unrestricted run, all 20 archetype directories; only the columns that moved are shown

mutation             depth_  forwarding_  reservoir_  retained_  the other
                     forwar. prediction   allocation  epilogue   16 archetypes
(baseline)           pass(42) pass(33)    pass(30)    pass(3)    all pass
retention-32         DET(15)  DET(21)     DET(6)      survives   all survive
retention-128        DET(12)  DET(21)     DET(3)      survives   all survive
retention-256        DET(18)  DET(21)     DET(3)      DET(3)     all survive
retention-osaka-256  DET(15)  DET(15)     n/a         survives   all survive
cold-account-6000    survives DET(15)     --          --         (restricted run)
cold-account-2600    survives DET(3)      --          --         (restricted run)
```

`n/a` = no test selected (`reservoir_allocation` is `valid_from("EIP8037")`, so an
Osaka-fork mutation selects nothing and the harness reports `UNTRUSTWORTHY` rather than
reading "no tests ran" as a pass).

**`retention-128` and `retention-32` are detected by these three classes and by nothing
else in the corpus.** `MUTATION-MATRIX.md` point 4 records `retention-128` as surviving
every proven archetype, correctly: keeping back `avail // 128` of a 2**24 budget is still
~131,072, above the ~110,026 a slot needs, so no *survival* test can see it. These classes
assert *agreement* and a *ratio* instead, so any change to the fraction shows regardless
of magnitude. `retention-256` is the expected overlap with `retained_epilogue`, which is
the one existing archetype that sees the divisor at all.

Which 7 of 11 fire under `retention-128`, and which 4 do not, is itself a check on the
design: the three `honours_the_promised_limit` params survive (a bigger clamp still
delivers in full), `is_short_on_a_value_bearing_call` survives (the clamp now exceeds
`gasLimit`, so the 2,300 stipend makes the child *over*-delivered, which trips the same
bound), and the four `agrees_with_delivery` params, the two remaining `is_short` arms and
the reservoir test all flip.

- **`retention-osaka-256`** (my mutation, `"fork": "Osaka"`) exists because an
  Amsterdam-only mutation never selects a `valid_until("Osaka")` test. It validates the
  pre-Amsterdam arm of the 16 KiB pair.
- **`cold-account-2600`** (another agent's mutation: revert EIP-8038's
  `COLD_ACCOUNT_ACCESS` rise) is detected by exactly 3 fixtures — the
  `is_short_on_a_16kb_return_buffer` test. That is the fork-split pair working as a
  two-sided bracket: undo the rise and the Amsterdam-side violation disappears.
- **`cold-account-6000` survives `depth_forwarding`**, which is the specificity result:
  a self-call chain warms its own address after the first hop, so `extra_gas` barely
  moves. When this class alone goes red, the cause is `extra_gas` or `memory_cost`, not
  the retention fraction.
- **`gas-reports-reservoir` survives, and the reason is worth recording** (another
  agent owns that mutation). If `GAS` returned `gas_left + reservoir`, the parent's
  prediction would be inflated by ~`reservoir * 63/64` — but the child receives the
  *entire* reservoir (class #16), so the child's own `GAS` reading is inflated by the
  full reservoir and the two inflations cancel to within `reservoir / 64`. A
  cross-boundary agreement test structurally cannot see this mutation; detecting it needs
  a single-frame test that compares `GAS` against something outside the gas system.

## Clean negative: the unclamped branch of `calculate_message_call_gas` is not testable

```python
if gas_left < extra_gas + memory_cost:
    return MessageCallGas(gas + extra_gas, gas + call_stipend)   # no 63/64 clamp
```
`amsterdam/vm/gas.py:838`. This looked like the sharpest possible canary for class #5 —
a path on which the retention rule does not apply at all. It cannot be tested, and the
reason is arithmetic rather than a gap in the harness.

**Reachability, per opcode (CHECKED, read at the pinned commit).** At Amsterdam, `call`
charges `extra_gas` and the memory cost *before* computing the grant and then passes
`memory_cost=GasCosts.ZERO, extra_gas=GasCosts.ZERO`
(`instructions/system.py:551-556`), so the condition becomes `gas_left < 0` and the
branch is **dead** for `CALL`. `CALLCODE`, `DELEGATECALL` and `STATICCALL`
(`system.py:666, 847, 950`) still pass the real terms, as do all four opcodes on
Berlin → Osaka, so there the branch *is* reachable.

**Observability (CHECKED).** Every reachable site is immediately followed by

```python
charge_gas(evm, message_call_gas.cost + extend_memory.cost)
```

with `cost = gas + extra_gas`. Writing `L` for `gas_left`, `E` for `extra_gas`, `M` for
`memory_cost` and `r >= 0` for the requested gas, the branch is taken only when
`L < E + M`, and the charge is then `r + E + M >= E + M > L`, so `charge_gas` raises
`OutOfGasError` **unconditionally**. The frame halts before the unclamped grant can reach
a child, so no committed effect can distinguish this path from any other out-of-gas.

A test asserting on it would be asserting on a plain OOG. Recorded here as a result, not
omitted: the branch is unreachable-in-effect on every fork Berlin → Amsterdam, and dead
code for `CALL` at Amsterdam specifically.

## Scaffolding audit

Per the standing caution that any literal gas operand is itself a frozen budget:

- `FORWARD_EVERYTHING = 2**32` is deliberately above every clamp; it is not a budget.
- `PARENT_GAS = 3,000,000` must cover the caller's two fresh slots after the call:
  220,048 at Amsterdam against ~2.98M available, 13x headroom.
- `FULL_DELIVERY_BOUND = 64` is a discriminator between "full delivery" (shortfall 2)
  and "short" (measured 287 … 6,944), chosen with two orders of magnitude of separation
  on each side.
- The reservoir test sets **no** `gas_limit`: EIP-8037 defines the reservoir as the part
  of `tx.gas` above `TX_MAX_GAS_LIMIT`, so passing both silently yields a zero reservoir
  and tests nothing. This cost an hour; see `allocate_evm_gas`, amsterdam/vm/gas.py:1105.
