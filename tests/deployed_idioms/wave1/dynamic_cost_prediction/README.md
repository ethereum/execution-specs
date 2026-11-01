# Class #18: dynamic-cost affordability prediction

**Invariant.** A contract that sizes an operation to fit a budget predicts its cost from a
**formula**, and the predicted cost of the chosen size is what the EVM actually charges —
so the operation is affordable.

**Status: 869 fill, Berlin→Amsterdam, 0 failures; `pass(135)` at Amsterdam. All 14
`cls18-` mutations DETECTED, 11 of them by this archetype alone.**

**Why this is not class #3 (hardcoded cost-equality).** A reprice of a *constant* shifts a
hardcoded quote by a constant. A reprice of a *coefficient* shifts it by an amount
proportional to the runtime size, so the same deployed contract is correct at small sizes
and wrong at large ones. The quadratic memory term makes it concrete: halving the divisor
`512 -> 256` changes **nothing at all** below 16 words and adds 8,192 gas at 2,048 words.
That is measured here, not argued — see the cliff table below.

---

## Deployed witnesses

Read out of `registry/L2-bytecode.jsonl`. **The brief's figures conflated two columns**:
`instances` counts *witnessing program points*, not addresses. Corrected:

```text
shape            runtimes   addresses   program points   FP       confidence
mem.mcopy         108,056     145,049          730,841   0.0003   CHECKED
pre.call.a4         3,367      24,448           92,537   0.0      CHECKED
```

* **`mem.mcopy`** — `MCOPY` used for memory movement, 10.87% of the 994,414 distinct
  mainnet runtimes scanned. FP from a deployment-block self-check: 31 of 108,056 runtimes
  predate Cancun and therefore cannot execute the path, leaving **107,535 usable**.
  Exemplar `<address withheld>` pc 1411, runtime shared by 4,302
  addresses.
* **`pre.call.a4`** — the identity precompile at `0x04` used as a `memcpy`, the pre-`MCOPY`
  form of the same idiom and the shape this archetype's frozen-budget bracket uses. FP 0.0
  from 8 hand disassemblies plus an independent instruction-stream oracle agreeing 120/120.
  Witnessed on **a major NFT exchange** `<address withheld>` (order-hash
  buffers); exemplar `<address withheld>` pc 1388/1578, runtime
  shared by **16,900** addresses.

L5 corroborates the volume dynamically: over mainnet blocks 26,250,000–26,259,999, `MCOPY`
ran 2,001,087 times in 276,273 transactions at 33.011 gas/execution, and memory-expansion
gas alone was 23,403,918 per 100 blocks.

---

## The coefficients under test

```text
memory expansion     3 * words + words**2 // 512     amsterdam/vm/gas.py:754-758
copy per word        OPCODE_COPY_PER_WORD      =  3  amsterdam/vm/gas.py:242
keccak per word      OPCODE_KECCAK256_PER_WORD =  6  amsterdam/vm/gas.py:246
log per byte         OPCODE_LOG_DATA_PER_BYTE  =  8  amsterdam/vm/gas.py:248
exp per byte         OPCODE_EXP_PER_BYTE       = 50  amsterdam/vm/gas.py:244
init code per word   CODE_INIT_PER_WORD        =  2  amsterdam/vm/gas.py:89
identity precompile  15 + 3 * words                  amsterdam/vm/gas.py:111-112
```

`CODE_INIT_PER_WORD` is the exception to the fork-stability below: EIP-3860 *introduced* it
at Shanghai, so that arm is `valid_from("Shanghai")`. Before it, longer init code was free
per word and a factory's prediction had no size term at all.

**All five opcode coefficients — memory, copy, keccak, log, exp — are identical on every
fork from Berlin to Amsterdam**, as is the identity precompile's `15 + 3`
(CHECKED: `grep` over `{berlin,london,cancun,prague,osaka,amsterdam}/vm/gas.py`), so one
expectation table covers the whole range. That identity is *demonstrated* by the fill
rather than assumed, in the same way `oog_as_signal`'s six-fork bracket demonstrates
`COLD_STORAGE_ACCESS` stability.

**`OPCODE_EXP_PER_BYTE` is the historical precedent this class exists for.** EIP-160 took
it from 10 to 50 at Spurious Dragon — a real 5x rise in a *coefficient*. A contract pricing
`EXP` on a 32-byte exponent went from 320 to 1,600 gas; on an 8-byte exponent from 90 to
410. The prediction error is `40 * bytes`, so it scales with the input.

---

## Three arms, and what separates them

1. **Prediction equality** — the contract evaluates its formula *in EVM bytecode* on a
   length it reads from calldata, and the result is compared with what the EVM actually
   charged, measured by two `GAS` readings. One coefficient per test, so a failure names
   the coefficient that moved. Two markers: `<kind>_dynamic_charge` (the exact number — this
   is the second archetype after `hardcoded_cost_equality` where SCHEMA §4.1's "unless the
   gas number IS the invariant" applies) and `<kind>_formula_predicts_charge` (the readable
   verdict).
2. **Affordability bracket** — a frozen budget buys N words and not N+1, asserted from both
   sides. A dearer reprice breaks the fitting arm; a cheaper one breaks the non-fitting arm.
3. **Differencing** — the per-word terms `CREATE2` charges are 8 gas against a measured total
   of 32,024 (pre-8037) or 195,624 (Amsterdam). No absolute expectation can reach them; two
   creates one word apart cancel everything else.

---

## The instrument, derived opcode by opcode

Both `GAS` readings stay on the **stack**. A memory-based instrument (as
`tests/tools/test_storage_cost_probe.py` uses) would pre-expand memory by two words and
change every expansion figure here. `GAS` costs 2 and is charged *before* it pushes, so the
trailing reading is inside the window and the leading one is not.

```text
arm      inside the measurement window                                  overhead
memory   PUSH1 0 (3) CALLDATALOAD 0x20 (6) MSTORE base (3) GAS (2)            14
copy     CALLDATALOAD 0 (6) PUSH1 0 (3) PUSH1 0 (3) MCOPY base (3) GAS (2)    17
keccak   CALLDATALOAD 0 (6) PUSH1 0 (3) SHA3 base (30) POP (2) GAS (2)        43
log      CALLDATALOAD 0 (6) PUSH1 0 (3) LOG0 base (375) GAS (2)              386
exp      CALLDATALOAD 0x20 (6) PUSH1 1 (3) EXP base (10) POP (2) GAS (2)      23
```

Derived first, then confirmed: `tests/tools/test_cls18_dynamic_cost_probe.py` asserts the
derived figure for every (operation, size) pair and passes **965 fills, Berlin to
Amsterdam**. Stage one of that probe asserted `0` for every param so the real charge
appeared in the mismatch message; stage two asserts the derivation. The two agree to the
gas at every point.

---

## Measured: the dynamic charge, and where the quadratic takes over

Memory expansion, Amsterdam (identical Berlin→Amsterdam, CHECKED):

```text
size      words   3*w     w**2//512   dynamic charge   quadratic share
    32        1      3             0                3             0.0%
   128        4     12             0               12             0.0%
   480       15     45             0               45             0.0%
   512       16     48             0               48             0.0%
  1024       32     96             2               98             2.0%
  4096      128    384            32              416             7.7%
 32768     1024   3072          2048             5120            40.0%
 65536     2048   6144          8192            14336            57.1%
```

The other coefficients, for the same sizes:

```text
size      copy 3w   keccak 6w   log 8*bytes
    32          3           6           256
   128         12          24         1,024
   480         45          90         3,840
   512         48          96         4,096
  1024         96         192         8,192
  4096        384         768        32,768
 32768      3,072       6,144       262,144
 65536      6,144      12,288       524,288

exponent bytes    1     2     4     8    16    32
exp 50*bytes     50   100   200   400   800  1,600
```

### The two affordability brackets, pinned to a single word

```text
identity precompile, frozen staticcall(1000, 0x04, ...)
  328 words (10,496 bytes)   15 + 984   =   999  <= 1,000   fits
  329 words (10,528 bytes)   15 + 987   = 1,002  >  1,000   does not

MCOPY child on a frozen call(100000, ...)
  child cost = 12 + 6w + w**2 // 512, where 12 is three PUSHes (9) plus
  MCOPY's own base (3) and 6w is copy 3w plus linear expansion 3w
  5,782 words (185,024 B)  12 + 34,692 + 65,296 = 100,000  == 100,000  fits
  5,783 words (185,056 B)  12 + 34,698 + 65,318 = 100,028  >  100,000  does not
```

The MCOPY bracket sits **exactly** on the budget: 100,000 of 100,000. Derived from the
constants, then measured, agreeing to the gas. At that size the quadratic term is 65,296 of
the 100,000 — **65% of the charge** — which is why this bracket moves when the divisor moves
and the identity bracket does not.

### Init-code per word, by differencing

```text
metered CREATE2 at size 32 (one word of init code), measured
  pre-EIP-8037    32,024 = 32,000 + 6 + 2 + 16     (Shanghai/Cancun/Prague/Osaka)
  Amsterdam      195,624 = 195,600 + 6 + 2 + 16
  slope               +8 per extra word, every fork from Shanghai

  32,000  = GAS_CREATE                            (pre-8037)
 195,600  = CREATE_ACCESS 12,000 + NEW_ACCOUNT 183,600  (Amsterdam)
       6  = OPCODE_KECCAK256_PER_WORD   x 1 word
       2  = CODE_INIT_PER_WORD          x 1 word
      16  = instrument: 4 PUSHes (12) + POP (2) + GAS (2)
```

Derived and measured, agreeing to the gas on all five forks. The **8 gas under test is
0.004% of the Amsterdam charge**, which is the whole argument for differencing: no absolute
expectation could carry the coefficient without also carrying 195,600 gas of fork-specific
account-creation cost.

---

## Prior art, and why it cannot fail under a reprice (CHECKED)

The official suite covers these operations for *conformance* and derives every budget from
the fork, so a coefficient change moves the expectation and the behaviour together:

```text
tests/cancun/eip5656_mcopy/test_mcopy_memory_expansion.py:106
    call_exact_cost = callee_bytecode.gas_cost(fork)      <- the tx limit IS the cost
tests/shanghai/eip3860_initcode/test_initcode.py:553-555
    expected_gas_usage = create_code.gas_cost(fork) + initcode.gas_cost(fork)
```

The two cited lines are **CHECKED** (read at the pinned commit). That those tests therefore
*cannot* fail under any mutation in `cls-18-23.json` is **INFERRED** — the inference, not a
measurement: the expectation and the behaviour are both functions of the same fork object,
so a coefficient change moves them together and the comparison is invariant. It was not
measured because `tools/mutate.py` discovers archetypes from `wave1/` only and
filling the official suite under a live mutation would mean hand-editing the shared EELS
tree, which this corpus's hygiene rules forbid.

This is `docs/COVERAGE-GAP.md`'s keystone result instantiated for this class: the gap is not
a missing test, it is a missing *shape*. The corpus's contribution is a **frozen** formula —
coefficients written into immutable bytecode — checked against the live one.

## What is deliberately not covered, and why

**Access-list cost per entry** (`TX_ACCESS_LIST_ADDRESS = 2,900`,
`TX_ACCESS_LIST_STORAGE_KEY = 2,000` at Amsterdam; EIP-7981 moved them). Two reasons, both
disqualifying:

1. It is levied in `calculate_intrinsic_cost` before the first opcode and **no opcode
   reports it** — the same argument `tests/intrinsic_cost/` makes about the 21,000. The
   instrument for that dimension already exists in that archetype.
2. More decisively, the class premise fails: an access list is sized by the **transaction
   sender**, off chain. No deployed contract predicts it, so there is no deployed idiom to
   pin. A test would assert a number nobody relies on.

The *consequence* of the access-list charge — whether a slot reads warm or cold — is
covered by `cls12-cold-read-{700,5000}` and the archetypes those fire on.

---

## Mutation result

Fourteen mutations, all in `tools/mutations/cls-18-23.json`: **eight dearer and six
cheaper**. The direction split matters, because five of the fifteen gas constants that ever
changed on mainnet moved *down*, and until recently every mutation in this corpus made gas
dearer. `cls18-exp-per-byte-10` is the sharpest of the cheaper six — it is **not an invented
number**, it restores the pre-EIP-160 value exactly.

```text
dearer  (8)  memory-per-word-6, memory-quadratic-256, copy-per-word-6,
             copy-per-word-osaka-6, keccak-per-word-12, log-byte-10,
             init-code-per-word-4, identity-per-word-4
cheaper (6)  memory-per-word-2, memory-quadratic-1024, copy-per-word-1,
             keccak-per-word-3, exp-per-byte-10, identity-per-word-2
```

```text
mutation                       dynamic_cost_prediction   what fails
(baseline)                     pass(135)
cls18-memory-per-word-6        DETECTED(27)              8 memory params + bracket (fits)
cls18-memory-per-word-2        DETECTED(27)              8 memory params + bracket (negative)
cls18-memory-quadratic-256     DETECTED(18)              5 memory params + bracket (fits)
cls18-memory-quadratic-1024    DETECTED(15)              4 memory params + bracket (negative)
cls18-copy-per-word-6          DETECTED(27)              8 copy params + bracket (fits)
cls18-copy-per-word-1          DETECTED(27)              8 copy params + bracket (negative)
cls18-copy-per-word-osaka-6    DETECTED(27)              the same, on the pre-8037 band
cls18-keccak-per-word-12       DETECTED(33)              8 keccak params + 3 init-code
cls18-keccak-per-word-3        DETECTED(33)              8 keccak params + 3 init-code
cls18-log-byte-10              DETECTED(24)              8 log params only
cls18-exp-per-byte-10          DETECTED(18)              6 exp params only
cls18-init-code-per-word-4     DETECTED( 9)              3 init-code params only
cls18-identity-per-word-4      DETECTED( 3)              identity bracket, fitting arm
cls18-identity-per-word-2      DETECTED( 3)              identity bracket, negative arm
```

**Every one of the fourteen counts was predicted from the arithmetic before the run and came
back identical** (135 Amsterdam tests = 24 memory + 24 copy + 24 keccak + 24 log + 18 exp +
6 identity-bracket + 6 mcopy-bracket + 9 init-code, each param in three fixture formats).
That is what makes the row diagnostic rather than just green. Three results worth reading
twice:

**1. The size-scaling property is measured, not asserted.** `cls18-memory-quadratic-256`
fails 5 of the 8 memory sizes and **survives the other three for an exact arithmetic
reason**: `floor(w**2/512) == floor(w**2/256) == 0` for every `w <= 15`. The 480-byte (15
words) and 512-byte (16 words) params were added specifically to bracket that, so the
corpus **locates the cliff to a single word** rather than returning a boolean — the same
move `floor-token-7`/`floor-token-8` makes for the calldata floor.

**2. The two divisor mutations have different cliffs, and integer flooring is why.**
Dearer (`512 -> 256`) first bites at **w = 16**; cheaper (`512 -> 1024`) first bites at
**w = 32**, because `floor(256/512) == floor(256/1024) == 0`. A contract is therefore
*more* exposed to the memory price going up than down, by one octave of size.

**3. `cls18-keccak-per-word-{12,3}` fires the init-code arm too, correctly.** `CREATE2`
charges `OPCODE_KECCAK256_PER_WORD` for hashing the init code
(`vm/instructions/system.py:278`), so the differencing arm measures `6 + 2` and a keccak
reprice moves 6 of those 8. The signature discriminates: keccak alone red means the hash
coefficient moved; `cls18-init-code-per-word-4` red alone means EIP-3860's term moved.

Two-sidedness is complete at the bracket level: for **every** bracket, one mutation breaks
the fitting arm and a different one breaks the non-fitting arm. A frozen-budget survival
test is structurally blind to the cheaper direction (an over-provisioned budget still
fits); the brackets are not.

### Specificity, from the unrestricted column (`mutate.py -k cls18- --md`, 24 archetypes)

**11 of the 14 mutations have exactly one detector — this archetype.** Nothing else in the
corpus can see a copy, keccak, log, exp, init-code or identity-precompile coefficient, or
the memory quadratic divisor in its dearer direction.

```text
mutation                       detectors  which
cls18-memory-quadratic-256         1      dynamic_cost_prediction(18)
cls18-copy-per-word-6              1      dynamic_cost_prediction(27)
cls18-copy-per-word-1              1      dynamic_cost_prediction(27)
cls18-copy-per-word-osaka-6        1      dynamic_cost_prediction(27)
cls18-keccak-per-word-12           1      dynamic_cost_prediction(33)
cls18-keccak-per-word-3            1      dynamic_cost_prediction(33)
cls18-log-byte-10                  1      dynamic_cost_prediction(24)
cls18-exp-per-byte-10              1      dynamic_cost_prediction(18)
cls18-init-code-per-word-4         1      dynamic_cost_prediction( 9)
cls18-identity-per-word-4          1      dynamic_cost_prediction( 3)
cls18-identity-per-word-2          1      dynamic_cost_prediction( 3)
cls18-memory-per-word-6            2      + hardcoded_cost_equality(6)
cls18-memory-quadratic-1024        2      + forwarding_prediction(3)
cls18-memory-per-word-2            3      + forwarding_prediction(3), hardcoded_cost_equality(6)
```

The three shared rows are shared for stated, correct reasons, and both are cross-checks
rather than noise:

* **`hardcoded_cost_equality`** documents its own instrument as `MSTORE 3 + 3 (one word of
  expansion)` inside a 17-gas overhead. `MEMORY_PER_WORD` is literally one of its 17 gas, so
  a change to it must move that archetype — and the fact that it does confirms the overhead
  derivation in *both* archetypes independently.
* **`forwarding_prediction`** reimplements `calculate_message_call_gas`, which subtracts a
  memory-cost term; `docs/INVARIANT-CLASSES.md` #5 predicted exactly this ("would break on
  any change to ... the memory-cost term"). Worth noting it is **graded by direction**: the
  *cheaper* memory mutations fire it and the *dearer* `memory-per-word-6` does not, because
  cheaper memory leaves more gas inside the clamp and moves the predicted-versus-delivered
  figure, while dearer memory stays inside that test's margin.

### The archetype row (`mutate.py --archetype dynamic_cost_prediction`, all 83 mutations)

This archetype detects **15 of the 83 registered mutations**: its own 14, plus one from
another contributor —

```text
cls11-no-child-gas-return   DETECTED(9)   only the init-code differencing arm
```

That one is correct and worth keeping. The differencing arm runs two `CREATE2`s at
*different* `gas_left`, so each forwards a different `all-but-1/64` to its child. If a child
never returns its unused gas, the two deltas diverge by far more than the 8 gas under test
and the arm fails — while every equality and bracket arm, which spawns no child, is
untouched. The count isolates it exactly: 9 of 135.

Sixty-eight mutations survive this archetype, which is the expected shape: nothing here
touches state gas, refunds, the retention divisor, the reservoir, or settlement.

---

## Reproduce

```bash
cd engine/eels
# never fill while a mutate.py run holds the lock
python3 ../../tools/locked_fill.py ../../wave1/dynamic_cost_prediction \
    --from Berlin --until Amsterdam --output /tmp/dcp -q -p no:cacheprovider

# the instrument, re-derived
python3 ../../tools/locked_fill.py ../../wave1/instruments \
    --from Berlin --until Amsterdam -k cls18 --output /tmp/c18 -q -p no:cacheprovider

cd ../../patterns
python3 tools/mutate.py -k cls18- --archetype dynamic_cost_prediction   # the row
python3 tools/mutate.py -k cls18- --md                                  # the column
```

**What a failure means.** The coefficient in some deployed contract's hardcoded cost formula
no longer matches the EVM's, and the error is proportional to the size that contract was
handed — so the contract keeps working on small inputs and out-of-gases, or silently
under-quotes, on large ones. For the frozen-budget arms the failure is not a revert: the
copy returns 0, the caller reads stale memory, and nothing surfaces an error.
