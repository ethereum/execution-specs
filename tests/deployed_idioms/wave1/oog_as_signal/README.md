# Archetype 12: the two-sided OOG-as-signal capability probe

## The invariant

A caller asks an unknown contract a yes/no question under a hardcoded gas literal and
reads **any** failure as "no". The invariant is two-sided: a **capable** target completes
within the literal, **and** an incapable one fails within it.

A reprice can flip either direction and **neither reverts**, so the caller commits effects
down the wrong branch with nothing surfacing an error. A failure here means the probe
derived the wrong boolean about a target's capability and the transaction succeeded
anyway. For a deployed AMM that selects the legacy swap path on a modern converter at seven call
sites; for ERC-165 it silently disables every interface-gated hook on a compliant
implementation.

This is the quietest failure shape in the corpus.

## Deployed witnesses (CHECKED by lens L5, mainnet blocks 26,250,000–26,259,999)

**a deployed AMM** `<address withheld>` (Sourcify: `a deployed AMM`,
solc 0.4.26) asks converters `isV28OrHigher()` (selector `0xd260529c`) under a hard cap,
in assembly, with the bet written in its own comment — `a deployed AMM.sol:1398-1415`:

```solidity
success := staticcall(
    5000,          // isV28OrHigher consumes 190 gas, but just for extra safety
    _converter, add(data, 32), mload(data), ret, 32)
...
return success && ret[0] != 0;        // ANY failure => "not v28+", silently
```

Seven call sites branch on the result (lines 1120, 1134, 1282, 1293, 1305, 1313, 1364).
Both arms are witnessed in the same window (`lenses/L5/sql/23-ammprobe-isv28-probe.sql`):

```text
succeeded   2,529 frames  818 txs  93 targets  avg 293.9 gas of 5,000  max 1,155
reverted      459 frames  230 txs   6 targets  avg 1,430.8            max 1,823
OUT OF GAS     10 frames    6 txs   3 targets
```

Resolved against Sourcify: the succeeding targets are `StandardPoolConverter` (solc
0.6.12); the out-of-gas targets are a deployed AMM contract (solc 0.4.21/0.4.23) — genuine
pre-v28 converters. So the probe is currently **correct**, which is exactly why it belongs
in a regression corpus rather than a vulnerability report. The erosion is the useful
number: the comment claims 190 gas, the measured cost today is 293, so headroom has
already fallen from 26x to 17x purely from intervening repricings. Counting unit: probe
frames, 1 distinct runtime, 1,054 distinct transactions. FP rate 0 by construction — the
detector pins one caller, one literal and one selector, and both arms were confirmed in
source.

**ERC-165** `supportsInterface(bytes4)` at exactly **30,000** is the same shape with the
literal written into a *standard* — EIP-165 says it "must use less than 30,000 gas" and
its reference caller does `staticcall(30000, ...)` — so the constant is not one contract's
choice. L3 counts **163,050** implementing addresses;
`lenses/L5/sql/25-erc165-30000.sql` at the ceiling:

```text
reverted   17,657 calls / 15,723 txs / 197 callers / 63 targets
                                     max gas used 29,588   <- 412 from the ceiling
succeeded   9,904 calls /  2,575 txs / 166 callers / 262 targets
                                     max gas used  8,476
```

**64.36% of live `supportsInterface` calls fail.** Callers are already habituated to
reading failure as "unsupported", so a reprice converting a compliant implementation into
an unsupported one would surface nowhere.

## Why the second arm is not hypothetical

The direction every gas catalogue forgets is a reprice that makes work **cheaper**, which
is what flips an incapable target into appearing capable. It is witnessed: of the fifteen
gas constants that changed value across the fifteen mainnet forks, **five moved down**,
and EIP-1108 cut `PRECOMPILE_ECMUL` 40,000 → 6,000 — a **6.7x reduction** — along with
`ECADD` 500 → 150 and `ECPAIRING_BASE` 100,000 → 45,000. A target whose work sits just
over a literal is precisely what such a cut converts into a false "yes".

## Measurement

Instrument: `tests/tools/test_capability_arms_probe.py`. Its failures are the measurement;
the passing `answer_N` param names the boolean the probe really derives.

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
for F in Berlin London Cancun Prague Osaka Amsterdam; do
  for T in overrun_2 overrun_3; do
    ./.venv/bin/fill ../../wave1/instruments --from $F --until $F \
      -k "probe_answer and state_test and target_$T-literal_5000-answer_1" \
      --output /tmp/p12-$F-$T -q --tb=no -p no:cacheprovider; done
  for T in overrun_14 overrun_15; do
    ./.venv/bin/fill ../../wave1/instruments --from $F --until $F \
      -k "probe_answer and state_test and target_$T-literal_30000-answer_1" \
      --output /tmp/p12b-$F-$T -q --tb=no -p no:cacheprovider; done
done
```

Result (CHECKED, **identical on all six forks**):

```text
literal   cold reads that ANSWER   cold reads that DO NOT   boundary
 5,000    2   (~ 4,210 gas)        3   (~ 6,315 gas)         5,000
30,000    14  (~29,470 gas)        15  (~31,575 gas)        30,000
```

Each literal is pinned from both sides, so **any** reprice of a storage read moves at
least one arm. This is the tight two-sided form `wave1/frozen_budget/README.md` asks for
in its "Known limitation" section, achieved here without a per-fork bracket table because
the only repricing-sensitive mechanism in the targets — `COLD_STORAGE_ACCESS`, 2,100
(`amsterdam/vm/gas.py:78`) — is unchanged across the whole Berlin..Amsterdam range. The
six-fork identity above is the evidence for that, not an assumption.

### Headroom honesty

The two literals differ in how faithful the bracket is to production, and the difference
is reported rather than smoothed over:

- the **30,000** arm is **faithful**. L5's tightest witnessed success is 29,588 of 30,000;
  the modelled capable target costs ~29,470. Production breaks on the first reprice of a
  read, and so does this test.
- the **5,000** arm is **tighter than production**. a deployed AMM's live implementations use 294
  gas on average (max 1,155), so production breaks at roughly a 4x read reprice whereas
  this arm fires at ~1.2x. It is an early-warning canary at that literal, deliberately,
  and should not be read as a faithful break point for a deployed AMM specifically.

## Fill

```bash
./.venv/bin/fill ../../wave1/oog_as_signal --until Amsterdam \
    --output /tmp/c12 -q --tb=no -p no:cacheprovider
```

**44 passed**, exit 0 (CHECKED). Berlin through Amsterdam, one test, 2 params, 12 fixtures
across 3 formats.

## Mutation result

`python3 tools/mutate.py -k cls12-` (full 20-archetype matrix, CHECKED). Baseline
`pass(6)`.

| mutation | verdict | arm it kills |
|---|---|---|
| `cls12-cold-read-5000` (COLD_STORAGE_ACCESS 2100→5000, reads **dearer**) | **DETECTED(6)** | the capable arm, at both literals — a capable target stops answering, so "supported" reads as "unsupported" |
| `cls12-cold-read-700` (COLD_STORAGE_ACCESS 2100→700, reads **cheaper**, EIP-1108-scale) | **DETECTED(6)** | the overrunning arm, at both literals — an incapable target starts answering, so "unsupported" reads as "supported" |

Both directions are detected at both literals (6 = 2 params × 3 fixture formats, i.e. every
collected test), which is the property the archetype exists to establish: a one-sided test
would have survived one of these two rows.

`cls12-cold-read-700` is this archetype's distinctive contribution to the shared matrix.
Before it, **every mutation in the corpus made gas dearer**, and every
budget-sufficiency archetype survives a cheaper reprice by construction. Across the
20-archetype run it is survived by all six of the budget-sufficiency family —
`frozen_budget`, `stipend_fallback`, `gasleft_sufficiency`, `retained_epilogue`,
`depth_forwarding`, `forwarding_prediction` — plus `subfloor_budget` and
`gas_monotonicity`. The archetypes that do detect it are the ones asserting an exact
value or a two-sided bracket: `oog_as_signal`, `hardcoded_cost_equality`,
`state_gas_clamp`, `reservoir_allocation`, `refund_not_spendable`, `refund_cap` and
`block_vs_sender_accounting`.

## Design notes

- **Three targets, one transaction, four markers.** The capable arm, a legacy halting arm,
  an overrunning arm, and a `prober_survived` marker. The fourth matters: a capability
  probe that *reverts* is a different and safer pattern, because the error surfaces. The
  prober's survival is part of the invariant, so it is asserted rather than assumed.
- **The halting target is `INVALID`, not an infinite loop.** solc ≤ 0.4.12 compiles `throw`
  to `INVALID`, which consumes the whole frame and is reported by tracers as "Out of gas" —
  exactly what L5 observed against the three a deployed AMM contract targets. It is also
  deliberately *not* repricing-sensitive: an exceptional halt fails at any literal, so this
  arm pins halt semantics rather than a cost, and it is the overrunning arm that carries
  the cheaper-reprice sensitivity. An unbounded loop would have looked similar and taught
  nothing, because it can never flip.
- **`STATICCALL`**, as both witnesses use, which also guarantees the probed frame committed
  nothing — the only thing crossing the boundary is the answer.
- **The boolean is a deployed AMM's own**: `success && returned_word != 0`. A failed call leaves the
  zero-initialised return buffer untouched, so failure and a zero answer are the same
  committed value — which is the mechanism that makes the failure silent, modelled rather
  than described.
- **`Op.X(a, b)` emits `b` first**, so the call must be sequenced before either `MLOAD`.
  Folding it into the `AND` reads the return buffer before the call fills it.
