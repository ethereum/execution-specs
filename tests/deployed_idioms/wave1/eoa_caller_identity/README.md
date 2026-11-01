# Archetype 25: caller identity as an EOA test

**Invariant.** `tx.origin == msg.sender` holds exactly when no frame that *rewrites the
caller* intervenes — flash-loan guards, anti-bot and anti-sandwich checks, "humans only"
mint gates all read it as "called directly by a wallet".

The wording matters and the measurement forced it. The naive statement — "exactly when no
contract frame intervenes" — is **already false**, and has been since Homestead, because
`DELEGATECALL` passes its own caller through. That is by design and every deployed proxy
depends on it, so it is pinned here as a control rather than reported as a break.

**This is the caller-side half of the break archetype 22 covers on the callee side.**

```text
EOA_DELEGATION_MARKER = b"\xef\x01\x00"                vm/eoa_delegation.py:36
  designator = 3-byte marker + 20-byte address = 23    vm/eoa_delegation.py:38
EXTCODESIZE: codesize = U256(len(code))                vm/instructions/environment.py:357
  -- raw length, NO delegation resolution
ORIGIN:  push(U256.from_be_bytes(evm.tx_env.origin))   vm/instructions/environment.py:107
  docstring, verbatim: "The origin address can only be an EOA."
CALLER:  push(U256.from_be_bytes(evm.caller))          vm/instructions/environment.py:130
DELEGATECALL passes caller=evm.caller                  vm/instructions/system.py:866
  -- the only call-like instruction that does. CALL (572), CALLCODE (687) and
     STATICCALL (969) all pass caller=evm.current_target, as does
     generic_create (140); generic_call (409) relays whatever it is handed.
```

So from Prague the two deployed "is this an EOA" idioms answer **differently for the same
account in the same block**: `code.length > 0` says contract, `tx.origin == msg.sender`
says wallet. Nothing reconciles them, and no repricing is involved in any of it — which is
why this class is in the semantic-identity family.

## Deployed witness

| detector | runtimes | addresses | FP | lens |
|---|---|---|---|---|
| `tx.origin == msg.sender` gate | 8,097 | 6,126 | 0.0 | L2 |
| closely related shape, independent sweep | 19,017 | 24,044 | — | L1 |

Counting unit: distinct runtime code hashes and distinct mainnet addresses, as stated by
L2. The two lenses disagree by ~2.3x on runtimes, which is expected — L1's shape is
related, not identical — and the smaller, FP-measured figure is the one used for ranking.

## Measured behaviour (CHECKED)

Instrument: `tests/tools/test_cls25_origin_probe.py`. Every observable is packed into one
slot, because `Storage` raises on its first mismatch and a multi-slot probe only ever
reveals its lowest unexpected slot.

```bash
cd tests/deployed_idioms
python3 tools/locked_fill.py tests/tools --from Amsterdam --until Amsterdam \
    -k "cls25 and state_test" --output /tmp/cls25 -q --tb=line -p no:cacheprovider
```

| call shape | `ORIGIN==CALLER` | `EXTCODESIZE(CALLER)` | `CALLER==tx.sender` |
|---|---|---|---|
| EOA → gate (direct) | **1** | 0 | 1 |
| EOA → relay –CALL→ gate | 0 | 35 (the relay) | 0 |
| EOA → entryPoint → account → gate | 0 | 35 (the account) | 0 |
| EOA → proxy –DELEGATECALL→ gate | **1** | 0 | 1 |
| 7702 self-sponsored, EOA's code → gate | **1** | **23** | 1 |
| 7702 sponsored by a relayer | 0 | **23** | 1 (= the signer) |

Two rows of that table are the result:

* **Row 5 is the break.** The gate answers "a wallet called me directly" for an account
  that is executing arbitrary contract code. Measured in the test: the delegated code
  calls the gate **twice in one transaction**, both calls pass, so a "one action per
  wallet per transaction" gate is a no-op and every flash-loan guard built on the same
  test is bypassable by any EOA that signs one authorization. This is the **false
  positive** direction.
* **Row 3 is the opposite failure, and it is live today.** Under ERC-4337 the bundler is
  the origin and the smart account is the sender, so the gate *rejects a real human*. The
  6,126 addresses carrying this gate exclude smart-account users outright. This is the
  **false negative** direction, and it needs no fork change at all.

Row 6 is the boundary that keeps row 5 honest: delegation alone is not enough, the
delegated EOA must also be the transaction's origin. Both 7702 rows still report 23, so
archetype 22's break is present in both while this archetype's break is present in only
one.

## Tests — 106 fill, Berlin → Amsterdam

114 tests collect; **106 fill**. The 8-test difference is not a skip in these tests: the
`blockchain_test_engine_from_state_test` format is only generated from Paris onward, so
the four Berlin-valid params yield 2 formats each on Berlin and London instead of 3
(verified with `fill --from Berlin --until London --collect-only`).

```text
test_origin_equals_caller_only_when_no_contract_frame_intervenes   3 params  (Berlin+)
test_a_delegatecall_proxy_keeps_the_caller_so_the_gate_still_passes 1        (Berlin+)
test_a_delegated_eoa_passes_the_eoa_gate_while_carrying_code       2 params  (Prague+)
```

Every gate instance also commits an **entry counter**. Without it, a gate that never ran
would leave zeros behind, and zero is the expected answer for two of the three arms of
the first test — the counter is what distinguishes "the gate said no" from "the gate was
never reached".

The 23 in the Prague test is asserted as an exact number. That is deliberate and allowed:
it is a semantic constant (`EOA_DELEGATION_MARKER` plus an address), not a cost, so
SCHEMA §4.1's prohibition on pinning gas numbers does not reach it. Archetype 22 makes the
same call for the same constant.

## Mutation result

```bash
cd tests/deployed_idioms
python3 tools/mutate.py -k cls25 --archetype eoa_caller_identity
python3 tools/mutate.py -k cls25-          # the specificity column
```

```text
(baseline)                              pass(18)
cls25-origin-is-the-current-caller      DETECTED(9)
cls25-caller-is-the-tx-origin           DETECTED(9)
cls25-delegatecall-rewrites-the-caller  DETECTED(3)
cls25-delegation-length-24              DETECTED(6)
```

Per test:

```text
cls25-origin-is-the-current-caller   ORIGIN -> evm.caller, so the equality is a tautology
cls25-caller-is-the-tx-origin        CALLER -> tx origin, the same equality from the other side
    both fire: no_contract_frame_intervenes[one_contract_frame, erc4337_entry_point]
               delegated_eoa[sponsored_by_a_relayer]
    both correctly leave alone: [direct_wallet_call] and delegated_eoa[self_sponsored],
    whose expected answer is 1 either way -- an equality cannot be falsified from the
    side where it already holds.
cls25-delegatecall-rewrites-the-caller
    delegatecall_proxy_keeps_the_caller          (its sole detector)
cls25-delegation-length-24
    delegated_eoa[self_sponsored, sponsored_by_a_relayer]
```

The equality is mutated **from both sides**, which is what INVARIANT-CLASSES.md's
"mutate in both directions" rule means for a semantic invariant: there is no cheaper or
dearer here, only "collapse the two readings together" and "pull them apart". The three
negative arms are the ones that can detect a collapse, and they do.

`cls25-delegation-length-24` makes `is_valid_delegation` stop recognising the 23-byte
designator `set_delegation` writes, so the delegation never resolves. It fires on both
7702 arms: the designator *format* is a single magic number that archetypes 22 and 25 both
hang off, and this mutation is the one that says so.

## Specificity

**All four `cls25-` mutations have exactly one detector**, over all 24 archetypes
(`python3 tools/mutate.py -k cls25- --md`; every baseline cell `pass`).

Run the other way — `python3 tools/mutate.py --archetype eoa_caller_identity`, all 61
mutations registered at the time of the run — this archetype **detects 5**, and the fifth
is the interesting one:

```text
cls25-origin-is-the-current-caller      9   mine
cls25-caller-is-the-tx-origin           9   mine
cls25-delegation-length-24              6   mine
cls25-delegatecall-rewrites-the-caller  3   mine
extcodesize-hides-delegation            6   the main session's, for archetype 22
```

**No gas mutation detects this archetype, and that is the correct result**, not a gap.
The corpus's 61 mutations are overwhelmingly gas-shaped, and nothing a reprice can do
changes what `ORIGIN` or `CALLER` reports. The only non-`cls25-` mutation that reaches
this archetype is the one other *semantic* mutation touching the same EIP-7702
designator. This is the second archetype in the corpus detected by exactly one foreign
mutation and no gas mutation at all (`code_presence_identity` is the first), and it is
the clearest demonstration that the semantic-identity family needed to exist.

`extcodesize-hides-delegation` previously had **exactly one detector** in
MUTATION-MATRIX.md's list of 19. It now has two, and the second is the caller-side
archetype: the Prague arms here assert `EXTCODESIZE(CALLER) == 23`, so repairing
`EXTCODESIZE` is visible from the caller's seat as well as the callee's. The two
archetypes together say that the 23-byte designator is load-bearing on **both** sides of
a call.

## What a failure means

Either `ORIGIN`/`CALLER` changed meaning — in which case 6,126 deployed access gates
changed behaviour with them — or the EIP-7702 designator format moved, and the
caller-side and callee-side identity idioms start disagreeing differently than they do
today.
