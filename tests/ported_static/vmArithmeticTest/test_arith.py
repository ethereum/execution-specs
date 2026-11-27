"""
Test a chain of arithmetic opcodes, each applied to the previous result.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmArithmeticTest/arithFiller.yml

@manually-enhanced: Do not overwrite. Built from readable steps.

The contract runs ADD, MUL, DIV, SDIV, SMOD and SUB in a chain, each on
the previous result and a constant, and stores the end of the chain
next to an independent `EXP(17, 9)`. The filler left the chain's result
unobserved on the stack; it is now stored. The constants reach the
stack from PUSH data (static) or calldata (dynamic), and every step's
expected value is computed next to the code that performs it.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
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
        ["state_tests/VMTests/vmArithmeticTest/arithFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize("operand_source", list(Operands.Source), ids=str),
]

POWER_SLOT = 0
CHAIN_SLOT = 1
WORD_MODULUS = 2**256


@pytest.fixture
def operands(operand_source: Operands.Source) -> Operands:
    """Return the operand supplier for the parametrized source."""
    return Operands(operand_source)


def test_arith(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    operands: Operands,
) -> None:
    """Store the end of an arithmetic chain and a power of 17."""
    chain = Op.ADD(operands(1), operands(1))
    expected_chain = 1 + 1
    chain = Op.MUL(operands(7), chain)
    expected_chain *= 7
    chain = Op.ADD(operands(5), chain)
    expected_chain += 5
    chain = Op.DIV(chain, operands(2))
    expected_chain //= 2
    # SDIV and SMOD on non-negative operands match Python's `//` and `%`.
    chain = Op.SDIV(chain, operands(33))
    expected_chain //= 33
    chain = Op.ADD(operands(23), chain)
    expected_chain += 23
    chain = Op.MUL(operands(3), chain)
    expected_chain *= 3
    chain = Op.SMOD(chain, operands(5))
    expected_chain %= 5
    # Wraps below zero.
    chain = Op.SUB(operands(3), chain)
    expected_chain = (3 - expected_chain) % WORD_MODULUS

    code = (
        Op.SSTORE(POWER_SLOT, Op.EXP(operands(17), operands(9)))
        + Op.SSTORE(CHAIN_SLOT, chain)
        + Op.STOP
    )
    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {
        contract: Account(
            storage={POWER_SLOT: 17**9, CHAIN_SLOT: expected_chain}
        )
    }
    state_test(pre=pre, post=post, tx=tx)
