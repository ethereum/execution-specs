"""EOF V1 Code Validation tests."""

from typing import List

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_INITCODE_SIZE
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7480.md"
REFERENCE_SPEC_VERSION = "3ee1334ef110420685f1c8ed63e80f9e1766c251"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

smallest_runtime_subcontainer = Container(
    name="Runtime Subcontainer",
    sections=[
        Section.Code(code=Op.STOP),
    ],
)

VALID: List[Container] = [
    Container(
        name="empty_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
            ),
            Section.Data(data=""),
        ],
    ),
    Container(
        name="small_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
            ),
            Section.Data(data="1122334455667788" * 4),
        ],
    ),
    Container(
        name="large_data_section",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
            ),
            Section.Data(data="1122334455667788" * 3 * 1024),
        ],
    ),
    Container(
        name="max_data_section",
        sections=[
            Section.Code(code=Op.STOP),
            # Hits the 49152 bytes limit for the entire container
            Section.Data(data=b"\x00" * (MAX_INITCODE_SIZE - len(smallest_runtime_subcontainer))),
        ],
    ),
    Container(
        name="DATALOADN_zero",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0] + Op.POP + Op.STOP,
            ),
            Section.Data(data="1122334455667788" * 16),
        ],
    ),
    Container(
        name="DATALOADN_middle",
        sections=[
            Section.Code(
                code=Op.DATALOADN[16] + Op.POP + Op.STOP,
            ),
            Section.Data(data="1122334455667788" * 16),
        ],
    ),
    Container(
        name="DATALOADN_edge",
        sections=[
            Section.Code(
                code=Op.DATALOADN[128 - 32] + Op.POP + Op.STOP,
            ),
            Section.Data(data="1122334455667788" * 16),
        ],
    ),
]

INVALID: List[Container] = [
    Container(
        name="DATALOADN_max_empty_data",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0xFFFF - 32] + Op.POP + Op.STOP,
            ),
        ],
        validity_error=EOFException.INVALID_DATALOADN_INDEX,
    ),
    Container(
        name="DATALOADN_max_small_data",
        sections=[
            Section.Code(
                code=Op.DATALOADN[0xFFFF - 32] + Op.POP + Op.STOP,
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
            ),
            Section.Data(data=("1122334455667788" * 4 * 1024)[2:]),
        ],
        validity_error=EOFException.INVALID_DATALOADN_INDEX,
    ),
    Container(
        name="data_section_over_container_limit",
        sections=[
            Section.Code(code=Op.STOP),
            # Over the 49152 bytes limit for the entire container
            Section.Data(data=(b"12345678" * 6 * 1024)[len(smallest_runtime_subcontainer) - 1 :]),
        ],
        validity_error=EOFException.CONTAINER_SIZE_ABOVE_LIMIT,
    ),
]


def container_name(c: Container):
    """Return the name of the container for use in pytest ids."""
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
        container=container,
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
        container=container,
        expect_exception=container.validity_error,
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="imm0",
            sections=[
                Section.Code(Op.DATALOADN),
                Section.Data(b"\xff" * 32),
            ],
        ),
        Container(
            name="imm1",
            sections=[
                Section.Code(Op.DATALOADN + b"\x00"),
                Section.Data(b"\xff" * 32),
            ],
        ),
        Container(
            name="imm_from_next_section",
            sections=[
                Section.Code(
                    Op.CALLF[1] + Op.JUMPF[2],
                    max_stack_height=1,
                ),
                Section.Code(
                    Op.DATALOADN + b"\x00",
                    code_outputs=1,
                ),
                Section.Code(
                    Op.STOP,
                ),
                Section.Data(b"\xff" * 32),
            ],
        ),
    ],
    ids=container_name,
)
def test_dataloadn_truncated_immediate(
    eof_test: EOFTestFiller,
    container: Container,
):
    """Test cases for DATALOADN instructions with truncated immediate bytes."""
    eof_test(container=container, expect_exception=EOFException.TRUNCATED_INSTRUCTION)
