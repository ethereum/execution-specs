"""
Test division and modulo opcodes with a zero divisor or modulus.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmArithmeticTest/divByZeroFiller.yml

@manually-enhanced: Do not overwrite. One contract per opcode.

Each case runs one contract that applies the opcode to every dividend
(or, for ADDMOD and MULMOD, every pair of addends or factors) with a
zero divisor, storing each result in its own slot pre-set to a
sentinel, so the zero result the EVM defines is actually observed. The
operands reach the stack from PUSH data (static) or calldata (dynamic).
"""

from itertools import product

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op, Opcode

from tests.ported_static.helpers import Operands

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmArithmeticTest/divByZeroFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize("operand_source", list(Operands.Source), ids=str),
]

SENTINEL = 0x0BAD
INT_MAX = 2**255 - 1
INT_MIN = 2**255


def neg(value: int) -> int:
    """Return the 256-bit two's complement encoding of `-value`."""
    return -value % 2**256


DIVIDENDS = (2, 1, 0, neg(1), neg(2), INT_MAX, INT_MIN)
# The EVM defines division and modulo by zero to return zero.
RESULT_BY_ZERO = 0


@pytest.fixture
def operands(operand_source: Operands.Source) -> Operands:
    """Return the operand supplier for the parametrized source."""
    return Operands(operand_source)


@pytest.mark.parametrize(
    "opcode",
    [Op.DIV, Op.SDIV, Op.MOD, Op.SMOD, Op.ADDMOD, Op.MULMOD],
    ids=lambda opcode: opcode._name_.lower(),
)
def test_div_by_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Opcode,
    operands: Operands,
) -> None:
    """Store the opcode's result for each dividend and a zero divisor."""
    if opcode in (Op.DIV, Op.SDIV, Op.MOD, Op.SMOD):
        dividends: list[tuple[int, ...]] = [(a,) for a in DIVIDENDS]
    elif opcode in (Op.ADDMOD, Op.MULMOD):
        dividends = list(product(DIVIDENDS, repeat=2))
    else:
        raise ValueError(f"Unexpected opcode: {opcode}")

    code = Bytecode()
    for slot, dividend in enumerate(dividends):
        stack_operands = [operands(value) for value in (*dividend, 0)]
        code += Op.SSTORE(slot, opcode(*stack_operands))
    code += Op.STOP

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(range(len(dividends)), SENTINEL)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {
        contract: Account(
            storage=dict.fromkeys(range(len(dividends)), RESULT_BY_ZERO)
        )
    }
    state_test(pre=pre, post=post, tx=tx)
