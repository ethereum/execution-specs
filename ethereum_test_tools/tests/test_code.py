"""
Test suite for `ethereum_test.code` module.
"""

from string import Template
from typing import Mapping, SupportsBytes

import pytest
from semver import Version

from ethereum_test_forks import Fork, Homestead, Shanghai, forks_from_until, get_deployed_forks
from evm_transition_tool import FixtureFormats, GethTransitionTool

from ..code import CalldataCase, Case, Code, Conditional, Initcode, Switch, Yul
from ..common import Account, Environment, TestAddress, Transaction, to_hash_bytes
from ..spec import StateTest
from ..vm.opcode import Opcodes as Op
from .conftest import SOLC_PADDING_VERSION


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


@pytest.fixture(params=forks_from_until(get_deployed_forks()[1], get_deployed_forks()[-1]))
def fork(request: pytest.FixtureRequest):
    """
    Return the target evm-version (fork) for solc compilation.

    Note:
    - get_deployed_forks()[1] (Homestead) is the first fork that solc supports.
    - forks_from_util: Used to remove the Glacier forks
    """
    return request.param


@pytest.fixture()
def yul_code(request: pytest.FixtureRequest, fork: Fork, padding_before: str, padding_after: str):
    """Return the Yul code for the test."""
    yul_code_snippets = request.param
    if padding_before is not None:
        compiled_yul_code = Code(padding_before)
    else:
        compiled_yul_code = Code("")
    for yul_code in yul_code_snippets:
        compiled_yul_code += Yul(yul_code, fork=fork)
    if padding_after is not None:
        compiled_yul_code += Code(padding_after)
    return compiled_yul_code


@pytest.fixture()
def expected_bytes(request: pytest.FixtureRequest, solc_version: Version, fork: Fork):
    """Return the expected bytes for the test."""
    expected_bytes = request.param
    if isinstance(expected_bytes, Template):
        if solc_version < SOLC_PADDING_VERSION or fork == Homestead:
            solc_padding = ""
        else:
            solc_padding = "00"
        return bytes.fromhex(expected_bytes.substitute(solc_padding=solc_padding))
    if isinstance(expected_bytes, bytes):
        if fork == Shanghai:
            expected_bytes = b"\x5f" + expected_bytes[2:]
        if solc_version < SOLC_PADDING_VERSION or fork == Homestead:
            return expected_bytes
        else:
            return expected_bytes + b"\x00"

    raise Exception("Unsupported expected_bytes type: {}".format(type(expected_bytes)))


@pytest.mark.parametrize(
    ["yul_code", "padding_before", "padding_after", "expected_bytes"],
    [
        pytest.param(
            (
                """
                {
                    sstore(1, 2)
                }
                """,
            ),
            None,
            None,
            Template("6002600155${solc_padding}"),
            id="simple",
        ),
        pytest.param(
            (
                """
                {
                    sstore(1, 2)
                }
                """,
            ),
            None,
            "0x00",
            Template("6002600155${solc_padding}00"),
            id="simple-with-padding",
        ),
        pytest.param(
            (
                """
                {
                    sstore(1, 2)
                }
                """,
            ),
            "0x00",
            None,
            Template("006002600155${solc_padding}"),
            id="simple-with-padding-2",
        ),
        pytest.param(
            (
                """
                {
                    sstore(1, 2)
                }
                """,
                """
                {
                    sstore(3, 4)
                }
                """,
            ),
            None,
            None,
            Template("6002600155${solc_padding}6004600355${solc_padding}"),
            id="multiple",
        ),
        pytest.param(
            ("{\n" + "\n".join(["sstore({0}, {0})".format(i) for i in range(5000)]) + "\n}",),
            None,
            None,
            b"".join([b"\x60" + i.to_bytes(1, "big") + b"\x80\x55" for i in range(256)])
            + b"".join([b"\x61" + i.to_bytes(2, "big") + b"\x80\x55" for i in range(256, 5000)]),
            id="large",
        ),
    ],
    indirect=["yul_code", "expected_bytes"],
)
def test_yul(
    yul_code: SupportsBytes, expected_bytes: bytes, padding_before: str, padding_after: str
):
    assert bytes(yul_code) == expected_bytes


@pytest.mark.parametrize(
    "initcode,bytecode",
    [
        pytest.param(
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
            id="empty-deployed-code",
        ),
        pytest.param(
            Initcode(deploy_code=bytes(), initcode_prefix=bytes([0x00])),
            bytes(
                [
                    0x00,
                    0x61,
                    0x00,
                    0x00,
                    0x60,
                    0x00,
                    0x81,
                    0x60,
                    0x0C,
                    0x82,
                    0x39,
                    0xF3,
                ]
            ),
            id="empty-deployed-code-with-prefix",
        ),
        pytest.param(
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
            id="empty-deployed-code-with-padding",
        ),
        pytest.param(
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
                + [0x00]  # deployed code
                + [0x00] * 8  # padding
            ),
            id="single-byte-deployed-code-with-padding",
        ),
        pytest.param(
            Initcode(
                deploy_code=bytes([0x00]),
                initcode_prefix=Op.SSTORE(0, 1),
                initcode_length=20,
            ),
            bytes(
                [
                    0x60,
                    0x01,
                    0x60,
                    0x00,
                    0x55,
                    0x61,
                    0x00,
                    0x01,
                    0x60,
                    0x00,
                    0x81,
                    0x60,
                    0x10,
                    0x82,
                    0x39,
                    0xF3,
                ]
                + [0x00]  # deployed code
                + [0x00] * 3  # padding
            ),
            id="single-byte-deployed-code-with-padding-and-prefix",
        ),
    ],
)
def test_initcode(initcode: Initcode, bytecode: bytes):
    assert bytes(initcode) == bytecode


@pytest.mark.parametrize(
    "conditional_bytecode,expected",
    [
        (
            Conditional(
                condition=Op.CALLDATALOAD(0),
                if_true=Op.MSTORE(0, Op.SLOAD(0)) + Op.RETURN(0, 32),
                if_false=Op.SSTORE(0, 69),
            ),
            bytes.fromhex("600035600d5801576045600055600f5801565b60005460005260206000f35b"),
        ),
    ],
)
def test_opcodes_if(conditional_bytecode: bytes, expected: bytes):
    """
    Test that the if opcode macro is transformed into bytecode as expected.
    """
    assert bytes(conditional_bytecode) == expected


@pytest.mark.parametrize(
    "tx_data,switch_bytecode,expected_storage",
    [
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                ],
                default_action=b"",
            ),
            {0: 1},
            id="no-default-action-condition-met",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[
                    CalldataCase(value=1, action=Op.SSTORE(0, 1)),
                    CalldataCase(value=2, action=Op.SSTORE(0, 2)),
                ],
                default_action=b"",
            ),
            {0: 1},
            id="no-default-action-condition-met-calldata",
        ),
        pytest.param(
            to_hash_bytes(0),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                ],
                default_action=b"",
            ),
            {0: 0},
            id="no-default-action-no-condition-met",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[],
                default_action=Op.SSTORE(0, 3),
            ),
            {0: 3},
            id="no-cases",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1))],
                default_action=Op.SSTORE(0, 3),
            ),
            {0: 1},
            id="one-case-condition-met",
        ),
        pytest.param(
            to_hash_bytes(0),
            Switch(
                cases=[Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1))],
                default_action=Op.SSTORE(0, 3),
            ),
            {0: 3},
            id="one-case-condition-not-met",
        ),
        pytest.param(
            to_hash_bytes(0),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                ],
                default_action=Op.SSTORE(0, 3),
            ),
            {0: 3},
            id="two-cases-no-condition-met",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                ],
                default_action=Op.SSTORE(0, 3),
            ),
            {0: 1},
            id="two-cases-first-condition-met",
        ),
        pytest.param(
            to_hash_bytes(2),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                ],
                default_action=Op.SSTORE(0, 3),
            ),
            {0: 2},
            id="two-cases-second-condition-met",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 3), action=Op.SSTORE(0, 3)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 4), action=Op.SSTORE(0, 4)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 5), action=Op.SSTORE(0, 5)),
                ],
                default_action=Op.SSTORE(0, 6),
            ),
            {0: 1},
            id="five-cases-first-condition-met",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[
                    CalldataCase(value=1, action=Op.SSTORE(0, 1)),
                    CalldataCase(value=2, action=Op.SSTORE(0, 2)),
                    CalldataCase(value=3, action=Op.SSTORE(0, 3)),
                    CalldataCase(value=4, action=Op.SSTORE(0, 4)),
                    CalldataCase(value=5, action=Op.SSTORE(0, 5)),
                ],
                default_action=Op.SSTORE(0, 6),
            ),
            {0: 1},
            id="five-cases-first-condition-met-calldata",
        ),
        pytest.param(
            to_hash_bytes(3),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 3), action=Op.SSTORE(0, 3)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 4), action=Op.SSTORE(0, 4)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 5), action=Op.SSTORE(0, 5)),
                ],
                default_action=Op.SSTORE(0, 6),
            ),
            {0: 3},
            id="five-cases-third-condition-met",
        ),
        pytest.param(
            to_hash_bytes(3),
            Switch(
                cases=[
                    CalldataCase(value=1, action=Op.SSTORE(0, 1)),
                    CalldataCase(value=2, action=Op.SSTORE(0, 2)),
                    CalldataCase(value=3, action=Op.SSTORE(0, 3)),
                    CalldataCase(value=4, action=Op.SSTORE(0, 4)),
                    CalldataCase(value=5, action=Op.SSTORE(0, 5)),
                ],
                default_action=Op.SSTORE(0, 6),
            ),
            {0: 3},
            id="five-cases-third-condition-met-calldata",
        ),
        pytest.param(
            to_hash_bytes(5),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 3), action=Op.SSTORE(0, 3)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 4), action=Op.SSTORE(0, 4)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 5), action=Op.SSTORE(0, 5)),
                ],
                default_action=Op.SSTORE(0, 6),
            ),
            {0: 5},
            id="five-cases-last-met",
        ),
        pytest.param(
            to_hash_bytes(3),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 3), action=Op.SSTORE(0, 3)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 3), action=Op.SSTORE(0, 4)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 3), action=Op.SSTORE(0, 5)),
                ],
                default_action=Op.SSTORE(0, 6),
            ),
            {0: 3},
            id="five-cases-multiple-conditions-met",  # first in list should be evaluated
        ),
        pytest.param(
            to_hash_bytes(9),
            Switch(
                cases=[
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 2), action=Op.SSTORE(0, 2)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 3), action=Op.SSTORE(0, 3)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 4), action=Op.SSTORE(0, 4)),
                    Case(condition=Op.EQ(Op.CALLDATALOAD(0), 5), action=Op.SSTORE(0, 5)),
                ],
                default_action=Op.SSTORE(0, 6),
            ),
            {0: 6},
            id="five-cases-no-condition-met",
        ),
        pytest.param(
            to_hash_bytes(0),
            Switch(
                cases=[
                    Case(condition=Op.EQ(1, 2), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(1, 2), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(1, 2), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(1, 1), action=Op.SSTORE(0, 2)),
                    Case(condition=Op.EQ(1, 2), action=Op.SSTORE(0, 1)),
                ],
                default_action=b"",
            ),
            {0: 2},
            id="no-calldataload-condition-met",
        ),
        pytest.param(
            to_hash_bytes(0),
            Switch(
                cases=[
                    Case(condition=Op.EQ(1, 2), action=Op.SSTORE(0, 1)),
                    Case(condition=Op.EQ(1, 2), action=Op.SSTORE(0, 1)),
                    Case(
                        condition=Op.EQ(1, 2),
                        action=Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.SSTORE(2, 1),
                    ),
                    Case(condition=Op.EQ(1, 1), action=Op.SSTORE(0, 2) + Op.SSTORE(1, 2)),
                    Case(condition=Op.EQ(1, 2), action=Op.SSTORE(0, 1)),
                ],
                default_action=b"",
            ),
            {0: 2, 1: 2},
            id="no-calldataload-condition-met-different-length-actions",
        ),
        pytest.param(
            to_hash_bytes(0),
            Switch(
                cases=[
                    Case(
                        condition=Op.EQ(1, 2),
                        action=Op.SSTORE(0, 1),
                    ),
                    Case(
                        condition=Op.EQ(Op.CALLDATALOAD(0), 1),
                        action=Op.SSTORE(0, 1),
                    ),
                    Case(
                        condition=Op.EQ(1, 2),
                        action=Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.SSTORE(2, 1),
                    ),
                    Case(
                        condition=Op.EQ(1, 1),
                        action=Op.SSTORE(0, 2) + Op.SSTORE(1, 2),
                    ),
                    Case(
                        condition=Op.EQ(Op.CALLDATALOAD(0), 1),
                        action=Op.SSTORE(0, 1),
                    ),
                ],
                default_action=b"",
            ),
            {0: 2, 1: 2},
            id="different-length-conditions-condition-met-different-length-actions",
        ),
        pytest.param(
            to_hash_bytes(0),
            Op.SSTORE(0x10, 1)
            + Switch(
                cases=[
                    Case(
                        condition=Op.EQ(1, 2),
                        action=Op.SSTORE(0, 1),
                    ),
                    Case(
                        condition=Op.EQ(Op.CALLDATALOAD(0), 1),
                        action=Op.SSTORE(0, 1),
                    ),
                    Case(
                        condition=Op.EQ(1, 2),
                        action=Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.SSTORE(2, 1),
                    ),
                    Case(
                        condition=Op.EQ(1, 1),
                        action=Op.SSTORE(0, 2) + Op.SSTORE(1, 2),
                    ),
                    Case(
                        condition=Op.EQ(Op.CALLDATALOAD(0), 1),
                        action=Op.SSTORE(0, 1),
                    ),
                ],
                default_action=b"",
            )
            + Op.SSTORE(0x11, 1),
            {0: 2, 1: 2, 0x10: 1, 0x11: 1},
            id="nested-within-bytecode",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1))],
                default_action=Op.PUSH32(2**256 - 1) * 8,
            ),
            {0: 1},
            id="jumpi-larger-than-1-byte",
        ),
        pytest.param(
            to_hash_bytes(1),
            Switch(
                cases=[Case(condition=Op.EQ(Op.CALLDATALOAD(0), 1), action=Op.SSTORE(0, 1))],
                default_action=Op.PUSH32(2**256 - 1) * 2048,
            ),
            {0: 1},
            id="jumpi-larger-than-4-bytes",
        ),
    ],
)
def test_switch(tx_data: bytes, switch_bytecode: bytes, expected_storage: Mapping):
    """
    Test that the switch opcode macro gets executed as using the t8n tool.
    """
    code_address = 0x100
    pre = {
        TestAddress: Account(balance=10_000_000, nonce=0),
        code_address: Account(code=switch_bytecode),
    }
    tx = Transaction(to=code_address, data=tx_data, gas_limit=1_000_000)
    post = {TestAddress: Account(nonce=1), code_address: Account(storage=expected_storage)}
    state_test = StateTest(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
        fixture_format=FixtureFormats.BLOCKCHAIN_TEST,
    )
    state_test.generate(
        t8n=GethTransitionTool(),
        fork=Shanghai,
        eips=None,
    )
