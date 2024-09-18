"""
Test suite for `ethereum_test_vm` module.
"""

import pytest

from ethereum_test_base_types import Address

from ..opcode import Bytecode
from ..opcode import Macros as Om
from ..opcode import Opcodes as Op


@pytest.mark.parametrize(
    "opcodes,expected",
    [
        pytest.param(Op.PUSH1(0x01), b"\x60\x01", id="PUSH1(0x01)"),
        pytest.param(Op.PUSH1[0x01], b"\x60\x01", id="PUSH1[0x01]"),
        pytest.param(Op.PUSH1("0x01"), b"\x60\x01", id="PUSH1('0x01')"),
        pytest.param(Op.PUSH1["0x01"], b"\x60\x01", id="PUSH1['0x01']"),
        pytest.param(Op.PUSH1(0xFF), b"\x60\xFF", id="PUSH1(0xFF)"),
        pytest.param(Op.PUSH1(-1), b"\x60\xFF", id="PUSH1(-1)"),
        pytest.param(Op.PUSH1[-1], b"\x60\xFF", id="PUSH1[-1]"),
        pytest.param(Op.PUSH1(-2), b"\x60\xFE", id="PUSH1(-2)"),
        pytest.param(Op.PUSH20(0x01), b"\x73" + b"\x00" * 19 + b"\x01", id="PUSH20(0x01)"),
        pytest.param(Op.PUSH20[0x01], b"\x73" + b"\x00" * 19 + b"\x01", id="PUSH20[0x01]"),
        pytest.param(Op.PUSH32(0xFF), b"\x7F" + b"\x00" * 31 + b"\xFF", id="PUSH32(0xFF)"),
        pytest.param(Op.PUSH32(-1), b"\x7F" + b"\xFF" * 32, id="PUSH32(-1)"),
        pytest.param(
            sum(Op.PUSH1(i) for i in range(0x2)),
            b"\x60\x00\x60\x01",
            id="sum(PUSH1(i) for i in range(0x2))",
        ),
        pytest.param(
            sum(Op.PUSH1[i] for i in range(0x2)),
            b"\x60\x00\x60\x01",
            id="sum(PUSH1[i] for i in range(0x2))",
        ),
        pytest.param(
            Op.SSTORE(
                -1,
                Op.CALL(
                    Op.GAS,
                    Op.ADDRESS,
                    Op.PUSH1(0x20),
                    0,
                    0,
                    0x20,
                    0x1234,
                ),
            ),
            bytes(
                [
                    0x61,
                    0x12,
                    0x34,
                    0x60,
                    0x20,
                    0x60,
                    0x00,
                    0x60,
                    0x00,
                    0x60,
                    0x20,
                    0x30,
                    0x5A,
                    0xF1,
                    0x7F,
                ]
                + [0xFF] * 32
                + [0x55]
            ),
            id="SSTORE(-1, CALL(GAS, ADDRESS, PUSH1(0x20), 0, 0, 0x20, 0x1234))",
        ),
        pytest.param(
            Op.CALL(Op.GAS, Op.PUSH20(0x1234), 0, 0, 0, 0, 32),
            b"\x60\x20\x60\x00\x60\x00\x60\x00\x60\x00\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x12\x34\x5A\xF1",
            id="CALL(GAS, PUSH20(0x1234), 0, 0, 0, 0, 32)",
        ),
        pytest.param(
            Op.CALL(Op.GAS, Address(0x1234), 0, 0, 0, 0, 32),
            b"\x60\x20\x60\x00\x60\x00\x60\x00\x60\x00\x61\x12\x34\x5A\xF1",
            id="CALL(GAS, Address(0x1234), 0, 0, 0, 0, 32)",
        ),
        pytest.param(Op.ADD(1, 2), bytes([0x60, 0x02, 0x60, 0x01, 0x01]), id="ADD(1, 2)"),
        pytest.param(
            Op.ADD(Op.ADD(1, 2), 3),
            bytes([0x60, 0x03, 0x60, 0x02, 0x60, 0x01, 0x01, 0x01]),
            id="ADD(ADD(1, 2), 3)",
        ),
        pytest.param(
            Op.CALL(1, 123, 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x60\x7b\x60\x01\xf1",
            id="CALL(1, 123, 4, 5, 6, 7, 8)",
        ),
        pytest.param(
            Op.CALL(1, Address(0x0123), 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x61\x01\x23\x60\x01\xf1",
            id="CALL(1, Address(0x0123), 4, 5, 6, 7, 8)",
        ),
        pytest.param(
            Op.CALL(1, 0x0123, 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x61\x01\x23\x60\x01\xf1",
            id="CALL(1, 0x0123, 4, 5, 6, 7, 8)",
        ),
        pytest.param(
            Op.CALL(1, 123, 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x60\x7b\x60\x01\xf1",
            id="CALL(1, 123, 4, 5, 6, 7, 8)",
        ),
        pytest.param(
            Op.CREATE(1, Address(12), 4, 5, 6, 7, 8, unchecked=True),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x60\x0c\x60\x01\xf0",
            id="CREATE(1, Address(12), 4, 5, 6, 7, 8, unchecked=True)",
        ),
        pytest.param(
            Om.OOG(),
            bytes([0x64, 0x17, 0x48, 0x76, 0xE8, 0x00, 0x60, 0x00, 0x20]),
            id="OOG()",
        ),
        pytest.param(
            Op.RJUMPV[1, 2, 3](Op.ORIGIN),
            bytes(
                [
                    Op.ORIGIN.int(),
                    Op.RJUMPV.int(),
                    0x02,  # Data portion, defined by the [1, 2, 3] argument
                    0x00,
                    0x01,
                    0x00,
                    0x02,
                    0x00,
                    0x03,
                ]
            ),
            id="RJUMPV[1, 2, 3](ORIGIN)",
        ),
        pytest.param(
            Op.RJUMPV[b"\x00"],
            bytes(
                [
                    Op.RJUMPV.int(),
                    0x00,
                ]
            ),
            id="RJUMPV[b'\\x00']",
        ),
        pytest.param(
            Op.RJUMPV[-1, -2, -3],
            bytes(
                [
                    Op.RJUMPV.int(),
                    0x02,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFE,
                    0xFF,
                    0xFD,
                ]
            ),
            id="RJUMPV[-1, -2, -3]",
        ),
        pytest.param(
            Op.RJUMPV[range(5)],  # TODO: on Python 3.11+: Op.RJUMPV[*range(5)]
            bytes(
                [
                    Op.RJUMPV.int(),
                    0x04,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0x00,
                    0x02,
                    0x00,
                    0x03,
                    0x00,
                    0x04,
                ]
            ),
            id="RJUMPV[range(5)]",
        ),
        pytest.param(
            Op.RJUMPV[1, 2, 3](Op.ORIGIN) + Op.STOP,
            bytes(
                [
                    Op.ORIGIN.int(),
                    Op.RJUMPV.int(),
                    0x02,  # Data portion, defined by the [1, 2, 3] argument
                    0x00,
                    0x01,
                    0x00,
                    0x02,
                    0x00,
                    0x03,
                    Op.STOP.int(),
                ]
            ),
            id="RJUMPV[1, 2, 3](ORIGIN) + STOP",
        ),
        pytest.param(
            Op.STOP * 2,
            bytes(
                [
                    Op.STOP.int(),
                    Op.STOP.int(),
                ]
            ),
            id="STOP * 2",
        ),
        pytest.param(
            Op.RJUMPV[0, 3, 6, 9], bytes.fromhex("e2030000000300060009"), id="RJUMPV[0, 3, 6, 9]"
        ),
        pytest.param(Op.RJUMPV[2, 0], bytes.fromhex("e20100020000"), id="RJUMPV[2, 0]"),
        pytest.param(
            Op.RJUMPV[b"\x02\x00\x02\xFF\xFF"],
            bytes.fromhex("e2020002ffff"),
            id="RJUMPV[b'\\x02\\x00\\x02\\xFF\\xFF']",
        ),
        pytest.param(
            Op.EXCHANGE[0x2 + 0x0, 0x3 + 0x0],
            bytes.fromhex("e800"),
            id="EXCHANGE[0x2 + 0x0, 0x3 + 0x0]",
        ),
        pytest.param(
            Op.EXCHANGE[0x2 + 0x0, 0x3 + 0xF],
            bytes.fromhex("e80f"),
            id="EXCHANGE[0x2 + 0x0, 0x3 + 0xF]",
        ),
        pytest.param(
            Op.EXCHANGE[0x2 + 0xF, 0x3 + 0xF + 0x0],
            bytes.fromhex("e8f0"),
            id="EXCHANGE[0x2 + 0xF, 0x3 + 0xF + 0x0]",
        ),
        pytest.param(
            Op.EXCHANGE[0x2 + 0xF, 0x3 + 0xF + 0xF],
            bytes.fromhex("e8ff"),
            id="EXCHANGE[0x2 + 0xF, 0x3 + 0xF + 0xF]",
        ),
        pytest.param(Op.PUSH0 * 0, bytes(), id="PUSH0 * 0"),
        pytest.param(
            Op.CREATE(value=1, offset=2, size=3),
            b"\x60\x03\x60\x02\x60\x01\xf0",
            id="Op.CREATE(value=1, offset=2, size=3)",
        ),
        pytest.param(
            Op.CREATE2(value=1, offset=2, size=3),
            b"\x60\x00\x60\x03\x60\x02\x60\x01\xf5",
            id="Op.CREATE2(value=1, offset=2, size=3)",
        ),
        pytest.param(
            Op.CALL(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5A\xF1",
            id="Op.CALL(address=1)",
        ),
        pytest.param(
            Op.STATICCALL(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5A\xFA",
            id="Op.STATICCALL(address=1)",
        ),
        pytest.param(
            Op.CALLCODE(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5A\xF2",
            id="Op.CALLCODE(address=1)",
        ),
        pytest.param(
            Op.DELEGATECALL(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5A\xF4",
            id="Op.DELEGATECALL(address=1)",
        ),
        pytest.param(
            Op.EXTCALL(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x01\xF8",
            id="Op.EXTCALL(address=1)",
        ),
        pytest.param(
            Op.EXTSTATICCALL(address=1),
            b"\x60\x00\x60\x00\x60\x01\xFB",
            id="Op.EXTSTATICCALL(address=1)",
        ),
        pytest.param(
            Op.EXTDELEGATECALL(address=1),
            b"\x60\x00\x60\x00\x60\x01\xF9",
            id="Op.EXTDELEGATECALL(address=1)",
        ),
        pytest.param(
            Om.MSTORE(b""),
            b"",
            id='Om.MSTORE(b"")',
        ),
        pytest.param(
            Om.MSTORE(bytes(range(32))),
            bytes(Op.MSTORE(0, bytes(range(32)))),
            id="Om.MSTORE(bytes(range(32)))",
        ),
        pytest.param(
            Om.MSTORE(bytes(range(64))),
            bytes(Op.MSTORE(0, bytes(range(32))) + Op.MSTORE(32, bytes(range(32, 64)))),
            id="Om.MSTORE(bytes(range(64)))",
        ),
        pytest.param(
            Om.MSTORE(bytes(range(33))),
            bytes(
                Op.MSTORE(0, bytes(range(32)))
                + Op.MLOAD(32)
                + Op.PUSH31[-1]
                + Op.AND
                + Op.PUSH32[b"\x20".ljust(32, b"\x00")]
                + Op.OR
                + Op.PUSH1(32)
                + Op.MSTORE
            ),
            id="Om.MSTORE(bytes(range(33)))",
        ),
        pytest.param(
            Om.MSTORE(bytes(range(63))),
            bytes(
                Op.MSTORE(0, bytes(range(32)))
                + Op.MLOAD(32)
                + Op.PUSH1[-1]
                + Op.AND
                + Op.PUSH32[bytes(range(32, 63)).ljust(32, b"\x00")]
                + Op.OR
                + Op.PUSH1(32)
                + Op.MSTORE
            ),
            id="Om.MSTORE(bytes(range(63)))",
        ),
    ],
)
def test_opcodes(opcodes: bytes, expected: bytes):
    """
    Test that the `opcodes` are transformed into bytecode as expected.
    """
    assert bytes(opcodes) == expected


def test_opcodes_repr():
    """
    Test that the `repr` of an `Op` is the same as its name.
    """
    assert f"{Op.CALL}" == "CALL"
    assert f"{Op.DELEGATECALL}" == "DELEGATECALL"
    assert f"{Om.OOG}" == "OOG"
    assert str(Op.ADD) == "ADD"
    assert f"{Op.DUPN[1]}" == "DUPN_0x01"
    assert f"{Op.DATALOADN[1]}" == "DATALOADN_0x0001"


def test_macros():
    """
    Test opcode and macros interaction
    """
    assert (Op.PUSH1(1) + Om.OOG) == (Op.PUSH1(1) + Op.SHA3(0, 100000000000))
    for opcode in Op:
        assert opcode != Om.OOG


@pytest.mark.parametrize(
    "bytecode,expected_popped_items,expected_pushed_items,"
    "expected_max_stack_height,expected_min_stack_height",
    [
        pytest.param(Op.PUSH1 + Op.POP, 0, 0, 1, 0, id="PUSH1 + POP"),
        pytest.param(Op.PUSH1 + Op.PUSH1, 0, 2, 2, 0, id="PUSH1 + PUSH1"),
        pytest.param(Op.PUSH1 * 3, 0, 3, 3, 0, id="PUSH1 * 3"),
        pytest.param(Op.POP + Op.POP, 2, 0, 2, 2, id="POP + POP"),
        pytest.param(Op.POP * 3, 3, 0, 3, 3, id="POP * 3"),
        pytest.param((Op.POP * 3) + Op.PUSH1, 3, 1, 3, 3, id="(POP * 3) + PUSH1"),
        pytest.param(Op.SWAP2 + Op.POP * 3, 3, 0, 3, 3, id="SWAP2 + POP * 3"),
        pytest.param(Op.SWAP2 + Op.PUSH1 * 3, 0, 3, 6, 3, id="SWAP2 + PUSH1 * 3"),
        pytest.param(Op.SWAP1 + Op.SWAP2, 0, 0, 3, 3, id="SWAP1 + SWAP2"),
        pytest.param(
            Op.POP * 2 + Op.PUSH1 + Op.POP * 2 + Op.PUSH1 * 3,
            3,
            3,
            3,
            3,
            id="POP * 2 + PUSH1 + POP * 2 + PUSH1 * 3",
        ),
        pytest.param(Op.CALL(1, 2, 3, 4, 5, 6, 7), 0, 1, 7, 0, id="CALL(1, 2, 3, 4, 5, 6, 7)"),
        pytest.param(
            Op.POP(Op.CALL(1, 2, 3, 4, 5, 6, 7)), 0, 0, 7, 0, id="POP(CALL(1, 2, 3, 4, 5, 6, 7))"
        ),
        pytest.param(
            Op.PUSH0 * 2 + Op.PUSH0 + Op.ADD + Op.PUSH0 + Op.POP * 2, 0, 1, 3, 0, id="parens1"
        ),
        pytest.param(
            Op.PUSH0 * 2 + (Op.PUSH0 + Op.ADD + Op.PUSH0 + Op.POP * 2), 0, 1, 3, 0, id="parens2"
        ),
        pytest.param(
            Op.PUSH0 * 2 + Op.PUSH0 + (Op.ADD + Op.PUSH0 + Op.POP * 2), 0, 1, 3, 0, id="parens3"
        ),
        pytest.param(
            Op.PUSH0 * 2 + Op.PUSH0 + (Op.ADD + Op.PUSH0) + Op.POP * 2, 0, 1, 3, 0, id="parens4"
        ),
        pytest.param(
            Op.PUSH0 * 2 + (Op.PUSH0 + Op.ADD + Op.PUSH0) + Op.POP * 2, 0, 1, 3, 0, id="parens5"
        ),
    ],
)
def test_bytecode_properties(
    bytecode: Bytecode,
    expected_popped_items: int,
    expected_pushed_items: int,
    expected_max_stack_height: int,
    expected_min_stack_height: int,
):
    """
    Test that the properties of the bytecode are as expected.
    """
    assert bytecode.popped_stack_items == expected_popped_items, "Popped stack items mismatch"
    assert bytecode.pushed_stack_items == expected_pushed_items, "Pushed stack items mismatch"
    assert bytecode.max_stack_height == expected_max_stack_height, "Max stack height mismatch"
    assert bytecode.min_stack_height == expected_min_stack_height, "Min stack height mismatch"


def test_opcode_comparison():
    """
    Test that the opcodes are comparable.
    """
    assert Op.STOP < Op.ADD
    assert Op.ADD == Op.ADD
    assert Op.ADD != Op.STOP
    assert Op.ADD > Op.STOP
