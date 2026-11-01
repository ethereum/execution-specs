# Archetype: precompile input admissibility (candidate class #29)

**Invariant.** A contract passes a precompile an input whose size comes from
runtime values. What it relies on is not "the call is affordable" but "this
input is **admissible**". EIP-7823 (Osaka) gave `MODEXP` upper bounds: a
base, exponent or modulus declared longer than 1,024 bytes is now rejected,
where before it was computed.

The rejection happens **before `charge_gas`**
(`osaka/vm/precompiled_contracts/modexp.py:32-41`), so it is an exceptional
halt: `CALL` returns 0, the entire forwarded budget is burned, and the caller
cannot tell it apart from an out-of-gas.

```python
base_length = U256.from_be_bytes(buffer_read(data, U256(0), U256(32)))
if base_length > U256(1024):
    raise ExceptionalHalt("Mod-exp base length is too large")
```

## Why this is a distinct class, and the test that proves it

Every budget class in the catalogue — **#1** frozen-budget survival, **#12**
two-sided OOG probe, **#18** dynamic-cost affordability prediction — asks
*can the caller afford it?*, and each is satisfiable by raising the budget.
This one is not. `test_oversized_modexp_is_unaffordable_at_any_price`
forwards **2,000,000 gas, about 360x the pre-Osaka cost of the very same
call**, and it still fails, while its 1,024-byte neighbour succeeds on the
same budget. No price exists at which an inadmissible input succeeds, so:

* no affordability test can express the invariant, and
* no affordability fix can repair a deployed contract that hits it.

It is also distinct from #18 in the *direction of dependence*. #18's
contracts **size** an operation to fit a budget, so the hazard is a changed
coefficient and the error scales with size. Here the size is dictated by the
data (an RSA modulus, a VDF accumulator) and the hazard is a changed
**admissible set** — a cliff, not a slope.

## Deployed witness, stated honestly

**CHECKED.** Six mainnet-verified `BigNumber` / `BigNumbers` sources pass
`MODEXP` operands whose byte length comes from runtime values and impose
**no upper bound of their own**. The only length `require`s present are
32-byte alignment (`require(val.length % 32 == 0)`) and a *lower* bound
(`require(_size >= _byteLength, "Number too large to represent")`). Each of
the six was read by hand; the grep that found them and the hand read are
both reproduced in `/tmp` scratch scripts described under "Measurement
commands".

```text
counting unit: distinct mainnet addresses whose verified compilation contains
               a matching source file (Sourcify v2)
population:    6 files / 52 addresses / 48 runtimes

<address withheld>  ForexToken          (BigNumbers)
<address withheld>  Lottery             src/libraries/BigNumbers.sol
<address withheld>  PolicyProposals     contracts/VDF/BigNumber.sol
<address withheld>  VDFVerifier         contracts/VDF/BigNumber.sol
<address withheld>  FactoringChallenge  BigNumber.sol
<address withheld>  FactoringChallenge  BigNumber.sol
```

These libraries multiply via `(a*b) = ((a+b)**2 - (a-b)**2) / 4`, and the
modulus for each squaring comes from `_powModulus(a, e)`, which sets
`mod_index := a.bitlen * e` — so **the operand length doubles with every
multiplication, with no cap**. From a 512-byte operand one multiplication
reaches exactly 1,024 bytes (the new bound) and a second reaches 2,048
(rejected from Osaka). Two of the six are literally named
`FactoringChallenge` — contracts built to handle large RSA moduli — and two
are Eco Protocol's VDF verifier, which squares repeatedly over a large
modulus.

**INFERRED, not measured.** That a specific deployed call has in fact passed
more than 1,024 bytes. I have **no** transaction-level evidence for that and
do not claim it; I did not query XATU for modexp input lengths. What is
CHECKED is that nothing in these contracts prevents it, which is the
property a regression test can defend.

## Measurement commands

```bash
cd tests/deployed_idioms

# the shape probe: declared lengths vs success / returndatasize / gas
python3 tools/locked_fill.py \
  "$PWD/expansion/tests/tools/test_precompile_address_probe.py" \
  --from Prague --until Prague --output <unique-dir> -q -p no:cacheprovider
# ... repeat per fork; the probe asserts a 0xdead sentinel, so its
# failures ARE the measurement (packed: success<<64 | rds<<32 | gas_delta)

# the archetype
python3 tools/verify_corpus.py --wave expansion
python3 tools/mutate.py --wave expansion -k exp-pre \
  --archetype precompile_input_admissibility

# the witness search (duckdb over the Sourcify v2 export, via
# lenses/L4/common.py's cached mainnet_sources.parquet):
#   regexp_matches(content, '(?i)library BigNumbers?|struct BigNumber')
#   joined to mainnet_srcmap.parquet on source_hash
```

## Measured (CHECKED)

`success` / `returndatasize` / caller-frame gas delta, 2,000,000 forwarded:

```text
shape (base/exp/mod bytes)   Berlin..Prague        Osaka, Amsterdam
1024 /    0 /    1           1 / 1    /   6,488    1 / 1    /    33,795
1025 /    0 /    1           1 / 1    /   6,574    0 / 0    / 2,001,027
   1 /    0 / 1024           1 / 1024 /   6,488    1 / 1024 /    33,795
   1 /    0 / 1025           1 / 1025 /   6,574    0 / 0    / 2,001,027
   1 / 1024 /    1           1 / 1    /   3,672    1 / 1    /   254,979
   1 / 1025 /    1           1 / 1    /   3,675    0 / 0    / 2,001,027
```

Three facts this nails down:

1. **The bound is per field, and all three fields moved together.** 1,024
   accepted and 1,025 rejected for base, exponent *and* modulus.
2. **No gas rule caused it.** Pre-Osaka the rejected `1025/0/1` shape costs
   **5,547** gas: 6,574 minus 1,027 of probe overhead (warm access, memory
   expansion to the probe's scratch area, the probe's own opcodes) — and
   that 1,027 comes out **identical in all six rows**, which is what makes
   the subtraction trustworthy. It was never expensive; it is simply no
   longer allowed.
3. **The whole forwarded budget is burned.** 2,001,027 against 2,000,000
   forwarded. A caller with a frozen budget loses all of it and reads the
   result as an out-of-gas.

## Prior art: thorough — and most of this surface is already covered

**A first pass claimed the official suite "never states the pre-Osaka half".
That is wrong**, and the correction is kept here rather than dropped.
`tests/osaka/eip7823_modexp_upper_bounds/` (357 + 96 + 228 lines) covers:

```text
test_modexp_upper_bounds               valid_from("Osaka")
  all three fields at 1,024 accepted   base/exp/mod/base+mod "boundary"
  all three fields at 1,025 rejected   "excess_length_{base,exponent,modulus}"
  plus exp=1025 against 0 / 1024 / 1025-byte bases, 0xff exponents, ...
test_modexp_upper_bounds_fork_transition
                                       valid_at_transition_to("Osaka")
  blockchain_test at timestamps 14,999 / 15,000 / 15,001, with
  expected_results = [True, False, False] -- so the pre-fork SUCCESS of a
  1,025-byte base IS asserted, for the base field, at one boundary
test_eip_mainnet                       valid_at("Osaka"), mainnet
```

The honest residue, in order of value:

1. **`test_oversized_modexp_is_unaffordable_at_any_price` is new, and it is
   the assertion that defines the class.** Every official test derives
   `precompile_gas` from the fork and runs under `gas_limit=6_000_000`; none
   demonstrates that *no* budget suffices. Without that assertion,
   "inadmissible" is indistinguishable from "expensive" and the class
   collapses into #1/#12/#18.
2. **Per-field before-fork coverage across the whole pre-Osaka window.** The
   official before-fork assertion is one vector (base only) at one
   transition; these arms cover base, exponent *and* modulus on every fork
   Berlin→Prague, as `state_test`s rather than a transition
   `blockchain_test`.
3. **The 1,024-accepted side pinned from Berlin** rather than from Osaka.
   **Thin**, and labelled as such: before Osaka there is no bound to lower,
   so it only matters to a counterfactual fork that introduced a bound
   earlier than EIP-7823 did. The official `Spec.MAX_LENGTH_BYTES` is itself
   a literal (not fork-derived), so the official suite would also catch
   `exp-pre-modexp-bound-512` on Osaka and later.

**Verdict: the class is worth recording in `INVARIANT-CLASSES.md` — an
admissible-set change is a different kind of rule from a price, and the
catalogue has no entry for it — but the test surface was largely built
already, and saying so is the result rather than something to paper over.**

## Fill and mutation result

```text
fill, Berlin..Amsterdam, 4 tests, 3 fixture formats        50 passed   CHECKED
baseline at Amsterdam                                      pass(9)    CHECKED
reference files restored, md5-verified, every run           OK        CHECKED
```

Detected (5 of 28 `exp-pre-*`):

```text
exp-pre-modexp-bound-512               DETECTED(6)  TIGHTER: 1024 -> 512 on
                                                    all three fields
exp-pre-modexp-bound-2048              DETECTED(6)  LOOSER: 1024 -> 2048,
                                                    EIP-7823 half-repealed
exp-pre-modexp-base-bound-removed      DETECTED(6)  PER FIELD: base check
                                                    gone, other two kept
exp-pre-modexp-small-complexity-32     DETECTED(3)  incidental, see below
exp-pre-modexp-exponent-length-term-32 DETECTED(3)  incidental, see below
```

**Two-sidedness for a non-numeric rule comes from loosening as well as
restricting**, following class #23's precedent — `bound-2048` is the
loosening and it breaks the complementary arm from `bound-512`, so the
failure set says which direction the bound moved.

**Per-field discrimination, verified rather than assumed.** All three field
slots live in one test, so the failure *count* cannot separate them; the
*slot label* does. Running `exp-pre-modexp-base-bound-removed` alone gives:

```text
6 failed, 3 passed in 0.38s
KeyValueMismatchError: ... key 0x..00 (base_at_1025_is_rejected):
                           want 0x0 (dec:0), got 0x3 (dec:3)
KeyValueMismatchError: ... key 0x..01 (base_at_1025_fails_on_360x_its_old_cost):
                           want 0x0 (dec:0), got 0x3 (dec:3)
```

Only the **base** slots report; the exponent and modulus slots stay silent,
and `test_modexp_accepts_the_largest_permitted_operands` passes. `got 0x3`
decodes as success 1 with a 1-byte return, so the message names both
channels. A single-field test would have read "detected" while two bounds
stayed uncovered.

**Incidental price sensitivity, recorded rather than tuned away.** The arms
forward a frozen `AMPLE = 400_000`, and the 1,024-byte *exponent* shape
costs 253,952 at Osaka, so the two mutations that double the exponent
coefficient also break this archetype. That is a real property of the shape
— the budget literal is part of it — and the signature still discriminates:
an admissibility mutation moves the `*_at_1024` / `*_at_1025` slots, while a
coefficient mutation moves only the exponent slot **and** lights up
`precompile_price_bracket`. This follows the matrix's own rule that a shared
mutation is fine when the signature is diagnostic.

**Recorded rather than tuned away:** the arms forward a frozen `AMPLE =
400_000`, and the 1,024-byte *exponent* shape costs 253,952 at Osaka, so a
mutation that doubles the exponent coefficient also breaks this archetype.
That is a real sensitivity, not a defect — the budget literal is part of the
shape — and the signature still discriminates, because an admissibility
mutation moves the `*_at_1024` / `*_at_1025` slots while a coefficient
mutation moves only the exponent slot and also lights up
`precompile_price_bracket`.

## What a failure means

A contract passed the precompile an input size the chain no longer accepts
(or newly accepts). On the `..._before_eip7823` arm, a `BigNumbers`
multiplication chain that completed now reverts; on the `..._from_eip7823`
arm, an input the chain must reject was computed instead. Neither is a
pricing problem and neither can be fixed by sending more gas.
