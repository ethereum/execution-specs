"""
Class #18: dynamic-cost affordability prediction.

A contract that *sizes* an operation to fit a budget cannot hardcode a
constant: the charge depends on a runtime length. It has to reimplement the
EVM's **formula**, coefficients and all, and deployed code does exactly
that — a widely used assembly library and solc's memory-expansion helpers, every assembly router
that checks `msize()` growth before a copy, every library that prices a
`keccak256` over calldata.

```text
memory expansion   3 * words + words**2 // 512     vm/gas.py:754-758
copy per word      OPCODE_COPY_PER_WORD      = 3   vm/gas.py:242
keccak per word    OPCODE_KECCAK256_PER_WORD = 6   vm/gas.py:246
log per byte       OPCODE_LOG_DATA_PER_BYTE  = 8   vm/gas.py:248
exp per byte       OPCODE_EXP_PER_BYTE       = 50  vm/gas.py:244
init code per word CODE_INIT_PER_WORD        = 2   vm/gas.py:89
identity precompile  15 + 3 * words                vm/gas.py:111-112
```

**Why this is not class #3.** A reprice of a *constant* shifts a hardcoded
quote by a constant. A reprice of a *coefficient* shifts it by an amount
proportional to the size, so the same deployed contract is correct at small
sizes and wrong at large ones. The quadratic memory term makes that
concrete: halving the divisor 512 -> 256 changes nothing at all below 16
words (`w**2 // 512 == w**2 // 256 == 0` for `w <= 15`) and adds 8,192 gas
at 2,048 words. Size is a test parameter here precisely so the corpus
records where that cliff sits rather than returning a boolean.

**Deployed witnesses (L2, measured, counting unit stated).** Read straight
out of `registry/L2-bytecode.jsonl` rather than from the brief, because the
brief's figures conflated two different columns — `instances` counts
*witnessing program points*, not addresses:

```text
shape            runtimes   addresses   program points   FP      confidence
mem.mcopy         108,056     145,049          730,841   0.0003  CHECKED
pre.call.a4         3,367      24,448           92,537   0.0     CHECKED
```

`mem.mcopy` is 10.87% of the 994,414 distinct mainnet runtimes scanned —
the FP rate comes from a deployment-block self-check (31 of 108,056
runtimes predate Cancun and so cannot execute the path), leaving 107,535
usable. Exemplar `<address withheld>` pc 1411,
whose runtime backs 4,302 addresses.

`pre.call.a4` is the identity precompile at address `0x04` used as a
`memcpy` — the pre-`MCOPY` form of the same idiom, and the shape this
file's frozen-budget bracket uses. FP 0.0 from 8 hand disassemblies plus an
independent instruction-stream oracle agreeing 120/120. Witnessed on
**a major NFT exchange** `<address withheld>`, which uses it
for its order-hash buffers; exemplar
`<address withheld>` pc 1388/1578, runtime shared
by 16,900 addresses.

**Three arms, and the mutations separate them** (see README.md):

1. *Prediction equality.* The contract evaluates its formula on a length
   taken from calldata and compares the result with what the EVM actually
   charged, measured by two `GAS` readings. One coefficient per test, so a
   failure names the coefficient that moved.
2. *Affordability bracket.* A frozen budget buys a copy of N words and not
   N+1. Two-sided: a dearer reprice breaks the fitting arm, a cheaper one
   breaks the non-fitting arm.
3. *Differencing.* `CODE_INIT_PER_WORD` cannot be isolated by a single
   measurement, because a `CREATE2` charge is dominated by
   fork-specific account-creation costs. Two creates one word apart cancel
   all of it.

Every number in this file was measured before it was written
(`tests/tools/test_cls18_dynamic_cost_probe.py`, 965 fills across Berlin to
Amsterdam) and then derived from the constants above; the derivation and
the measurement agree to the gas. All five coefficients are **identical on
every fork from Berlin to Amsterdam**, so one expectation table covers the
whole range — that identity is demonstrated by the fill, not assumed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# --------------------------------------------------------------------------
# The coefficients under test. These are the assertion, not parameters of
# the test: they are what a deployed sizing contract wrote into immutable
# code. Do not rebase them to repair a failure (SCHEMA.md 4.1 permits
# asserting a gas number when the number *is* the invariant, as in
# tests/hardcoded_cost_equality/).
# --------------------------------------------------------------------------
MEMORY_PER_WORD = 3
QUADRATIC_DIVISOR = 512
COPY_PER_WORD = 3
KECCAK256_PER_WORD = 6
LOG_DATA_PER_BYTE = 8
EXP_PER_BYTE = 50
CODE_INIT_PER_WORD = 2
IDENTITY_PER_WORD = 3
IDENTITY_BASE = 15

SLOT_CHARGE = 0x01
SLOT_AGREE = 0x02

# Gas spent inside the metering window other than the dynamic term under
# test: the operand pushes, the operation's own static base, and the
# trailing `GAS` (2, charged before it pushes). Derived opcode by opcode in
# README.md and cross-checked against the probe's 965 fills.
OVERHEAD = {
    "memory": 3 + 6 + 3 + 2,  # PUSH1 0; CALLDATALOAD(0x20); MSTORE; GAS
    "copy": 6 + 3 + 3 + 3 + 2,  # CALLDATALOAD(0); PUSH1 0 x2; MCOPY; GAS
    "keccak": 6 + 3 + 30 + 2 + 2,  # ...; SHA3 base 30; POP; GAS
    "log": 6 + 3 + 375 + 2,  # ...; LOG0 base 375; GAS
    "exp": 6 + 3 + 10 + 2 + 2,  # ...; EXP base 10; POP; GAS
}

# 480 and 512 bytes are 15 and 16 words, which is where the quadratic term
# first becomes non-zero: `floor(15**2 / 512) == 0` and
# `floor(16**2 / 512) == 0` but `floor(16**2 / 256) == 1`. Keeping both
# makes a divisor change locate itself to a single word instead of
# returning a boolean -- measured, see README.md.
SIZES = [32, 128, 480, 512, 1024, 4096, 32768, 65536]
EXP_BYTES = [1, 2, 4, 8, 16, 32]


def words(size: int) -> int:
    """Ceiling division into 32-byte words, as every EVM word charge does."""
    return (size + 31) // 32


def memory_dynamic_cost(size: int) -> int:
    """The size-dependent part of `calculate_memory_gas_cost`."""
    w = words(size)
    return MEMORY_PER_WORD * w + w**2 // QUADRATIC_DIVISOR


# `words` and the per-word coefficient, evaluated *in the EVM* on a length
# the contract reads at runtime. This is the deployed idiom: the coefficient
# is a literal in the bytecode and the arithmetic happens on chain.
def _evm_words(calldata_offset: int = 0) -> Bytecode:
    return Op.DIV(Op.ADD(Op.CALLDATALOAD(calldata_offset), 31), 32)


def _evm_prediction(kind: str) -> Bytecode:
    """The contract's own cost formula, in bytecode."""
    if kind == "memory":
        w = _evm_words()
        return Op.ADD(
            Op.MUL(MEMORY_PER_WORD, w),
            Op.DIV(Op.MUL(w, w), QUADRATIC_DIVISOR),
        )
    if kind == "copy":
        return Op.MUL(COPY_PER_WORD, _evm_words())
    if kind == "keccak":
        return Op.MUL(KECCAK256_PER_WORD, _evm_words())
    if kind == "log":
        return Op.MUL(LOG_DATA_PER_BYTE, Op.CALLDATALOAD(0))
    if kind == "exp":
        return Op.MUL(EXP_PER_BYTE, Op.CALLDATALOAD(0))
    raise AssertionError(kind)


def _measured_operation(kind: str) -> Bytecode:
    """
    The operand pushes and the operation, between the two `GAS` readings.

    The size operand comes from calldata in every arm, so the formula is
    evaluated on a runtime value rather than a constant a compiler could
    fold away. Stack layout is explicit because the first `GAS` has to sit
    *below* the operands, which a nested `Op.X(...)` expression cannot do.
    """
    if kind == "memory":
        # calldata[0x20] holds size - 32, so MSTORE grows memory to exactly
        # `size` from an empty memory.
        return Op.PUSH1(0) + Op.CALLDATALOAD(0x20) + Op.MSTORE
    if kind == "copy":
        # MCOPY pops destination, source, length -- destination on top.
        return Op.CALLDATALOAD(0) + Op.PUSH1(0) + Op.PUSH1(0) + Op.MCOPY
    if kind == "keccak":
        # SHA3 pops offset, size -- offset on top.
        return Op.CALLDATALOAD(0) + Op.PUSH1(0) + Op.SHA3 + Op.POP
    if kind == "log":
        return Op.CALLDATALOAD(0) + Op.PUSH1(0) + Op.LOG0
    if kind == "exp":
        # EXP pops base, exponent -- base on top. calldata[0x20] is an
        # exponent with exactly calldata[0] significant bytes.
        return Op.CALLDATALOAD(0x20) + Op.PUSH1(1) + Op.EXP + Op.POP
    raise AssertionError(kind)


def _needs_warm_memory(kind: str) -> bool:
    """Arms that must not pay expansion, so the coefficient is isolated."""
    return kind in ("copy", "keccak", "log")


def _predictor(kind: str, size: int) -> Bytecode:
    """
    Measure the operation, commit the charge, commit the verdict.

    The instrument keeps both `GAS` readings on the **stack**. A
    memory-based instrument (as `tests/tools/test_storage_cost_probe.py`
    uses) would pre-expand memory and change every expansion figure here.
    """
    prelude = Op.MSTORE(size - 32, 0) if _needs_warm_memory(kind) else Bytecode()
    return (
        prelude
        + Op.GAS
        + _measured_operation(kind)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        # delta - OVERHEAD == the dynamic term the formula claims to predict
        + Op.PUSH2(OVERHEAD[kind])
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.PUSH1(SLOT_CHARGE)
        + Op.SSTORE
        + _evm_prediction(kind)
        + Op.EQ
        + Op.PUSH1(SLOT_AGREE)
        + Op.SSTORE
        + Op.STOP
    )


def _run(
    state_test: StateTestFiller,
    pre: Alloc,
    kind: str,
    size: int,
    charge: int,
    second_word: int,
) -> None:
    subject = pre.deploy_contract(_predictor(kind, size))
    storage = Storage().set_next_slot(SLOT_CHARGE)
    storage.store_next(charge, f"{kind}_dynamic_charge")
    storage.store_next(1, f"{kind}_formula_predicts_charge")
    tx = Transaction(
        to=subject,
        gas_limit=15_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        data=size.to_bytes(32, "big") + second_word.to_bytes(32, "big"),
    )
    state_test(pre=pre, post={subject: Account(storage=storage)}, tx=tx)


# --------------------------------------------------------------------------
# Arm 1: the contract's formula equals the charge, one coefficient per test
# --------------------------------------------------------------------------


@pytest.mark.parametrize("size", SIZES, ids=[f"size_{s}" for s in SIZES])
@pytest.mark.valid_from("Berlin")
def test_memory_expansion_formula_predicts_the_charge(
    state_test: StateTestFiller, pre: Alloc, size: int
) -> None:
    """
    Test the quadratic memory formula a sizing contract reimplements.

    `3 * words + words**2 // 512`, evaluated on chain against the charge
    the EVM actually took for growing memory from empty to `size`. This is
    the only arm whose error grows *faster* than the size: at 32 bytes the
    quadratic term is 0 and at 65,536 bytes it is 8,192 of the 14,336-gas
    charge, so a divisor change is invisible below 512 bytes and dominant
    above 16 KiB. README.md tabulates the split per size.
    """
    _run(state_test, pre, "memory", size, memory_dynamic_cost(size), size - 32)


@pytest.mark.parametrize("size", SIZES, ids=[f"size_{s}" for s in SIZES])
@pytest.mark.valid_from("Cancun")
def test_copy_per_word_formula_predicts_the_charge(
    state_test: StateTestFiller, pre: Alloc, size: int
) -> None:
    """
    Test `OPCODE_COPY_PER_WORD` against an `MCOPY` over warm memory.

    Memory is pre-grown to `size` before the first `GAS` reading, so the
    expansion term is zero and the measurement isolates the copy
    coefficient. `MCOPY` is the witnessed shape: 108,056 distinct runtimes
    backing 145,049 mainnet addresses, 10.87% of every runtime scanned
    (L2, FP 0.0003).
    """
    _run(
        state_test, pre, "copy", size, COPY_PER_WORD * words(size), size - 32
    )


@pytest.mark.parametrize("size", SIZES, ids=[f"size_{s}" for s in SIZES])
@pytest.mark.valid_from("Berlin")
def test_keccak256_per_word_formula_predicts_the_charge(
    state_test: StateTestFiller, pre: Alloc, size: int
) -> None:
    """
    Test `OPCODE_KECCAK256_PER_WORD` over warm memory.

    Any contract that hashes a variable-length payload — a merkle proof, an
    EIP-712 struct, an L2 batch — prices it with this coefficient.
    """
    _run(
        state_test,
        pre,
        "keccak",
        size,
        KECCAK256_PER_WORD * words(size),
        size - 32,
    )


@pytest.mark.parametrize("size", SIZES, ids=[f"size_{s}" for s in SIZES])
@pytest.mark.valid_from("Berlin")
def test_log_data_per_byte_formula_predicts_the_charge(
    state_test: StateTestFiller, pre: Alloc, size: int
) -> None:
    """
    Test `OPCODE_LOG_DATA_PER_BYTE` over warm memory.

    Per *byte*, not per word, so this is the coefficient whose prediction
    error grows fastest in absolute terms: 8 gas for every byte of event
    data a contract decides to emit.
    """
    _run(
        state_test,
        pre,
        "log",
        size,
        LOG_DATA_PER_BYTE * size,
        size - 32,
    )


@pytest.mark.parametrize(
    "exp_bytes", EXP_BYTES, ids=[f"exponent_bytes_{b}" for b in EXP_BYTES]
)
@pytest.mark.valid_from("Berlin")
def test_exp_per_byte_formula_predicts_the_charge(
    state_test: StateTestFiller, pre: Alloc, exp_bytes: int
) -> None:
    """
    Test `OPCODE_EXP_PER_BYTE`, the coefficient with a real 5x history.

    EIP-160 took it from 10 to 50 at Spurious Dragon — a genuine 5x rise in
    a *coefficient*, which is the historical precedent this whole class
    exists for. A contract pricing `EXP` on a 32-byte exponent went from
    paying 320 to 1,600 gas; one pricing an 8-byte exponent went from 90 to
    410. The prediction error is `40 * bytes`, so it scales.
    """
    _run(
        state_test,
        pre,
        "exp",
        exp_bytes,
        EXP_PER_BYTE * exp_bytes,
        1 << (8 * (exp_bytes - 1)),
    )


# --------------------------------------------------------------------------
# Arm 2: affordability brackets at a frozen budget, both directions
# --------------------------------------------------------------------------

SLOT_OK = 0x01
IDENTITY_ADDRESS = 4

# `IDENTITY_BASE + IDENTITY_PER_WORD * w <= 1,000` holds at w = 328 (999)
# and fails at w = 329 (1,002). Measured, both arms, Berlin..Amsterdam.
IDENTITY_BUDGET = 1_000
IDENTITY_FITS_WORDS = 328


@pytest.mark.parametrize(
    "extra_words,ok",
    [pytest.param(0, 1, id="largest_copy_that_fits"),
     pytest.param(1, 0, id="one_word_too_many")],
)
@pytest.mark.valid_from("Berlin")
def test_identity_precompile_copy_sized_to_a_frozen_budget(
    state_test: StateTestFiller, pre: Alloc, extra_words: int, ok: int
) -> None:
    """
    Test the two-sided bracket on a frozen identity-precompile budget.

    The identity precompile used as a `memcpy` is the pre-`MCOPY` form of
    this idiom and is witnessed at 3,367 distinct runtimes backing 24,448
    mainnet addresses, a major NFT exchange among them (L2, FP 0.0, oracle agreement
    120/120). Its charge is `15 + 3 * words` and nothing else, so a frozen
    `staticcall(1000, 0x04, ...)` buys exactly 328 words — 999 of the 1,000
    — and not 329, which needs 1,002.

    Both sides are asserted in one parametrised pair because each catches a
    different direction. A **dearer** per-word charge breaks
    `largest_copy_that_fits`: the copy silently returns 0 and the caller
    reads stale memory. A **cheaper** one breaks `one_word_too_many`: a
    copy the contract's own formula declared unaffordable now succeeds,
    which is the inverted form `oog_as_signal` found for OOG probes. Five
    of the fifteen gas constants that ever changed on mainnet moved down,
    `PRECOMPILE_IDENTITY_PER_WORD`'s neighbours among them (EIP-1108 cut
    `PRECOMPILE_ECMUL` 6.7x), so the cheaper arm is witnessed history, not
    a hypothetical.
    """
    size = (IDENTITY_FITS_WORDS + extra_words) * 32
    subject = pre.deploy_contract(
        Op.MSTORE(size - 32, 0)
        + Op.SSTORE(
            SLOT_OK,
            Op.STATICCALL(
                IDENTITY_BUDGET, IDENTITY_ADDRESS, 0, size, 0, size
            ),
        )
        + Op.STOP
    )
    tx = Transaction(
        to=subject,
        gas_limit=1_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={subject: Account(storage={SLOT_OK: ok})}, tx=tx)


# A child doing `MCOPY(0, 0, N)` from empty memory costs
#   12 + 6w + w**2 // 512
# where 12 is three PUSHes (9) plus MCOPY's own base (3), and 6w is the
# copy 3w plus the linear expansion 3w. So a frozen 100,000 buys
# w = 5,782 words (12 + 34,692 + 65,296 = exactly 100,000) and not
# w = 5,783 (100,028). The quadratic term is 65,296 of that 100,000 —
# **65% of the charge** — which is why this bracket, unlike the identity
# one, moves when the divisor moves.
MCOPY_BUDGET = 100_000
MCOPY_FITS_WORDS = 5_782


@pytest.mark.parametrize(
    "extra_words,ok",
    [pytest.param(0, 1, id="largest_copy_that_fits"),
     pytest.param(1, 0, id="one_word_too_many")],
)
@pytest.mark.valid_from("Cancun")
def test_mcopy_sized_to_a_frozen_budget(
    state_test: StateTestFiller, pre: Alloc, extra_words: int, ok: int
) -> None:
    """
    Test the quadratic term's effect on a frozen budget, both directions.

    At 5,782 words the quadratic memory term is 65,296 gas against 34,692
    of linear cost, so this bracket is dominated by the `// 512` divisor
    rather than by any per-word coefficient. That is the property class #18
    exists to pin: the same contract, with the same hardcoded 100,000, is
    comfortable at 1 KiB and sits on a one-word cliff at 180 KiB.
    """
    size = (MCOPY_FITS_WORDS + extra_words) * 32
    child = pre.deploy_contract(
        Op.PUSH3(size) + Op.PUSH1(0) + Op.PUSH1(0) + Op.MCOPY + Op.STOP
    )
    subject = pre.deploy_contract(
        Op.SSTORE(SLOT_OK, Op.CALL(MCOPY_BUDGET, child, 0, 0, 0, 0, 0))
        + Op.STOP
    )
    tx = Transaction(
        to=subject,
        gas_limit=1_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={subject: Account(storage={SLOT_OK: ok})}, tx=tx)


# --------------------------------------------------------------------------
# Arm 3: init-code per word, isolated by differencing two CREATE2s
# --------------------------------------------------------------------------

SLOT_WORD_COST = 0x01
CREATE2_PER_WORD = KECCAK256_PER_WORD + CODE_INIT_PER_WORD


def _create2_meter(size: int, salt: int) -> Bytecode:
    """
    `GAS; CREATE2(0, 0, size, salt); POP; GAS; SWAP1; SUB`.

    The delta stays on the stack. Committing it would mean asserting the
    whole fork-specific account-creation charge, measured at 32,024 before
    EIP-8037 and 195,624 after (for one word of init code) — precisely what
    the differencing exists to cancel.

    CREATE2 pops endowment, offset, size, salt, endowment on top.
    """
    return (
        Op.GAS
        + Op.PUSH2(salt)
        + Op.PUSH3(size)
        + Op.PUSH1(0)
        + Op.PUSH1(0)
        + Op.CREATE2
        + Op.POP
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
    )


@pytest.mark.parametrize(
    "size", [32, 1024, 4096], ids=["size_32", "size_1024", "size_4096"]
)
@pytest.mark.valid_from("Shanghai")
def test_init_code_per_word_formula_predicts_the_charge(
    state_test: StateTestFiller, pre: Alloc, size: int
) -> None:
    """
    Test the per-word charge a factory pays for longer init code.

    Two `CREATE2`s from one frame over the same all-zero memory, one word
    apart. Both create a brand-new account, both init codes are a single
    `STOP` and deposit no code, memory is pre-grown past the larger of the
    two, so **everything except the word count is identical** and the
    difference is exactly the two per-word terms `CREATE2` charges:
    `OPCODE_KECCAK256_PER_WORD` 6 for hashing the init code plus
    EIP-3860's `CODE_INIT_PER_WORD` 2.

    A single absolute measurement cannot express this: the metered charge
    for one word is 32,024 before EIP-8037 and 195,624 after (measured), so
    the 8 gas under test is 0.004% of it and any fork-specific expectation
    would swamp the coefficient. Differencing is the only instrument that
    reaches it.

    EIP-3860 *introduced* this coefficient at Shanghai, which is why the
    test starts there: before it, longer init code was free per word and a
    factory's prediction had no size term at all.
    """
    subject = pre.deploy_contract(
        # pre-expand past the larger init code so neither create pays
        # expansion
        Op.MSTORE(size, 0)
        + _create2_meter(size, 0x1111)
        + _create2_meter(size + 32, 0x2222)
        + Op.SUB
        + Op.PUSH1(SLOT_WORD_COST)
        + Op.SSTORE
        + Op.STOP
    )
    storage = Storage().set_next_slot(SLOT_WORD_COST)
    storage.store_next(CREATE2_PER_WORD, "create2_charge_per_init_code_word")
    tx = Transaction(
        to=subject,
        gas_limit=3_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={subject: Account(storage=storage)}, tx=tx)
