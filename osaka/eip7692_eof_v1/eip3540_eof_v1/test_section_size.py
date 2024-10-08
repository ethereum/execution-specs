"""
EOF Container, test custom_size field for sections
"""

from enum import IntEnum

import pytest

from ethereum_test_exceptions.exceptions import EOFExceptionInstanceOrList
from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section, SectionKind

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


class SectionSize(IntEnum):
    """
    Enum for the section size
    """

    NORMAL = -1
    ZERO = 0
    UNDERSIZE = 2
    OVERSIZE = 100
    HUGE = 0x8000
    MAX = 0xFFFF

    def __str__(self) -> str:
        """
        Returns the string representation of the section kind
        """
        return self.name


@pytest.mark.parametrize(
    "section_kind, section_size, exception",
    [
        pytest.param(SectionKind.DATA, SectionSize.NORMAL, None),
        pytest.param(SectionKind.DATA, SectionSize.ZERO, EOFException.INVALID_SECTION_BODIES_SIZE),
        pytest.param(
            SectionKind.DATA, SectionSize.UNDERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
        pytest.param(
            SectionKind.DATA, SectionSize.OVERSIZE, EOFException.TOPLEVEL_CONTAINER_TRUNCATED
        ),
        pytest.param(
            SectionKind.DATA, SectionSize.HUGE, EOFException.TOPLEVEL_CONTAINER_TRUNCATED
        ),
        pytest.param(SectionKind.DATA, SectionSize.MAX, EOFException.TOPLEVEL_CONTAINER_TRUNCATED),
        pytest.param(
            SectionKind.CODE, SectionSize.NORMAL, None, marks=pytest.mark.skip(reason="duplicate")
        ),
        pytest.param(SectionKind.CODE, SectionSize.ZERO, EOFException.ZERO_SECTION_SIZE),
        pytest.param(
            SectionKind.CODE, SectionSize.UNDERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
        pytest.param(
            SectionKind.CODE, SectionSize.OVERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
        pytest.param(SectionKind.CODE, SectionSize.HUGE, EOFException.INVALID_SECTION_BODIES_SIZE),
        pytest.param(SectionKind.CODE, SectionSize.MAX, EOFException.INVALID_SECTION_BODIES_SIZE),
        pytest.param(
            SectionKind.TYPE, SectionSize.NORMAL, None, marks=pytest.mark.skip(reason="duplicate")
        ),
        pytest.param(
            SectionKind.TYPE,
            SectionSize.ZERO,
            [EOFException.ZERO_SECTION_SIZE, EOFException.INVALID_SECTION_BODIES_SIZE],
            id="type_size_zero",
        ),
        pytest.param(
            SectionKind.TYPE, SectionSize.UNDERSIZE, EOFException.INVALID_TYPE_SECTION_SIZE
        ),
        pytest.param(
            SectionKind.TYPE, SectionSize.OVERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
        pytest.param(SectionKind.TYPE, SectionSize.HUGE, EOFException.INVALID_SECTION_BODIES_SIZE),
        pytest.param(
            SectionKind.TYPE,
            SectionSize.MAX,
            [EOFException.INVALID_SECTION_BODIES_SIZE, EOFException.INVALID_TYPE_SECTION_SIZE],
            id="type_size_max",
        ),
        pytest.param(
            SectionKind.CONTAINER,
            SectionSize.NORMAL,
            None,
            marks=pytest.mark.skip(reason="duplicate"),
        ),
        pytest.param(SectionKind.CONTAINER, SectionSize.ZERO, EOFException.ZERO_SECTION_SIZE),
        pytest.param(
            SectionKind.CONTAINER, SectionSize.UNDERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
        pytest.param(
            SectionKind.CONTAINER, SectionSize.OVERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
        pytest.param(
            SectionKind.CONTAINER, SectionSize.HUGE, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
        pytest.param(
            SectionKind.CONTAINER, SectionSize.MAX, EOFException.INVALID_SECTION_BODIES_SIZE
        ),
    ],
)
def test_section_size(
    eof_test: EOFTestFiller,
    section_size: SectionSize,
    section_kind: SectionKind,
    exception: EOFExceptionInstanceOrList,
):
    """
    Test custom_size is auto, more or less then the actual size of the section
    """
    eof_code = Container()

    if section_size != SectionSize.NORMAL and section_kind == SectionKind.TYPE:
        eof_code.sections.append(
            Section(
                kind=SectionKind.TYPE,
                data="0x00800001",
                custom_size=section_size,
            ),
        )

    if section_size != SectionSize.NORMAL and section_kind == SectionKind.CODE:
        eof_code.sections.append(
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP,
                custom_size=section_size,
            )
        )
    else:
        eof_code.sections.append(
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP,
            )
        )

    if section_size != SectionSize.NORMAL and section_kind == SectionKind.CONTAINER:
        eof_code.sections.append(
            Section.Container(
                container=Container(
                    sections=[
                        Section.Code(Op.RETURNCONTRACT[0](0, 0)),
                        Section.Container(container=Container(sections=[Section.Code(Op.STOP)])),
                    ]
                ),
                custom_size=section_size,
            )
        )
    else:
        eof_code.sections.append(
            Section.Container(
                container=Container(
                    sections=[
                        Section.Code(Op.RETURNCONTRACT[0](0, 0)),
                        Section.Container(container=Container(sections=[Section.Code(Op.STOP)])),
                    ]
                ),
            )
        )

    if section_size != SectionSize.NORMAL and section_kind == SectionKind.DATA:
        eof_code.sections.append(Section.Data("0x00daaa", custom_size=section_size))
    else:
        eof_code.sections.append(Section.Data("0x00aaaa"))
    eof_test(
        data=eof_code,
        expect_exception=exception,
    )


@pytest.mark.parametrize(
    "truncation_len, exception",
    [
        # The original container is not valid by itself because its 2-byte code section
        # starts with the terminating instruction: INVALID.
        pytest.param(0, EOFException.UNREACHABLE_INSTRUCTIONS),
        pytest.param(1, EOFException.INVALID_SECTION_BODIES_SIZE, id="EOF1_truncated_section_2"),
        pytest.param(3, EOFException.INVALID_SECTION_BODIES_SIZE, id="EOF1_truncated_section_1"),
        pytest.param(6, EOFException.INVALID_SECTION_BODIES_SIZE, id="EOF1_truncated_section_0"),
    ],
)
def test_truncated_container_without_data(
    eof_test: EOFTestFiller,
    truncation_len: int,
    exception: EOFException,
):
    """
    This test takes a semi-valid container and removes some bytes from its tail.
    Migrated from EOFTests/efValidation/EOF1_truncated_section_.json (cases without data section).
    """
    container = Container(sections=[Section.Code(Op.INVALID + Op.INVALID)])
    bytecode = bytes(container)
    eof_test(
        data=bytecode[: len(bytecode) - truncation_len],
        expect_exception=exception,
    )


@pytest.mark.parametrize(
    "truncation_len, exception",
    [
        pytest.param(0, None),
        pytest.param(1, EOFException.TOPLEVEL_CONTAINER_TRUNCATED, id="EOF1_truncated_section_4"),
        pytest.param(2, EOFException.TOPLEVEL_CONTAINER_TRUNCATED, id="EOF1_truncated_section_3"),
    ],
)
def test_truncated_container_with_data(
    eof_test: EOFTestFiller,
    truncation_len: int,
    exception: EOFException,
):
    """
    This test takes a valid container with data and removes some bytes from its tail.
    Migrated from EOFTests/efValidation/EOF1_truncated_section_.json (cases with data section).
    """
    data = b"\xaa\xbb"
    container = Container(
        sections=[
            Section.Code(Op.INVALID),
            Section.Data(data[0 : (len(data) - truncation_len)], custom_size=2),
        ]
    )
    eof_test(
        data=container,
        expect_exception=exception,
    )
