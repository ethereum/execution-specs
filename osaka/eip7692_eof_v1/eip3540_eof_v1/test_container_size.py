"""
EOF validation tests for EIP-3540 container size
"""

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_INITCODE_SIZE

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "6b313505c75afa49a4f34de39c609ebebc7be87f"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

VALID_CONTAINER = Container(sections=[Section.Code(code=Op.STOP)])


@pytest.mark.parametrize(
    "over_limit",
    [0, 1, 2, 2**16 - MAX_INITCODE_SIZE],
)
def test_max_size(
    eof_test: EOFTestFiller,
    over_limit: int,
):
    """
    Verify EOF container valid at maximum size, invalid above
    """
    # Expand the minimal EOF code by more noop code, reaching the desired target container size.
    code = Container(
        sections=[
            Section.Code(
                code=Op.JUMPDEST * (MAX_INITCODE_SIZE - len(VALID_CONTAINER) + over_limit)
                + Op.STOP
            )
        ]
    )
    assert len(code) == MAX_INITCODE_SIZE + over_limit
    eof_test(
        data=bytes(code),
        expect_exception=None if over_limit == 0 else EOFException.CONTAINER_SIZE_ABOVE_LIMIT,
    )


@pytest.mark.parametrize(
    "size",
    [MAX_INITCODE_SIZE + 1, MAX_INITCODE_SIZE * 2],
)
def test_above_max_size_raw(
    eof_test: EOFTestFiller,
    size: int,
):
    """
    Verify EOF container invalid above maximum size, regardless of header contents
    """
    code = Op.INVALID * size
    eof_test(
        data=bytes(code),
        expect_exception=EOFException.CONTAINER_SIZE_ABOVE_LIMIT,
    )


@pytest.mark.parametrize(
    "code",
    [
        pytest.param(
            Container(sections=[Section.Code(code=Op.STOP, custom_size=MAX_INITCODE_SIZE)]),
            id="1st_code_section",
        ),
        pytest.param(
            Container(
                sections=[
                    Section.Code(code=Op.STOP),
                    Section.Code(code=Op.STOP, custom_size=MAX_INITCODE_SIZE),
                ]
            ),
            id="2nd_code_section",
        ),
        pytest.param(
            Container(
                sections=[
                    Section.Code(code=Op.STOP),
                    Section.Container(container=Op.STOP, custom_size=MAX_INITCODE_SIZE),
                ]
            ),
            id="1st_container_section",
        ),
        pytest.param(
            Container(
                sections=[
                    Section.Code(code=Op.STOP),
                    Section.Container(container=Op.STOP),
                    Section.Container(container=Op.STOP, custom_size=MAX_INITCODE_SIZE),
                ]
            ),
            id="2nd_container_section",
        ),
    ],
)
def test_section_after_end_of_container(
    eof_test: EOFTestFiller,
    code: Container,
):
    """
    Verify EOF container is invalid if any of sections declares above container size
    """
    eof_test(
        data=bytes(code),
        expect_exception=EOFException.INVALID_SECTION_BODIES_SIZE,
    )
