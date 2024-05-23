"""
EOF JUMPF tests covering simple cases.
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


def test_jumpf_forward(
    eof_state_test: EOFStateTestFiller,
):
    """Test JUMPF jumping forward"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.JUMPF[1],
                    code_outputs=NON_RETURNING_SECTION,
                ),
                Section.Code(
                    Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                    code_outputs=NON_RETURNING_SECTION,
                    max_stack_height=2,
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
                    code_outputs=NON_RETURNING_SECTION,
                    max_stack_height=2,
                ),
                Section.Code(
                    code=Op.RETF,
                ),
                Section.Code(
                    code=Op.JUMPF[1],
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
                    code_outputs=NON_RETURNING_SECTION,
                    max_stack_height=2,
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
                    code_outputs=NON_RETURNING_SECTION,
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
                    code_outputs=NON_RETURNING_SECTION,
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
                    code_outputs=NON_RETURNING_SECTION,
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
                    code_outputs=NON_RETURNING_SECTION,
                ),
                Section.Code(
                    code=Op.STOP,
                    outputs=NON_RETURNING_SECTION,
                ),
            ],
            validity_error=EOFException.MISSING_STOP_OPCODE,
        ),
    )
