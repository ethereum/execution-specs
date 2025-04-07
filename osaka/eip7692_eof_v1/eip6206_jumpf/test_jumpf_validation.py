"""EOF validation tests for JUMPF instruction."""

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from ..eip4750_functions.test_code_validation import MAX_RUNTIME_OPERAND_STACK_HEIGHT

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6206.md"
REFERENCE_SPEC_VERSION = "2f365ea0cd58faa6e26013ea77ce6d538175f7d0"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="to_0",
            sections=[
                Section.Code(
                    Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    Op.JUMPF[0],
                    code_outputs=0,
                ),
            ],
        ),
        Container(
            name="to_2",
            sections=[
                Section.Code(
                    Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    Op.JUMPF[2],
                    code_outputs=0,
                ),
                Section.Code(
                    Op.INVALID,
                ),
            ],
        ),
        Container(
            name="to_retf",
            sections=[
                Section.Code(
                    Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    Op.JUMPF[2],
                    code_outputs=0,
                ),
                Section.Code(
                    Op.RETF,
                ),
            ],
        ),
    ],
    ids=lambda container: container.name,
)
def test_returning_jumpf(
    eof_test: EOFTestFiller,
    container: Container,
):
    """Test cases for JUMPF instruction validation in a returning sections."""
    eof_test(container=container, expect_exception=EOFException.INVALID_NON_RETURNING_FLAG)


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="jumpf1",
            sections=[
                Section.Code(
                    Op.JUMPF[1],
                )
            ],
        ),
        Container(
            name="jumpf2",
            sections=[
                Section.Code(
                    Op.JUMPF[2],
                ),
                Section.Code(
                    Op.STOP,
                ),
            ],
        ),
        Container(
            name="jumpf1_jumpf2",
            sections=[
                Section.Code(
                    Op.JUMPF[1],
                ),
                Section.Code(
                    Op.JUMPF[2],
                ),
            ],
        ),
    ],
    ids=lambda container: container.name,
)
def test_invalid_code_section_index(
    eof_test: EOFTestFiller,
    container: Container,
):
    """Test cases for JUMPF instructions with invalid target code section index."""
    eof_test(container=container, expect_exception=EOFException.INVALID_CODE_SECTION_INDEX)


def test_returning_section_aborts_jumpf(
    eof_test: EOFTestFiller,
):
    """
    Test EOF container validation where in the same code section we have returning
    and nonreturning terminating instructions.
    """
    container = Container(
        sections=[
            Section.Code(code=Op.CALLF[1] + Op.STOP, max_stack_height=1),
            Section.Code(
                code=Op.PUSH0 * 2 + Op.RJUMPI[4] + Op.POP + Op.JUMPF[2] + Op.RETF,
                code_outputs=1,
            ),
            Section.Code(
                code=Op.PUSH0 * 2 + Op.RJUMPI[1] + Op.RETF + Op.INVALID,
                code_inputs=0,
                code_outputs=1,
            ),
        ],
    )
    eof_test(container=container)


@pytest.mark.parametrize("stack_height", [512, 513, 1023])
def test_jumpf_self_stack_overflow(eof_test: EOFTestFiller, stack_height: int):
    """Test JUMPF instruction jumping to itself causing validation time stack overflow."""
    container = Container(
        sections=[
            Section.Code(
                code=(Op.PUSH0 * stack_height) + Op.JUMPF[0],
                max_stack_height=stack_height,
            ),
        ],
    )
    stack_overflow = stack_height > MAX_RUNTIME_OPERAND_STACK_HEIGHT // 2
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_OVERFLOW if stack_overflow else None,
    )


@pytest.mark.parametrize("stack_height_other", [1, 2, 512, 513, 1023])
@pytest.mark.parametrize("stack_height", [1, 2, 512, 513, 1023])
def test_jumpf_other_stack_overflow(
    eof_test: EOFTestFiller, stack_height: int, stack_height_other: int
):
    """Test JUMPF instruction jumping to itself causing validation time stack overflow."""
    container = Container(
        sections=[
            Section.Code(
                code=(Op.PUSH0 * stack_height) + Op.JUMPF[1],
                max_stack_height=stack_height,
            ),
            Section.Code(
                code=(Op.PUSH0 * stack_height_other) + Op.STOP,
                max_stack_height=stack_height_other,
            ),
        ],
    )
    stack_overflow = stack_height + stack_height_other > MAX_RUNTIME_OPERAND_STACK_HEIGHT
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_OVERFLOW if stack_overflow else None,
    )


@pytest.mark.parametrize("code_inputs", [0, 3])
@pytest.mark.parametrize("stack_height", [0, 2, 3, 4])
def test_jumpf_to_non_returning(eof_test: EOFTestFiller, stack_height: int, code_inputs: int):
    """Test JUMPF jumping to a non-returning function."""
    container = Container(
        sections=[
            Section.Code(
                code=Op.PUSH0 * stack_height + Op.JUMPF[1], max_stack_height=stack_height
            ),
            Section.Code(code=Op.STOP, code_inputs=code_inputs, max_stack_height=code_inputs),
        ],
    )
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_UNDERFLOW if stack_height < code_inputs else None,
    )


@pytest.mark.parametrize("code_inputs", [0, 1, 3, 5])
def test_jumpf_to_non_returning_variable_stack(eof_test: EOFTestFiller, code_inputs: int):
    """Test JUMPF jumping to a non-returning function with stack depending on RJUMPI."""
    container = Container(
        sections=[
            Section.Code(
                code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 * 2 + Op.JUMPF[1],
                max_stack_height=3,
            ),
            Section.Code(code=Op.INVALID, code_inputs=code_inputs, max_stack_height=code_inputs),
        ],
    )
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_UNDERFLOW if code_inputs >= 3 else None,
    )


@pytest.mark.parametrize("code_inputs", [0, 3])
@pytest.mark.parametrize("code_outputs", [1, 2])
@pytest.mark.parametrize("stack_height", [0, 1, 2, 3, 4, 5])
def test_jumpf_to_returning(
    eof_test: EOFTestFiller, code_inputs: int, code_outputs: int, stack_height: int
):
    """Test JUMPF jumping to a returning function."""
    exceptions = []
    if code_inputs > stack_height or (stack_height - code_inputs + code_outputs) < 2:
        exceptions.append(EOFException.STACK_UNDERFLOW)
    if stack_height - code_inputs + code_outputs > 2:
        exceptions.append(EOFException.STACK_HIGHER_THAN_OUTPUTS)

    third_cs_stack_height = code_inputs if code_inputs > code_outputs else code_outputs
    third_cs = None
    if code_outputs < code_inputs:
        third_cs = Op.POP * (code_inputs - code_outputs) + Op.RETF
    else:
        third_cs = Op.PUSH0 * (code_outputs - code_inputs) + Op.RETF

    container = Container(
        sections=[
            Section.Code(code=Op.CALLF[1] + Op.STOP, max_stack_height=2),
            Section.Code(code=Op.PUSH0 * stack_height + Op.JUMPF[2], code_outputs=2),
            Section.Code(
                code=third_cs,
                code_inputs=code_inputs,
                code_outputs=code_outputs,
                max_stack_height=third_cs_stack_height,
            ),
        ],
    )

    eof_test(
        container=container,
        expect_exception=exceptions if exceptions else None,
    )


@pytest.mark.parametrize("code_inputs", [0, 1, 3, 5])
@pytest.mark.parametrize("code_outputs", [1, 3])
@pytest.mark.parametrize("stack_increase", [0, 1, 2, 3, 4])
def test_jumpf_to_returning_variable_stack_1(
    eof_test: EOFTestFiller,
    code_inputs: int,
    code_outputs: int,
    stack_increase: int,
):
    """Test JUMPF with variable stack jumping to a returning function increasing the stack."""
    exception = None
    if code_inputs >= 3 or code_outputs + 1 < 3:  # 3 = Section 1's max stack
        exception = EOFException.STACK_UNDERFLOW
    if 3 - code_inputs + code_outputs > 3:
        exception = EOFException.STACK_HIGHER_THAN_OUTPUTS

    container = Container(
        sections=[
            Section.Code(code=Op.CALLF[1] + Op.STOP, max_stack_height=3),
            Section.Code(
                code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 * 2 + Op.JUMPF[2],
                code_outputs=3,
                max_stack_height=3,
            ),
            Section.Code(
                code=Op.PUSH0 * stack_increase + Op.RETF,
                code_inputs=code_inputs,
                code_outputs=code_outputs,
                max_stack_height=code_inputs if code_inputs > code_outputs else code_outputs,
            ),
        ],
    )

    eof_test(
        container=container,
        expect_exception=exception,
    )


@pytest.mark.parametrize("code_inputs", [1, 3, 5])
@pytest.mark.parametrize("code_outputs", [1])
@pytest.mark.parametrize("stack_decrease", [0, 2, 4])
def test_jumpf_to_returning_variable_stack_2(
    eof_test: EOFTestFiller,
    code_inputs: int,
    code_outputs: int,
    stack_decrease: int,
):
    """Test JUMPF with variable stack jumping to a returning function decreasing the stack."""
    exceptions = []
    if code_inputs >= 3 or code_outputs + 1 < 3:  # 3 = Section 1's max stack
        exceptions.append(EOFException.STACK_UNDERFLOW)
    if 3 - code_inputs + code_outputs > 2:
        exceptions.append(EOFException.STACK_HIGHER_THAN_OUTPUTS)

    container = Container(
        sections=[
            Section.Code(code=Op.CALLF[1] + Op.STOP, max_stack_height=2),
            Section.Code(
                code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 * 2 + Op.JUMPF[2],
                code_outputs=2,
                max_stack_height=3,
            ),
            Section.Code(
                code=Op.POP * stack_decrease + Op.RETF,
                code_inputs=code_inputs,
                code_outputs=code_outputs,
                max_stack_height=code_inputs if code_inputs > code_outputs else code_outputs,
            ),
        ],
    )

    eof_test(
        container=container,
        expect_exception=exceptions,
    )


def test_jumpf_to_returning_variable_stack_3(eof_test: EOFTestFiller):
    """Test JUMPF with variable stack jumping to a returning function increasing the stack."""
    container = Container(
        sections=[
            Section.Code(code=Op.CALLF[1] + Op.STOP, max_stack_height=2),
            Section.Code(
                code=Op.PUSH0 + Op.PUSH1[0] + Op.RJUMPI[2] + Op.PUSH0 * 2 + Op.JUMPF[2],
                code_outputs=2,
                max_stack_height=3,
            ),
            Section.Code(
                code=Op.PUSH0 + Op.RETF,
                code_outputs=1,
                max_stack_height=1,
            ),
        ],
    )

    eof_test(
        container=container,
        expect_exception=EOFException.STACK_HIGHER_THAN_OUTPUTS,
    )
