"""Test execution of EOF code in the context of the operand stack height."""

import pytest

from ethereum_test_exceptions import EOFException
from ethereum_test_tools import Account, EOFStateTestFiller
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.constants import MAX_RUNTIME_STACK_HEIGHT
from ethereum_test_types.eof.v1 import Container, Section
from ethereum_test_types.eof.v1.constants import (
    MAX_CODE_INPUTS,
    MAX_STACK_INCREASE_LIMIT,
    NON_RETURNING_SECTION,
)

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-5450.md"
REFERENCE_SPEC_VERSION = "f20b164b00ae5553f7536a6d7a83a0f254455e09"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize("code_inputs", [0, 1, 16, 127, 128])
@pytest.mark.parametrize("call_op", [Op.CALLF, Op.JUMPF])
def test_execution_at_max_stack_height(
    eof_state_test: EOFStateTestFiller, code_inputs: int, call_op: Op
):
    """
    Test execution at the maximum runtime operand stack height (1024).
    EOF doesn't allow to increase the stack height of a single code section more than 1023.
    The effect of the maximum runtime stack height is achieved by using non-zero number
    of the code section inputs and increasing the runtime stack to the limit accordingly.
    The test pushes consecutive numbers starting from 0 (including inputs).
    At the maximum stack height SSTORE is used so it should store 1022 at key 1023.
    """
    max_stack_increase = MAX_RUNTIME_STACK_HEIGHT - code_inputs
    container = Container(
        sections=[
            Section.Code(
                (
                    sum(Op.PUSH1(x) for x in range(code_inputs))
                    + call_op[1]
                    + (Op.STOP if call_op == Op.CALLF else b"")
                ),
            ),
            Section.Code(
                sum(Op.PUSH2(x) for x in range(code_inputs, MAX_RUNTIME_STACK_HEIGHT))
                + Op.SSTORE
                + Op.POP * (MAX_RUNTIME_STACK_HEIGHT - Op.SSTORE.popped_stack_items)
                + (Op.RETF if call_op == Op.CALLF else Op.STOP),
                code_inputs=code_inputs,
                code_outputs=0 if call_op == Op.CALLF else NON_RETURNING_SECTION,
                max_stack_increase=max_stack_increase,
            ),
        ],
    )

    exception = None
    if max_stack_increase > MAX_STACK_INCREASE_LIMIT:
        exception = EOFException.MAX_STACK_INCREASE_ABOVE_LIMIT
    elif code_inputs > MAX_CODE_INPUTS:
        exception = EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT

    eof_state_test(
        container=container,
        expect_exception=exception,
        container_post=Account(
            storage={MAX_RUNTIME_STACK_HEIGHT - 1: MAX_RUNTIME_STACK_HEIGHT - 2}
        ),
    )
