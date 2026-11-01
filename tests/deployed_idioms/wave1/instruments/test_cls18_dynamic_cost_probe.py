"""
Measurement instrument for class #18, not a corpus test.

What does a frame actually get charged, from inside the EVM, for an
operation whose cost depends on a runtime size? Memory expansion
(quadratic), copy-per-word, KECCAK256-per-word, LOG-per-byte and
EXP-per-byte.

Stage 1 of this probe asserted 0 for every param, so the mismatch message
printed the real charge. Stage 2 (this file) asserts the **derived**
figure, so a clean pass is a confirmation of the model rather than a
fitted constant. Every number below was first observed, then derived, and
the two agree exactly.

The instrument is **stack-only**: both `GAS` readings stay on the stack and
nothing is written to memory before the operation, so the operation's own
memory expansion starts from an empty memory and is not perturbed by the
instrument. (A memory-based instrument, as `test_storage_cost_probe.py`
uses, would pre-expand memory by two words and change every expansion
figure measured here.)

Reproduce (from engine/eels):
  python3 ../../tools/locked_fill.py ../../wave1/instruments \\
      --from Berlin --until Amsterdam -k cls18 --output /tmp/c18 \\
      -q --tb=line -p no:cacheprovider
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

SLOT_MEASURED = 0x09

MEMORY_PER_WORD = 3
QUADRATIC_DIVISOR = 512
COPY_PER_WORD = 3
KECCAK256_PER_WORD = 6
LOG_DATA_PER_BYTE = 8
EXP_PER_BYTE = 50


def mem_cost(words: int) -> int:
    """`calculate_memory_gas_cost`, amsterdam/vm/gas.py:754-758."""
    return MEMORY_PER_WORD * words + words**2 // QUADRATIC_DIVISOR


def _meter(op_with_pushes: Bytecode, prelude: Bytecode = Bytecode()) -> Bytecode:
    """
    prelude (paid before the first GAS) + GAS + op + GAS + SWAP1 + SUB.

    Everything between the two readings is the operand pushes, the
    operation, and the trailing `GAS` (2, charged before it pushes).
    """
    return (
        prelude
        + Op.GAS
        + op_with_pushes
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH1(SLOT_MEASURED)
        + Op.SSTORE
        + Op.STOP
    )


def _expand(n: int) -> Bytecode:
    """Pre-expand memory to exactly n bytes (n a multiple of 32)."""
    return Op.MSTORE(n - 32, 0)


SIZES = [32, 128, 480, 512, 1024, 4096, 32768, 65536]
EXP_BYTES = [1, 2, 4, 8, 16, 32]


def _shape(kind: str, n: int) -> tuple[Bytecode, int]:
    """Return (metered body, derived charge) for one (kind, size) pair."""
    w = n // 32
    if kind == "mcopy_cold":
        # memory empty at the first GAS: base + copy + expansion
        return (
            _meter(Op.PUSH3(n) + Op.PUSH1(0) + Op.PUSH1(0) + Op.MCOPY),
            9 + 3 + COPY_PER_WORD * w + mem_cost(w) + 2,
        )
    if kind == "mcopy_warm":
        # memory already n wide: base + copy only
        return (
            _meter(
                Op.PUSH3(n) + Op.PUSH1(0) + Op.PUSH1(0) + Op.MCOPY,
                prelude=_expand(n),
            ),
            9 + 3 + COPY_PER_WORD * w + 2,
        )
    if kind == "mstore_expand":
        # memory empty: MSTORE base + expansion only
        return (
            _meter(Op.PUSH1(0) + Op.PUSH3(n - 32) + Op.MSTORE),
            6 + 3 + mem_cost(w) + 2,
        )
    if kind == "keccak_warm":
        return (
            _meter(
                Op.PUSH3(n) + Op.PUSH1(0) + Op.SHA3 + Op.POP,
                prelude=_expand(n),
            ),
            6 + 30 + KECCAK256_PER_WORD * w + 2 + 2,
        )
    if kind == "log0_warm":
        return (
            _meter(Op.PUSH3(n) + Op.PUSH1(0) + Op.LOG0, prelude=_expand(n)),
            6 + 375 + LOG_DATA_PER_BYTE * n + 2,
        )
    raise AssertionError(kind)


def _run(
    state_test: StateTestFiller, pre: Alloc, body: Bytecode, expected: int
) -> None:
    subject = pre.deploy_contract(body)
    tx = Transaction(
        to=subject,
        gas_limit=15_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={subject: Account(storage={SLOT_MEASURED: expected})},
        tx=tx,
    )


@pytest.mark.parametrize("kind", ["mstore_expand", "keccak_warm", "log0_warm"])
@pytest.mark.parametrize("size", SIZES)
@pytest.mark.valid_from("Berlin")
def test_cls18_sized_op_cost(
    state_test: StateTestFiller, pre: Alloc, kind: str, size: int
) -> None:
    """Probe: in-frame gas delta across one size-dependent operation."""
    body, expected = _shape(kind, size)
    _run(state_test, pre, body, expected)


@pytest.mark.parametrize("kind", ["mcopy_cold", "mcopy_warm"])
@pytest.mark.parametrize("size", SIZES)
@pytest.mark.valid_from("Cancun")
def test_cls18_mcopy_cost(
    state_test: StateTestFiller, pre: Alloc, kind: str, size: int
) -> None:
    """Probe: the same, for MCOPY (EIP-5656, Cancun onwards)."""
    body, expected = _shape(kind, size)
    _run(state_test, pre, body, expected)


@pytest.mark.parametrize("exp_bytes", EXP_BYTES)
@pytest.mark.valid_from("Berlin")
def test_cls18_exp_cost(
    state_test: StateTestFiller, pre: Alloc, exp_bytes: int
) -> None:
    """Probe: in-frame gas delta across one EXP with an N-byte exponent."""
    exponent = 1 << (8 * (exp_bytes - 1))
    # EXP pops base (top) then exponent, so push the exponent first.
    _run(
        state_test,
        pre,
        _meter(Op.PUSH32(exponent) + Op.PUSH1(1) + Op.EXP + Op.POP),
        6 + 10 + EXP_PER_BYTE * exp_bytes + 2 + 2,
    )


# --------------------------------------------------------------------------
# init-code per word, by differencing two CREATE2s
# --------------------------------------------------------------------------

CODE_INIT_PER_WORD = 2
SLOT_WORD_COST = 0x0C


def _create2_meter(size: int, salt: int) -> Bytecode:
    """
    GAS; CREATE2(value=0, offset=0, size, salt); POP; GAS; SWAP1; SUB.

    Leaves the delta on the stack -- storing the two intermediates would
    need them in the post condition and they carry the whole fork-specific
    CREATE charge, which is what the differencing exists to cancel.

    CREATE2 pops endowment, offset, size, salt -- endowment on top -- so
    the pushes go salt, size, offset, endowment.
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


@pytest.mark.parametrize("size", [32, 1024, 4096])
@pytest.mark.valid_from("Shanghai")
def test_cls18_init_code_word_cost(
    state_test: StateTestFiller, pre: Alloc, size: int
) -> None:
    """
    Probe: the per-word charge for init code, isolated by differencing.

    Two CREATE2s from the same frame over the same all-zero memory, one a
    word longer than the other. Everything else is identical -- the account
    is new in both cases, both init codes are `STOP` and deposit no code --
    so the difference is exactly the per-word terms CREATE2 charges:
    `OPCODE_KECCAK256_PER_WORD` for hashing the init code (6) plus
    `CODE_INIT_PER_WORD` from EIP-3860 (2).
    """
    subject = pre.deploy_contract(
        # pre-expand memory past the larger init code, so neither CREATE2
        # pays any expansion
        _expand(size + 32)
        + _create2_meter(size, 0x1111)
        + _create2_meter(size + 32, 0x2222)
        + Op.SUB
        + Op.PUSH1(SLOT_WORD_COST)
        + Op.SSTORE
        + Op.STOP
    )
    tx = Transaction(
        to=subject,
        gas_limit=3_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={
            subject: Account(
                storage={
                    SLOT_WORD_COST: KECCAK256_PER_WORD + CODE_INIT_PER_WORD
                }
            )
        },
        tx=tx,
    )


# --------------------------------------------------------------------------
# Affordability brackets: where does a frozen budget run out?
# --------------------------------------------------------------------------

IDENTITY_BASE = 15
IDENTITY_PER_WORD = 3
IDENTITY_ADDRESS = 4
SLOT_OK = 0x01

# `15 + 3w <= 1000` holds for w = 328 (999) and fails for w = 329 (1,002).
IDENTITY_BUDGET = 1_000
IDENTITY_BRACKET = [(328 * 32, 1), (329 * 32, 0)]


@pytest.mark.parametrize("size,ok", IDENTITY_BRACKET)
@pytest.mark.valid_from("Berlin")
def test_cls18_identity_precompile_bracket(
    state_test: StateTestFiller, pre: Alloc, size: int, ok: int
) -> None:
    """Probe: the largest identity-precompile copy a 1,000 literal buys."""
    subject = pre.deploy_contract(
        _expand(size)
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
# where 12 is three PUSHes (9) plus MCOPY's base (3), and 6w is copy 3w
# plus linear expansion 3w.
# So a frozen 100,000 buys w = 5,782 words exactly (100,000) and not
# w = 5,783 (100,028). At that size the quadratic term is 65,296 of the
# 100,000 -- 65% of the charge.
MCOPY_BUDGET = 100_000
MCOPY_BRACKET = [(5782 * 32, 1), (5783 * 32, 0)]


@pytest.mark.parametrize("size,ok", MCOPY_BRACKET)
@pytest.mark.valid_from("Cancun")
def test_cls18_mcopy_budget_bracket(
    state_test: StateTestFiller, pre: Alloc, size: int, ok: int
) -> None:
    """Probe: the largest MCOPY a frozen 100,000 buys."""
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
