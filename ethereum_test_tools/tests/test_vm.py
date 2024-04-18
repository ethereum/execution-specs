"""
Test suite for `ethereum_test_tools.vm` module.
"""

import pytest

from ..common.base_types import Address
from ..vm.opcode import Macros as Om
from ..vm.opcode import Opcodes as Op


@pytest.mark.parametrize(
    "opcodes,expected",
    [
        (
            Op.PUSH1(0x01),
            bytes(
                [
                    0x60,
                    0x01,
                ]
            ),
        ),
        (
            Op.PUSH1[0x01],
            bytes(
                [
                    0x60,
                    0x01,
                ]
            ),
        ),
        (
            Op.PUSH1("0x01"),
            bytes(
                [
                    0x60,
                    0x01,
                ]
            ),
        ),
        (
            Op.PUSH1["0x01"],
            bytes(
                [
                    0x60,
                    0x01,
                ]
            ),
        ),
        (
            Op.PUSH1(0xFF),
            bytes(
                [
                    0x60,
                    0xFF,
                ]
            ),
        ),
        (
            Op.PUSH1(-1),
            bytes(
                [
                    0x60,
                    0xFF,
                ]
            ),
        ),
        (
            Op.PUSH1[-1],
            bytes(
                [
                    0x60,
                    0xFF,
                ]
            ),
        ),
        (
            Op.PUSH1(-2),
            bytes(
                [
                    0x60,
                    0xFE,
                ]
            ),
        ),
        (
            Op.PUSH20(0x01),
            bytes([0x73] + [0x00] * 19 + [0x01]),
        ),
        (
            Op.PUSH20[0x01],
            bytes([0x73] + [0x00] * 19 + [0x01]),
        ),
        (
            Op.PUSH32(0xFF),
            bytes([0x7F] + [0x00] * 31 + [0xFF]),
        ),
        (
            Op.PUSH32(-1),
            bytes([0x7F] + [0xFF] * 32),
        ),
        (
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
        ),
        (
            Op.CALL(Op.GAS, Op.PUSH20(0x1234), 0, 0, 0, 0, 32),
            b"\x60\x20\x60\x00\x60\x00\x60\x00\x60\x00\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x12\x34\x5A\xF1",
        ),
        (
            Op.CALL(Op.GAS, Address(0x1234), 0, 0, 0, 0, 32),
            b"\x60\x20\x60\x00\x60\x00\x60\x00\x60\x00\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x12\x34\x5A\xF1",
        ),
        (Op.ADD(1, 2), bytes([0x60, 0x02, 0x60, 0x01, 0x01])),
        (Op.ADD(Op.ADD(1, 2), 3), bytes([0x60, 0x03, 0x60, 0x02, 0x60, 0x01, 0x01, 0x01])),
        (
            Op.CALL(1, 123, 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x60\x7b\x60\x01\xf1",
        ),
        (
            Op.CALL(1, Address(0x0123), 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x23\x60\x01\xf1",
        ),
        (
            Op.CALL(1, 0x0123, 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x61\x01\x23\x60\x01\xf1",
        ),
        (
            Op.CALL(1, 123, 4, 5, 6, 7, 8),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x60\x7b\x60\x01\xf1",
        ),
        (
            Op.CREATE(1, Address(12), 4, 5, 6, 7, 8, unchecked=True),
            b"\x60\x08\x60\x07\x60\x06\x60\x05\x60\x04\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x60\x01\xf0",
        ),
        (
            Om.OOG(),
            bytes([0x64, 0x17, 0x48, 0x76, 0xE8, 0x00, 0x60, 0x00, 0x20]),
        ),
        (
            Op.RJUMPV[1, 2, 3](Op.ORIGIN),
            bytes(
                [
                    Op.ORIGIN.int(),
                    Op.RJUMPV.int(),
                    0x03,  # Data portion, defined by the [1, 2, 3] argument
                    0x00,
                    0x01,
                    0x00,
                    0x02,
                    0x00,
                    0x03,
                ]
            ),
        ),
        (
            Op.RJUMPV[b"\x00"],
            bytes(
                [
                    Op.RJUMPV.int(),
                    0x00,
                ]
            ),
        ),
        (
            Op.RJUMPV[-1, -2, -3],
            bytes(
                [
                    Op.RJUMPV.int(),
                    0x03,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFE,
                    0xFF,
                    0xFD,
                ]
            ),
        ),
        (
            Op.RJUMPV[range(5)],  # TODO: on Python 3.11+: Op.RJUMPV[*range(5)]
            bytes(
                [
                    Op.RJUMPV.int(),
                    0x05,
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
        ),
        (
            Op.RJUMPV[1, 2, 3](Op.ORIGIN) + Op.STOP,
            bytes(
                [
                    Op.ORIGIN.int(),
                    Op.RJUMPV.int(),
                    0x03,  # Data portion, defined by the [1, 2, 3] argument
                    0x00,
                    0x01,
                    0x00,
                    0x02,
                    0x00,
                    0x03,
                    Op.STOP.int(),
                ]
            ),
        ),
        (
            Op.STOP * 2,
            bytes(
                [
                    Op.STOP.int(),
                    Op.STOP.int(),
                ]
            ),
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


def test_macros():
    """
    Test opcode and macros interaction
    """
    assert (Op.PUSH1(1) + Om.OOG) == (Op.PUSH1(1) + Op.SHA3(0, 100000000000))
    for opcode in Op:
        assert opcode != Om.OOG
