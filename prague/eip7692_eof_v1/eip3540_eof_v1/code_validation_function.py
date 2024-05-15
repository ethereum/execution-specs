"""
Code validation of CALLF, RETF opcodes tests
"""

from typing import List

from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_CODE_SECTIONS
from ethereum_test_tools.vm.opcode import Opcodes as Op


def bytes_concatenate(bytes_list: List[bytes]) -> bytes:
    """
    Concatenates a list of bytes into a single object
    """
    r = bytes()
    for b in bytes_list:
        r += b
    return r


VALID: List[Container] = [
    Container(
        name="retf_code_input_output",
        sections=[
            Section.Code(
                code=Op.PUSH0 + Op.CALLF[1] + Op.POP + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=0,
                max_stack_height=2,
            ),
            Section.Code(
                code=Op.PUSH0 + Op.RETF,
                code_inputs=1,
                code_outputs=2,
                max_stack_height=2,
            ),
        ],
    ),
    Container(
        name="stack_height_equal_code_outputs_retf_zero_stop",
        sections=[
            Section.Code(
                code=Op.CALLF[1] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=0,
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
            Section.Code(
                code=(
                    bytes_concatenate([Op.CALLF[i] for i in range(1, MAX_CODE_SECTIONS)]) + Op.STOP
                ),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            )
        ]
        + (
            [
                Section.Code(
                    code=Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=0,
                )
            ]
            * (MAX_CODE_SECTIONS - 1)
        ),
    ),
    Container(
        name="callf_max_code_sections_2",
        sections=[
            Section.Code(
                code=(Op.CALLF[i + 1] + Op.RETF),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            )
            for i in range(MAX_CODE_SECTIONS - 1)
        ]
        + [
            Section.Code(
                code=Op.RETF,
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            )
        ],
    ),
]

INVALID: List[Container] = [
    Container(
        name="function_underflow",
        sections=[
            Section.Code(
                code=(Op.PUSH0 + Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=2,
            ),
            Section.Code(
                code=(Op.POP + Op.POP + Op.RETF),
                code_inputs=1,
                code_outputs=0,
                max_stack_height=2,
            ),
        ],
        validity_error="StackUnderflow",
    ),
    Container(
        name="stack_higher_than_code_outputs",
        sections=[
            Section.Code(
                code=(Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            ),
            Section.Code(
                code=(Op.PUSH0 + Op.RETF),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=1,
            ),
        ],
        validity_error="InvalidRetf",
    ),
    Container(
        name="stack_shorter_than_code_outputs",
        sections=[
            Section.Code(
                code=(Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            ),
            Section.Code(
                code=(Op.PUSH0 + Op.RETF),
                code_inputs=0,
                code_outputs=2,
                max_stack_height=1,
            ),
        ],
        validity_error="InvalidRetf",
    ),
    Container(
        name="oob_callf_1",
        sections=[
            Section.Code(
                code=(Op.PUSH0 + Op.CALLF[2] + Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=1,
            ),
            Section.Code(
                code=(Op.POP + Op.POP + Op.RETF),
                code_inputs=1,
                code_outputs=0,
                max_stack_height=2,
            ),
        ],
        validity_error="StackUnderflow",
    ),
    Container(
        name="overflow_code_sections_1",
        sections=[
            Section.Code(
                code=(Op.CALLF[i + 1] + Op.RETF),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            )
            for i in range(MAX_CODE_SECTIONS)
        ]
        + [
            Section.Code(
                code=Op.RETF,
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            )
        ],
        validity_error="InvalidTypeSize",
    ),
]
