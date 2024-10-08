"""
EOF validation tests for EIP-3540 container format
"""


import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools.eof.v1 import (
    VERSION_MAX_SECTION_KIND,
    AutoSection,
    Container,
    ContainerKind,
    Section,
    SectionKind,
)
from ethereum_test_tools.eof.v1.constants import (
    MAX_CODE_INPUTS,
    MAX_CODE_OUTPUTS,
    MAX_CODE_SECTIONS,
    MAX_OPERAND_STACK_HEIGHT,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

VALID_CONTAINER = Container(sections=[Section.Code(code=Op.STOP)])


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="single_code_section_max_stack_size",
            sections=[
                Section.Code(
                    code=(Op.CALLER * MAX_OPERAND_STACK_HEIGHT)
                    + (Op.POP * MAX_OPERAND_STACK_HEIGHT)
                    + Op.STOP,
                    max_stack_height=MAX_OPERAND_STACK_HEIGHT,
                ),
            ],
        ),
        Container(
            name="code_section_with_inputs_outputs",
            sections=[
                Section.Code(
                    code=(Op.PUSH0 + Op.CALLF[1] + Op.STOP),
                ),
                Section.Code(
                    code=Op.POP + Op.PUSH0 + Op.RETF,
                    code_inputs=1,
                    code_outputs=1,
                ),
            ],
        ),
        Container(
            name="code_section_input_maximum",
            sections=[
                Section.Code(
                    code=((Op.PUSH0 * MAX_CODE_INPUTS) + Op.CALLF[1] + Op.STOP),
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
            name="code_section_output_maximum",
            sections=[
                Section.Code(
                    code=(Op.CALLF[1] + Op.STOP),
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
            name="multiple_code_sections",
            sections=[
                Section.Code(
                    Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    code=Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                ),
            ],
        ),
        Container(
            name="multiple_code_sections_max_inputs_max_outputs",
            sections=[
                Section.Code(
                    (Op.PUSH0 * MAX_CODE_OUTPUTS) + Op.CALLF[1] + Op.STOP,
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
        Container(
            name="single_subcontainer_without_data",
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section.Container(Container.Code(Op.INVALID)),
            ],
        ),
        Container(
            name="single_subcontainer_with_data",
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section.Container(Container.Code(Op.INVALID)),
                Section.Data(data="0xAA"),
            ],
        ),
    ],
    ids=lambda c: c.name,
)
def test_valid_containers(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Test creating various types of valid EOF V1 contracts using legacy
    initcode and a contract creating transaction.
    """
    assert (
        container.validity_error is None
    ), f"Valid container with validity error: {container.validity_error}"
    eof_test(
        data=bytes(container),
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="empty_container",
            raw_bytes=b"",
            validity_error=[
                EOFException.INVALID_MAGIC,
            ],
        ),
        Container(
            name="single_code_section_no_data_section",
            sections=[
                Section.Code(Op.STOP),
            ],
            auto_data_section=False,
            validity_error=[
                EOFException.MISSING_DATA_SECTION,
                EOFException.UNEXPECTED_HEADER_KIND,
            ],
        ),
        Container(
            name="incomplete_magic",
            raw_bytes="ef",
            validity_error=EOFException.INVALID_MAGIC,
        ),
        Container(
            name="no_version",
            raw_bytes="ef00",
            validity_error=[EOFException.INVALID_VERSION, EOFException.INVALID_MAGIC],
        ),
        Container(
            name="no_type_header",
            raw_bytes="ef00 01",
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="no_type_section_size",
            raw_bytes="ef00 01 01",
            validity_error=[
                EOFException.MISSING_HEADERS_TERMINATOR,
                EOFException.INVALID_TYPE_SECTION_SIZE,
            ],
        ),
        Container(
            name="incomplete_type_section_size",
            raw_bytes="ef00010100",
            validity_error=[
                EOFException.INCOMPLETE_SECTION_SIZE,
                EOFException.INVALID_TYPE_SECTION_SIZE,
            ],
        ),
        Container(
            name="no_code_header",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04]),
            validity_error=[
                EOFException.MISSING_CODE_HEADER,
                EOFException.MISSING_HEADERS_TERMINATOR,
            ],
        ),
        Container(
            name="no_code_header_2",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0xFE]),
            validity_error=[EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_code_header_3",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x00]),
            validity_error=[EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="code_section_count_missing",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02]),
            validity_error=EOFException.INCOMPLETE_SECTION_NUMBER,
        ),
        Container(
            name="code_section_count_incomplete",
            raw_bytes="ef00 01 01 0004 02 00",
            validity_error=EOFException.INCOMPLETE_SECTION_NUMBER,
        ),
        Container(
            name="code_section_size_missing",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x00, 0x01]),
            validity_error=[
                EOFException.MISSING_HEADERS_TERMINATOR,
                EOFException.ZERO_SECTION_SIZE,
            ],
        ),
        Container(
            name="code_section_size_incomplete",
            raw_bytes="ef00 01 01 0004 02 0001 00",
            validity_error=[EOFException.INCOMPLETE_SECTION_SIZE, EOFException.ZERO_SECTION_SIZE],
        ),
        Container(
            name="code_section_count_0x8000_truncated",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x80, 0x00]),
            validity_error=EOFException.TOO_MANY_CODE_SECTIONS,
        ),
        Container(
            name="code_section_count_0xFFFF_truncated",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0xFF, 0xFF]),
            validity_error=EOFException.TOO_MANY_CODE_SECTIONS,
        ),
        Container(
            name="code_section_count_0x8000",
            raw_bytes=bytes(
                [0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x80, 0x00] + [0x00, 0x01] * 0x8000
            ),
            validity_error=EOFException.CONTAINER_SIZE_ABOVE_LIMIT,
        ),
        Container(
            name="code_section_count_0xFFFF",
            raw_bytes=bytes(
                [0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0xFF, 0xFF] + [0x00, 0x01] * 0xFFFF
            ),
            validity_error=EOFException.CONTAINER_SIZE_ABOVE_LIMIT,
        ),
        Container(
            name="code_section_size_0x8000_truncated",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x00, 0x01, 0x80, 0x00]),
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="code_section_size_0xFFFF_truncated",
            raw_bytes=bytes([0xEF, 0x00, 0x01, 0x01, 0x00, 0x04, 0x02, 0x00, 0x01, 0xFF, 0xFF]),
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="terminator_incomplete",
            header_terminator=b"",
            sections=[
                Section(kind=SectionKind.TYPE, data=b"", custom_size=4),
                Section.Code(code=b"", custom_size=0x01),
            ],
            expected_bytecode="ef00 01 01 0004 02 0001 0001 04 0000",
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="truncated_header_data_section",
            raw_bytes="ef00 01 01 0004 02 0001 0001",
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="no_data_section_size",
            raw_bytes="ef00 01 01 0004 02 0001 0001 04",
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="data_section_size_incomplete",
            raw_bytes="ef00 01 01 0004 02 0001 0001 04 00",
            validity_error=EOFException.INCOMPLETE_SECTION_SIZE,
        ),
        Container(
            name="no_container_section_count",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03",
            validity_error=EOFException.INCOMPLETE_SECTION_NUMBER,
        ),
        Container(
            name="incomplete_container_section_count",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 00",
            validity_error=EOFException.INCOMPLETE_SECTION_NUMBER,
        ),
        Container(
            name="zero_container_section_count",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0000 04 0000 00 00800000 00",
            validity_error=EOFException.ZERO_SECTION_SIZE,
        ),
        Container(
            name="no_container_section_size",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0001",
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="incomplete_container_section_size",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0001 00",
            validity_error=EOFException.INCOMPLETE_SECTION_SIZE,
        ),
        Container(
            name="incomplete_container_section_size_2",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0002 0001",
            validity_error=EOFException.INCOMPLETE_SECTION_SIZE,
        ),
        Container(
            name="incomplete_container_section_size_3",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0002 0001 00",
            validity_error=EOFException.INCOMPLETE_SECTION_SIZE,
        ),
        Container(
            name="zero_size_container_section",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0001 0000 04 0000 00 00800000 00",
            validity_error=EOFException.ZERO_SECTION_SIZE,
        ),
        Container(
            name="truncated_header_data_section_with_container_section",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0001 0001",
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="no_data_section_size_with_container_section",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0001 0001 04",
            validity_error=EOFException.MISSING_HEADERS_TERMINATOR,
        ),
        Container(
            name="data_section_size_incomplete_with_container_section",
            raw_bytes="ef00 01 01 0004 02 0001 0001 03 0001 0001 04 00",
            validity_error=EOFException.INCOMPLETE_SECTION_SIZE,
        ),
        Container(
            name="no_sections",
            sections=[],
            auto_data_section=False,
            auto_type_section=AutoSection.NONE,
            expected_bytecode="ef0001 00",
            validity_error=[EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_code_section_header",
            sections=[
                Section(kind=SectionKind.TYPE, data=b"\0\x80\0\0"),
                Section.Data("0x00"),
            ],
            expected_bytecode="ef00 01 01 0004 04 0001 00 00800000 00",
            auto_type_section=AutoSection.NONE,
            validity_error=[EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="too_many_code_sections",
            sections=[
                Section.Code(Op.JUMPF[i + 1] if i < MAX_CODE_SECTIONS else Op.STOP)
                for i in range(MAX_CODE_SECTIONS + 1)
            ],
            validity_error=EOFException.TOO_MANY_CODE_SECTIONS,
        ),
        Container(
            name="zero_code_sections_header",
            raw_bytes="ef00 01 01 0004 02 0000 04 0000 00 00800000",
            validity_error=[
                EOFException.ZERO_SECTION_SIZE,
                EOFException.INCOMPLETE_SECTION_NUMBER,
            ],
        ),
        Container(
            name="zero_code_sections_header_empty_type_section",
            raw_bytes="ef00 01 01 0000 02 0000 04 0000 00",
            validity_error=[
                EOFException.ZERO_SECTION_SIZE,
                EOFException.INCOMPLETE_SECTION_NUMBER,
            ],
        ),
        # The basic `no_section_terminator` cases just remove the terminator
        # and the `00` for zeroth section inputs looks like one. Error is because
        # the sections are wrongly sized.
        Container(
            name="no_section_terminator",
            header_terminator=bytes(),
            sections=[Section.Code(code=Op.STOP)],
            validity_error=[
                EOFException.INVALID_SECTION_BODIES_SIZE,
                EOFException.INVALID_FIRST_SECTION_TYPE,
            ],
        ),
        Container(
            name="no_section_terminator_1",
            header_terminator=bytes(),
            sections=[Section.Code(code=Op.STOP, custom_size=2)],
            validity_error=[
                EOFException.INVALID_SECTION_BODIES_SIZE,
                EOFException.INVALID_FIRST_SECTION_TYPE,
            ],
        ),
        Container(
            name="no_section_terminator_2",
            header_terminator=bytes(),
            sections=[Section.Code(code="0x", custom_size=3)],
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="no_section_terminator_3",
            header_terminator=bytes(),
            sections=[Section.Code(code=Op.PUSH1(0) + Op.STOP)],
            validity_error=[
                EOFException.INVALID_SECTION_BODIES_SIZE,
                EOFException.INVALID_FIRST_SECTION_TYPE,
            ],
        ),
        # The following cases just remove the terminator
        # and the `00` for zeroth section inputs looks like one. Section bodies
        # are as the size prescribes here, so the error is about the inputs of zeroth section.
        Container(
            name="no_section_terminator_section_bodies_ok_1",
            header_terminator=bytes(),
            sections=[Section.Code(code=Op.JUMPDEST + Op.STOP, custom_size=1)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="no_section_terminator_section_bodies_ok_2",
            header_terminator=bytes(),
            sections=[Section.Code(code=Op.JUMPDEST * 2 + Op.STOP, custom_size=2)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        # Here the terminator is missing but made to look like a different section
        # or arbitrary byte
        Container(
            name="no_section_terminator_nonzero",
            header_terminator=b"01",
            sections=[Section.Code(code=Op.STOP)],
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_section_terminator_nonzero_1",
            header_terminator=b"02",
            sections=[Section.Code(code=Op.STOP, custom_size=2)],
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_section_terminator_nonzero_2",
            header_terminator=b"03",
            sections=[Section.Code(code="0x", custom_size=3)],
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_section_terminator_nonzero_3",
            header_terminator=b"04",
            sections=[Section.Code(code=Op.PUSH1(0) + Op.STOP)],
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_section_terminator_nonzero_4",
            header_terminator=b"fe",
            sections=[Section.Code(code=Op.PUSH1(0) + Op.STOP)],
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="truncated_before_type_section",
            sections=[
                Section(kind=SectionKind.TYPE, data=b"", custom_size=4),
                Section.Code(code=b"", custom_size=0x01),
            ],
            expected_bytecode="ef00 01 01 0004 02 0001 0001 04 0000 00",
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="truncated_type_section_before_outputs",
            sections=[
                Section(kind=SectionKind.TYPE, data=b"\0", custom_size=4),
                Section.Code(code=b"", custom_size=0x01),
            ],
            expected_bytecode="ef00 01 01 0004 02 0001 0001 04 0000 00 00",
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="truncated_type_section_before_max_stack_height",
            sections=[
                Section(kind=SectionKind.TYPE, data=b"\0\x80", custom_size=4),
                Section.Code(code=b"", custom_size=0x01),
            ],
            expected_bytecode="ef00 01 01 0004 02 0001 0001 04 0000 00 0080",
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="truncated_type_section_truncated_max_stack_height",
            sections=[
                Section(kind=SectionKind.TYPE, data=b"\0\x80\0", custom_size=4),
                Section.Code(code=b"", custom_size=0x01),
            ],
            expected_bytecode="ef00 01 01 0004 02 0001 0001 04 0000 00 008000",
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="no_code_section_contents",
            sections=[Section.Code(code="0x", custom_size=0x01)],
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="incomplete_code_section_contents",
            sections=[
                Section.Code(code=Op.STOP, custom_size=0x02),
            ],
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="trailing_bytes_after_code_section",
            sections=[Section.Code(code=Op.PUSH1(0) + Op.STOP)],
            extra=bytes([0xDE, 0xAD, 0xBE, 0xEF]),
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="empty_code_section",
            sections=[Section.Code(code="0x")],
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
            name="no_container_section_contents",
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section(kind=SectionKind.CONTAINER, data=b"", custom_size=20),
            ],
            validity_error=EOFException.INVALID_SECTION_BODIES_SIZE,
        ),
        Container(
            name="no_container_section_contents_with_data",
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section(kind=SectionKind.CONTAINER, data=b"", custom_size=20),
                Section.Data(b"\0" * 20),
            ],
            validity_error=EOFException.TOPLEVEL_CONTAINER_TRUNCATED,
        ),
        Container(
            name="no_data_section_contents",
            sections=[
                Section.Code(Op.STOP),
                Section.Data(data="0x", custom_size=1),
            ],
            code="ef0001 010004 0200010001 040001 00 00800000 00",
            validity_error=EOFException.TOPLEVEL_CONTAINER_TRUNCATED,
        ),
        Container(
            name="data_section_contents_incomplete",
            sections=[
                Section.Code(Op.STOP),
                Section.Data(data="0xAABBCC", custom_size=4),
            ],
            validity_error=EOFException.TOPLEVEL_CONTAINER_TRUNCATED,
        ),
        Container(
            name="data_section_preceding_code_section",
            auto_data_section=False,
            auto_sort_sections=AutoSection.NONE,
            sections=[
                Section.Data(data="0xDEADBEEF"),
                Section.Code(Op.STOP),
            ],
            validity_error=[EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="data_section_without_code_section",
            sections=[Section.Data(data="0xDEADBEEF")],
            # TODO the actual exception should be EOFException.MISSING_CODE_HEADER
            validity_error=[EOFException.ZERO_SECTION_SIZE, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_section_terminator_3a",
            header_terminator=bytes(),
            sections=[Section.Code(code="0x030004")],
            # TODO the exception must be about terminator
            validity_error=[
                EOFException.INVALID_SECTION_BODIES_SIZE,
                EOFException.INVALID_FIRST_SECTION_TYPE,
            ],
        ),
        Container(
            name="no_section_terminator_4a",
            header_terminator=bytes(),
            sections=[
                Section.Code(Op.STOP),
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
            expected_bytecode=(
                "ef00 01 01 0004 02 0001 0003 04 0003 04 0003 00 00800001 600000 AABBCC AABBCC"
            ),
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="multiple_code_headers",
            sections=[
                Section.Code(Op.JUMPF[1]),
                Section.Data(data="0xAA"),
                Section.Code(Op.STOP),
            ],
            auto_sort_sections=AutoSection.ONLY_BODY,
            expected_bytecode=(
                "ef00 01 01 0008 02 0001 0003 04 0001 02 0001 0001 00"
                "00800000 00800000 E50001 00 AA"
            ),
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="multiple_code_headers_2",
            sections=[
                Section.Code(Op.JUMPF[1]),
                Section.Code(Op.STOP),
                Section.Data(data="0xAA"),
            ],
            skip_join_concurrent_sections_in_header=True,
            expected_bytecode=(
                "ef00 01 01 0008 02 0001 0003 02 0001 0001 04 0001 00"
                "00800000 00800000 E50001 00 AA"
            ),
            validity_error=[
                EOFException.MISSING_DATA_SECTION,
                EOFException.UNEXPECTED_HEADER_KIND,
            ],
        ),
        Container(
            name="duplicated_code_header",
            sections=[
                Section.Code(Op.STOP),
                Section.Code(
                    b"",
                    custom_size=1,
                    skip_types_header_listing=True,
                    skip_types_body_listing=True,
                ),
                Section.Data(data="0xAA"),
            ],
            skip_join_concurrent_sections_in_header=True,
            expected_bytecode=(
                "ef00 01 01 0004 02 0001 0001 02 0001 0001 04 0001 00 00800000 00 AA"
            ),
            validity_error=[
                EOFException.MISSING_DATA_SECTION,
                EOFException.UNEXPECTED_HEADER_KIND,
            ],
        ),
        Container(
            name="multiple_code_and_data_sections",
            sections=[
                Section.Code(Op.JUMPF[1]),
                Section.Code(Op.STOP),
                Section.Data(data="0xAA"),
                Section.Data(data="0xAA"),
            ],
            expected_bytecode=(
                "ef00 01 01 0008 02 0002 0003 0001 04 0001 04 0001 00"
                "00800000 00800000 E50001 00 AA AA"
            ),
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="multiple_code_and_data_sections_2",
            sections=[
                Section.Code(Op.JUMPF[1]),
                Section.Code(Op.STOP),
                Section.Data(data="0xAA"),
                Section.Data(data="0xAA"),
            ],
            skip_join_concurrent_sections_in_header=True,
            expected_bytecode=(
                "ef00 01 01 0008 02 0001 0003 02 0001 0001 04 0001 04 0001 00"
                "00800000 00800000 E50001 00 AA AA"
            ),
            validity_error=[
                EOFException.MISSING_DATA_SECTION,
                EOFException.UNEXPECTED_HEADER_KIND,
            ],
        ),
        Container(
            name="multiple_container_headers",
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.EOFCREATE[1](0, 0, 0, 0) + Op.STOP),
                Section.Container(Container.Code(code=Op.INVALID)),
                Section.Data(data="0xAA"),
                Section.Container(Container.Code(code=Op.INVALID)),
            ],
            auto_sort_sections=AutoSection.ONLY_BODY,
            expected_bytecode=(
                "ef00 01 01 0004 02 0001 0015 03 0001 0014 04 0001 03 0001 0014 00"
                "00800005 6000600060006000ec00 6000600060006000ec01 00"
                "ef00 01 01 0004 02 0001 0001 04 0000 00 00800000 fe"
                "ef00 01 01 0004 02 0001 0001 04 0000 00 00800000 fe"
                "aa"
            ),
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="multiple_container_headers_2",
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.EOFCREATE[1](0, 0, 0, 0) + Op.STOP),
                Section.Container(Container.Code(code=Op.INVALID)),
                Section.Container(Container.Code(code=Op.INVALID)),
                Section.Data(data="0xAA"),
            ],
            skip_join_concurrent_sections_in_header=True,
            expected_bytecode=(
                "ef00 01 01 0004 02 0001 0015 03 0001 0014 03 0001 0014 04 0001 00"
                "00800005 6000600060006000ec00 6000600060006000ec01 00"
                "ef00 01 01 0004 02 0001 0001 04 0000 00 00800000 fe"
                "ef00 01 01 0004 02 0001 0001 04 0000 00 00800000 fe"
                "aa"
            ),
            validity_error=[
                EOFException.MISSING_DATA_SECTION,
                EOFException.UNEXPECTED_HEADER_KIND,
            ],
        ),
        Container(
            name="duplicated_container_header",
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section.Container(Container.Code(code=Op.INVALID)),
                Section(kind=SectionKind.CONTAINER, data=b"", custom_size=20),
                Section.Data(data="0xAA"),
            ],
            skip_join_concurrent_sections_in_header=True,
            expected_bytecode=(
                "ef00 01 01 0004 02 0001 000b 03 0001 0014 03 0001 0014 04 0001 00"
                "00800004 6000600060006000ec00 00"
                "ef00 01 01 0004 02 0001 0001 04 0000 00 00800000 fe"
                "aa"
            ),
            validity_error=[
                EOFException.MISSING_DATA_SECTION,
                EOFException.UNEXPECTED_HEADER_KIND,
            ],
        ),
        Container(
            name="unknown_section_1",
            sections=[
                Section.Code(Op.STOP),
                Section.Data(data="0x"),
                Section(kind=VERSION_MAX_SECTION_KIND + 1, data="0x01"),
            ],
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="unknown_section_2",
            sections=[
                Section(kind=VERSION_MAX_SECTION_KIND + 1, data="0x01"),
                Section.Data(data="0x"),
                Section.Code(Op.STOP),
            ],
            # TODO the exception should be about unknown section definition
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="unknown_section_empty",
            sections=[
                Section.Code(Op.STOP),
                Section.Data(data="0x"),
                Section(kind=VERSION_MAX_SECTION_KIND + 1, data="0x"),
            ],
            validity_error=[EOFException.MISSING_TERMINATOR, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="no_type_section",
            sections=[
                Section.Code(code=Op.STOP),
                Section.Data("0x00"),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=[EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="too_many_type_sections",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x00000000"),
                Section(kind=SectionKind.TYPE, data="0x00000000"),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=[EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="too_many_type_sections_2",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x00800000"),
                Section(kind=SectionKind.TYPE, data="0x00800000"),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=[EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="empty_type_section",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x"),
                Section.Code(Op.STOP),
            ],
            expected_bytecode="ef00 01 01 0000 02 0001 0001 04 0000 00 00",
            validity_error=[
                EOFException.ZERO_SECTION_SIZE,
                EOFException.INVALID_SECTION_BODIES_SIZE,
            ],
        ),
        Container(
            name="type_section_too_small_single_code_section_1",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x00"),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        Container(
            name="type_section_too_small_single_code_section_2",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x008000"),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        Container(
            name="type_section_too_big_single_code_section",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x0080000000"),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        Container(
            name="type_section_too_small_multiple_code_sections_1",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x0080000000"),
                Section.Code(Op.STOP),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        Container(
            name="type_section_too_small_multiple_code_sections_2",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x008000000080"),
                Section.Code(Op.STOP),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        Container(
            name="type_section_too_big_multiple_code_sections",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x008000000080000000"),
                Section.Code(Op.STOP),
                Section.Code(Op.STOP),
            ],
            auto_type_section=AutoSection.NONE,
            validity_error=EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        Container(
            name="invalid_first_code_section_inputs_0x01",
            sections=[Section.Code(code=Op.POP + Op.RETF, code_inputs=1)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="invalid_first_code_section_inputs_0x80",
            sections=[Section.Code(code=Op.POP + Op.RETF, code_inputs=0x80)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="invalid_first_code_section_inputs_0xff",
            sections=[Section.Code(code=Op.POP + Op.RETF, code_inputs=0xFF)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="invalid_first_code_section_outputs_0x00",
            sections=[Section.Code(code=Op.PUSH0 + Op.RETF, code_outputs=0)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="invalid_first_code_section_outputs_0x7f",
            sections=[Section.Code(code=Op.PUSH0 + Op.RETF, code_outputs=0x7F)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="invalid_first_code_section_outputs_0x81",
            sections=[Section.Code(code=Op.PUSH0 + Op.RETF, code_outputs=0x81)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="invalid_first_code_section_outputs_0xff",
            sections=[Section.Code(code=Op.PUSH0 + Op.RETF, code_outputs=0xFF)],
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="multiple_code_section_non_zero_inputs",
            sections=[
                Section.Code(code=Op.POP + Op.RETF, code_inputs=1),
                Section.Code(Op.STOP),
            ],
            # TODO the actual exception should be EOFException.INVALID_TYPE_BODY,
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="multiple_code_section_non_zero_outputs",
            sections=[
                Section.Code(code=Op.PUSH0, code_outputs=1),
                Section.Code(Op.STOP),
            ],
            # TODO the actual exception should be EOFException.INVALID_TYPE_BODY,
            validity_error=EOFException.INVALID_FIRST_SECTION_TYPE,
        ),
        Container(
            name="data_section_before_code_with_type",
            sections=[
                Section.Data(data="0xAA"),
                Section.Code(Op.STOP),
            ],
            auto_sort_sections=AutoSection.NONE,
            validity_error=[EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
        ),
        Container(
            name="data_section_listed_in_type",
            sections=[
                Section.Data(data="0x00", force_type_listing=True),
                Section.Code(Op.STOP),
            ],
            validity_error=[
                EOFException.INVALID_TYPE_SECTION_SIZE,
                EOFException.INVALID_SECTION_BODIES_SIZE,
            ],
        ),
        Container(
            name="single_code_section_incomplete_type",
            sections=[
                Section(kind=SectionKind.TYPE, data="0x00", custom_size=2),
                Section.Code(Op.STOP),
            ],
            validity_error=[
                EOFException.INVALID_SECTION_BODIES_SIZE,
                EOFException.INVALID_TYPE_SECTION_SIZE,
            ],
        ),
        Container(
            name="code_section_input_too_large",
            sections=[
                Section.Code(
                    code=((Op.PUSH0 * (MAX_CODE_INPUTS + 1)) + Op.CALLF[1] + Op.STOP),
                    max_stack_height=(MAX_CODE_INPUTS + 1),
                ),
                Section.Code(
                    code=(Op.POP * (MAX_CODE_INPUTS + 1)) + Op.RETF,
                    code_inputs=(MAX_CODE_INPUTS + 1),
                    code_outputs=0,
                    max_stack_height=0,
                ),
            ],
            validity_error=EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT,
        ),
        Container(
            name="invalid_inputs_to_non_returning_code_section_2",
            sections=[
                Section.Code(
                    code=Op.PUSH1(0) * 128 + Op.CALLF[1] + Op.STOP,
                    max_stack_height=128,
                ),
                Section.Code(
                    Op.STOP,
                    code_inputs=128,
                    code_outputs=0,
                    max_stack_height=128,
                ),
            ],
            validity_error=EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT,
        ),
        Container(
            name="code_section_output_too_large",
            sections=[
                Section.Code(
                    code=(Op.CALLF[1] + Op.STOP),
                    max_stack_height=(MAX_CODE_OUTPUTS + 2),
                ),
                Section.Code(
                    code=(Op.PUSH0 * (MAX_CODE_OUTPUTS + 2)) + Op.RETF,
                    code_inputs=0,
                    code_outputs=(MAX_CODE_OUTPUTS + 2),
                    max_stack_height=(MAX_CODE_OUTPUTS + 2),
                ),
            ],
            validity_error=EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT,
        ),
        Container(
            name="single_code_section_max_stack_size_too_large",
            sections=[
                Section.Code(
                    code=Op.CALLER * 1024 + Op.POP * 1024 + Op.STOP,
                    max_stack_height=1024,
                ),
            ],
            # TODO auto types section generation probably failed, the exception must be about code
            validity_error=EOFException.MAX_STACK_HEIGHT_ABOVE_LIMIT,
        ),
    ],
    ids=lambda c: c.name,
)
def test_invalid_containers(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Test creating various types of valid EOF V1 contracts using legacy
    initcode and a contract creating transaction.
    """
    assert container.validity_error is not None, "Invalid container without validity error"
    eof_test(
        data=bytes(container),
        expect_exception=container.validity_error,
    )


@pytest.mark.parametrize("magic_0", [0, 1, 0xEE, 0xEF, 0xF0, 0xFF])
@pytest.mark.parametrize("magic_1", [0, 1, 2, 0xFE, 0xFF])
def test_magic_validation(
    eof_test: EOFTestFiller,
    magic_0: int,
    magic_1: int,
):
    """
    Verify EOF container 2-byte magic
    """
    if magic_0 == 0xEF and magic_1 == 0:
        pytest.skip("Valid magic")
    code = bytearray(bytes(VALID_CONTAINER))
    code[0] = magic_0
    code[1] = magic_1
    eof_test(
        data=bytes(code),
        expect_exception=None if magic_0 == 0xEF and magic_1 == 0 else EOFException.INVALID_MAGIC,
    )


@pytest.mark.parametrize("version", [0, 1, 2, 0xFE, 0xFF])
def test_version_validation(
    eof_test: EOFTestFiller,
    version: int,
):
    """
    Verify EOF container version
    """
    if version == 1:
        pytest.skip("Valid version")
    code = bytearray(bytes(VALID_CONTAINER))
    code[2] = version
    eof_test(
        data=bytes(code),
        expect_exception=None if version == 1 else EOFException.INVALID_VERSION,
    )


@pytest.mark.parametrize("plus_data", [False, True])
@pytest.mark.parametrize("plus_container", [False, True])
def test_single_code_section(
    eof_test: EOFTestFiller,
    plus_data: bool,
    plus_container: bool,
):
    """
    Verify EOF container maximum number of code sections
    """
    sections = [Section.Code(Op.RETURNCONTRACT[0](0, 0) if plus_container else Op.STOP)]
    if plus_container:
        sections.append(
            Section.Container(
                container=Container(
                    sections=[
                        Section.Code(Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP)
                        for i in range(MAX_CODE_SECTIONS)
                    ],
                )
            )
        )
    if plus_data:
        sections.append(Section.Data(data=b"\0"))
    eof_test(
        data=Container(
            name="single_code_section",
            sections=sections,
            kind=ContainerKind.INITCODE if plus_container else ContainerKind.RUNTIME,
        ),
    )


@pytest.mark.parametrize("plus_data", [False, True])
@pytest.mark.parametrize("plus_container", [False, True])
def test_max_code_sections(
    eof_test: EOFTestFiller,
    plus_data: bool,
    plus_container: bool,
):
    """
    Verify EOF container maximum number of code sections
    """
    if plus_container:
        sections = [
            Section.Code(
                Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.RETURNCONTRACT[0](0, 0)
            )
            for i in range(MAX_CODE_SECTIONS)
        ]
        sections.append(
            Section.Container(
                container=Container(
                    sections=[
                        Section.Code(Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP)
                        for i in range(MAX_CODE_SECTIONS)
                    ],
                )
            )
        )
    else:
        sections = [
            Section.Code(Op.JUMPF[i + 1] if i < (MAX_CODE_SECTIONS - 1) else Op.STOP)
            for i in range(MAX_CODE_SECTIONS)
        ]
    if plus_data:
        sections.append(Section.Data(data=b"\0"))
    eof_test(
        data=Container(
            name="max_code_sections",
            sections=sections,
            kind=ContainerKind.INITCODE if plus_container else ContainerKind.RUNTIME,
        ),
    )
