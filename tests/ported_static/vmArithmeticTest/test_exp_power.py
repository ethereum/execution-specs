"""
Test EXP results for powers of 2 and powers of 255, 256 and 257.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmArithmeticTest/expPower2Filler.yml
state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml
state_tests/VMTests/vmArithmeticTest/expPower256Of256Filler.yml

@manually-enhanced: Do not overwrite. Built from a loop over the exponent.

Each case runs one contract that stores the result for every exponent
of a range in its own slot, pre-set to a sentinel so that a result that
wraps to zero is still observable. The bases and exponents reach the
stack from PUSH data (static) or calldata (dynamic), and the expected
storage comes from Python's modular `pow`. `test_exp_power2` raises 2
to `2**m` and its neighbours, `test_exp_power256` raises 255, 256 and
257 to small exponents, and `test_exp_power256_of256` raises them to
the result of a nested EXP.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

from tests.ported_static.helpers import Operands

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/VMTests/vmArithmeticTest/expPower2Filler.yml",
            "state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml",
            "state_tests/VMTests/vmArithmeticTest/expPower256Of256Filler.yml",
        ],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize("operand_source", list(Operands.Source), ids=str),
]

WORD_MODULUS = 2**256
SENTINEL = 0x0BAD
# Powers of 256 overflow a word from exponent 32 on.
EXPONENTS = range(34)
# `test_exp_power2` raises 2 to `2**m + offset` for each of these `m`.
POWER2_LOGS = range(1, 9)
BASES = [255, 256, 257]


@pytest.fixture
def operands(operand_source: Operands.Source) -> Operands:
    """Return the operand supplier for the parametrized source."""
    return Operands(operand_source)


@pytest.mark.parametrize(
    "exponent_offset",
    [
        pytest.param(-1, id="minus_one"),
        pytest.param(0, id="exact"),
        pytest.param(1, id="plus_one"),
    ],
)
def test_exp_power2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    exponent_offset: int,
    operands: Operands,
) -> None:
    """Store `EXP(2, 2**m + exponent_offset)` in slot `m`."""
    code = Bytecode()
    expected = {}
    for m in POWER2_LOGS:
        exponent = 2**m + exponent_offset
        code += Op.SSTORE(m, Op.EXP(operands(2), operands(exponent)))
        expected[m] = pow(2, exponent, WORD_MODULUS)
    code += Op.STOP

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(expected, SENTINEL)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage=expected)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("base", BASES, ids=lambda base: f"base_{base}")
def test_exp_power256(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    base: int,
    operands: Operands,
) -> None:
    """Store `EXP(base, n)` in slot `n`."""
    code = Bytecode()
    expected = {}
    for n in EXPONENTS:
        code += Op.SSTORE(n, Op.EXP(operands(base), operands(n)))
        expected[n] = pow(base, n, WORD_MODULUS)
    code += Op.STOP

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(expected, SENTINEL)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage=expected)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "exponent_base", BASES, ids=lambda base: f"exponent_base_{base}"
)
@pytest.mark.parametrize("base", BASES, ids=lambda base: f"base_{base}")
def test_exp_power256_of256(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    base: int,
    exponent_base: int,
    operands: Operands,
) -> None:
    """Store `EXP(base, EXP(exponent_base, n))` in slot `n`."""
    code = Bytecode()
    expected = {}
    for n in EXPONENTS:
        exponent = Op.EXP(operands(exponent_base), operands(n))
        code += Op.SSTORE(n, Op.EXP(operands(base), exponent))
        expected[n] = pow(
            base, pow(exponent_base, n, WORD_MODULUS), WORD_MODULUS
        )
    code += Op.STOP

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(expected, SENTINEL)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage=expected)}
    state_test(pre=pre, post=post, tx=tx)
