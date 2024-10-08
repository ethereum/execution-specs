"""
EOF JUMPF tests covering stack and code validation rules.
"""

import pytest

from ethereum_test_tools import Account, EOFException, EOFStateTestFiller, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_BYTECODE_SIZE
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import JumpDirection, slot_code_worked, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4200.md"
REFERENCE_SPEC_VERSION = "17d4a8d12d2b5e0f2985c866376c16c8c6df7cba"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

RJUMP_LEN = len(Op.RJUMP[0])


def test_rjump_positive_negative(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0001 (Valid) EOF code containing RJUMP (Positive, Negative)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.RJUMPI[3]
                    + Op.RJUMP[7]
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                    + Op.RJUMP[-10],
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjump_zero(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0002 (Valid) EOF code containing RJUMP (Zero)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RJUMP[0] + Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjump_maxes(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0003 EOF with RJUMP containing the maximum positive and negative offset (32767)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.RJUMPI[
                        RJUMP_LEN
                    ]  # The push/jumpi is to allow the NOOPs to be forward referenced
                    + Op.RJUMP[0x7FFF]
                    + Op.NOOP * (0x7FFF - 7)
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                    + Op.RJUMP[0x8000],
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjump_max_bytecode_size(
    eof_test: EOFTestFiller,
):
    """
    EOF1V4200_0003 EOF with RJUMP containing the maximum offset that does not exceed the maximum
    bytecode size
    """
    NOOP_COUNT = MAX_BYTECODE_SIZE - 27
    code = (
        Op.RJUMPI[RJUMP_LEN](Op.ORIGIN)  # The jumpi is to allow the NOOPs to be forward referenced
        + Op.RJUMP[len(Op.NOOP) * NOOP_COUNT]
        + (Op.NOOP * NOOP_COUNT)
        + Op.STOP
    )
    container = Container.Code(code=code)
    assert len(container) == MAX_BYTECODE_SIZE
    eof_test(data=container)


def test_rjump_truncated_rjump(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0001 (Invalid) EOF code containing truncated RJUMP"""
    eof_test(
        data=Container(
            sections=[Section.Code(code=Op.RJUMP)],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_rjump_truncated_rjump_2(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0002 (Invalid) EOF code containing truncated RJUMP"""
    eof_test(
        data=Container(
            sections=[Section.Code(code=Op.RJUMP + Op.STOP)],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_rjump_into_header(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0003 (Invalid) EOF code containing RJUMP with target outside code bounds
    (Jumping into header)
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[-5]),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_before_header(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0004 (Invalid) EOF code containing RJUMP with target outside code bounds
    (Jumping before code begin)
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[-23]),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_data(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0005 (Invalid) EOF code containing RJUMP with target outside code bounds
    (Jumping into data section)
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[2]),
                Section.Data(data=b"\xaa\xbb\xcc"),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_outside_other_section_before(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target outside code bounds (prior code section)"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.JUMPF[1]),
                Section.Code(code=Op.RJUMP[-6]),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_outside_other_section_after(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target outside code bounds (Subsequent code section)"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.JUMPF[1]),
                Section.Code(code=Op.RJUMP[3] + Op.JUMPF[2]),
                Section.Code(code=Op.STOP),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_after_container(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0006 (Invalid) EOF code containing RJUMP with target outside code bounds
    (Jumping after code end)
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[2]),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_to_code_end(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0007 (Invalid) EOF code containing RJUMP with target outside code bounds
    (Jumping to code end)
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[1] + Op.STOP),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize("offset", range(1, Op.RJUMP.data_portion_length + 1))
def test_rjump_into_self_data_portion(
    eof_test: EOFTestFiller,
    offset: int,
):
    """EOF1I4200_0008 (Invalid) EOF code containing RJUMP with target self RJUMP immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[-offset] + Op.STOP),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_self_remaining_code(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0008 (Invalid) EOF code containing RJUMP with target self RJUMP but remaining
    unreachable code
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[-len(Op.RJUMP[0])] + Op.STOP),
            ],
        ),
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS,
    )


def test_rjump_into_self(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target self RJUMP"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[-len(Op.RJUMP[0])]),
            ],
        ),
    )


def test_rjump_into_self_pre_code(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target self RJUMP with non-zero stack before RJUMP"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.PUSH1(0) + Op.RJUMP[-len(Op.RJUMP[0])]),
            ],
        ),
    )


def test_rjump_into_stack_height_diff(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target instruction that causes stack height difference"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.PUSH1(0) + Op.RJUMP[-(len(Op.RJUMP[0]) + len(Op.PUSH1(0)))]),
            ],
        ),
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_rjump_into_stack_height_diff_2(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target instruction that cause stack height difference"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0) + Op.POP + Op.RJUMP[-(len(Op.RJUMP[0]) + len(Op.POP))]
                ),
            ],
        ),
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_rjump_into_stack_underflow(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target instruction that cause stack underflow"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.ORIGIN
                    + Op.RJUMPI[len(Op.RJUMP[0])]
                    + Op.RJUMP[len(Op.STOP)]
                    + Op.STOP
                    + Op.POP
                    + Op.STOP
                ),
            ],
        ),
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


def test_rjump_into_rjump(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0009 (Invalid) EOF code containing RJUMP with target other RJUMP immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=Op.RJUMP[1] + Op.RJUMP[0]),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_rjumpi(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0010 (Invalid) EOF code containing RJUMP with target RJUMPI immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RJUMP[5] + Op.STOP + Op.PUSH1(1) + Op.RJUMPI[-6] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize("jump", [JumpDirection.FORWARD, JumpDirection.BACKWARD])
def test_rjump_into_push_1(eof_test: EOFTestFiller, jump: JumpDirection):
    """EOF1I4200_0011 (Invalid) EOF code containing RJUMP with target PUSH1 immediate"""
    code = (
        Op.PUSH1[1] + Op.RJUMP[-4] if jump == JumpDirection.BACKWARD else Op.RJUMP[1] + Op.PUSH1[1]
    ) + Op.STOP
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=code),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.PUSH2,
        Op.PUSH3,
        Op.PUSH4,
        Op.PUSH5,
        Op.PUSH6,
        Op.PUSH7,
        Op.PUSH8,
        Op.PUSH9,
        Op.PUSH10,
        Op.PUSH11,
        Op.PUSH12,
        Op.PUSH13,
        Op.PUSH14,
        Op.PUSH15,
        Op.PUSH16,
        Op.PUSH17,
        Op.PUSH18,
        Op.PUSH19,
        Op.PUSH20,
        Op.PUSH21,
        Op.PUSH22,
        Op.PUSH23,
        Op.PUSH24,
        Op.PUSH25,
        Op.PUSH26,
        Op.PUSH27,
        Op.PUSH28,
        Op.PUSH29,
        Op.PUSH30,
        Op.PUSH31,
        Op.PUSH32,
    ],
)
@pytest.mark.parametrize("jump", [JumpDirection.FORWARD, JumpDirection.BACKWARD])
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjump_into_push_n(
    eof_test: EOFTestFiller,
    opcode: Op,
    jump: JumpDirection,
    data_portion_end: bool,
):
    """EOF1I4200_0011 (Invalid) EOF code containing RJUMP with target PUSH2+ immediate"""
    data_portion_length = int.from_bytes(opcode, byteorder="big") - 0x5F
    if jump == JumpDirection.FORWARD:
        offset = data_portion_length if data_portion_end else 1
        code = Op.RJUMP[offset] + opcode[0] + Op.STOP
    else:
        offset = -4 if data_portion_end else -4 - data_portion_length + 1
        code = opcode[0] + Op.RJUMP[offset]
    eof_test(
        data=Container(
            sections=[
                Section.Code(code=code),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize("target_rjumpv_table_size", [1, 256])
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjump_into_rjumpv(
    eof_test: EOFTestFiller,
    target_rjumpv_table_size: int,
    data_portion_end: bool,
):
    """EOF1I4200_0012 (Invalid) EOF code containing RJUMP with target RJUMPV immediate"""
    invalid_destination = 4 + (2 * target_rjumpv_table_size) if data_portion_end else 4
    target_jump_table = [0 for _ in range(target_rjumpv_table_size)]
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RJUMP[invalid_destination]
                    + Op.STOP
                    + Op.PUSH1(1)
                    + Op.RJUMPV[target_jump_table]
                    + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjump_into_callf(
    eof_test: EOFTestFiller,
    data_portion_end: bool,
):
    """EOF1I4200_0013 (Invalid) EOF code containing RJUMP with target CALLF immediate"""
    invalid_destination = 2 if data_portion_end else 1
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RJUMP[invalid_destination] + Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    code=Op.SSTORE(1, 1) + Op.RETF,
                    code_outputs=0,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_dupn(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target DUPN immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.RJUMP[1]
                    + Op.DUPN[1]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_swapn(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target SWAPN immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.RJUMP[1]
                    + Op.SWAPN[1]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_exchange(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target EXCHANGE immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(2)
                    + Op.PUSH1(3)
                    + Op.RJUMP[1]
                    + Op.EXCHANGE[0x00]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_eofcreate(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target EOFCREATE immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.RJUMP[1] + Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP,
                ),
                Section.Container(
                    container=Container(
                        sections=[
                            Section.Code(
                                code=Op.RETURNCONTRACT[0](0, 0),
                            ),
                            Section.Container(
                                container=Container(
                                    sections=[
                                        Section.Code(code=Op.STOP),
                                    ]
                                )
                            ),
                        ]
                    )
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_into_returncontract(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMP with target RETURNCONTRACT immediate"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP,
                ),
                Section.Container(
                    container=Container(
                        sections=[
                            Section.Code(
                                code=Op.RJUMP[5] + Op.RETURNCONTRACT[0](0, 0),
                            ),
                            Section.Container(
                                container=Container(
                                    sections=[
                                        Section.Code(code=Op.STOP),
                                    ]
                                )
                            ),
                        ]
                    )
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjump_unreachable_code(
    eof_test: EOFTestFiller,
):
    """
    EOF code containing instructions skipped by RJUMP
    """
    container = Container.Code(code=(Op.RJUMP[len(Op.STOP)] + Op.STOP + Op.STOP))
    eof_test(
        data=container,
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS,
    )


def test_rjump_backwards_reference_only(
    eof_test: EOFTestFiller,
):
    """
    EOF code containing instructions only reachable by backwards RJUMP
    """
    container = Container.Code(
        code=(Op.RJUMP[RJUMP_LEN] + Op.RJUMP[RJUMP_LEN] + Op.RJUMP[-(2 * RJUMP_LEN)] + Op.STOP)
    )
    eof_test(
        data=container,
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS,
    )


def test_rjump_backwards_illegal_stack_height(
    eof_test: EOFTestFiller,
):
    """
    Invalid backward jump, found via fuzzing coverage
    """
    eof_test(
        data=Container.Code(
            code=(
                Op.PUSH0
                + Op.RJUMPI[3]
                + Op.RJUMP(7)
                + Op.PUSH2(0x2015)
                + Op.PUSH3(0x015500)
                + Op.RJUMP[-10]
            ),
            max_stack_height=0x24,
        ),
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_rjump_backwards_infinite_loop(
    eof_test: EOFTestFiller,
):
    """
    Validate that a backwards RJUMP as terminal operation is valid
    """
    eof_test(
        data=Container(
            name="backwards_rjump_terminal",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.RJUMPI[3]
                    + Op.RJUMP[7]
                    + Op.SSTORE(1, 0x2015)
                    + Op.STOP
                    + Op.RJUMP[-10]
                ),
                Section.Data(data="0xdeadbeef"),
            ],
        ),
    )
