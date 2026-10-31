# Archetype 10: gas monotonicity across a call (M2 and M4)

**Invariant.** `gasleft()` after a call is no larger than before it, so `before - after`
is the gas consumed and cannot underflow.

**Deployed witness.** L4's `gas-delta` probe: **252,006 mainnet addresses from 2,499
source files**, FP **0/18** hand-validated. Safe's `gasUsed.sub(gasleft())` is the
canonical instance. Every gas meter and every gas-refunding relayer depends on this.

**Severity splits by compiler, and the quieter case is the worse one** (L4, and it matters
for ranking):

- solc ≥ 0.8 or SafeMath → the underflow **reverts**: a liveness failure.
- plain `-` under solc < 0.8 → it **wraps** to a value near 2²⁵⁶, and the relayer is
  reimbursed an astronomically wrong amount: a correctness and funds failure that
  surfaces nothing.

The second marker in each test (`SLOT_NO_WRAP`) pins exactly that case, using a
`1 << 128` discriminator — far above any real gas delta and far below the wrap, so it
separates the two without asserting a cost.

**Why there are four tests, not two.** EIP-8037 has **two distinct refund paths** and a
test can only reach one at a time:

```text
credit_state_gas_refund   LIFO: gas_left up to the spill, then reservoir
                          called from instructions/storage.py:151   => IN-FRAME (M2)
repay_state_gas_spill     reservoir -> gas_left, up to outstanding spill
                          called from vm/__init__.py:240            => CHILD MERGE (M4)
```

In a `DELEGATECALL` child the child's own spill is 0, so `from_gas_left` is already 0
there and the parent's `gas_left` only grows on merge. **The mutation matrix found this:**
on its first run `m2-no-inframe-refill` was detected by nothing, because the cross-frame
test reaches only M4. The same-frame set/clear pair was added to close it.

**Measured** (`tests/tools/test_monotonicity_probe.py`, CHECKED): `GT(g1, g2)` is 1 on
Berlin and Osaka, 0 on Amsterdam — both paths.

**Reproduce**

```bash
cd engine/eels
./.venv/bin/fill ../../wave1/gas_monotonicity --until Amsterdam \
    --output /tmp/gm -q -p no:cacheprovider          # 44 passed
cd ../../patterns && python3 tools/mutate.py -k m2-no-inframe-refill
cd ../../patterns && python3 tools/mutate.py -k m4-no-merge-repay
```

**Mutation result** (CHECKED), with perfect specificity:

```text
mutation               gas_monotonicity   every other archetype
m2-no-inframe-refill   DETECTED(3)        survives
m4-no-merge-repay      DETECTED(3)        survives
```

**Why the violation is pinned as well as the invariant.** The pre-8037 tests assert
monotonicity on the forks where it holds — which L4 established **no existing test does**;
only the Amsterdam violation is covered anywhere. Pinning both keeps the pair honest: if a
later fork restores monotonicity, the `valid_from("EIP8037")` tests fail and the
pre-8037 ones start applying again, which is the signal we want instead of silence.

**What a failure means.** The relationship between a frame's two `GAS` readings changed.
Every deployed gas meter is now computing a different number, and under solc < 8 it is
computing a wrapped one.
