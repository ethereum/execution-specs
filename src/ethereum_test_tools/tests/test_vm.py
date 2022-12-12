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
    ],
)
def test_opcodes(opcodes: bytes, expected: bytes):
    assert bytes(opcodes) == expected
