# Archetype 21: return-data pass-through fidelity (revert bubbling)

**Invariant.** A failed child's revert payload reaches the caller's caller verbatim —
same bytes, same length.

**Deployed witness — the largest in the corpus.** L2 measured the bubbling shape at
**723,118 distinct runtime code hashes across 4,755,135 addresses**, FP 0.0, plus a
further 76,218 runtimes of `proxy return-data pass-through`. Every `try/catch` that
inspects a custom error, every proxy forwarding a revert reason, and every router
attributing a failure to a specific leg depends on it.

**Two rules hold it up, so there are two arms**, and the mutation result shows they are
genuinely independent:

```text
mutation                 returndata_fidelity   what it proves
returndatasize-halved    DETECTED(12)          semantics: every test fails
rdcopy-per-word-2000     DETECTED(3)           cost: only the frozen-budget arm fails
```

1. **Semantics** — `RETURNDATASIZE`/`RETURNDATACOPY` expose the payload, and `REVERT` of
   that buffer propagates it unchanged. No gas involved. Mutating `RETURNDATASIZE` to
   under-report breaks all 12 tests.
2. **Cost** — bubbling is only possible if the frame can afford the memory expansion and
   the copy: `OPCODE_RETURNDATACOPY_PER_WORD = 3` (`vm/gas.py:235`) plus memory expansion
   at `MEMORY_PER_WORD = 3` (`vm/gas.py:94`) with a quadratic term. Raising the copy cost
   to 2,000/word makes a 4 KiB reason cost 256,000 — past the frozen 200,000 a deployed
   proxy's caller forwards — and only that arm fails.

**Why both the head word and the exact size are asserted.** Asserting only the size would
miss a zeroed buffer; asserting only the head would miss a truncation. The payload leads
with a distinctive `0xDEADBEEF` so a degraded bubble is distinguishable from a legitimate
empty revert.

**The failure mode is silent degradation, not an error.** When the bubble cannot be
afforded, the proxy reverts with *nothing* and the observer misattributes the failure —
the call still reverts, so no monitoring notices, but the reason is gone. For a router
that selects a fallback path based on the error, that is a behaviour change with no
signal.

**Payload sizes** are parametrised over the three real shapes: one word (a bare selector
or `Error(string)` head), 128 bytes (a custom error with arguments), and 4 KiB (a long
reason string) — the last being where the quadratic memory term starts to matter.

**Reproduce**

```bash
cd engine/eels
./.venv/bin/fill ../../wave1/returndata_fidelity --until Amsterdam \
    --output /tmp/rdf -q -p no:cacheprovider          # 88 passed
cd ../../patterns
python3 tools/mutate.py -k returndatasize --archetype returndata_fidelity
python3 tools/mutate.py -k rdcopy        --archetype returndata_fidelity
```

**What a failure means.** Either return-data semantics changed, or copying a revert
reason stopped fitting in the budgets deployed proxies forward. In the second case,
4.76 million addresses' worth of error propagation silently starts losing reasons.
