# Archetype: unassigned-precompile identity (candidate class #28)

**Invariant.** An address holding neither code nor a precompile answers a
`CALL` the way every empty account does — the call **succeeds** (pushes 1)
and leaves **zero-length return data** — and deployed code uses exactly that
to decide whether a precompile exists yet. Assigning a precompile to the
address changes the answer while **moving no gas rule at all**.

**Why it is not an existing class.** The 26 catalogued classes are either
gas-shaped (#1–#20) or about the meaning of *code*, a *caller*, or an
*address derivation* (#21–#25). This one is about what an **address** is, on
the only channel that can see it. In particular:

| class | instrument | why it cannot reach this |
|---|---|---|
| #22 code-presence identity | `EXTCODESIZE` / `EXTCODEHASH` | measured `0` for a live precompile, for one assigned at Osaka, and for one never assigned — on all six forks |
| #12 two-sided OOG probe | a frozen gas literal | here the literal is `gas()`; no price moved |
| #27 environment-field semantics | what a *field* reports | this is what an *address* is |

The sibling result in the opcode space is
`expansion/tests/undefined_opcode_halt/` (an undefined byte becoming an
instruction). Different rule, different mechanism (`InvalidOpcode` halt vs
the empty-account call convention), different observable — no overlap.

## Deployed witness, with address

**a widely used contract library `utils/cryptography/P256.sol`**, functions
`verify` / `verifyNative` / `_tryVerifyNative` / `_rip7212`.

```text
counting unit: distinct mainnet addresses whose verified compilation contains
               a source file matching the pattern (Sourcify v2 export)

`_tryVerifyNative`                35 files /  78 addresses /  62 runtimes
address literal 0x..0100 (any
spelling, incl. address(0x100))   58 files / 176 addresses / 155 runtimes
```

Hand-read exemplars:

```text
<address withheld>  @stdlib/.../P256.sol
<address withheld>  ChipAccount (that library P256.sol)
<address withheld>  MetaMask HybridDeleGator
                                            (P256SCLVerifierLib: "As mentioned
                                            in the 7212 RIP Spec, the
                                            P256Verify Precompile address is
                                            0x100")
<address withheld>  WebAuthnValidator (P256.sol)
<address withheld>  a widely used assembly library P256.sol ("Currently, we
                                            don't support EIP-7212's
                                            precompile at 0x0b as it has not
                                            been finalized")
<address withheld>  POH   (verifyNative -> revert
<address withheld>  ZUGZUG Errors.MissingPrecompile)
```

The library states the invariant and the reason it must be probed
behaviourally, in its own source:

```solidity
// Given precompiles have no bytecode (i.e. `address(0x100).code.length == 0`),
// we use a valid signature with small `r` and `s` values to check if the
// precompile is present.
// RIP-7212 precompiles return empty bytes when an invalid signature is passed,
// making it impossible to distinguish the presence of the precompile.
mstore(0x00, 0) // zero out scratch space in case the precompile doesn't return anything
if iszero(staticcall(gas(), 0x100, ptr, 0xa0, 0x00, 0x20)) { invalid() }
isValid := mload(0x00)
```

Two separate things are load-bearing: the call **must succeed** (otherwise
`invalid()` burns the caller's whole frame instead of falling back to
`verifySolidity`), and **empty return data must mean "absent"** (the result
is read from a pre-zeroed scratch word, so "no data" and "returned false"
are the same observation). `verifyNative` turns the same probe into
`revert Errors.MissingPrecompile(address(0x100))`, so a contract on that
path goes from always-reverting to working at Osaka.

**Caveat (SCHEMA §7.3).** The three population figures are *source-text
match* counts with **no measured false-positive rate**, so they must not
enter a registry record without hand validation. Six of them were hand-read
(above) and all six are true positives; one hit on the bare `0x..0100`
pattern was a false positive and is named for the record:
`<address withheld>` `chillapeclub_Burn` uses
`0x…0100` as a *burn address*, not a precompile probe. So the broad address
pattern is contaminated; the `_tryVerifyNative` pattern (35 / 78 / 62) is
the defensible one.

## Measurement commands

```bash
cd tests/deployed_idioms

# the bare-call channel, six forks
python3 tools/locked_fill.py \
  "$PWD/expansion/tests/tools/test_precompile_address_probe.py" \
  --from Berlin --until Berlin --output <unique-dir> -q -p no:cacheprovider

# that library's probe with that library's own wycheproof vector, plus code inspection
python3 tools/locked_fill.py \
  "$PWD/expansion/tests/tools/test_lib_p256_probe.py" \
  --from Osaka --until Osaka --output <unique-dir> -q -p no:cacheprovider

# the archetype itself
python3 tools/verify_corpus.py --wave expansion
python3 tools/mutate.py --wave expansion -k exp-pre \
  --archetype unassigned_precompile_identity

# the witness search: duckdb over the Sourcify v2 export, using
# lenses/L4/common.py's cached mainnet_sources.parquet + mainnet_srcmap.parquet
#   WITH hits AS (SELECT source_hash FROM sources
#                 WHERE regexp_matches(content, '_tryVerifyNative'))
#   SELECT COUNT(DISTINCT h.source_hash), COUNT(DISTINCT m.address),
#          COUNT(DISTINCT m.runtime_code_hash)
#   FROM hits h JOIN srcmap m USING (source_hash)
# and, for the broader (contaminated) address pattern:
#   '0x0{37}100\b|address\(0x100\)|uint160\(0x100\)|address\(256\)'
```

Both probes assert deliberately wrong sentinels, so **their failures are the
measurement** — the `KeyValueMismatchError` prints `want 0xdead, got 0x…`.
The observables are packed into one word per test because only the first
mismatching slot is reported.

## Measured (CHECKED)

`STATICCALL(50_000, addr, 0, 0, 0, 0)` → success / returndatasize /
caller-frame gas delta:

```text
addr    Berlin      London      Cancun      Prague      Osaka       Amsterdam
0x05    1/0/350     1/0/350     1/0/350     1/0/350     1/0/650     1/0/650
0x0a    1/0/2650    1/0/2650    0/0/50150   0/0/50150   0/0/50150   0/0/50150
0x0b    1/0/2650    1/0/2650    1/0/2650    0/0/50150   0/0/50150   0/0/50150
0x100   1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/7050    1/0/7050
0x12    1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/3050
0x200   1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/3050
```

Every cell decomposes exactly, which is why these are CHECKED rather than
inferred:

```text
2,650  = COLD_ACCOUNT_ACCESS 2,600 +     0 + 50 probe overhead
3,050  = COLD_ACCOUNT_ACCESS 3,000 +     0 + 50      (EIP-8038 raised it)
  350  = warm             100 + modexp floor 200 + 50
  650  = warm             100 + modexp floor 500 + 50 (EIP-7883)
7,050  = warm             100 + P256VERIFY 6,900 + 50
50,150 = warm             100 + 50,000 burned by an exceptional halt + 50
```

Three assignment events, **three different break shapes**:

* **0x0a at Cancun**, **0x0b at Prague** — the precompile rejects the probe's
  input length *before* `charge_gas` (`point_evaluation` raises
  `KZGProofError` on `len != 192`; `bls12_g1_add` raises `InvalidParameter`
  on `len != 256`), so `CALL` returns **0** and the whole forwarded budget
  is burned. Under that library's guard that is `invalid()`.
* **0x100 at Osaka** — `p256verify` charges 6,900 and returns *empty* output
  for anything it does not verify, so success stays **1** and
  returndatasize stays **0** for a malformed probe. Only a well-formed
  probe sees the change.

that library's own vector through that library's own probe:

```text
fork       success  returndatasize  isValid   what that library concludes
Berlin     1        0               0         absent -> verifySolidity
London     1        0               0         absent
Cancun     1        0               0         absent
Prague     1        0               0         absent
Osaka      1        32              1         present, signature valid
Amsterdam  1        32              1         present
```

**`success` is 1 on all six forks; only `RETURNDATASIZE` moves.** That is the
sharpest available statement about this surface: call success does not
distinguish a precompile from an empty account, so a contract treating "the
call succeeded" as "the operation was performed" is wrong on every fork,
before *and* after assignment.

Code inspection, all six forks, all three addresses:
`EXTCODESIZE = 0`, `EXTCODEHASH = 0`, `BALANCE = 0`. Identical for `0x05`
(a precompile since Byzantium), `0x100`, and `0x12`.

## Prior art — and a correction to my own first claim

**A first pass at this archetype claimed "nothing in `tests/` asserts what a
`CALL` to a not-yet-assigned precompile address returns". That claim is
false.** It is recorded here rather than quietly dropped. All three
assignment events, plus the warm/cold channel, have official coverage:

```text
tests/cancun/eip4844_blobs/test_point_evaluation_precompile.py:713
    test_precompile_before_fork         valid_at_transition_to("Cancun")
tests/prague/eip2537_bls_12_381_precompiles/test_bls12_precompiles_before_fork.py
    pytestmark                          valid_at_transition_to("Prague")
tests/osaka/eip7951_p256verify_precompiles/test_p256verify_before_fork.py
    test_precompile_before_fork         valid_at_transition_to("Osaka")
    docstring: "The call must succeed but the output must be empty."
tests/berlin/eip2929_gas_cost_increases/test_precompile_warming.py  (186 lines)
    the warm/cold channel, via BALANCE across a transition; even reaches 32
    addresses above the highest precompile
```

Both channels are therefore covered and **neither is rebuilt here**. That is
also why no "precompiles are not pre-warmed" mutation is registered in
`exp-precompile.json`: it would be an undetected row describing coverage
that exists elsewhere.

Five things those tests cannot state, which is what this archetype adds:

1. **The deployed idiom, not the bare call.** They assert `call_succeeds`
   and `expected_output` at the transaction level with each precompile's own
   vectors. None runs a presence probe *from inside a contract* and commits
   the boolean the contract derives. that library's probe has three features that
   carry the invariant and a bare call does not: the pre-zeroed scratch word
   (so "no data" and "returned false" are the same observation), the return
   buffer aliased onto that word, and the `invalid()` guard that destroys
   the caller's frame on failure. All three are reproduced.
2. **Scope.** Every official before-fork test is `valid_at_transition_to(X)`
   — it exists at exactly one fork boundary. These arms are
   `valid_from("Berlin")` with `valid_until("Shanghai")` or
   `valid_until("Prague")`: every fork on which the convention held. The
   never-assigned controls run through Amsterdam.
3. **Never-assigned addresses as the subject**, which pins the *convention*
   rather than one address's history. The warming test reaches such
   addresses but only via `BALANCE`, for warmth.
4. **The code-inspection blindness, asserted beside the call channel**, with
   a deployed-contract positive control. Nothing official states it, and it
   is what forces the behavioural probe to exist.
5. **Three assignment events in one archetype**, which is what reveals the
   three *different* break shapes. Each official suite tests its own EIP in
   isolation and cannot state the contrast.

And structurally: those tests derive gas from the fork
(`fork.transitions_to().gas_costs().PRECOMPILE_P256VERIFY`,
`gas_map[addr](len(input_data))`), so per `docs/COVERAGE-GAP.md` they cannot
fail under a reprice.

## Fill and mutation result

```text
fill, Berlin..Amsterdam, 6 tests, 3 fixture formats        75 passed   CHECKED
  (tests/tools excluded; command above)
baseline at Amsterdam                                      pass(12)   CHECKED
reference files restored, md5-verified, every run           OK        CHECKED
```

Detected (4 of the 28 `exp-pre-*` mutations; the other 24 target pricing or
admissibility and correctly survive here):

```text
exp-pre-unassign-p256verify      DETECTED(3)  0x100 made empty again at
                                              Amsterdam: that library's probe flips
                                              back to "absent"
exp-pre-assign-0x12              DETECTED(3)  the OPPOSITE direction -- an
                                              address asserted still-empty
                                              becomes a precompile
exp-pre-prague-assign-0x100      DETECTED(3)  reaches the valid_until("Prague")
                                              arm; the failed call trips that library's
                                              invalid() and discards the whole
                                              frame, so every slot vanishes
exp-pre-shanghai-assign-0x0a     DETECTED(3)  the ONLY mutation that reaches
                                              the all-unassigned arm, which
                                              is valid_until("Shanghai")
```

**None of the four changes a gas constant.** That is the same signature
`eoa_caller_identity` and `code_presence_identity` carry, and the cleanest
argument that this is a semantic class and not a pricing one. The last two
also show why fork-scoped mutations were necessary: an Amsterdam-only
mutation set leaves every `valid_until(...)` arm in this archetype
unprotected, and the matrix would have read "covered".

`exp-pre-p256-halts-on-malformed-length` **survives here and is detected by
`precompile_price_bracket` instead** — correctly, because this archetype's
P256 arms use that library's well-formed 160-byte vector while the price bracket uses
an empty input. The pair documents the channel: a malformed input is where
"success with empty output" lives, and a well-formed one is where
returndatasize appears.

## What a failure means

The contract answered the wrong question about an address. On an
`..._before_assignment` arm: a contract that should take its software
fallback takes the native path, or `invalid()`s and burns the caller's frame.
On an `..._after_assignment` arm: a contract that should use the precompile
keeps running a software implementation, or `verifyNative` keeps reverting.

**Fork-scoping is the product.** The `before` arms are `valid_until(...)` and
*would* fail if run on a later fork. That is the invariant being pinned, not
staleness — do not repair a failure by widening a fork window.
