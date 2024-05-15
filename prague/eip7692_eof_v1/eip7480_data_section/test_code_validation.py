"""
EOF V1 Code Validation tests
"""

from typing import List

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7480.md"
REFERENCE_SPEC_VERSION = "3ee1334ef110420685f1c8ed63e80f9e1766c251"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

VALID: List[Container] = [
    Container(
        name="empty_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data=""),
        ],
    ),
    Container(
        name="small_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data="1122334455667788" * 4),
        ],
    ),
    Container(
        name="large_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data="1122334455667788" * 3 * 1024),
        ],
    ),
    Container(
        name="max_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data=("1122334455667788" * 8 * 1024)[2:]),
        ],
    ),
    Container(
        name="DATALOADN_zero",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data="1122334455667788" * 16),
        ],
    ),
    Container(
        name="DATALOADN_middle",
        sections=[
            Section.Code(
                code=Op.DATALOADN[16] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data="1122334455667788" * 16),
        ],
    ),
    Container(
        name="DATALOADN_edge",
        sections=[
            Section.Code(
                code=Op.DATALOADN[128 - 32] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data="1122334455667788" * 16),
        ],
    ),
    Container(
        name="DATALOADN_max",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0xFFFF - 32] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data=("1122334455667788" * 8 * 1024)[2:]),
        ],
    ),
]

INVALID: List[Container] = [
    Container(
        name="DATALOADN_max_empty_data",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0xFFFF - 32] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
        ],
        validity_error=EOFException.INVALID_DATALOADN_INDEX,
    ),
    Container(
        name="DATALOADN_max_small_data",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0xFFFF - 32] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data="1122334455667788" * 16),
        ],
        validity_error=EOFException.INVALID_DATALOADN_INDEX,
    ),
    Container(
        name="DATALOADN_max_half_data",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0xFFFF - 32] + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1,
            ),
            Section.Data(data=("1122334455667788" * 4 * 1024)[2:]),
        ],
        validity_error=EOFException.INVALID_DATALOADN_INDEX,
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
    VALID,
    ids=container_name,
)
def test_legacy_initcode_valid_eof_v1_contract(
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
        data=container,
    )


@pytest.mark.parametrize(
    "container",
    INVALID,
    ids=container_name,
)
def test_legacy_initcode_invalid_eof_v1_contract(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Test creating various types of valid EOF V1 contracts using legacy
    initcode and a contract creating transaction.
    """
    assert container.validity_error is not None, "Invalid container without validity error"
    eof_test(
        data=container,
        expect_exception=container.validity_error,
    )
