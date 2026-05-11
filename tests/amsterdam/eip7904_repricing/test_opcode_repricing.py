"""
Test EIP-7904 opcode gas repricing.

Verify the new gas cost charged for `MOD`, `SDIV`, `SMOD`, `MULMOD` after the
Amsterdam fork.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import Spec, ref_spec_7904

REFERENCE_SPEC_GIT_PATH = ref_spec_7904.git_path
REFERENCE_SPEC_VERSION = ref_spec_7904.version

pytestmark = [pytest.mark.valid_from("Amsterdam")]


OPCODE_CASES = [
    pytest.param(Op.MOD(7, 3), 2, Spec.OPCODE_MOD, id="mod"),
    pytest.param(Op.SDIV(-7, 3), 2, Spec.OPCODE_SDIV, id="sdiv"),
    pytest.param(Op.SMOD(-7, 3), 2, Spec.OPCODE_SMOD, id="smod"),
    pytest.param(Op.MULMOD(7, 3, 5), 3, Spec.OPCODE_MULMOD, id="mulmod"),
]


@pytest.mark.parametrize(
    "opcode_bytecode,n_operands,expected_gas", OPCODE_CASES
)
def test_opcode_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode_bytecode: Bytecode,
    n_operands: int,
    expected_gas: int,
) -> None:
    """
    Verify the measured gas cost of the repriced opcode matches the new
    EIP-7904 value.
    """
    measure = CodeGasMeasure(
        code=opcode_bytecode,
        # One PUSH1 (3 gas) per operand the bytecode pushed onto the stack.
        overhead_cost=3 * n_operands,
        extra_stack_items=1,
    )
    contract = pre.deploy_contract(code=measure)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=1_000_000,
    )

    post = {contract: Account(storage={0: expected_gas})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "opcode_bytecode,n_operands,expected_gas", OPCODE_CASES
)
def test_opcode_oog_at_new_price(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode_bytecode: Bytecode,
    n_operands: int,
    expected_gas: int,
) -> None:
    """
    Run the opcode in a sub-call with one gas less than the new EIP-7904 cost
    and assert the sub-call runs out of gas (CALL returns 0).
    """
    # Operand pushes (PUSH1 * n) consume 3 gas each before the opcode runs.
    sub_call_gas = 3 * n_operands + expected_gas - 1

    callee = pre.deploy_contract(code=opcode_bytecode + Op.STOP)
    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(sub_call_gas, callee, 0, 0, 0, 0, 0))
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=1_000_000,
    )

    # CALL returns 0 when the sub-call hits OOG.
    post = {caller: Account(storage={0: 0})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
