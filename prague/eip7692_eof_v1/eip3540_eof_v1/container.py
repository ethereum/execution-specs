"""
Test EVM Object Format Version 1
"""

from typing import List

from ethereum_test_tools.eof import LATEST_EOF_VERSION
from ethereum_test_tools.eof.v1 import VERSION_MAX_SECTION_KIND, AutoSection, Container, Section
from ethereum_test_tools.eof.v1 import SectionKind as Kind
from ethereum_test_tools.eof.v1.constants import (
    MAX_CODE_INPUTS,
    MAX_CODE_OUTPUTS,
    MAX_CODE_SECTIONS,
    MAX_OPERAND_STACK_HEIGHT,
    NON_RETURNING_SECTION,
)
from ethereum_test_tools.exceptions import EOFException
from ethereum_test_tools.vm.opcode import Opcodes as Op

VALID: List[Container] = [
    Container(
        name="single_code_single_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data="0xef"),
        ],
    ),
    Container(
        # EOF allows truncated data section
        name="no_data_section_contents",
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0x", custom_size=1),
        ],
        code="ef0001 010004 0200010001 040001 00 00800000 00",
    ),
    Container(
        # EOF allows truncated data section
        name="data_section_contents_incomplete",
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0xAABBCC", custom_size=4),
        ],
    ),
    Container(
        name="max_code_sections",
        sections=[
            Section.Code(
                Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
            )
            for i in range(MAX_CODE_SECTIONS)
        ],
    ),
    Container(
        name="max_code_sections_plus_data",
        sections=[
            Section.Code(
                Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
            )
            for i in range(MAX_CODE_SECTIONS)
        ]
        + [Section.Data(data="0x00")],
    ),
    Container(
        name="max_code_sections_plus_container",
        sections=[
            Section.Code(
                Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
            )
            for i in range(MAX_CODE_SECTIONS)
        ]
        + [
            Section.Container(
                container=Container(
                    name="max_code_sections",
                    sections=[
                        Section.Code(
                            Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP,
                            code_outputs=NON_RETURNING_SECTION,
                        )
                        for i in range(MAX_CODE_SECTIONS)
                    ],
                )
            )
        ],
    ),
    Container(
        name="max_code_sections_plus_data_plus_container",
        sections=[
            Section.Code(
                Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
            )
            for i in range(MAX_CODE_SECTIONS)
        ]
        + [
            Section.Container(
                container=Container(
                    name="max_code_sections",
                    sections=[
                        Section.Code(
                            Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP,
                            code_outputs=NON_RETURNING_SECTION,
                        )
                        for i in range(MAX_CODE_SECTIONS)
                    ],
                )
            )
        ]
        + [Section.Data(data="0x00")],
    ),
    # TODO: Add more valid scenarios
]

INVALID: List[Container] = [
    Container(
        name="single_code_section_no_data_section",
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_data_section=False,
        validity_error=EOFException.MISSING_DATA_SECTION,
    ),
    Container(
        name="incomplete_magic",
        raw_bytes=bytes([0xEF]),
        validity_error=EOFException.INVALID_MAGIC,
    ),
    Container(
        name="no_version",
        raw_bytes=bytes([0xEF, 0x00]),
        validity_error=EOFException.INVALID_VERSION,
    ),
    Container(
        name="no_type_header",
        raw_bytes=bytes([0xEF, 0x00, 0x01]),
        # TODO the exception must be about missing section types
        validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
    ),
    Container(
        name="no_type_section_size",
        raw_bytes=bytes(
            [0xEF, 0x00, 0x01, 0x01],
        ),
        # TODO the exception must be about incomplete section in the header
        validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
    ),
    Container(
        name="code_section_size_incomplete_1",
        raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02]),
        validity_error=EOFException.INCOMPLETE_SECTION_NUMBER,
    ),
    Container(
        name="code_section_size_incomplete_2",
        raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x00]),
        validity_error=EOFException.INCOMPLETE_SECTION_NUMBER,
    ),
    Container(
        name="code_section_size_incomplete_3",
        raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x00, 0x01]),
        validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
    ),
    Container(
        name="code_section_size_incomplete_4",
        raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x00, 0x01]),
        validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
    ),
    Container(
        name="code_section_size_incomplete_5",
        raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x00, 0x01, 0x00]),
        validity_error=EOFException.INCOMPLETE_SECTION_SIZE,
    ),
    Container(
        name="no_data_section_size",
        raw_bytes=bytes(
            [
                0xEF,
                0x00,
                0x01,
                0x01,
                0x00,
                0x04,
                0x02,
                0x00,
                0x01,
                0x00,
                0x00,
                0x04,
            ]
        ),
        # TODO it looks like data section is missing or section header of type 0x00
        validity_error=EOFException.ZERO_SECTION_SIZE,
    ),
    Container(
        name="data_section_size_incomplete",
        raw_bytes=bytes(
            [
                0xEF,
                0x00,
                0x01,
                0x01,
                0x00,
                0x04,
                0x02,
                0x00,
                0x01,
                0x00,
                0x00,
                0x03,
                0x00,
            ]
        ),
        validity_error=EOFException.ZERO_SECTION_SIZE,
    ),
    Container(
        name="no_sections",
        sections=[],
        auto_data_section=False,
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.MISSING_TYPE_HEADER,
    ),
    Container(
        name="invalid_magic_01",
        magic=b"\xef\x01",
        sections=[Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION)],
        validity_error=EOFException.INVALID_MAGIC,
    ),
    Container(
        name="invalid_magic_ff",
        magic=b"\xef\xFF",
        sections=[Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION)],
        validity_error=EOFException.INVALID_MAGIC,
    ),
    Container(
        name="invalid_version_zero",
        version=b"\x00",
        sections=[Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION)],
        validity_error=EOFException.INVALID_VERSION,
    ),
    Container(
        name="invalid_version_plus_one",
        version=int.to_bytes(LATEST_EOF_VERSION + 1, length=1, byteorder="big"),
        sections=[Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION)],
        validity_error=EOFException.INVALID_VERSION,
    ),
    Container(
        name="invalid_version_high",
        version=b"\xFF",
        sections=[Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION)],
        validity_error=EOFException.INVALID_VERSION,
    ),
    Container(
        name="no_code_section",
        sections=[
            Section(kind=Kind.TYPE, data=bytes([0] * 4)),
            Section.Data("0x00"),
        ],
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.MISSING_CODE_HEADER,
    ),
    Container(
        name="too_many_code_sections",
        sections=[
            Section.Code(
                Op.JUMPF[i + 1] if i < MAX_CODE_SECTIONS else Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
            )
            for i in range(MAX_CODE_SECTIONS + 1)
        ],
        validity_error=EOFException.TOO_MANY_CODE_SECTIONS,
    ),
    Container(
        name="zero_code_sections_header",
        raw_bytes=bytes(
            [
                0xEF,
                0x00,
                0x01,
                0x01,
                0x00,
                0x04,
                0x02,
                0x00,
                0x00,
                0x03,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        ),
        validity_error=EOFException.ZERO_SECTION_SIZE,
    ),
    Container(
        name="no_section_terminator_1",
        header_terminator=bytes(),
        sections=[Section.Code(code=Op.STOP, custom_size=2, code_outputs=NON_RETURNING_SECTION)],
        # TODO the exception must be about terminator
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="no_section_terminator_2",
        header_terminator=bytes(),
        sections=[Section.Code(code="0x", custom_size=3, code_outputs=NON_RETURNING_SECTION)],
        # TODO the exception must be about terminator
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="no_section_terminator_3",
        header_terminator=bytes(),
        sections=[Section.Code(code=Op.PUSH1(0) + Op.STOP, code_outputs=NON_RETURNING_SECTION)],
        # TODO the exception must be about terminator
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="no_code_section_contents",
        sections=[Section.Code(code="0x", custom_size=0x01, code_outputs=NON_RETURNING_SECTION)],
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="incomplete_code_section_contents",
        sections=[
            Section.Code(code=Op.STOP, custom_size=0x02, code_outputs=NON_RETURNING_SECTION),
        ],
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="trailing_bytes_after_code_section",
        sections=[Section.Code(code=Op.PUSH1(0) + Op.STOP, code_outputs=NON_RETURNING_SECTION)],
        extra=bytes([0xDE, 0xAD, 0xBE, 0xEF]),
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="empty_code_section",
        sections=[Section.Code(code="0x", code_outputs=NON_RETURNING_SECTION)],
        # TODO the exception must be about code section EOFException.INVALID_CODE_SECTION,
        validity_error=EOFException.ZERO_SECTION_SIZE,
    ),
    Container(
        name="empty_code_section_with_non_empty_data",
        sections=[
            Section.Code(code="0x"),
            Section.Data(data="0xDEADBEEF"),
        ],
        # TODO the exception must be about code section EOFException.INVALID_CODE_SECTION,
        validity_error=EOFException.ZERO_SECTION_SIZE,
    ),
    Container(
        name="data_section_preceding_code_section",
        auto_data_section=False,
        auto_sort_sections=AutoSection.NONE,
        sections=[
            Section.Data(data="0xDEADBEEF"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        validity_error=EOFException.MISSING_CODE_HEADER,
    ),
    Container(
        name="data_section_without_code_section",
        sections=[Section.Data(data="0xDEADBEEF")],
        # TODO the actual exception should be EOFException.MISSING_CODE_HEADER
        validity_error=EOFException.ZERO_SECTION_SIZE,
    ),
    Container(
        name="no_section_terminator_3a",
        header_terminator=bytes(),
        sections=[
            Section.Code(
                code="0x030004",
                code_outputs=NON_RETURNING_SECTION,
            )
        ],
        # TODO the exception must be about terminator
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="no_section_terminator_4a",
        header_terminator=bytes(),
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0xAABBCCDD"),
        ],
        # TODO: The error of this validation can be random.
        validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
    ),
    Container(
        name="trailing_bytes_after_data_section",
        extra=bytes([0xEE]),
        sections=[
            Section.Code(code=Op.PUSH1(0) + Op.STOP),
            Section.Data(data="0xAABBCCDD"),
        ],
        # TODO should be more specific exception about trailing bytes
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="multiple_data_sections",
        sections=[
            Section.Code(code=Op.PUSH1(0) + Op.STOP),
            Section.Data(data="0xAABBCC"),
            Section.Data(data="0xAABBCC"),
        ],
        validity_error=EOFException.MISSING_TERMINATOR,
    ),
    Container(
        name="multiple_code_and_data_sections_1",
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0xAA"),
            Section.Data(data="0xAA"),
        ],
        validity_error=EOFException.MISSING_TERMINATOR,
    ),
    Container(
        name="multiple_code_and_data_sections_2",
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0xAA"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0xAA"),
        ],
        validity_error=EOFException.MISSING_TERMINATOR,
    ),
    Container(
        name="unknown_section_1",
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0x"),
            Section(kind=VERSION_MAX_SECTION_KIND + 1, data="0x01"),
        ],
        validity_error=EOFException.MISSING_TERMINATOR,
    ),
    Container(
        name="unknown_section_2",
        sections=[
            Section(kind=VERSION_MAX_SECTION_KIND + 1, data="0x01"),
            Section.Data(data="0x"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        # TODO the exception should be about unknown section definition
        validity_error=EOFException.MISSING_TERMINATOR,
    ),
    Container(
        name="unknown_section_empty",
        sections=[
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
            Section.Data(data="0x"),
            Section(kind=VERSION_MAX_SECTION_KIND + 1, data="0x"),
        ],
        validity_error=EOFException.MISSING_TERMINATOR,
    ),
    Container(
        name="no_type_section",
        sections=[
            Section.Code(code=Op.STOP),
            Section.Data("0x00"),
        ],
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.MISSING_TYPE_HEADER,
    ),
    Container(
        name="too_many_type_sections",
        sections=[
            Section(kind=Kind.TYPE, data="0x00000000"),
            Section(kind=Kind.TYPE, data="0x00000000"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.MISSING_CODE_HEADER,
    ),
    Container(
        name="empty_type_section",
        sections=[
            Section(kind=Kind.TYPE, data="0x"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_type_section=AutoSection.NONE,
        # TODO the exception must be about type section EOFException.INVALID_TYPE_SECTION_SIZE,
        validity_error=EOFException.ZERO_SECTION_SIZE,
    ),
    Container(
        name="type_section_too_small_1",
        sections=[
            Section(kind=Kind.TYPE, data="0x00"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
    ),
    Container(
        name="type_section_too_small_2",
        sections=[
            Section(kind=Kind.TYPE, data="0x000000"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
    ),
    Container(
        name="type_section_too_big",
        sections=[
            Section(kind=Kind.TYPE, data="0x0000000000"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
    ),
]

# TODO: Max initcode as specified on EIP-3860

"""
EIP-4750 Valid and Invalid Containers
"""

VALID += [
    Container(
        name="single_code_section_max_stack_size",
        sections=[
            Section.Code(
                code=(Op.CALLER * MAX_OPERAND_STACK_HEIGHT)
                + (Op.POP * MAX_OPERAND_STACK_HEIGHT)
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=MAX_OPERAND_STACK_HEIGHT,
            ),
        ],
    ),
    Container(
        name="single_code_section_input_maximum",
        sections=[
            Section.Code(
                code=((Op.PUSH0 * MAX_CODE_INPUTS) + Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=MAX_CODE_INPUTS,
            ),
            Section.Code(
                code=(Op.POP * MAX_CODE_INPUTS) + Op.RETF,
                code_inputs=MAX_CODE_INPUTS,
                code_outputs=0,
                max_stack_height=MAX_CODE_INPUTS,
            ),
        ],
    ),
    Container(
        name="single_code_section_output_maximum",
        sections=[
            Section.Code(
                code=(Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=MAX_CODE_OUTPUTS,
            ),
            Section.Code(
                code=(Op.PUSH0 * MAX_CODE_OUTPUTS) + Op.RETF,
                code_inputs=0,
                code_outputs=MAX_CODE_OUTPUTS,
                max_stack_height=MAX_CODE_OUTPUTS,
            ),
        ],
    ),
    Container(
        name="multiple_code_section_max_inputs_max_outputs",
        sections=[
            Section.Code(
                (Op.PUSH0 * MAX_CODE_OUTPUTS) + Op.CALLF[1] + Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=MAX_CODE_OUTPUTS,
            ),
            Section.Code(
                code=Op.RETF,
                code_inputs=MAX_CODE_INPUTS,
                code_outputs=MAX_CODE_OUTPUTS,
                max_stack_height=MAX_CODE_INPUTS,
            ),
        ],
    ),
]

INVALID += [
    Container(
        name="single_code_section_non_zero_inputs",
        sections=[
            Section.Code(code=Op.POP + Op.RETF, code_inputs=1, code_outputs=NON_RETURNING_SECTION)
        ],
        # TODO the exception must be about code or non, cause it looks legit
        validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
    ),
    Container(
        name="single_code_section_non_zero_outputs",
        sections=[Section.Code(code=Op.PUSH0 + Op.RETF, code_outputs=1)],
        # TODO the exception must be about code or non, cause it looks legit
        validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
    ),
    Container(
        name="multiple_code_section_non_zero_inputs",
        sections=[
            Section.Code(code=Op.POP + Op.RETF, code_inputs=1, code_outputs=NON_RETURNING_SECTION),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        # TODO the actual exception should be EOFException.INVALID_TYPE_BODY,
        validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
    ),
    Container(
        name="multiple_code_section_non_zero_outputs",
        sections=[
            Section.Code(code=Op.PUSH0, code_outputs=1),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        # TODO the actual exception should be EOFException.INVALID_TYPE_BODY,
        validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
    ),
    Container(
        name="data_section_before_code_with_type",
        sections=[
            Section.Data(data="0xAA"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_sort_sections=AutoSection.NONE,
        validity_error=EOFException.MISSING_CODE_HEADER,
    ),
    Container(
        name="data_section_listed_in_type",
        sections=[
            Section.Data(data="0x00", force_type_listing=True),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
    ),
    Container(
        name="single_code_section_incomplete_type",
        sections=[
            Section(kind=Kind.TYPE, data="0x00"),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        auto_type_section=AutoSection.NONE,
        validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
    ),
    Container(
        name="single_code_section_incomplete_type_2",
        sections=[
            Section(kind=Kind.TYPE, data="0x00", custom_size=2),
            Section.Code(Op.STOP, code_outputs=NON_RETURNING_SECTION),
        ],
        validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
    ),
    Container(
        name="single_code_section_input_too_large",
        sections=[
            Section.Code(
                code=((Op.PUSH0 * (MAX_CODE_INPUTS + 1)) + Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=(MAX_CODE_INPUTS + 1),
            ),
            Section.Code(
                code=(Op.POP * (MAX_CODE_INPUTS + 1)) + Op.RETF,
                code_inputs=(MAX_CODE_INPUTS + 1),
                code_outputs=0,
                max_stack_height=0,
            ),
        ],
        # TODO auto types section generation probably failed. the exception must be about code
        validity_error=EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT,
    ),
    Container(
        name="single_code_section_output_too_large",
        sections=[
            Section.Code(
                code=(Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=(MAX_CODE_OUTPUTS + 2),
            ),
            Section.Code(
                code=(Op.PUSH0 * (MAX_CODE_OUTPUTS + 2)) + Op.RETF,
                code_inputs=0,
                code_outputs=(MAX_CODE_OUTPUTS + 2),
                max_stack_height=(MAX_CODE_OUTPUTS + 1),
            ),
        ],
        # TODO the exception must be about code body
        validity_error=EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT,
    ),
    Container(
        name="single_code_section_max_stack_size_too_large",
        sections=[
            Section.Code(
                code=Op.CALLER * 1024 + Op.POP * 1024 + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1024,
            ),
        ],
        # TODO auto types section generation probably failed, the exception must be about code
        validity_error=EOFException.MAX_STACK_HEIGHT_ABOVE_LIMIT,
    ),
]
