"""
Different variations of EOF sections displacement
"""

from enum import Enum
from typing import List

import pytest

from ethereum_test_exceptions.exceptions import EOFExceptionInstanceOrList
from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import AutoSection, Container, Section, SectionKind

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


class SectionTest(Enum):
    """
    Enum for the test type
    """

    MISSING = 1
    WRONG_ORDER = 2


class CasePosition(Enum):
    """
    Enum for the test position
    """

    BODY = 1
    HEADER = 2
    BODY_AND_HEADER = 3


def get_expected_code_exception(
    section_kind, section_test, test_position
) -> tuple[str, EOFExceptionInstanceOrList | None]:
    """
    Verification vectors with code and exception based on test combinations
    """
    match (section_kind, section_test, test_position):
        case (SectionKind.TYPE, SectionTest.MISSING, CasePosition.HEADER):
            return (
                "ef000102000100030400010000800001305000ef",
                [EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.TYPE, SectionTest.MISSING, CasePosition.BODY):
            return (
                "ef0001010004020001000304000100305000ef",
                [
                    EOFException.INVALID_SECTION_BODIES_SIZE,
                    EOFException.INVALID_FIRST_SECTION_TYPE,
                ],
            )
        case (SectionKind.TYPE, SectionTest.MISSING, CasePosition.BODY_AND_HEADER):
            return (
                "ef0001020001000304000100305000ef",
                [EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.TYPE, SectionTest.WRONG_ORDER, CasePosition.HEADER):
            return (
                "ef000102000100030100040400010000800001305000ef",
                [EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.TYPE, SectionTest.WRONG_ORDER, CasePosition.BODY):
            return (
                "ef000101000402000100030400010030500000800001ef",
                # TODO why invalid first section type? it should say that the body incorrect
                EOFException.INVALID_FIRST_SECTION_TYPE,
            )
        case (SectionKind.TYPE, SectionTest.WRONG_ORDER, CasePosition.BODY_AND_HEADER):
            return (
                "ef000102000100030100040400010030500000800001ef",
                [EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.CODE, SectionTest.MISSING, CasePosition.HEADER):
            return (
                "ef00010100040400010000800001305000ef",
                [EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.CODE, SectionTest.MISSING, CasePosition.BODY):
            return (
                "ef000101000402000100030400010000800001ef",
                # TODO should be an exception of empty code bytes, because it can understand that
                # last byte is data section byte
                [EOFException.INVALID_SECTION_BODIES_SIZE, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.CODE, SectionTest.MISSING, CasePosition.BODY_AND_HEADER):
            return (
                "ef00010100040400010000800001ef",
                [EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.CODE, SectionTest.WRONG_ORDER, CasePosition.HEADER):
            return (
                "ef000101000404000102000100030000800001305000ef",
                [EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.CODE, SectionTest.WRONG_ORDER, CasePosition.BODY):
            return (
                "ef000101000402000100030400010000800001ef305000",
                EOFException.UNDEFINED_INSTRUCTION,
            )
        case (SectionKind.CODE, SectionTest.WRONG_ORDER, CasePosition.BODY_AND_HEADER):
            return (
                "ef000101000404000102000100030000800001ef305000",
                [EOFException.MISSING_CODE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.DATA, SectionTest.MISSING, CasePosition.HEADER):
            return (
                "ef000101000402000100030000800001305000ef",
                [EOFException.MISSING_DATA_SECTION, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.DATA, SectionTest.MISSING, CasePosition.BODY):
            return (
                "ef000101000402000100030400010000800001305000",
                EOFException.TOPLEVEL_CONTAINER_TRUNCATED,
            )
        case (SectionKind.DATA, SectionTest.MISSING, CasePosition.BODY_AND_HEADER):
            return (
                "ef000101000402000100030000800001305000",
                [EOFException.MISSING_DATA_SECTION, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.DATA, SectionTest.WRONG_ORDER, CasePosition.HEADER):
            return (
                "ef000104000101000402000100030000800001305000ef",
                [EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
        case (SectionKind.DATA, SectionTest.WRONG_ORDER, CasePosition.BODY):
            return (
                "ef0001010004020001000304000100ef00800001305000",
                EOFException.INVALID_FIRST_SECTION_TYPE,
            )
        case (SectionKind.DATA, SectionTest.WRONG_ORDER, CasePosition.BODY_AND_HEADER):
            return (
                "ef0001040001010004020001000300ef00800001305000",
                [EOFException.MISSING_TYPE_HEADER, EOFException.UNEXPECTED_HEADER_KIND],
            )
    return "", None


@pytest.mark.parametrize("section_kind", [SectionKind.TYPE, SectionKind.CODE, SectionKind.DATA])
@pytest.mark.parametrize("section_test", [SectionTest.MISSING, SectionTest.WRONG_ORDER])
@pytest.mark.parametrize(
    "test_position", [CasePosition.BODY, CasePosition.HEADER, CasePosition.BODY_AND_HEADER]
)
def test_section_order(
    eof_test: EOFTestFiller,
    section_kind: SectionKind,
    section_test: SectionTest,
    test_position: CasePosition,
):
    """
    Test sections order and it appearance in body and header
    """

    def calculate_skip_flag(kind, position) -> bool:
        return (
            False
            if (section_kind != kind)
            else (
                True
                if section_test == SectionTest.MISSING
                and (test_position == position or test_position == CasePosition.BODY_AND_HEADER)
                else False
            )
        )

    def make_section_order(kind) -> List[Section]:
        if section_test != SectionTest.WRONG_ORDER:
            return [section_type, section_code, section_data]
        if kind == SectionKind.TYPE:
            return [section_code, section_type, section_data]
        if kind == SectionKind.CODE:
            return [section_type, section_data, section_code]
        if kind == SectionKind.DATA:
            return [section_data, section_type, section_code]
        return [section_type, section_code, section_data]

    section_code = Section.Code(
        code=Op.ADDRESS + Op.POP + Op.STOP,
        skip_header_listing=calculate_skip_flag(SectionKind.CODE, CasePosition.HEADER),
        skip_body_listing=calculate_skip_flag(SectionKind.CODE, CasePosition.BODY),
    )
    section_type = Section(
        kind=SectionKind.TYPE,
        data=bytes.fromhex("00800001"),
        custom_size=4,
        skip_header_listing=calculate_skip_flag(SectionKind.TYPE, CasePosition.HEADER),
        skip_body_listing=calculate_skip_flag(SectionKind.TYPE, CasePosition.BODY),
    )
    section_data = Section.Data(
        "ef",
        skip_header_listing=calculate_skip_flag(SectionKind.DATA, CasePosition.HEADER),
        skip_body_listing=calculate_skip_flag(SectionKind.DATA, CasePosition.BODY),
    )

    expected_code, expected_exception = get_expected_code_exception(
        section_kind, section_test, test_position
    )

    eof_code = Container(
        sections=make_section_order(section_kind),
        auto_type_section=AutoSection.NONE,
        auto_sort_sections=(
            AutoSection.AUTO
            if section_test != SectionTest.WRONG_ORDER
            else (
                AutoSection.ONLY_BODY
                if test_position == CasePosition.HEADER
                else (
                    AutoSection.ONLY_HEADER
                    if test_position == CasePosition.BODY
                    else AutoSection.NONE
                )
            )
        ),
        expected_bytecode=expected_code,
    )

    eof_test(
        data=eof_code,
        expect_exception=expected_exception,
    )


@pytest.mark.parametrize("container_position", range(4))
@pytest.mark.parametrize(
    "test_position", [CasePosition.BODY, CasePosition.HEADER, CasePosition.BODY_AND_HEADER]
)
def test_container_section_order(
    eof_test: EOFTestFiller,
    container_position: int,
    test_position: CasePosition,
):
    """
    Test containers section being out of order in the header and/or body.
    This extends and follows the convention of the test_section_order()
    for the optional container section.
    """
    if container_position == 2:
        pytest.skip("Skip valid container section position")

    section_code = Section.Code(
        code=Op.EOFCREATE[0](0, 0, 0, 0)
        # TODO: Migrated tests had the following infinite loop, so it is kept here
        #       to equalize code coverage.
        + Op.RJUMP[0]
        + Op.STOP()
    )
    section_type = Section(kind=SectionKind.TYPE, data=bytes.fromhex("00800004"))
    section_data = Section.Data("ef")
    section_container = Section.Container(Container.Code(Op.INVALID))

    sections = [section_type, section_code, section_data]
    sections.insert(container_position, section_container)
    eof_code = Container(
        sections=sections,
        auto_type_section=AutoSection.NONE,
        auto_sort_sections=(
            AutoSection.ONLY_BODY
            if test_position == CasePosition.HEADER
            else (
                AutoSection.ONLY_HEADER if test_position == CasePosition.BODY else AutoSection.NONE
            )
        ),
    )

    def get_expected_exception():
        match container_position, test_position:
            case 2, _:
                return None  # Valid containers section position
            case 0, CasePosition.BODY:  # Messes up with the type section
                return EOFException.INVALID_FIRST_SECTION_TYPE
            case 1, CasePosition.BODY:  # Messes up with the code section
                return EOFException.UNDEFINED_INSTRUCTION
            case 3, CasePosition.BODY:  # Data section messes up with the container section
                return EOFException.INVALID_MAGIC
            case 0, CasePosition.HEADER | CasePosition.BODY_AND_HEADER:
                return EOFException.MISSING_TYPE_HEADER
            case 1, CasePosition.HEADER | CasePosition.BODY_AND_HEADER:
                return EOFException.MISSING_CODE_HEADER
            case 3, CasePosition.HEADER | CasePosition.BODY_AND_HEADER:
                return EOFException.MISSING_TERMINATOR

    eof_test(
        data=eof_code,
        expect_exception=get_expected_exception(),
    )
