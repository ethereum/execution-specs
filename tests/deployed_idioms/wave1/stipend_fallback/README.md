# Archetype 7: stipend-funded fallback survival

**Invariant.** A value-bearing `transfer()`/`send()` recipient's fallback completes inside
the 2,300-gas stipend.

**Why it is the strongest historical case in the corpus.** EIP-1884 raised `SLOAD`
200 → 800 and broke deployed fallbacks on mainnet. L4 established that **EIP-1884 has zero
tests from any angle**: no `istanbul/eip1884*` directory exists, and
`generators.py:524` raises `ValueError("Gas tests before Berlin are not supported due to
CALL gas changes")`, so the generic gas-test harness refuses to cover it.

**Mechanism** (CHECKED):

```text
call_stipend = ZERO if value == 0 else call_stipend      amsterdam/vm/gas.py:838
CALL_STIPEND = 2300                                      amsterdam/vm/gas.py:84
COLD_STORAGE_ACCESS = 2100, unchanged since Berlin       amsterdam/vm/gas.py:78
COLD_ACCOUNT_ACCESS = 2600 Berlin..Osaka -> 3000 Amsterdam  (EIP-8038)
SSTORE sentry: check_gas(max(access_cost, CALL_STIPEND + 1))
                                        amsterdam/vm/instructions/storage.py:104
```

Two consequences worth stating:

- **The margin is ~195 gas.** A fallback doing one cold `SLOAD` costs about 2,105
  (key push + 2,100 + POP) against a 2,300 stipend. This is the tightest canary in the
  corpus, and it is tight by protocol design rather than by our choice.
- **Cold *account* access never fitted the stipend at all** — 2,600 before Amsterdam and
  3,000 after, both above 2,300. Only storage access fits.

**Observability.** Success is recorded by the *caller*, not the recipient: the SSTORE
sentry above makes an `SSTORE` impossible on a stipend-funded frame by construction, so
the recipient cannot write its own marker. The caller stores `CALL`'s return value.

**Reproduce**

```bash
cd engine/eels
./.venv/bin/fill ../../wave1/stipend_fallback --until Amsterdam \
    --output /tmp/sf -q -p no:cacheprovider          # 22 passed
cd ../../patterns && python3 tools/mutate.py -k 'sload-cold|stipend-2000'
```

**Mutation result** (CHECKED), with perfect specificity — no other archetype moves:

```text
mutation           stipend_fallback   every other archetype
sload-cold-2300    DETECTED(3)        survives     <- an EIP-1884-shaped access reprice
stipend-2000       DETECTED(3)        survives     <- the stipend itself shrinks
```

**What a failure means.** A reprice has pushed ordinary fallback work past the stipend.
Historically this bricked `transfer()` to a large class of deployed recipients; it is the
canonical "a reprice broke real contracts" event and the corpus's reason to exist.
