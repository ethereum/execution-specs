"""
Test suite for `ethereum_test.code` module.
"""

from typing import SupportsBytes

import pytest

from ethereum_test_forks import Merge

from ..code import Code, Initcode, Yul


@pytest.mark.parametrize(
    "code,expected_bytes",
    [
        ("", bytes()),
        ("0x", bytes()),
        ("0x01", bytes.fromhex("01")),
        ("01", bytes.fromhex("01")),
    ],
)
def test_code_init(code: str | bytes | SupportsBytes, expected_bytes: bytes):
    """
    Test `ethereum_test.types.code`.
    """
    assert bytes(Code(code)) == expected_bytes


@pytest.mark.parametrize(
    "code,expected_bytes",
    [
        (Code("0x01") + "0x02", bytes.fromhex("0102")),
        ("0x01" + Code("0x02"), bytes.fromhex("0102")),
        ("0x01" + Code("0x02") + "0x03", bytes.fromhex("010203")),
    ],
)
def test_code_operations(code: Code, expected_bytes: bytes):
    """
    Test `ethereum_test.types.code`.
    """
    assert bytes(code) == expected_bytes


@pytest.mark.parametrize(
    "yul_code,expected_bytes",
    [
        (
            Yul(
                """
            {
                sstore(1, 2)
            }
            """
            ),
            bytes.fromhex("6002600155"),
        ),
        (
            Yul(
                """
                {
                    sstore(1, 2)
                }
                """
            )
            + "0x00",
            bytes.fromhex("600260015500"),
        ),
        (
            "0x00"
            + Yul(
                """
                {
                    sstore(1, 2)
                }
                """
            ),
            bytes.fromhex("006002600155"),
        ),
        (
            Yul(
                """
                {
                    sstore(1, 2)
                }
                """
            )
            + Yul(
                """
                {
                    sstore(3, 4)
                }
                """
            ),
            bytes.fromhex("60026001556004600355"),
        ),
        (
            Yul(
                "{\n" + "\n".join(["sstore({0}, {0})".format(i) for i in range(5000)]) + "\n}",
                # TODO(dan): workaround until it's understood why Shanghai takes so long to compile
                fork=Merge,
            ),
            b"".join([b"\x60" + i.to_bytes(1, "big") + b"\x80\x55" for i in range(256)])
            + b"".join([b"\x61" + i.to_bytes(2, "big") + b"\x80\x55" for i in range(256, 5000)]),
        ),
    ],
    ids=[
        "simple",
        "simple with padding",
        "simple with padding 2",
        "multiple",
        "large",
    ],
)
def test_yul(yul_code: SupportsBytes, expected_bytes: bytes):
    assert bytes(yul_code) == expected_bytes


@pytest.mark.parametrize(
    "initcode,bytecode",
    [
        (
            Initcode(deploy_code=bytes()),
            bytes(
                [
                    0x61,
                    0x00,
                    0x00,
                    0x60,
                    0x00,
                    0x81,
                    0x60,
                    0x0B,
                    0x82,
                    0x39,
                    0xF3,
                ]
            ),
        ),
        (
            Initcode(deploy_code=bytes(), initcode_length=20),
            bytes(
                [
                    0x61,
                    0x00,
                    0x00,
                    0x60,
                    0x00,
                    0x81,
                    0x60,
                    0x0B,
                    0x82,
                    0x39,
                    0xF3,
                ]
                + [0x00] * 9  # padding
            ),
        ),
        (
            Initcode(deploy_code=bytes([0x00]), initcode_length=20),
            bytes(
                [
                    0x61,
                    0x00,
                    0x01,
                    0x60,
                    0x00,
                    0x81,
                    0x60,
                    0x0B,
                    0x82,
                    0x39,
                    0xF3,
                ]
                + [0x00]
                + [0x00] * 8  # padding
            ),
        ),
    ],
)
def test_initcode(initcode: Initcode, bytecode: bytes):
    assert bytes(initcode) == bytecode
