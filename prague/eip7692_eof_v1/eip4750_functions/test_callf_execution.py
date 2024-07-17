"""
EOF CALLF execution tests
"""

import pytest

from ethereum_test_tools import Account, EOFStateTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section

from .. import EOF_FORK_NAME
from .helpers import slot_code_worked, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4750.md"
REFERENCE_SPEC_VERSION = "14400434e1199c57d912082127b1d22643788d11"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_callf_stack_size_1024(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in called function"""
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
                    Op.PUSH0 + Op.POP + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=1,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_callf_with_inputs_stack_size_1024(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in called function with inputs"""
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
                    Op.PUSH0 + Op.POP + Op.RETF,
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=4,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_callf_stack_size_1024_at_callf(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in called function at CALLF instruction"""
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
                    Op.CALLF[2] +
                    # stack has 1024 items
                    Op.POP + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=1,
                ),
                Section.Code(
                    Op.PUSH0 + Op.RETF,  # stack has 1024 items
                    code_inputs=0,
                    code_outputs=1,
                    max_stack_height=1,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_callf_stack_size_1024_at_push(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in nested called function at PUSH0 instruction"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 1022
                    + Op.CALLF[1]
                    + Op.POP * 1022
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.RETURN(0, 0),
                    max_stack_height=1022,
                ),
                Section.Code(
                    Op.PUSH0 +
                    # stack has 1023 items
                    Op.CALLF[2] + Op.POP + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=1,
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


def test_callf_stack_overflow(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack overflowing 1024 items in called function"""
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
                    Op.PUSH0 +
                    # Stack has 1024 items
                    Op.CALLF[2] + Op.POP + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=1,
                ),
                Section.Code(
                    Op.PUSH0 +
                    # Runtime stack overflow
                    Op.POP + Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=1,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: 0}),
    )


def test_callf_with_inputs_stack_size_1024_at_push(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack reaching 1024 items in nested called function with inputs at PUSH0 instruction"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 1022
                    + Op.CALLF[1]
                    + Op.POP * 1022
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.RETURN(0, 0),
                    max_stack_height=1022,
                ),
                Section.Code(
                    Op.PUSH0 +
                    # Stack has 1023 items
                    Op.CALLF[2] + Op.POP + Op.RETF,
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=4,
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


def test_callf_with_inputs_stack_overflow(
    eof_state_test: EOFStateTestFiller,
):
    """Test stack overflowing 1024 items in called function with inputs"""
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
                    Op.PUSH0 +
                    # Stack has 1024 items
                    Op.CALLF[2] + Op.POP + Op.RETF,
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=4,
                ),
                Section.Code(
                    Op.PUSH0 +
                    # Runtime stackoverflow
                    Op.POP + Op.RETF,
                    code_inputs=3,
                    code_outputs=3,
                    max_stack_height=4,
                ),
            ],
        ),
        container_post=Account(storage={slot_code_worked: 0}),
    )
