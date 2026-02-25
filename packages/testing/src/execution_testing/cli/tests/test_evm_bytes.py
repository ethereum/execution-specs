"""Test suite for `cli.evm_bytes` module."""

import pytest

from execution_testing.vm import Op

from ..evm_bytes import process_evm_bytes_string

basic_vector = [
    "0x60008080808061AAAA612d5ff1600055",
    "Op.SSTORE(key=0x0, value=Op.CALL(gas=0x2d5f, "
    "address=0xaaaa, value=Op.DUP1, args_offset=Op.DUP1, "
    "args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))",
]
complex_vector = [
    "0x7fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf5f527fc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf6020527fe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff60405260786040356020355f35608a565b5f515f55602051600155604051600255005b5e56",  # noqa: E501
    "Op.MSTORE(offset=Op.PUSH0, "
    "value="
    "0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
    ") + Op.MSTORE(offset=0x20, "
    "value=0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf) + Op.MSTORE(offset=0x40, value=0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff) + Op.PUSH1[0x78] + Op.CALLDATALOAD(offset=0x40) + Op.CALLDATALOAD(offset=0x20) + Op.CALLDATALOAD(offset=Op.PUSH0) + Op.JUMP(pc=0x8a) + Op.JUMPDEST + Op.SSTORE(key=Op.PUSH0, value=Op.MLOAD(offset=Op.PUSH0)) + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20)) + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40)) + Op.STOP + Op.JUMPDEST + Op.MCOPY + Op.JUMP",  # noqa: E501
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
def test_evm_bytes(evm_bytes: str, python_opcodes: str) -> None:
    """Test evm_bytes using the basic and complex vectors."""
    assert process_evm_bytes_string(evm_bytes) == python_opcodes


DUPLICATES = [Op.NOOP]


@pytest.mark.parametrize(
    "opcode",
    [op for op in Op if op not in DUPLICATES],
    ids=lambda op: op._name_,
)
def test_individual_opcodes(opcode: Op) -> None:
    """Test each opcode individually."""
    data_portion = b""
    if opcode.data_portion_length > 0:
        expected_output = f"Op.{opcode._name_}[0x0]"
        data_portion = b"\x00" * opcode.data_portion_length
    else:
        expected_output = f"Op.{opcode._name_}"

    bytecode = opcode.int().to_bytes(1, byteorder="big") + data_portion
    assert process_evm_bytes_string("0x" + bytecode.hex()) == expected_output


def test_invalid_opcode() -> None:
    """Invalid hex string."""
    with pytest.raises(ValueError):
        process_evm_bytes_string("0xZZ")


def test_unknown_opcode() -> None:
    """Opcode not defined in Op."""
    with pytest.raises(ValueError):
        process_evm_bytes_string("0x0F")
        process_evm_bytes_string("0x0F")
