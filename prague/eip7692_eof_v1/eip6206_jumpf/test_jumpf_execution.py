"""
EOF JUMPF tests covering simple cases.
"""

import pytest

from ethereum_test_tools import Account, EOFException, EOFStateTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import slot_code_worked, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6206.md"
REFERENCE_SPEC_VERSION = "2f365ea0cd58faa6e26013ea77ce6d538175f7d0"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_jumpf_forward(
    eof_state_test: EOFStateTestFiller,
):
    """Test JUMPF jumping forward"""
    eof_state_test(
        data=Container(
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
        tx_data=b"\1",
    )


def test_jumpf_backward(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping backward"""
    eof_state_test(
        data=Container(
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
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        tx_data=b"\1",
    )


def test_jumpf_to_self(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to self"""
    eof_state_test(
        data=Container(
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
        tx_data=b"\1",
    )


def test_jumpf_too_large(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to a section outside the max section range"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[1025],
                )
            ],
            validity_error=EOFException.UNDEFINED_EXCEPTION,
        ),
    )


def test_jumpf_way_too_large(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to uint64.MAX"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[0xFFFF],
                )
            ],
            validity_error=EOFException.UNDEFINED_EXCEPTION,
        ),
    )


def test_jumpf_to_nonexistent_section(
    eof_state_test: EOFStateTestFiller,
):
    """Tests JUMPF jumping to valid section number but where the section does not exist"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[5],
                )
            ],
            validity_error=EOFException.UNDEFINED_EXCEPTION,
        ),
    )


def test_callf_to_non_returning_section(
    eof_state_test: EOFStateTestFiller,
):
    """Tests CALLF into a non-returning section"""
    eof_state_test(
        data=Container(
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
    """Test stack reaching 1024 items in target function of JUMPF"""
    eof_state_test(
        data=Container(
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
    """Test stack reaching 1024 items in target function of JUMPF with inputs"""
    eof_state_test(
        data=Container(
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
    """Test stack reaching 1024 items in JUMPF target function at PUSH0 instruction"""
    eof_state_test(
        data=Container(
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
                    Op.PUSH0 +
                    # stack has 1024 items
                    Op.POP + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=1,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_jumpf_stack_overflow(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack overflowing 1024 items in JUMPF target function"""
    eof_state_test(
        data=Container(
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
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=0,
                ),
                Section.Code(
                    Op.PUSH0 + Op.PUSH0 +
                    # Runtime stack overflow
                    Op.POP + Op.POP + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=2,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: 0}),
    )


def test_jumpf_with_inputs_stack_size_1024_at_push(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in JUMPF target function with inputs at PUSH0 instruction"""
    eof_state_test(
        data=Container(
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
                    Op.PUSH0 +
                    # Stack has 1024 items
                    Op.POP + Op.RETF,
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
    """Test stack overflowing 1024 items in JUMPF target function with inputs"""
    eof_state_test(
        data=Container(
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
                    Op.PUSH0 + Op.PUSH0 +
                    # Runtime stackoverflow
                    Op.POP + Op.POP + Op.RETF,
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=5,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: 0}),
    )
