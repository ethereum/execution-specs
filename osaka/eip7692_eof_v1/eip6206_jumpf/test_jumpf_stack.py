"""EOF JUMPF tests covering stack validation rules."""

import pytest

from ethereum_test_specs import EOFTestFiller
from ethereum_test_tools import Account, EOFException, EOFStateTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from ..eip4750_functions.test_code_validation import MAX_RUNTIME_OPERAND_STACK_HEIGHT
from .helpers import slot_code_worked, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6206.md"
REFERENCE_SPEC_VERSION = "2f365ea0cd58faa6e26013ea77ce6d538175f7d0"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "target_inputs",
    [0, 2, 4],
    ids=lambda x: "ti-%d" % x,
)
@pytest.mark.parametrize(
    "stack_height",
    [0, 2, 4],
    ids=lambda x: "h-%d" % x,
)
def test_jumpf_stack_non_returning_rules(
    eof_state_test: EOFStateTestFiller,
    target_inputs: int,
    stack_height: int,
):
    """
    Tests for JUMPF validation stack rules.  Non-returning section cases.
    Valid cases are executed.
    """
    container = Container(
        name="stack-non-retuning_h-%d_ti-%d" % (stack_height, target_inputs),
        sections=[
            Section.Code(
                code=Op.JUMPF[1],
            ),
            Section.Code(
                code=Op.PUSH0 * stack_height + Op.JUMPF[2],
                max_stack_height=stack_height,
            ),
            Section.Code(
                code=Op.POP * target_inputs
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
                code_inputs=target_inputs,
                max_stack_height=max(2, target_inputs),
            ),
        ],
    )

    if stack_height < target_inputs:
        container.validity_error = EOFException.STACK_UNDERFLOW

    eof_state_test(
        container=container,
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        data=b"\1",
    )


@pytest.mark.parametrize(
    "source_outputs",
    [0, 2, 4],
    ids=lambda x: "so-%d" % x,
)
@pytest.mark.parametrize(
    "target_outputs",
    [0, 2, 4],
    ids=lambda x: "to-%d" % x,
)
@pytest.mark.parametrize(
    "target_inputs",
    [0, 2, 4],
    ids=lambda x: "ti-%d" % x,
)
@pytest.mark.parametrize("stack_diff", [-1, 0, 1], ids=["less-stack", "same-stack", "more-stack"])
def test_jumpf_stack_returning_rules(
    eof_state_test: EOFStateTestFiller,
    source_outputs: int,
    target_outputs: int,
    target_inputs: int,
    stack_diff: int,
):
    """
    Tests for JUMPF validation stack rules.  Returning section cases.
    Valid cases are executed.
    """
    if target_outputs > source_outputs:
        # These create invalid containers without JUMPF validation, Don't test.
        return
    if target_inputs == 0 and stack_diff < 0:
        # Code generation is impossible for this configuration.  Don't test.
        return

    target_delta = target_outputs - target_inputs
    container = Container(
        name="stack-retuning_co-%d_to-%d_ti-%d_diff-%d"
        % (source_outputs, target_outputs, target_inputs, stack_diff),
        sections=[
            Section.Code(
                code=Op.CALLF[1] + Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                max_stack_height=2 + source_outputs,
            ),
            Section.Code(
                code=Op.PUSH0 * max(0, target_inputs + stack_diff) + Op.JUMPF[2],
                code_outputs=source_outputs,
                max_stack_height=target_inputs,
            ),
            Section.Code(
                code=(Op.POP * -target_delta if target_delta < 0 else Op.PUSH0 * target_delta)
                + Op.RETF,
                code_inputs=target_inputs,
                code_outputs=target_outputs,
                max_stack_height=max(target_inputs, target_outputs),
            ),
        ],
    )

    if stack_diff < source_outputs - target_outputs:
        container.validity_error = EOFException.STACK_UNDERFLOW
    elif stack_diff > source_outputs - target_outputs:
        container.validity_error = EOFException.STACK_HIGHER_THAN_OUTPUTS

    eof_state_test(
        container=container,
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        data=b"\1",
    )


@pytest.mark.parametrize(
    ["target_inputs", "target_outputs", "stack_height", "expected_exception"],
    [
        pytest.param(1, 0, 1, EOFException.STACK_UNDERFLOW, id="less_stack"),
        pytest.param(2, 1, 2, None, id="same_stack"),
        pytest.param(
            3, 2, 3, EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS, id="more_stack"
        ),
        pytest.param(
            2, 2, 1, EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS, id="less_output"
        ),
        pytest.param(1, 1, 1, None, id="same_output"),
        pytest.param(0, 0, 1, None, id="more_output"),
    ],
)
def test_jumpf_incompatible_outputs(
    eof_test: EOFTestFiller,
    target_inputs: int,
    target_outputs: int,
    stack_height: int,
    expected_exception: EOFException,
):
    """Tests JUMPF into a section with incorrect number of outputs."""
    current_section_outputs = 1
    if (current_section_outputs + target_inputs - target_outputs) != stack_height:
        assert expected_exception is not None
    eof_test(
        container=Container(
            sections=[
                Section.Code(Op.CALLF(1) + Op.STOP, max_stack_height=1),
                Section.Code(
                    Op.PUSH0 * stack_height + Op.JUMPF(2),
                    code_outputs=current_section_outputs,
                ),
                Section.Code(
                    Op.POP * (target_inputs - target_outputs) + Op.RETF,
                    code_inputs=target_inputs,
                    code_outputs=target_outputs,
                    max_stack_height=target_inputs,
                ),
            ]
        ),
        expect_exception=expected_exception,
    )


@pytest.mark.parametrize(
    ["target_inputs", "target_outputs", "stack_height", "expected_exception"],
    [
        pytest.param(1, 0, 1, EOFException.STACK_UNDERFLOW, id="less_stack"),
        pytest.param(2, 1, 2, EOFException.STACK_HIGHER_THAN_OUTPUTS, id="same_stack"),
        pytest.param(
            3, 2, 3, EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS, id="more_stack"
        ),
        pytest.param(
            2, 2, 1, EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS, id="less_output"
        ),
        pytest.param(1, 1, 1, EOFException.STACK_HIGHER_THAN_OUTPUTS, id="same_output"),
        pytest.param(0, 0, 1, EOFException.STACK_HIGHER_THAN_OUTPUTS, id="more_output"),
    ],
)
def test_jumpf_diff_max_stack_height(
    eof_test: EOFTestFiller,
    target_inputs: int,
    target_outputs: int,
    stack_height: int,
    expected_exception: EOFException,
):
    """Tests jumpf with a different max stack height."""
    current_section_outputs = 1
    eof_test(
        container=Container(
            sections=[
                Section.Code(Op.CALLF(1) + Op.STOP, max_stack_height=1),
                Section.Code(
                    (Op.PUSH0 * stack_height)  # (0, 0)
                    + Op.PUSH0  # (stack_height, stack_height)
                    + Op.RJUMPI[1]  # (stack_height + 1, stack_height + 1)
                    + Op.PUSH0  # (stack_height, stack_height)
                    + Op.JUMPF(2),  # (stack_height, stack_height + 1)
                    code_outputs=current_section_outputs,
                ),
                Section.Code(
                    Op.POP * (target_inputs - target_outputs) + Op.RETF,
                    code_inputs=target_inputs,
                    code_outputs=target_outputs,
                    max_stack_height=target_inputs,
                ),
            ]
        ),
        expect_exception=expected_exception,
    )


@pytest.mark.parametrize(
    ["target_inputs", "target_outputs", "stack_height", "expected_exception"],
    [
        pytest.param(1, 0, 1, EOFException.STACK_UNDERFLOW, id="less_stack"),
        pytest.param(2, 1, 2, EOFException.STACK_UNDERFLOW, id="same_stack"),
        pytest.param(
            3, 2, 3, EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS, id="more_stack"
        ),
        pytest.param(
            2, 2, 1, EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS, id="less_output"
        ),
        pytest.param(1, 1, 1, EOFException.STACK_UNDERFLOW, id="same_output"),
        pytest.param(0, 0, 1, EOFException.STACK_UNDERFLOW, id="more_output"),
    ],
)
def test_jumpf_diff_min_stack_height(
    eof_test: EOFTestFiller,
    target_inputs: int,
    target_outputs: int,
    stack_height: int,
    expected_exception: EOFException,
):
    """Tests jumpf with a different min stack height."""
    current_section_outputs = 1
    eof_test(
        container=Container(
            sections=[
                Section.Code(Op.CALLF(1) + Op.STOP, max_stack_height=1),
                Section.Code(
                    (Op.PUSH0 * (stack_height - 1))  # (0, 0)
                    + Op.PUSH0  # (stack_height - 1, stack_height - 1)
                    + Op.RJUMPI[1]  # (stack_height, stack_height)
                    + Op.PUSH0  # (stack_height - 1, stack_height - 1)
                    + Op.JUMPF(2),  # (stack_height - 1, stack_height)
                    code_outputs=current_section_outputs,
                ),
                Section.Code(
                    Op.POP * (target_inputs - target_outputs) + Op.RETF,
                    code_inputs=target_inputs,
                    code_outputs=target_outputs,
                    max_stack_height=target_inputs,
                ),
            ]
        ),
        expect_exception=expected_exception,
    )


def test_jumpf_self_variadic_stack_overflow(eof_test: EOFTestFiller):
    """Test JUMPF calling self causing EOF validation stack overflow."""
    container = Container(
        name="jumpf_stack_overflow_variable_stack_0",
        sections=[
            Section.Code(
                code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 * 511 + Op.JUMPF[0],
                max_stack_height=512,
            ),
        ],
    )
    eof_test(container=container)


@pytest.mark.parametrize("stack_height", [512, 1022, 1023])
@pytest.mark.parametrize("callee_stack_height", [0, 1, 2, 5, 511, 512, 513])
def test_jumpf_variadic_stack_overflow(
    eof_test: EOFTestFiller, stack_height: int, callee_stack_height: int
):
    """Test JUMPF stack validation causing stack overflow with variable stack height."""
    container = Container(
        sections=[
            Section.Code(
                code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 * (stack_height - 1) + Op.JUMPF[1],
                max_stack_height=stack_height,
            ),
            Section.Code(
                code=Op.PUSH0 * callee_stack_height + Op.STOP,
                max_stack_height=callee_stack_height,
            ),
        ],
        validity_error=EOFException.STACK_OVERFLOW
        if stack_height + callee_stack_height > MAX_RUNTIME_OPERAND_STACK_HEIGHT
        else None,
    )
    eof_test(container=container)


@pytest.mark.parametrize("stack_height", [1022, 1023])
@pytest.mark.parametrize("callee_stack_increase", [0, 1, 2])
def test_jumpf_with_inputs_stack_overflow(
    eof_test: EOFTestFiller, stack_height: int, callee_stack_increase: int
):
    """Test validation of JUMPF with inputs causing stack overflow."""
    container = Container(
        sections=[
            Section.Code(
                code=Op.PUSH0 * stack_height + Op.JUMPF[1],
                max_stack_height=stack_height,
            ),
            Section.Code(
                code=Op.PUSH0 * callee_stack_increase + Op.STOP,
                code_inputs=2,
                max_stack_height=2 + callee_stack_increase,
            ),
        ],
        validity_error=EOFException.STACK_OVERFLOW
        if stack_height + callee_stack_increase > MAX_RUNTIME_OPERAND_STACK_HEIGHT
        else None,
    )
    eof_test(container=container)


@pytest.mark.parametrize("stack_height", [1022, 1023])
@pytest.mark.parametrize("callee_stack_increase", [0, 1, 2])
def test_jumpf_with_inputs_stack_overflow_variable_stack(
    eof_test: EOFTestFiller, stack_height: int, callee_stack_increase: int
):
    """Test JUMPF with variable stack depending on RJUMPI calling function with inputs."""
    container = Container(
        sections=[
            Section.Code(
                code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 * (stack_height - 1) + Op.JUMPF[1],
                max_stack_height=stack_height,
            ),
            Section.Code(
                code=Op.PUSH0 * callee_stack_increase + Op.STOP,
                code_inputs=2,
                max_stack_height=2 + callee_stack_increase,
            ),
        ],
        validity_error=EOFException.STACK_OVERFLOW
        if stack_height + callee_stack_increase > MAX_RUNTIME_OPERAND_STACK_HEIGHT
        else None,
    )
    eof_test(container=container)
