# Archetype 4: retained-gas epilogue survival (the 63/64 rule)

**Invariant.** The gas retained by the 63/64 rule covers the caller's own post-call work.

**Why nothing else can catch it.** `call(gas(), ...)` forwards all-but-1/64:
`gas = min(requested, max_message_call_gas(gas_left - memory_cost - extra_gas))` with
`max_message_call_gas(g) = g - g // 64` (`amsterdam/vm/gas.py:861`). A caller that
forwards everything still depends on the retained `avail // 64` funding its epilogue —
releasing a reentrancy lock, emitting, recording a result. **This shape contains no gas
literal anywhere**: the budget is implicit in the retention fraction, so a frozen-budget
test (archetype 1) is structurally blind to it. The mutation matrix confirms this — A4 is
the **only** archetype that detects `retention-256`.

**Deployed witness.** L4's `retention-6364` probe: **245,595 mainnet addresses from 183
source files**, FP **0/18** hand-validated — a 1,342× spread between the file count and
the address count, which is why the counting unit must always be stated. L5 independently
found 239 transactions across 77 runtimes that commit *only* because of the rule.

**Reproduce**

```bash
cd engine/eels
./.venv/bin/fill ../../wave1/retained_epilogue --until Amsterdam \
    --output /tmp/re -q -p no:cacheprovider          # 22 passed
cd ../../patterns && python3 tools/mutate.py -k retention
```

**Mutation result** (CHECKED):

```text
mutation         retained_epilogue   note
retention-128    survives            CORRECT, not a hole: keeping back avail//128 of a
                                     2**24 budget is ~131,072, still above the measured
                                     ~110,026 needed to create one slot
retention-256    DETECTED(3)         ~65,536 retained, below the floor
cpsb-x2.6        DETECTED(3)         the epilogue's own state charge outgrows the retention
```

The graded pair is the point: *which* mutations fire measures how large the change was,
so this is a cliff-locator rather than a boolean.

**Design notes.** The child is `GasConsumer(gas=None, fork=fork)` — bytecode that runs out
of gas, so it consumes the entire forwarded allowance and returns 0. (`GasConsumer`
requires `fork=`; omitting it raises a `TypeError` that is easy to misread as a finding.)
The transaction pins `state_gas_reservoir=0`, so the epilogue's state charge must come out
of retained execution gas rather than a reservoir.

**What a failure means.** Either the retention fraction changed, or the cost of ordinary
post-call work outgrew it. Deployed callers that forward everything can no longer finish.
