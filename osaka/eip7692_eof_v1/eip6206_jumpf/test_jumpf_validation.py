"""EOF validation tests for JUMPF instruction."""

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6206.md"
REFERENCE_SPEC_VERSION = "2f365ea0cd58faa6e26013ea77ce6d538175f7d0"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="jumpf1",
            sections=[
                Section.Code(
                    Op.JUMPF[1],
                )
            ],
        ),
        Container(
            name="jumpf2",
            sections=[
                Section.Code(
                    Op.JUMPF[2],
                ),
                Section.Code(
                    Op.STOP,
                ),
            ],
        ),
        Container(
            name="jumpf1_jumpf2",
            sections=[
                Section.Code(
                    Op.JUMPF[1],
                ),
                Section.Code(
                    Op.JUMPF[2],
                ),
            ],
        ),
    ],
    ids=lambda container: container.name,
)
def test_invalid_code_section_index(
    eof_test: EOFTestFiller,
    container: Container,
):
    """Test cases for JUMPF instructions with invalid target code section index."""
    eof_test(data=container, expect_exception=EOFException.INVALID_CODE_SECTION_INDEX)
