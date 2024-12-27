"""EOF Classes example use."""

import pytest

from ethereum_test_tools import Bytecode, EOFException, EOFTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import AutoSection, Container, Section

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_eof_example(eof_test: EOFTestFiller):
    """Example of python EOF classes."""
    # Lets construct an EOF container code
    eof_code = Container(
        name="valid_container_example",
        sections=[
            # TYPES section is constructed automatically based on CODE
            # CODE section
            Section.Code(
                code=Op.CALLF[1](Op.PUSH0) + Op.STOP,  # bytecode to be deployed in the body
                # Code: call section 1 with a single zero as input, then stop.
                max_stack_height=1,  # define code header (in body) stack size
            ),
            # There can be multiple code sections
            Section.Code(
                # Remove input and call section 2 with no inputs, then remove output and return
                code=Op.POP + Op.CALLF[2]() + Op.POP + Op.RETF,
                code_inputs=1,
                code_outputs=0,
                max_stack_height=1,
            ),
            Section.Code(
                # Call section 3 with two inputs (address twice), return
                code=Op.CALLF[3](Op.DUP1, Op.ADDRESS) + Op.POP + Op.POP + Op.RETF,
                code_outputs=1,
                max_stack_height=3,
            ),
            Section.Code(
                # Duplicate one input and return
                code=Op.DUP1 + Op.RETF,
                code_inputs=2,
                code_outputs=3,
                max_stack_height=3,
            ),
            # DATA section
            Section.Data("0xef"),
        ],
    )

    # This will construct a valid EOF container with these bytes
    assert bytes(eof_code) == bytes.fromhex(
        "ef0001010010020004000500060008000204000100008000010100000100010003020300035fe300010050"
        "e3000250e43080e300035050e480e4ef"
    )

    eof_test(
        data=eof_code,
        expect_exception=eof_code.validity_error,
    )


def test_eof_example_custom_fields(eof_test: EOFTestFiller):
    """Example of python EOF container class tuning."""
    # if you need to overwrite certain structure bytes, you can use customization
    # this is useful for unit testing the eof structure format, you can reorganize sections
    # and overwrite the header bytes for testing purposes
    # most of the combinations are covered by the unit tests

    # This features are subject for development and will change in the future

    eof_code = Container(
        name="valid_container_example_2",
        magic=b"\xef\x00",  # magic can be overwritten for test purposes, (default is 0xEF00)
        version=b"\x01",  # version can be overwritten for testing purposes (default is 0x01)
        header_terminator=b"\x00",  # terminator byte can be overwritten (default is 0x00)
        extra=b"",  # extra bytes to be trailed after the container body bytes (default is None)
        sections=[
            # TYPES section is constructed automatically based on CODE
            # CODE section
            Section.Code(
                code=Op.PUSH1(2)
                + Op.STOP,  # this is the actual bytecode to be deployed in the body
                max_stack_height=1,  # define code header (in body) stack size
            ),
            # DATA section
            Section.Data(
                data="0xef",
                # custom_size overrides the size bytes, so you can put only 1 byte into data
                # but still make the header size of 2 to produce invalid section
                # if custom_size != len(data), the section will be invalid
                custom_size=1,
            ),
        ],
        # auto generate types section based on provided code sections
        # AutoSection.ONLY_BODY - means the section will be generated only for the body bytes
        # AutoSection.ONLY_BODY - means the section will be generated only for the header bytes
        auto_type_section=AutoSection.AUTO,
        # auto generate default data section (0x empty), by default is True
        auto_data_section=True,
        # auto sort section by order 01 02 03 04
        # AutoSection.ONLY_BODY - means the sorting will be done only for the body bytes
        # AutoSection.ONLY_BODY - means the section will be done only for the header bytes
        auto_sort_sections=AutoSection.AUTO,
    )

    eof_test(
        data=eof_code,
        expect_exception=eof_code.validity_error,
    )


@pytest.mark.parametrize(
    "data_section_bytes",
    (b"\x01", b"\xef"),
)
@pytest.mark.parametrize(
    "code_section_code, exception",
    [(Op.PUSH1(10) + Op.STOP, None), (Op.PUSH1(14), EOFException.MISSING_STOP_OPCODE)],
)
def test_eof_example_parameters(
    eof_test: EOFTestFiller,
    data_section_bytes: bytes,
    code_section_code: Bytecode,
    exception: EOFException,
):
    """Example of python EOF classes."""
    eof_code = Container(
        name="parametrized_eof_example",
        sections=[
            Section.Code(
                code=code_section_code,
                max_stack_height=1,
            ),
            Section.Data(data_section_bytes),
        ],
        validity_error=exception,
    )

    eof_test(
        data=eof_code,
        expect_exception=eof_code.validity_error,
    )
