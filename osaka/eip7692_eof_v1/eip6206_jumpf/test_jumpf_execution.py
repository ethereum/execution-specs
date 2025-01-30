"""EOF JUMPF tests covering simple cases."""

import pytest

from ethereum_test_tools import Account, EOFException, EOFStateTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import slot_code_worked, slot_stack_canary, value_canary_written, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6206.md"
REFERENCE_SPEC_VERSION = "2f365ea0cd58faa6e26013ea77ce6d538175f7d0"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_jumpf_forward(
    eof_state_test: EOFStateTestFiller,
):
    """Test JUMPF jumping forward."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[1],
                ),
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        data=b"\1",
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="forward",
            sections=[
                Section.Code(
                    code=Op.CALLF[1] + Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                ),
                Section.Code(
                    code=Op.JUMPF[2],
                    code_outputs=0,
                ),
                Section.Code(
                    code=Op.RETF,
                    code_outputs=0,
                ),
            ],
        ),
        Container(
            name="backward",
            sections=[
                Section.Code(
                    code=Op.CALLF[2] + Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                ),
                Section.Code(
                    code=Op.RETF,
                    code_outputs=0,
                ),
                Section.Code(
                    code=Op.JUMPF[1],
                    code_outputs=0,
                ),
            ],
        ),
    ],
    ids=lambda container: container.name,
)
def test_jumpf_to_retf(eof_state_test: EOFStateTestFiller, container: Container):
    """Tests JUMPF to a returning section with RETF."""
    eof_state_test(
        container=container,
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        data=b"\1",
    )


def test_jumpf_to_self(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to self."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.SLOAD(slot_code_worked)
                    + Op.ISZERO
                    + Op.RJUMPI[1]
                    + Op.STOP
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.JUMPF[0],
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        data=b"\1",
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="1_to_2_arg0",
            sections=[
                Section.Code(
                    Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    Op.PUSH0 + Op.RJUMPI[3] + Op.JUMPF[2] + Op.RETF,
                    code_outputs=0,
                ),
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.RETF,
                    code_outputs=0,
                ),
            ],
        ),
        Container(
            name="1_to_2_arg1",
            sections=[
                Section.Code(
                    Op.PUSH1[1] + Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    Op.RJUMPI[1]
                    + Op.RETF
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.JUMPF[2],
                    code_inputs=1,
                    code_outputs=0,
                ),
                Section.Code(
                    Op.RETF,
                    code_outputs=0,
                ),
            ],
        ),
        Container(
            name="1_to_0_to_1",
            sections=[
                Section.Code(
                    Op.ISZERO(Op.SLOAD(slot_code_worked)) + Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    Op.RJUMPI[1]
                    + Op.RETF
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.JUMPF[0],
                    code_inputs=1,
                    code_outputs=0,
                ),
            ],
        ),
        Container(
            name="retf_in_nonreturning",
            sections=[
                Section.Code(
                    Op.PUSH0 + Op.JUMPF[1],
                ),
                Section.Code(
                    Op.RJUMPI[1] + Op.RETF + Op.JUMPF[0],
                    code_inputs=1,
                ),
            ],
            validity_error=EOFException.INVALID_NON_RETURNING_FLAG,
        ),
        Container(
            name="jumpf_to_returning",
            sections=[
                Section.Code(
                    Op.PUSH0 + Op.JUMPF[1],
                ),
                Section.Code(
                    Op.RJUMPI[1] + Op.RETF + Op.JUMPF[2],
                    code_inputs=1,
                ),
                Section.Code(
                    Op.RETF,
                    code_outputs=0,
                ),
            ],
            validity_error=EOFException.INVALID_NON_RETURNING_FLAG,
        ),
        Container(
            name="jumpf_to_returning_2",
            sections=[
                Section.Code(
                    Op.PUSH0 + Op.JUMPF[1],
                ),
                Section.Code(
                    Op.RJUMPI[3] + Op.JUMPF[2] + Op.RETF,
                    code_inputs=1,
                ),
                Section.Code(
                    Op.RETF,
                    code_outputs=0,
                ),
            ],
            validity_error=EOFException.INVALID_NON_RETURNING_FLAG,
        ),
    ],
    ids=lambda container: container.name,
)
def test_jumpf_and_retf(eof_state_test: EOFStateTestFiller, container: Container):
    """Tests JUMPF and RETF in the same section."""
    eof_state_test(
        container=container,
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_jumpf_too_large(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to a section outside the max section range."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[1025],
                )
            ],
            validity_error=EOFException.INVALID_CODE_SECTION_INDEX,
        ),
    )


def test_jumpf_way_too_large(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to uint64.MAX."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[0xFFFF],
                )
            ],
            validity_error=EOFException.INVALID_CODE_SECTION_INDEX,
        ),
    )


def test_jumpf_to_nonexistent_section(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to valid section number but where the section does not exist."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[5],
                )
            ],
            validity_error=EOFException.INVALID_CODE_SECTION_INDEX,
        ),
    )


def test_callf_to_non_returning_section(
    eof_state_test: EOFStateTestFiller,
):
    """Tests CALLF into a non-returning section."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.CALLF[1],
                ),
                Section.Code(
                    code=Op.STOP,
                    code_outputs=0,
                ),
            ],
            validity_error=EOFException.MISSING_STOP_OPCODE,
        ),
    )


def test_jumpf_stack_size_1024(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in target function of JUMPF."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 1022 + Op.JUMPF[1],
                    max_stack_height=1022,
                ),
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                    code_inputs=0,
                    code_outputs=NON_RETURNING_SECTION,
                    max_stack_height=2,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_jumpf_with_inputs_stack_size_1024(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in target function of JUMPF with inputs."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 1022 + Op.JUMPF[1],
                    max_stack_height=1022,
                ),
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                    code_inputs=3,
                    code_outputs=NON_RETURNING_SECTION,
                    max_stack_height=5,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_jumpf_stack_size_1024_at_push(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in JUMPF target function at PUSH0 instruction."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 1023
                    + Op.CALLF[1]
                    + Op.POP * 1023
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.RETURN(0, 0),
                    max_stack_height=1023,
                ),
                Section.Code(
                    # stack has 1023 items
                    Op.JUMPF[2],
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=0,
                ),
                Section.Code(
                    Op.PUSH0
                    +
                    # stack has 1024 items
                    Op.POP
                    + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=1,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


@pytest.mark.parametrize(
    ("stack_height", "failure"),
    (
        pytest.param(1021, False, id="no_overflow"),
        pytest.param(1022, True, id="rule_overflow"),
        pytest.param(1023, True, id="execution_overflow"),
    ),
)
def test_jumpf_stack_overflow(
    stack_height: int,
    failure: bool,
    eof_state_test: EOFStateTestFiller,
):
    """
    Test rule #2 in execution semantics, where we make sure we have enough stack to guarantee
    safe execution (the "reserved stack rule") max possible stack will not exceed 1024. But some
    executions may not overflow the stack, so we need to ensure the rule is checked.

    `no_overflow` - the stack does not overflow at JUMPF call, executes to end
    `rule_overflow` - reserved stack rule triggers, but execution would not overflow if allowed
    `execution_overflow` - execution would overflow (but still blocked by reserved stack rule)
    """
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * stack_height
                    + Op.CALLF[1]
                    + Op.POP * stack_height
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.RETURN(0, 0),
                    max_stack_height=stack_height,
                ),
                Section.Code(
                    # Stack has stack_height items
                    Op.JUMPF[2],
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=0,
                ),
                Section.Code(
                    Op.CALLDATALOAD(0)
                    + Op.ISZERO
                    + Op.RJUMPI[6]
                    + Op.PUSH0 * 3
                    + Op.POP * 3
                    + Op.SSTORE(slot_stack_canary, value_canary_written)
                    + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=3,
                ),
            ],
        ),
        container_post=Account(
            storage={
                slot_code_worked: 0 if failure else value_code_worked,
                slot_stack_canary: 0 if failure else value_canary_written,
            }
        ),
    )


def test_jumpf_with_inputs_stack_size_1024_at_push(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in JUMPF target function with inputs at PUSH0 instruction."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 1023
                    + Op.CALLF[1]
                    + Op.POP * 1023
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.RETURN(0, 0),
                    max_stack_height=1023,
                ),
                Section.Code(
                    # Stack has 1023 items
                    Op.JUMPF[2],
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=3,
                ),
                Section.Code(
                    Op.PUSH0
                    +
                    # Stack has 1024 items
                    Op.POP
                    + Op.RETF,
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=4,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_jumpf_with_inputs_stack_overflow(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack overflowing 1024 items in JUMPF target function with inputs."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 1023
                    + Op.CALLF[1]
                    + Op.POP * 1023
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.RETURN(0, 0),
                    max_stack_height=1023,
                ),
                Section.Code(
                    # Stack has 1023 items
                    Op.JUMPF[2],
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=3,
                ),
                Section.Code(
                    Op.PUSH0
                    + Op.PUSH0
                    +
                    # Runtime stackoverflow
                    Op.POP
                    + Op.POP
                    + Op.RETF,
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=5,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: 0}),
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="self",
            sections=[
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.JUMPF[0],
                ),
            ],
        ),
        Container(
            name="1_to_0",
            sections=[
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.JUMPF[1],
                ),
                Section.Code(
                    Op.JUMPF[0],
                ),
            ],
        ),
        Container(
            name="2_to_1",
            sections=[
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.JUMPF[1],
                ),
                Section.Code(
                    Op.JUMPF[2],
                ),
                Section.Code(
                    Op.JUMPF[1],
                ),
            ],
        ),
        Container(
            name="2_to_1_returning",
            sections=[
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    Op.JUMPF[2],
                    code_outputs=0,
                ),
                Section.Code(
                    Op.JUMPF[1],
                    code_outputs=0,
                ),
            ],
        ),
        Container(
            name="1_to_0_invalid",
            sections=[
                Section.Code(
                    Op.JUMPF[1],
                ),
                Section.Code(
                    Op.JUMPF[0],
                    code_outputs=0,
                ),
            ],
            validity_error=EOFException.INVALID_NON_RETURNING_FLAG,
        ),
    ],
    ids=lambda container: container.name,
)
def test_jumpf_infinite_loop(eof_state_test: EOFStateTestFiller, container: Container):
    """Tests JUMPF causing an infinite loop."""
    eof_state_test(
        tx_gas=100_000,
        container=container,
        container_post=Account(storage={slot_code_worked: 0}),
    )
