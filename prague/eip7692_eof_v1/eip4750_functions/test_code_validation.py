"""
Code validation of CALLF, RETF opcodes tests
"""

from typing import List

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_CODE_SECTIONS
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4750.md"
REFERENCE_SPEC_VERSION = "14400434e1199c57d912082127b1d22643788d11"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

VALID: List[Container] = [
    Container(
        name="retf_code_input_output",
        sections=[
            Section.Code(code=Op.PUSH0 + Op.CALLF[1] + Op.POP + Op.POP + Op.STOP),
            Section.Code(
                code=Op.PUSH0 + Op.RETF,
                code_outputs=1,
            ),
        ],
    ),
    Container(
        name="stack_height_equal_code_outputs_retf_zero_stop",
        sections=[
            Section.Code(
                code=Op.CALLF[1] + Op.POP + Op.STOP,
                code_inputs=0,
                max_stack_height=1,
            ),
            Section.Code(
                code=(
                    Op.RJUMPI[len(Op.PUSH0) + len(Op.RETF)](Op.ORIGIN)
                    + Op.PUSH0
                    + Op.RETF
                    + Op.STOP
                ),
                code_inputs=0,
                code_outputs=1,
                max_stack_height=1,
            ),
        ],
    ),
    Container(
        name="callf_max_code_sections_1",
        sections=[
            Section.Code(code=(sum(Op.CALLF[i] for i in range(1, MAX_CODE_SECTIONS)) + Op.STOP))
        ]
        + (
            [
                Section.Code(
                    code=Op.RETF,
                    code_outputs=0,
                )
            ]
            * (MAX_CODE_SECTIONS - 1)
        ),
    ),
    Container(
        name="callf_max_code_sections_2",
        sections=[Section.Code(code=(Op.CALLF[1] + Op.STOP))]
        + [
            Section.Code(
                code=(Op.CALLF[i + 2] + Op.RETF),
                code_outputs=0,
            )
            for i in range(MAX_CODE_SECTIONS - 2)
        ]
        + [
            Section.Code(
                code=Op.RETF,
                code_outputs=0,
            )
        ],
    ),
]

INVALID: List[Container] = [
    Container(
        name="function_underflow",
        sections=[
            Section.Code(code=(Op.PUSH0 + Op.CALLF[1] + Op.STOP)),
            Section.Code(
                code=(Op.POP + Op.POP + Op.RETF),
                code_inputs=1,
                code_outputs=0,
            ),
        ],
        validity_error=EOFException.STACK_UNDERFLOW,
    ),
    Container(
        name="stack_higher_than_code_outputs",
        sections=[
            Section.Code(
                code=(Op.CALLF[1] + Op.STOP),
            ),
            Section.Code(
                code=(Op.PUSH0 + Op.RETF),
                code_outputs=0,
            ),
        ],
        validity_error=EOFException.STACK_HIGHER_THAN_OUTPUTS,
    ),
    Container(
        name="stack_shorter_than_code_outputs",
        sections=[
            Section.Code(
                code=(Op.CALLF[1] + Op.STOP),
            ),
            Section.Code(
                code=(Op.PUSH0 + Op.RETF),
                code_outputs=2,
                max_stack_height=1,
            ),
        ],
        validity_error=EOFException.INVALID_MAX_STACK_HEIGHT,
    ),
    Container(
        name="oob_callf_1",
        sections=[
            Section.Code(
                code=(Op.CALLF[2] + Op.STOP),
            ),
            Section.Code(
                code=(Op.RETF),
                code_outputs=0,
            ),
        ],
        validity_error=EOFException.INVALID_CODE_SECTION_INDEX,
    ),
    Container(
        name="overflow_code_sections_1",
        sections=[
            Section.Code(
                code=(Op.CALLF[1] + Op.STOP),
            )
        ]
        + [
            Section.Code(
                code=(Op.CALLF[i + 2] + Op.RETF),
                code_outputs=0,
            )
            for i in range(MAX_CODE_SECTIONS)
        ]
        + [
            Section.Code(
                code=Op.RETF,
                code_outputs=0,
            )
        ],
        validity_error=EOFException.TOO_MANY_CODE_SECTIONS,
    ),
]


def container_name(c: Container):
    """
    Return the name of the container for use in pytest ids.
    """
    if hasattr(c, "name"):
        return c.name
    else:
        return c.__class__.__name__


@pytest.mark.parametrize(
    "container",
    [*VALID, *INVALID],
    ids=container_name,
)
def test_eof_validity(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Test EOF container validaiton for features around EIP-4750 / Functions / Code Sections
    """
    eof_test(
        data=bytes(container),
        expect_exception=container.validity_error,
    )
