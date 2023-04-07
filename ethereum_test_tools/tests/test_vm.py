"""
Test suite for `ethereum_test_tools.vm` module.
"""

import pytest

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
    ],
)
def test_opcodes(opcodes: bytes, expected: bytes):
    assert bytes(opcodes) == expected
