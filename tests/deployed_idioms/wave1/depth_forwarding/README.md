# Class #6 — compounded depth forwarding

**The invariant.** The leaf of a depth-*n* chain of `call(gas(), ...)` hops runs on
roughly `(63/64)**n` of the budget the root frame had, and it still completes its work.

**What a failure means.** Either the deepest frame of a realistic call chain no longer
completes, or the fraction each hop keeps back has changed.

## Deployed witness

L5 measured **38,325 instances across 142 distinct runtimes** of `call(gas(), ...)`
chains at depth. The idiom is structural rather than library-specific: proxy →
implementation → router → pool → hook stacks, relayer stacks, and diamond/facet
dispatch all build them. No gas literal appears anywhere in the shape, which is why a
frozen-budget test cannot express this class: the budget at the leaf is a pure function
of the retention fraction and the chain's length.

```text
forwarding   gas = min(requested, max_message_call_gas(gas_left - memory_cost - extra_gas))
             max_message_call_gas(g) = g - g // 64          amsterdam/vm/gas.py:861
```

## The shape

One self-recursive contract; every frame is the same address, so the leaf's writes land
in one account the test asserts on and intermediate frames write nothing. Calldata
carries two words down the chain: the hops remaining, and the **root frame's `GAS`
reading**, forwarded unchanged. The leaf therefore has both its own reading and the
root's, and can compare them *as a ratio* — with no gas literal involved anywhere.

Two markers, written by the leaf:

```text
leaf_committed         1   the deepest frame created a storage slot that did not exist
compounded_below_half  (leaf_gas * 2 < root_gas)
```

`hops` counts `CALL` hops below the root's reading, so a `hops`-param chain is
`hops` nested frames under the root contract.

## Measurements

Instrument: `tests/tools/test_cls6_depth_probe.py`. The leaf stores
`10000 * leaf_gas / root_gas` and the probe asserts the slot is `0`, so each failure
prints the measured basis-point ratio. A *passing* probe param means the leaf never ran.

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/instruments --from Amsterdam --until Amsterdam \
    -k "cls6 and state_test and hops_44]" --output /tmp/p6 -q --tb=line \
    -p no:cacheprovider
```

`gas_limit = 4,000,000`, `state_gas_reservoir = 0`. **Measured identical, to the basis
point, on Berlin, Osaka and Amsterdam** for every depth at which the leaf commits — the
compounding law is fork-stable, so the ratio marker needs no fork split.

```text
hops   measured bp   (63/64)**hops bp   deficit   marker
   1         9,836              9,844         8        0
   2         9,682              9,690         8        0
   4         9,380              9,389         9        0
   8         8,806              8,816        10        0
  16         7,760              7,773        13        0
  32         6,025              6,041        16        0
  40         5,308              5,326        18        0
  43         5,061              5,080        19        0
  44         4,982              5,001        19        1   <- measured crossing
  45         4,904              4,923        19        1   <- ideal crossing
  48         4,676              4,696        20        1
  64         3,627              3,650        23        1
  96         2,179              2,205        26        1
 128         1,304              1,332        28        1
 176           596                626        30        1
 180           558                587                  1
 184           522                552                  1
```

`ln 2 / ln(64/63) = 44.014`, so **45** is the first integer power of `63/64` strictly
below one half: `(63/64)**44 = 5,001 bp` clears one half by a single basis point.
**The measured crossing is 44**, one hop earlier, because each hop also pays its own
per-frame cost and the resulting 19 bp deficit at that depth is larger than the 1 bp of
ideal headroom. CHECKED, and the `deficit` column is the internal cross-check: it grows
smoothly and monotonically with depth, exactly as a constant per-frame overhead
compounding predicts (~148 gas per hop effective at this budget; the self-address is warm
after the first hop).

Sensitivity of each side, stated precisely because the margins are small:

```text
hops=44 marker 1   18 bp below the threshold. Flips if the fraction LOOSENS, and also
                   if per-frame cost were cut by ~172 gas/hop -- i.e. essentially
                   removed. Not safe against an arbitrary reprice; safe against any
                   cost *increase*, which only deepens the deficit.
hops=43 marker 0   61 bp above the threshold. The cost-sensitive side: a per-frame cost
                   rise of ~3x would flip it.
hops=40 / 48       the same statement with ~6% of margin on each side.
```

Keeping all four is deliberate: a failure pattern then distinguishes "the divisor moved"
(40 or 48 flips) from "per-frame cost drifted" (only 43 or 44 flips).

### The cliff, and that EIP-8037 moved it

Same budget, leaf creating two fresh slots:

```text
hops    Berlin..Osaka            Amsterdam
176     commits (596 bp)         commits (596 bp)
180     commits (558 bp)         commits (558 bp)
184     commits (522 bp)         commits (522 bp)
188     commits (488 bp)         LEAF DEAD
192     commits (456 bp)         LEAF DEAD
256     commits (147 bp)         LEAF DEAD
320     LEAF DEAD                LEAF DEAD
```

The compounded budget is identical on every fork. The leaf's *work* is not: two fresh
slots cost `2 x 22,100 = 44,200` through Osaka and `2 x 110,020 = 220,040` at Amsterdam
(plus the leaf's own arithmetic).
So **EIP-8037 shortened the maximum useful forwarding chain for a fixed budget, from
beyond 256 hops to between 184 and 187.** CHECKED, at `gas_limit = 4,000,000`.

## Tests

| test | params | asserts |
|---|---|---|
| `test_depth_chain_leaf_commits` | hops 1, 2, 4, 8, 16, 32, 40, 43, 44, 48, 64, 96, 128 | `leaf_committed = 1`; `compounded_below_half` per the table |
| `test_depth_cliff_leaf_commits_at_192_hops` | 192 | leaf commits, Berlin→Osaka |
| `test_depth_cliff_leaf_dies_at_192_hops_from_eip8037` | 192 | leaf does not commit, from Amsterdam |

The param table of the first test **is** the compounding law, and it is two-sided: the
`0` entries fail when the fraction tightens, the `1` entries when it loosens.

`ROOT_GAS = 4,000,000` is part of the measurement, not a free parameter — it fixes where
the cliff is. Do not change it without re-running the probe.

## Mutation results

```bash
cd /home/devops/toni/datanalysis/eip-8037/patterns
python3 tools/mutate.py -k "retention-" --md          # unrestricted
python3 tools/mutate.py -k cold-account --archetype depth_forwarding
```

Counts are fixtures: test cases x 3 fixture formats. `depth_forwarding` has 14 test cases
at Amsterdam (13 depth params plus the Amsterdam cliff arm) and 14 at Osaka (the pre-8037
cliff arm replaces it).

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

- **`retention-128`** survives the *survival* marker correctly — a leaf given more gas
  still commits — and is caught by `compounded_below_half`, because
  `(127/128)**48 = 6,863 bp` is above one half where `(63/64)**48 = 4,676 bp` is below.
  The crossing depth moves 44 → 89, so params 44, 48, 64 and 96 flip: DET(12).
- **`retention-256`** moves the crossing to 178, so more params flip: DETECTED(18) vs
  DETECTED(12).
- **`retention-32`** is the tightening direction (my mutation; `core-gas.json` only
  loosens). The crossing moves 44 → 22, so the 32, 40 and 43 params flip on the ratio
  marker, and 96 and 128 flip on the survival marker because the leaf no longer reaches
  220,040: DET(15), both markers firing at once.
- **`cold-account-6000` survives**, correctly and informatively: after the first hop the
  self-address is warm, so a cold-access reprice barely touches this chain. That is the
  specificity result — when `forwarding_prediction` alone goes red the cause is
  `extra_gas`, and when both go red it is the retention fraction.

## Scaffolding audit

- The compounding marker uses `MUL(leaf_gas, 2)` — a pure ratio. No gas literal.
- `ROOT_GAS = 4,000,000` must leave the leaf enough for two fresh slots at the deepest
  asserted param: at 128 hops the leaf holds 1,304 bp ≈ 518,000 gas against ~220,040
  needed, 2.35x headroom. That is the tightest asserted param and it is deliberate — the
  128-hop param is a loose survival canary, the 43/44 pair is the tight one.
- The 192-hop cliff pair's pre-8037 arm needs 44,200 and has ~181,000, 4x headroom.
