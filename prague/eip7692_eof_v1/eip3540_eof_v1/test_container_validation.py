"""
EOF validation tests for EIP-3540 container format
"""


import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, ContainerKind, Section
from ethereum_test_tools.eof.v1.constants import MAX_CODE_SECTIONS

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

VALID_CONTAINER = Container(sections=[Section.Code(code=Op.STOP)])


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
            name="max_code_sections",
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
