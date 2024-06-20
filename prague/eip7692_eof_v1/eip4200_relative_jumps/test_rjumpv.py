"""
EOF JUMPF tests covering stack and code validation rules.
"""

import pytest

from ethereum_test_tools import Account, EOFException, EOFStateTestFiller, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import JumpDirection, slot_code_worked, slot_conditional_result, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4200.md"
REFERENCE_SPEC_VERSION = "17d4a8d12d2b5e0f2985c866376c16c8c6df7cba"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(0, id="c0"),
        pytest.param(1, id="c1"),
        pytest.param(3, id="c3"),
        pytest.param(255, id="c255"),
        pytest.param(256, id="c256"),
        pytest.param(2**256 - 1, id="c2^256-1"),
    ],
)
@pytest.mark.parametrize(
    "table_size",
    [
        pytest.param(1, id="t1"),
        pytest.param(3, id="t3"),
        pytest.param(256, id="t256"),
    ],
)
def test_rjumpv_condition(
    eof_state_test: EOFStateTestFiller,
    calldata: int,
    table_size: int,
):
    """Test RJUMPV contract switching based on external input"""
    value_fall_through = 0xFFFF
    value_base = 0x1000  # Force a `PUSH2` instruction to be used on all targets
    target_length = 7
    jump_table = [(i + 1) * target_length for i in range(table_size)]

    jump_targets = sum(
        (Op.SSTORE(slot_conditional_result, i + value_base) + Op.STOP) for i in range(table_size)
    )

    fall_through_case = Op.SSTORE(slot_conditional_result, value_fall_through) + Op.STOP

    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.CALLDATALOAD
                    + Op.RJUMPV[jump_table]
                    + fall_through_case
                    + jump_targets,
                )
            ]
        ),
        tx_data=calldata.to_bytes(32, "big"),
        container_post=Account(
            storage={
                slot_conditional_result: calldata + value_base
                if calldata < table_size
                else value_fall_through,
            }
        ),
    )


def test_rjumpv_forwards(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0008 (Valid) EOF with RJUMPV table size 1 (Positive)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0)
                    + Op.RJUMPV[3]
                    + Op.NOOP
                    + Op.NOOP
                    + Op.STOP
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_backwards(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0009 (Valid) EOF with RJUMPV table size 1 (Negative)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0)
                    + Op.RJUMPI[7]
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                    + Op.PUSH1(0)
                    + Op.RJUMPV[-13]
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_zero(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0010 (Valid) EOF with RJUMPV table size 1 (Zero)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0)
                    + Op.RJUMPV[0]
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_size_3(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0011 (Valid) EOF with RJUMPV table size 3"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0)
                    + Op.RJUMPV[3, 0, -10]
                    + Op.NOOP
                    + Op.NOOP
                    + Op.STOP
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_full_table(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0012 (Valid) EOF with RJUMPV table size 256 (Target 0)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0)
                    + Op.RJUMPV[range(256)]
                    + Op.NOOP * 256
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_full_table_mid(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0013 (Valid) EOF with RJUMPV table size 256 (Target 100)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(100)
                    + Op.RJUMPV[range(256)]
                    + Op.NOOP * 256
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_full_table_end(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0014 (Valid) EOF with RJUMPV table size 256 (Target 254)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(254)
                    + Op.RJUMPV[range(256)]
                    + Op.NOOP * 256
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_full_table_last(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0015 (Valid) EOF with RJUMPV table size 256 (Target 256)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH2(256)
                    + Op.RJUMPV[range(256)]
                    + Op.NOOP * 256
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_max_forwards(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0016 (Valid) EOF with RJUMPV containing the maximum offset (32767)"""
    eof_state_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPV[32767]
                    + Op.NOOP * 32768
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpv_truncated(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0027 (Invalid) EOF code containing RJUMPV with max_index 0 but no immediates"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[b"\0"],
                )
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_rjumpv_truncated_1(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0028 (Invalid) EOF code containing truncated RJUMPV"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV,
                )
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )
    #     - data: |


def test_rjumpv_truncated_2(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0029 (Invalid) EOF code containing truncated RJUMPV"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[b"\0\0"],
                )
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_rjumpv_truncated_3(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0030 (Invalid) EOF code containing truncated RJUMPV"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[b"\0\0"],
                )
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_rjumpv_truncated_4(
    eof_test: EOFTestFiller,
):
    """EOF code containing truncated RJUMPV table"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[b"\2\0\0\0\0"],
                )
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_into_header(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """
    EOF1I4200_0031 (Invalid) EOF code containing RJUMPV with target outside code bounds
    (Jumping into header)
    """
    invalid_destination = -5 - (2 * table_size)
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_before_container(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """
    EOF1I4200_0032 (Invalid) EOF code containing RJUMPV with target outside code bounds
    (Jumping to before code begin)
    """
    invalid_destination = -13 - (2 * table_size)
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_into_data(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """
    EOF1I4200_0033 (Invalid) EOF code containing RJUMPV with target outside code bounds
    (Jumping into data section)
    """
    invalid_destination = 2
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP,
                ),
                Section.Data(data=b"\xaa\xbb\xcc"),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_after_container(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """
    EOF1I4200_0034 (Invalid) EOF code containing RJUMPV with target outside code bounds
    (Jumping to after code end)
    """
    invalid_destination = 2
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_at_end(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """
    EOF1I4200_0035 (Invalid) EOF code containing RJUMPV with target outside code bounds
    (Jumping to code end)
    """
    invalid_destination = 1
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpv_into_self(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
    data_portion_end: bool,
):
    """EOF1I4200_0036 (Invalid) EOF code containing RJUMPV with target same RJUMPV immediate"""
    invalid_destination = -1 if data_portion_end else -(2 * table_size) - 1
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpv_into_rjump(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
    data_portion_end: bool,
):
    """EOF1I4200_0037 (Invalid) EOF code containing RJUMPV with target RJUMP immediate"""
    invalid_destination = 3 if data_portion_end else 2
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    if table_size > 1:
        valid_index = 0
        if valid_index == invalid_index:
            valid_index += 1
        jump_table[valid_index] = 1
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP + Op.RJUMP[0] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpv_into_rjumpi(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
    data_portion_end: bool,
):
    """EOF1I4200_0038 (Invalid) EOF code containing RJUMPV with target RJUMPI immediate"""
    invalid_destination = 5 if data_portion_end else 4
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    if table_size > 1:
        valid_index = 0
        if valid_index == invalid_index:
            valid_index += 1
        jump_table[valid_index] = 1
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPV[jump_table]
                    + Op.STOP
                    + Op.PUSH1(1)
                    + Op.RJUMPI[0]
                    + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
@pytest.mark.parametrize("jump", [JumpDirection.FORWARD, JumpDirection.BACKWARD])
def test_rjumpv_into_push_1(
    eof_test: EOFTestFiller,
    jump: JumpDirection,
    table_size: int,
    invalid_index: int,
):
    """EOF1I4200_0039 (Invalid) EOF code containing RJUMPV with target PUSH1 immediate"""
    if jump == JumpDirection.FORWARD:
        invalid_destination = 2
        jump_table = [0 for _ in range(table_size)]
        jump_table[invalid_index] = invalid_destination
        code = (
            Op.PUSH1(1)
            + Op.RJUMPV[jump_table]
            + Op.STOP
            + Op.PUSH1(1)
            + Op.PUSH1(1)
            + Op.SSTORE
            + Op.STOP
        )
    else:
        invalid_destination = -(2 * table_size) - 3
        jump_table = [0 for _ in range(table_size)]
        jump_table[invalid_index] = invalid_destination
        code = Op.PUSH1(1) + Op.RJUMPV[jump_table] + Op.STOP
    eof_test(
        data=Container(
            sections=[Section.Code(code=code)],
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
@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
@pytest.mark.parametrize("jump", [JumpDirection.FORWARD, JumpDirection.BACKWARD])
def test_rjumpv_into_push_n(
    eof_test: EOFTestFiller,
    opcode: Op,
    jump: JumpDirection,
    table_size: int,
    invalid_index: int,
    data_portion_end: bool,
):
    """EOF1I4200_0039 (Invalid) EOF code containing RJUMPV with target PUSH1 immediate"""
    data_portion_length = int.from_bytes(opcode, byteorder="big") - 0x5F
    if jump == JumpDirection.FORWARD:
        invalid_destination = data_portion_length + 1 if data_portion_end else 2
        jump_table = [0 for _ in range(table_size)]
        jump_table[invalid_index] = invalid_destination
        code = (
            Op.PUSH1(1)
            + Op.RJUMPV[jump_table]
            + Op.STOP
            + opcode[1]
            + Op.PUSH1(1)
            + Op.SSTORE
            + Op.STOP
        )
    else:
        invalid_destination = (
            -(2 * table_size) - 3
            if data_portion_end
            else -(2 * table_size) - 2 - data_portion_length
        )
        jump_table = [0 for _ in range(table_size)]
        jump_table[invalid_index] = invalid_destination
        code = opcode[1] + Op.RJUMPV[jump_table] + Op.STOP
    eof_test(
        data=Container(
            sections=[Section.Code(code=code)],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "source_table_size,invalid_index",
    [
        pytest.param(1, 0, id="s1i0"),
        pytest.param(256, 0, id="s256i0"),
        pytest.param(256, 255, id="s256i255"),
    ],
)
@pytest.mark.parametrize("target_table_size", [1, 256], ids=["t1", "t256"])
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpv_into_rjumpv(
    eof_test: EOFTestFiller,
    source_table_size: int,
    target_table_size: int,
    invalid_index: int,
    data_portion_end: bool,
):
    """EOF1I4200_0040 (Invalid) EOF code containing RJUMPV with target other RJUMPV immediate"""
    invalid_destination = 4 + (2 * target_table_size) if data_portion_end else 4
    source_jump_table = [0 for _ in range(source_table_size)]
    source_jump_table[invalid_index] = invalid_destination
    target_jump_table = [0 for _ in range(target_table_size)]
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPV[source_jump_table]
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
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpv_into_callf(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
    data_portion_end: bool,
):
    """EOF1I4200_0041 (Invalid) EOF code containing RJUMPV with target CALLF immediate"""
    invalid_destination = 2 if data_portion_end else 1
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0) + Op.RJUMPV[jump_table] + Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    code=Op.SSTORE(1, 1) + Op.RETF,
                    code_outputs=0,
                ),
            ]
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_into_dupn(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """EOF code containing RJUMP with target DUPN immediate"""
    invalid_destination = 1
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.PUSH1(0)
                    + Op.RJUMPV[jump_table]
                    + Op.DUPN[1]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_into_swapn(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """EOF code containing RJUMP with target SWAPN immediate"""
    invalid_destination = 1
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.PUSH1(0)
                    + Op.RJUMPV[jump_table]
                    + Op.SWAPN[1]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjump_into_exchange(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """EOF code containing RJUMP with target EXCHANGE immediate"""
    invalid_destination = 1
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(2)
                    + Op.PUSH1(3)
                    + Op.PUSH1(0)
                    + Op.RJUMPV[1]
                    + Op.EXCHANGE[0x00]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_into_eofcreate(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """EOF code containing RJUMP with target EOFCREATE immediate"""
    invalid_destination = 9
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0)
                    + Op.RJUMPV[jump_table]
                    + Op.EOFCREATE[0](0, 0, 0, 0)
                    + Op.STOP,
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


@pytest.mark.parametrize(
    "table_size,invalid_index",
    [
        pytest.param(1, 0, id="t1i0"),
        pytest.param(256, 0, id="t256i0"),
        pytest.param(256, 255, id="t256i255"),
    ],
)
def test_rjumpv_into_returncontract(
    eof_test: EOFTestFiller,
    table_size: int,
    invalid_index: int,
):
    """EOF code containing RJUMP with target RETURNCONTRACT immediate"""
    invalid_destination = 5
    jump_table = [0 for _ in range(table_size)]
    jump_table[invalid_index] = invalid_destination
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
                                code=Op.PUSH1(0)
                                + Op.RJUMPV[jump_table]
                                + Op.RETURNCONTRACT[0](0, 0),
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
