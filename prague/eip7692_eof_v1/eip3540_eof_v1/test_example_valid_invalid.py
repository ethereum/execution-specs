"""
EOF Classes example use
"""

import pytest

from ethereum_test_tools import EOFTestFiller, Opcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Bytes, Container, EOFException, Section

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "eof_code,expected_hex_bytecode,exception",
    [
        pytest.param(
            # Check that simple EOF1 deploys
            Container(
                name="EOF1V0001",
                sections=[
                    Section.Code(
                        code=Op.ADDRESS + Op.POP + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0xef"),
                ],
            ),
            "ef000101000402000100030400010000800001305000ef",
            None,
            id="simple_eof_1_deploy",
        ),
        pytest.param(
            # Check that EOF1 undersize data is ok (4 declared, 2 provided)
            # https://github.com/ipsilon/eof/blob/main/spec/eof.md#data-section-lifecycle
            Container(
                name="EOF1V0016",
                sections=[
                    Section.Code(
                        code=Op.ADDRESS + Op.POP + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad", custom_size=4),
                ],
            ),
            "ef0001010004020001000304000400008000013050000bad",
            None,
            id="undersize_data_ok",
        ),
        pytest.param(
            # Check that EOF1 with too many or too few bytes fails
            Container(
                name="EOF1I0006",
                sections=[
                    Section.Code(
                        code=Op.ADDRESS + Op.POP + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A70BAD", custom_size=4),
                ],
            ),
            "ef0001010004020001000304000400008000013050000bad60A70BAD",
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="oversize_data_fail",
        ),
        pytest.param(
            # Check that data section size is valid
            Container(
                name="EOF1V0001",
                sections=[
                    Section.Code(
                        code=Op.ADDRESS + Op.POP + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000304000400008000013050000bad60A7",
            None,
            id="data_ok",
        ),
        pytest.param(
            # Check that EOF1 with an illegal opcode fails
            Container(
                name="EOF1I0008",
                sections=[
                    Section.Code(
                        code=Op.ADDRESS + Opcode(0xEF) + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef00010100040200010003040004000080000130ef000bad60A7",
            EOFException.UNDEFINED_INSTRUCTION,
            id="illegal_opcode_fail",
        ),
        pytest.param(
            # Check that valid EOF1 can include 0xFE, the designated invalid opcode
            Container(
                name="EOF1V0004",
                sections=[
                    Section.Code(
                        code=Op.ADDRESS + Op.POP + Op.INVALID,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000304000400008000013050fe0bad60A7",
            None,
            id="fe_opcode_ok",
        ),
        pytest.param(
            # Check that EOF1 with a bad end of sections number fails
            Container(
                name="EOF1I0005",
                sections=[
                    Section.Code(
                        code=Op.ADDRESS + Op.POP + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0xef"),
                ],
                header_terminator=Bytes(b"\xFF"),
            ),
            "ef00010100040200010003040001ff00800001305000ef",
            EOFException.MISSING_TERMINATOR,
            id="headers_terminator_invalid",
        ),
        pytest.param(
            # Check that code that uses a new style relative jump succeeds
            Container(
                name="EOF1V0008",
                sections=[
                    Section.Code(
                        code=Op.PUSH0
                        + Op.RJUMPI[3]
                        + Op.RJUMP[3]
                        + Op.RJUMP[3]
                        + Op.RJUMP[-6]
                        + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000E04000400008000015FE10003E00003E00003E0FFFA000bad60A7",
            None,
            id="rjump_valid",
        ),
        pytest.param(
            # Sections with unreachable code fail
            Container(
                name="EOF1I0023",
                sections=[
                    Section.Code(code=Op.RJUMP[1] + Op.NOOP + Op.STOP),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef000101000402000100050400040000800000E000015B000bad60A7",
            EOFException.UNREACHABLE_INSTRUCTIONS,
            id="unreachable_code",
        ),
        pytest.param(
            # Check that code that uses a new style conditional jump succeeds
            Container(
                name="EOF1V0011",
                sections=[
                    Section.Code(
                        code=Op.PUSH1(1) + Op.RJUMPI[1] + Op.NOOP + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000704000400008000016001E100015B000bad60A7",
            None,
            id="rjumpi_valid",
        ),
        pytest.param(
            # Sections that end with a legit terminating opcode are OK
            Container(
                name="EOF1V0014",
                sections=[
                    Section.Code(
                        code=Op.PUSH0
                        + Op.CALLDATALOAD
                        + Op.RJUMPV[0, 3, 6, 9]
                        + Op.JUMPF[1]
                        + Op.JUMPF[2]
                        + Op.JUMPF[3]
                        + Op.CALLF[4]
                        + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Code(
                        code=Op.PUSH0 + Op.PUSH0 + Op.RETURN,
                        max_stack_height=2,
                    ),
                    Section.Code(
                        code=Op.PUSH0 + Op.PUSH0 + Op.REVERT,
                        max_stack_height=2,
                    ),
                    Section.Code(code=Op.INVALID),
                    Section.Code(
                        code=Op.RETF,
                        code_outputs=0,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "EF0001010014020005001900030003000100010400040000800001008000020080000200800000000"
            "000005f35e2030000000300060009e50001e50002e50003e30004005f5ff35f5ffdfee40bad60a7",
            None,
            id="rjumpv_section_terminator_valid",
        ),
        pytest.param(
            # Check that jump tables work
            Container(
                name="EOF1V0013",
                sections=[
                    Section.Code(
                        code=Op.PUSH1(1)
                        + Op.RJUMPV[2, 0]
                        + Op.ADDRESS
                        + Op.POP
                        + Op.ADDRESS
                        + Op.POP
                        + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000D04000400008000016001E2010002000030503050000bad60A7",
            None,
            id="jump_tables_valid",
        ),
        pytest.param(
            # Check that jumps into the middle on an opcode are not allowed
            Container(
                name="EOF1I0019",
                sections=[
                    Section.Code(
                        code=Op.PUSH1(1)
                        + Op.RJUMPV[b"\x02\x00\x02\xFF\xFF"]
                        + Op.ADDRESS
                        + Op.POP
                        + Op.ADDRESS
                        + Op.POP
                        + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000D04000400008000016001E2020002FFFF30503050000bad60A7",
            EOFException.INVALID_RJUMP_DESTINATION,
            id="rjump_invalid",
        ),
        pytest.param(
            # TODO why here is expected an exception by the comment but test is valid
            # Check that you can't get to the same opcode with two different stack heights
            Container(
                name="EOF1I0020",
                sections=[
                    Section.Code(
                        code=Op.PUSH1(1) + Op.RJUMPI[1] + Op.ADDRESS + Op.NOOP + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000804000400008000016001E10001305B000bad60A7",
            None,
            id="jump_to_opcode_ok",
        ),
        pytest.param(
            # Check that jumps into the middle on an opcode are not allowed
            Container(
                name="EOF1I0019",
                sections=[
                    Section.Code(code=Op.RJUMP[3] + Op.RJUMP[2] + Op.RJUMP[-6] + Op.STOP),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef0001010004020001000A0400040000800000E00003E00002E0FFFA000bad60A7",
            EOFException.INVALID_RJUMP_DESTINATION,
            id="rjump_3_2_m6_fails",
        ),
        pytest.param(
            # Check that jumps into the middle on an opcode are not allowed
            Container(
                name="EOF1I0019",
                sections=[
                    Section.Code(
                        code=Op.PUSH1(0)
                        + Op.PUSH1(0)
                        + Op.PUSH1(0)
                        + Op.RJUMPI[3]
                        + Op.RJUMPI[2]
                        + Op.RJUMPI[-6]
                        + Op.STOP,
                        max_stack_height=3,
                    ),
                    Section.Data("0x0bad60A7"),
                ],
            ),
            "ef000101000402000100100400040000800003600060006000E10003E10002E1FFFA000bad60A7",
            EOFException.INVALID_RJUMP_DESTINATION,
            id="push1_0_0_0_rjump_3_2_m6_fails",
        ),
        pytest.param(
            # Check that that code that uses removed opcodes fails
            Container(
                name="EOF1I0015",
                sections=[
                    Section.Code(
                        code=Op.PUSH1(3) + Op.JUMP + Op.JUMPDEST + Op.STOP,
                        max_stack_height=1,
                    ),
                    Section.Data("0xef"),
                ],
            ),
            "ef0001010004020001000504000100008000016003565B00ef",
            EOFException.UNDEFINED_INSTRUCTION,
            id="jump_jumpdest_fails",
        ),
    ],
)
def test_example_valid_invalid(
    eof_test: EOFTestFiller,
    eof_code: Container,
    expected_hex_bytecode: str,
    exception: EOFException | None,
):
    """
    Verify eof container construction and exception
    """
    # TODO remove this after Container class implementation is reliable
    assert bytes(eof_code).hex() == bytes.fromhex(expected_hex_bytecode).hex()

    eof_test(
        data=eof_code,
        expect_exception=exception,
    )


@pytest.mark.parametrize(
    "skip_header_listing, skip_body_listing, skip_types_body_listing, skip_types_header_listing,"
    "expected_code, expected_exception",
    [
        (
            # Data 16 test case of valid invalid eof ori filler
            True,  # second section is not in code header array
            True,  # second section is not in container's body (it's code bytes)
            False,  # but it's code input bytes still listed in container's body
            False,  # but it's code input bytes size still added to types section size
            "ef000101000802000100030400040000800001000000003050000bad60A7",
            EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        (
            True,  # second section is not in code header array
            False,  # second section code is in container's body (3050000)
            False,  # but it's code input bytes still listed in container's body
            False,  # but it's code input bytes size still added to types section size
            "ef000101000802000100030400040000800001000000003050003050000bad60A7",
            EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        (
            False,  # second section is mentioned in code header array (0003)
            True,  # second section is not in container's body (it's code bytes)
            False,  # but it's code input bytes still listed in container's body
            False,  # but it's code input bytes size still added to types section size
            "ef0001010008020002000300030400040000800001000000003050000bad60A7",
            EOFException.UNREACHABLE_CODE_SECTIONS,
        ),
        (
            False,  # second section is mentioned in code header array (0003)
            False,  # second section code is in container's body (3050000)
            False,  # but it's code input bytes still listed in container's body
            False,  # but it's code input bytes size still added to types section size
            "ef0001010008020002000300030400040000800001000000003050003050000bad60A7",
            EOFException.UNREACHABLE_CODE_SECTIONS,
        ),
        (
            # Data 17 test case of valid invalid eof ori filler
            True,  # second section is not in code header array
            True,  # second section is not in container's body (it's code bytes)
            True,  # it's code input bytes are not listed in container's body (00000000)
            False,  # but it's code input bytes size still added to types section size
            "ef0001010008020001000304000400008000013050000bad60a7",
            EOFException.INVALID_TYPE_SECTION_SIZE,
        ),
        (
            True,  # second section is not in code header array
            True,  # second section is not in container's body (it's code bytes)
            True,  # it's code input bytes are not listed in container's body (00000000)
            True,  # and it is bytes size is not counted in types header
            "ef0001010004020001000304000400008000013050000bad60a7",
            None,
        ),
    ],
)
def test_code_section_header_body_mismatch(
    eof_test: EOFTestFiller,
    skip_header_listing: bool,
    skip_body_listing: bool,
    skip_types_body_listing: bool,
    skip_types_header_listing: bool,
    expected_code: str,
    expected_exception: EOFException | None,
):
    """
    Inconsistent number of code sections (between types and code)
    """
    eof_code = Container(
        name="EOF1I0018",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                max_stack_height=1,
            ),
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
                # weather to not mention it in code section header list
                skip_header_listing=skip_header_listing,
                # weather to not print it's code in containers body
                skip_body_listing=skip_body_listing,
                # weather to not print it's input bytes in containers body
                skip_types_body_listing=skip_types_body_listing,
                # weather to not calculate it's input bytes size in types section's header
                skip_types_header_listing=skip_types_header_listing,
            ),
            Section.Data("0x0bad60A7"),
        ],
    )

    # TODO remove this after Container class implementation is reliable
    assert bytes(eof_code).hex() == bytes.fromhex(expected_code).hex()

    eof_test(
        data=eof_code,
        expect_exception=expected_exception,
    )
