# Archetype: precompile price bracket (class #1/#3 shape, a rule neither covers)

**Invariant.** A frozen gas literal in immutable code, forwarded to a
precompile, is exactly sufficient — and the precompile's price is pinned
from **both** sides (`price` suffices, `price - 1` does not) so a reprice in
either direction fails a slot.

**Honest placement: the archetype is not new.** It is the two-sided bracket
`tests/oog_as_signal/` established, applied to precompile pricing, plus a
fork-split arm pair for the one precompile whose price actually moved inside
Berlin→Amsterdam. What *is* new is the rule and the **direction coverage**,
and that is stated rather than dressed up as a new class. The argument for
building it anyway:

* `INVARIANT-CLASSES.md`'s "repricing DOWNWARD" section records that **#1
  frozen-budget survival is invisible to a reduction** — an
  over-provisioned budget still fits — and that `cls12-cold-read-700`, the
  corpus's only cheaper mutation at the time, is **survived by all six
  budget-sufficiency archetypes**.
* Precompiles are the one surface where mainnet repricing has gone **both
  ways**, so this is where that imbalance can be fixed with real values
  rather than invented ones.
* L4 rated the `precompile-pricing` axis **conformance-only**, and no
  `istanbul/eip1108_*` or `berlin/eip2565_*` directory exists at all.

```text
PRECOMPILE_ECADD              500 ->    150   EIP-1108, Istanbul   3.3x cheaper
PRECOMPILE_ECMUL           40,000 ->  6,000   EIP-1108             6.7x cheaper
PRECOMPILE_ECPAIRING_BASE 100,000 -> 45,000   EIP-1108
PRECOMPILE_ECPAIRING_PER_POINT
                           80,000 -> 34,000   EIP-1108
MODEXP (32-byte operands)   1,360 ->  4,080   EIP-7883, Osaka      3.0x dearer
```

The lower rail is what makes a reduction observable: if `ECADD` became 50
gas, a 149-gas forward would start succeeding, and the test says so.

## Deployed witnesses, with addresses (CHECKED, Sourcify v2)

**1. A frozen literal equal to the price, zero margin.**
`<address withheld>` a deployed Groth16 verifier,
`contracts/verifiers/a deployed Groth16 verifier.sol:125`:

```solidity
res_ := staticcall(6000, 7, add(pointer_, 64), 96, add(pointer_, 64), 64) // ecMul
res_ := and(res_, gt(returndatasize(), 0)) // check that multiplication succeeded
```

6,000 is *exactly* `PRECOMPILE_ECMUL`. The first gas this precompile ever
costs above 6,000 breaks this verifier, and it reads the failure as
"multiplication did not succeed" rather than surfacing an error — class #12's
quiet shape, on a price.

**2. A frozen literal that writes down the price and the date it was
checked.** a deployed zk protocol a deployed zk verifier, three deployments —
`<address withheld>`,
`<address withheld>`,
`<address withheld>` — a deployed zk verifier.sol:62-65`:

```solidity
// ecMul gas cost is fixed at 6000. Add 33.3% gas for safety buffer.
// Last checked in 2024 Oct, evm codename Cancun
// ref: https://www.evm.codes/precompiled?fork=cancun#0x07
success := staticcall(8000, 7, mIn, 96, mIn, 64)
```

A deployed contract naming the constant it depends on, the margin it chose,
and the fork it verified against. Companion evidence to a deployed oracle network's
`GAS_FOR_CALL_EXACT_CHECK` comment in class #5.

**3. Two sibling deployments whose literals bracket EIP-7883.** Both compute
a modular inverse by Fermat's little theorem — `modexp(value, p - 2, p)` with
`p` the secp256r1 field prime, i.e. 32/32/32 byte lengths and a 256-bit
exponent — under a frozen literal, and both wrap the call in
`switch success case 0 { revert(0x0, 0x0) }`:

```text
<address withheld>  a deployed passkey validation module
    .../PasskeyValidationModules/Secp256r1.sol:183
    staticcall(1500,  0x5, freemem, 0xc0, freemem, 0x20)
    population for this exact literal: 1 file / 3 addresses / 1 runtime

<address withheld>  a sibling fallback handler
    .../verification/secp256r1/utils/LibSecp256r1.sol:366
    staticcall(14000, 0x5, freemem, 0xc0, freemem, 0x20)
    population: 1 file / 1 address / 1 runtime
```

Low prevalence, and in scope: SCHEMA §1 — "Rarity is fine; a pattern with 3
instances is in scope." Counting unit: distinct mainnet addresses whose
verified compilation contains the matching source file.

Also found and **deliberately not built**, with the reason: the identity
precompile used as a memcpy under a frozen literal —
`staticcall(450, 0x4, ...)` in `BigNumber.sol`
(`<address withheld>`,
`<address withheld>`,
`<address withheld>`) and
`staticcall(10000, 0x04, ...)` in `RsaBounty`
`<address withheld>`. This is class **#18**'s
`pre.call.a4` record (3,367 runtimes / 24,448 addresses, FP 0.0), already
covered by `tests/dynamic_cost_prediction/`. Cited, not rebuilt.

## Measurement commands

```bash
cd tests/deployed_idioms

# the price ladder: six ascending budgets per shape, packed as a bitmask
python3 tools/locked_fill.py \
  "$PWD/expansion/tests/tools/test_precompile_price_probe.py" \
  --from Osaka --until Osaka --output <unique-dir> -q -p no:cacheprovider
# mask printed MSB-first; bit i set == budgets[i] sufficed. The probe
# asserts a 0xdead sentinel, so its failures ARE the measurement.

python3 tools/verify_corpus.py --wave expansion
python3 tools/mutate.py --wave expansion -k exp-pre \
  --archetype precompile_price_bracket
```

## Prior art: the same bracket shape exists officially and is blind — MEASURED

`tests/byzantium/eip196_ec_add_mul/test_gas.py::test_gas_costs` already
implements this exact shape — `gas = precompile_gas if enough_gas else
precompile_gas - 1`, committing 1 or 0 — and so does
`tests/byzantium/eip197_ec_pairing/test_gas.py`. Both rails come from
`fork.gas_costs()` (`eip196_ec_add_mul/conftest.py:24-31`,
`eip197_ec_pairing/conftest.py:20-27`), so a reprice moves both together —
`docs/COVERAGE-GAP.md`'s structural argument.

**That was tested, not assumed.** A *real* reprice was simulated by editing
**both** gas tables at once — the spec's `amsterdam/vm/gas.py` **and the test
framework's own independent copy** at
`packages/testing/src/execution_testing/forks/forks/eips/istanbul/eip_1108.py:21`
— setting `PRECOMPILE_ECADD` 150 → 50 (a 3x reduction, the EIP-1108
direction):

```text
tests/byzantium/eip196_ec_add_mul/test_gas.py     24 passed   <- BLIND
expansion/.../precompile_price_bracket             3 failed   <- DETECTED
```

This is the first *measured* demonstration of the coverage gap on the
precompile-pricing axis, and it carries a methodological warning the whole
corpus needs:

> **A mutation-harness "DETECTED" on a fork-derived official test proves
> nothing.** `execution_testing` keeps its own gas table, separate from
> `src/ethereum/forks/*/vm/gas.py`. Perturbing only the spec side makes the
> two disagree, so *every* fork-derived test goes red for that reason alone.
> Measured: under the single-table `exp-pre-ecadd-50`, `tests/byzantium/`
> reports `3 failed, 1797 passed` — and those 3 are exactly the
> `enough_gas_False` ecadd params, failing because the framework still
> forwarded 149 while the spec charged 50. Under the two-table edit the same
> 3 pass. Only a literal frozen in the *test's own source* fails under both.

`tests/osaka/eip7883_modexp_gas_increase/` has the same property by the same
route: `conftest.py:233-239` picks `Spec` or `Spec7883` from
`fork.is_eip_enabled(7883)` and recomputes the budget, and
`test_modexp_gas_usage_contract_wrapper` brackets it +1 / 0 / -1. The shape
is right; the rails move. L4's "conformance-only" rating of the
`precompile-pricing` axis is correct and now has a measurement behind it.

Reproduce — a two-file edit, so `mutate.py` cannot express it. Take the
shared `tools/.mutate.lock`, apply **both** edits, fill, restore both,
md5-verify. **Never wrap a lock-holding script in `timeout`**: SIGTERM skips
`finally` and leaves two trees dirty.

```text
engine/eels/src/ethereum/forks/amsterdam/vm/gas.py
  PRECOMPILE_ECADD: Final[ExecutionGas] = ExecutionGas(Uint(150))
    -> ...Uint(50))
engine/eels/packages/testing/src/execution_testing/forks/forks/eips/istanbul/eip_1108.py
  PRECOMPILE_ECADD=150,   ->   PRECOMPILE_ECADD=50,

then, --from Amsterdam --until Amsterdam:
  tests/byzantium/eip196_ec_add_mul/test_gas.py
  expansion/precompile_price_bracket
```

## Measured (CHECKED): every price located to a single gas

```text
shape                        Berlin..Prague        Osaka, Amsterdam
ECADD, 128 zero bytes        exactly 150           exactly 150
ECMUL, 96 zero bytes         exactly 6,000         exactly 6,000
ECPAIRING, 0 pairs           exactly 45,000        exactly 45,000
ECPAIRING, 1 pair            exactly 79,000        exactly 79,000
MODEXP, 32/32/32, exp=p-2    exactly 1,360         exactly 4,080
MODEXP, base 1024            exactly 5,461         exactly 32,768
MODEXP, exponent 1024        exactly 2,645         exactly 253,952
P256VERIFY, empty input      n/a (empty account)   exactly 6,900
```

Why these are direct measurements and not subtractions: all-zero inputs are
the point at infinity for G1 and G2 and the scalar 0, `py_ecc` returns
`FQ12.one()` for a pairing involving infinity, and a precompile frame has no
code — so the precompile's own charge is the frame's *entire* cost and
`forwarded >= cost` is exactly `success`.

The bn128 prices are **identical on all six forks** (EIP-1108 landed at
Istanbul, before this range), so one fork-free test pins them — the same
argument `oog_as_signal` uses for `COLD_STORAGE_ACCESS`, demonstrated rather
than assumed. The pairing pair separates the two constants: 45,000 is
`ECPAIRING_BASE` alone, and `79,000 - 45,000 = 34,000` is
`ECPAIRING_PER_POINT`, so a mutation to either is attributable.

### The deployed break this located

```text
budget   Berlin..Prague   Osaka, Amsterdam   deployed at
 1,359   fails            fails              --
 1,360   SUCCEEDS         fails              --
 1,500   SUCCEEDS         FAILS              a deployed passkey validation module
 4,079   succeeds         fails              --
 4,080   succeeds         SUCCEEDS           --
14,000   succeeds         succeeds           a sibling fallback handler
```

**a deployed passkey validation module `staticcall(1500, 0x5, ...)` succeeds on
Berlin through Prague and fails from Osaka.** Derivation and measurement
agree to the gas: 32-byte operands give `complexity = 16`, a 256-bit
exponent gives `iterations = 255`, so the cost is `16 x 255 = 4,080`; before
EIP-7883 the same product was divided by `GQUADDIVISOR = 3`, giving 1,360.
The literal sat 140 gas above the old cost and sits 2,580 below the new one.
Its sibling at 14,000 keeps 3.43x headroom, so **the two deployed literals
bracket the change** — the only such pair found on this surface.

Consequence: `primemod` reverts, so passkey (WebAuthn) signature
verification in that module cannot complete. A liveness failure, loud rather
than silent, in an immutable module. Parallel in kind to class #5's
a deployed oracle network finding.

### What the two large-operand brackets add

The 32-byte inverse cannot reach either large-operand coefficient: with
`max_length <= 32` the word term is a flat constant, and with a 32-byte
exponent the length term is never evaluated. The pair of fork arms also
measures **how unevenly EIP-7883 treated the two terms**:

```text
term                        before 7883    from 7883    factor
words**2 (base 1024)        5,461          32,768       6.0x
8|16 * (exp_len - 32)       2,645          253,952      96.0x
```

So a contract sized against the old *exponent* term is 16x more exposed than
one sized against the old *word* term — a distinction only a
per-coefficient bracket can show, and the reason this archetype has four
modexp brackets rather than one.

## Fill and mutation result

```text
fill, Berlin..Amsterdam, 6 tests, 3 fixture formats        72 passed   CHECKED
baseline at Amsterdam                                      pass(12)    CHECKED
mutations detected                                         22 of 28
reference files restored, md5-verified, every run           OK         CHECKED
```

Detected (22), with the direction split that was the point of building this:

```text
DEARER   (10)  ecadd-200, ecmul-6500, ecpairing-base-50000,
               ecpairing-per-point-40000, p256verify-7000,
               modexp-floor-5000, modexp-small-complexity-32,
               modexp-word-complexity-x4, modexp-exponent-length-term-32,
               prague-modexp-restore-no-divisor
CHEAPER   (9)  ecadd-50, ecmul-1000, ecpairing-base-20000,
               ecpairing-per-point-10000, p256verify-3450,
               modexp-restore-gquaddivisor, modexp-small-complexity-8,
               modexp-word-complexity-x1, modexp-exponent-length-term-8
SEMANTIC  (2)  p256-halts-on-malformed-length, unassign-p256verify
DOMAIN    (1)  modexp-bound-512 (shared with the admissibility archetype)
```

**All nine cheaper mutations are DETECTED.** Three of them restore real
historical values exactly rather than inventing one:
`modexp-restore-gquaddivisor` is EIP-2565's `cost // 3` with its 200 floor,
`modexp-word-complexity-x1` is EIP-2565's `words**2`, and
`modexp-exponent-length-term-8` is EIP-2565's `8 * (n - 32)` — the same
discipline as `cls18-exp-per-byte-10`.

Graded results worth keeping:

* `exp-pre-modexp-small-complexity-32` and
  `exp-pre-modexp-word-complexity-x4` are **complementary**: the first moves
  the 32-byte inverse and the 1024-byte *exponent* shape and leaves the
  1024-byte *base* shape alone (it takes the `max_length > 32` branch); the
  second does the opposite. So the two `complexity` code paths are
  discriminated by signature, not merely both covered.
* `exp-pre-ecpairing-base-*` breaks **both** pairing brackets;
  `exp-pre-ecpairing-per-point-*` breaks **only the one-pair** bracket. The
  two constants are therefore separable from the failure set alone.
* `exp-pre-modexp-small-complexity-8` is graded: the lower rail (4,079)
  starts succeeding while a deployed account-abstraction stack's 1,500 still does not fit, so the
  deployed-literal slot stays green and the failure says "cheaper, but not
  that much cheaper".
* `exp-pre-unassign-p256verify` fires here as well as on
  `unassigned_precompile_identity`, correctly: an empty account answers on
  *any* budget, so the lower rail starts succeeding. Signature: both red
  means an address was unassigned; price-bracket alone means a price moved.

### One mutation deliberately survives: `exp-pre-noop-canary`

It is a comment-only edit to `modexp.py` that changes no behaviour, so it
**must** read `survives` in every column. The corpus has no such row yet,
and it is worth one: `MUTATION-MATRIX.md`'s hygiene section records three
independent incidents where lock contention or a tree left dirty by a killed
run produced failures that did not reproduce. A matrix in which the canary
goes red is a broken matrix, not a finding — and a no-op row makes that
checkable instead of a matter of discipline. It appears in `mutate.py`'s
"UNDETECTED" list by design; the stated reason is here, per the matrix's own
rule that a mutation surviving *for a stated reason* is a result.

## What a failure means

A deployed frozen budget no longer matches what the precompile charges. A
failing **upper** rail (`..._suffices`) means the price rose and the
deployed contract now reverts or reads "operation failed". A failing
**lower** rail (`..._does_not_suffice`) means the price fell, which breaks
the opposite population — probes that read failure as a negative answer
(class #12) begin reading success.

Do not repair a failure by adjusting a budget: the deployed literals come
from the contracts named above, and the +/-1 rails are the measured price.
