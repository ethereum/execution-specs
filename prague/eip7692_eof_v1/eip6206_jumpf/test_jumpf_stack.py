"""
EOF JUMPF tests covering stack validation rules.
"""
import pytest

from ethereum_test_tools import Account, EOFException, EOFStateTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .helpers import slot_code_worked, value_code_worked
from .spec import EOF_FORK_NAME

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
                code_outputs=NON_RETURNING_SECTION,
            ),
            Section.Code(
                code=Op.PUSH0 * stack_height + Op.JUMPF[2],
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=stack_height,
            ),
            Section.Code(
                code=Op.POP * target_inputs
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
                code_inputs=target_inputs,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=max(2, target_inputs),
            ),
        ],
    )

    if stack_height < target_inputs:
        container.validity_error = EOFException.STACK_UNDERFLOW

    eof_state_test(
        data=container,
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        tx_data=b"\1",
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
    ids=lambda x: "to-%d" % x,
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
                code_outputs=NON_RETURNING_SECTION,
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
        data=container,
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        tx_data=b"\1",
    )
