"""
Test suite for `cli.evm_bytes_to_python` module.
"""

import pytest

from ethereum_test_tools import Opcodes as Op

from ..evm_bytes_to_python import process_evm_bytes

basic_vector = [
    "0x60008080808061AAAA612d5ff1600055",
    'Op.PUSH1("0x00") + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH2("0xaaaa") + Op.PUSH2("0x2d5f") + Op.CALL + Op.PUSH1("0x00") + Op.SSTORE',  # noqa: E501
]
complex_vector = [
    "0x7fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf5f527fc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf6020527fe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff60405260786040356020355f35608a565b5f515f55602051600155604051600255005b5e56",  # noqa: E501
    'Op.PUSH32("0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf") + Op.PUSH0 + Op.MSTORE + Op.PUSH32("0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf") + Op.PUSH1("0x20") + Op.MSTORE + Op.PUSH32("0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff") + Op.PUSH1("0x40") + Op.MSTORE + Op.PUSH1("0x78") + Op.PUSH1("0x40") + Op.CALLDATALOAD + Op.PUSH1("0x20") + Op.CALLDATALOAD + Op.PUSH0 + Op.CALLDATALOAD + Op.PUSH1("0x8a") + Op.JUMP + Op.JUMPDEST + Op.PUSH0 + Op.MLOAD + Op.PUSH0 + Op.SSTORE + Op.PUSH1("0x20") + Op.MLOAD + Op.PUSH1("0x01") + Op.SSTORE + Op.PUSH1("0x40") + Op.MLOAD + Op.PUSH1("0x02") + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.MCOPY + Op.JUMP',  # noqa: E501
]


@pytest.mark.parametrize(
    "evm_bytes, python_opcodes",
    [
        (basic_vector[0], basic_vector[1]),
        (basic_vector[0][2:], basic_vector[1]),  # no "0x" prefix
        (complex_vector[0], complex_vector[1]),
        (complex_vector[0][2:], complex_vector[1]),  # no "0x" prefix
    ],
)
def test_evm_bytes_to_python(evm_bytes, python_opcodes):
    """Test evm_bytes_to_python using the basic and complex vectors"""
    assert process_evm_bytes(evm_bytes) == python_opcodes


DUPLICATES = [Op.NOOP]


@pytest.mark.parametrize(
    "opcode",
    [op for op in Op if op not in DUPLICATES],
    ids=lambda op: op._name_,
)
def test_individual_opcodes(opcode):
    """Test each opcode individually"""
    if opcode.data_portion_length > 0:
        expected_output = f'Op.{opcode._name_}("0x")'
    else:
        expected_output = f"Op.{opcode._name_}"

    bytecode = opcode.int().to_bytes(1, byteorder="big").hex()
    assert process_evm_bytes("0x" + bytecode) == expected_output


def test_invalid_opcode():
    """Invalid hex string"""
    with pytest.raises(ValueError):
        process_evm_bytes("0xZZ")


def test_unknown_opcode():
    """Opcode not defined in Op"""
    with pytest.raises(ValueError):
        process_evm_bytes("0x0F")
