"""
Tests for RETURNCONTRACT instruction validation
"""
import pytest

from ethereum_test_tools import EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, ContainerKind, Section
from ethereum_test_tools.exceptions import EOFException
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "f20b164b00ae5553f7536a6d7a83a0f254455e09"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_returncontract_valid_index_0(
    eof_test: EOFTestFiller,
):
    """Deploy container index 0"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCONTRACT[0](0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
    )


def test_returncontract_valid_index_1(
    eof_test: EOFTestFiller,
):
    """Deploy container index 1"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RJUMPI[6](0) + Op.RETURNCONTRACT[0](0, 0) + Op.RETURNCONTRACT[1](0, 0),
                    max_stack_height=2,
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
    )


def test_returncontract_valid_index_255(
    eof_test: EOFTestFiller,
):
    """Deploy container index 255"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    sum((Op.RJUMPI[6](0) + Op.RETURNCONTRACT[i](0, 0)) for i in range(256))
                    + Op.REVERT(0, 0),
                    max_stack_height=2,
                )
            ]
            + [Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)]))]
            * 256
        ),
    )


def test_returncontract_invalid_truncated_immediate(
    eof_test: EOFTestFiller,
):
    """Truncated immediate"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH0 + Op.RETURNCONTRACT,
                ),
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_returncontract_invalid_index_0(
    eof_test: EOFTestFiller,
):
    """Referring to non-existent container section index 0"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCONTRACT[0](0, 0),
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )


def test_returncontract_invalid_index_1(
    eof_test: EOFTestFiller,
):
    """Referring to non-existent container section index 1"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCONTRACT[1](0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )


def test_returncontract_invalid_index_255(
    eof_test: EOFTestFiller,
):
    """Referring to non-existent container section index 255"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCONTRACT[255](0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )


def test_returncontract_terminating(
    eof_test: EOFTestFiller,
):
    """Unreachable code after RETURNCONTRACT"""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCONTRACT[0](0, 0) + Op.REVERT(0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS,
    )
