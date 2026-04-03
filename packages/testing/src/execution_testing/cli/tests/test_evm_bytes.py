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
    "0x7fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf5f527fc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf6020527fe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff60405260786040356020355f35608a565b5f515f55602051600155604051600255005b5e56",
    "Op.MSTORE(offset=Op.PUSH0, "
    "value="
    "0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
    ") + Op.MSTORE(offset=0x20, "
    "value=0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf)"
    " + Op.MSTORE(offset=0x40, "
    "value=0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff)"
    " + Op.PUSH1[0x78] + Op.CALLDATALOAD(offset=0x40) + "
    "Op.CALLDATALOAD(offset=0x20) + Op.CALLDATALOAD(offset=Op.PUSH0) + "
    "Op.JUMP(pc=0x8a) + Op.JUMPDEST + Op.SSTORE(key=Op.PUSH0, "
    "value=Op.MLOAD(offset=Op.PUSH0)) + Op.SSTORE(key=0x1, "
    "value=Op.MLOAD(offset=0x20)) + Op.SSTORE(key=0x2, "
    "value=Op.MLOAD(offset=0x40)) + Op.STOP + Op.JUMPDEST + Op.MCOPY + "
    "Op.JUMP",
]
repeating_vector = [
    "0x600060006000600060003061c3505a03f100" + "5b" * 15000,
    "Op.CALL(gas=Op.SUB(Op.GAS, 0xc350), address=Op.ADDRESS, value=0x0, "
    "args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0) + Op.STOP "
    "+ Op.JUMPDEST * 15000",
]
edge_case_vectors = [
    pytest.param(
        "0x6060",
        "Op.PUSH1[0x60]",
        id="push_data_matches_push1_opcode_byte",
    ),
    pytest.param(
        "0x605f5f",
        "Op.PUSH1[0x5f] + Op.PUSH0",
        id="push_data_matches_push0_opcode_byte",
    ),
    pytest.param(
        "0x616060",
        "Op.PUSH2[0x6060]",
        id="push2_data_contains_push1_opcode_bytes",
    ),
    pytest.param(
        "0x60606060",
        "Op.PUSH1[0x60] * 2",
        id="repeating_push1_is_compacted",
    ),
    pytest.param(
        "0x60616060",
        "Op.PUSH1[0x61] + Op.PUSH1[0x60]",
        id="distinct_push1_values_are_not_compacted",
    ),
    pytest.param(
        "0x600035600035",
        "Op.CALLDATALOAD(offset=0x0) * 2",
        id="repeating_folded_expression_is_compacted",
    ),
    pytest.param(
        "0x600035600135",
        "Op.CALLDATALOAD(offset=0x0) + Op.CALLDATALOAD(offset=0x1)",
        id="distinct_folded_expressions_are_not_compacted",
    ),
]
truncated_push_vectors = [
    pytest.param("0x60", "Op.PUSH1[0x0]", id="push1_missing_data_zero_pads"),
    pytest.param(
        "0x6160",
        "Op.PUSH2[0x60]",
        id="push2_missing_trailing_byte_zero_pads",
    ),
]
malformed_hex_strings = [
    pytest.param("0xZZ", id="non_hex_chars_with_prefix"),
    pytest.param("ZZ", id="non_hex_chars_without_prefix"),
    pytest.param("0x0", id="odd_length_with_prefix"),
    pytest.param("0", id="odd_length_without_prefix"),
]
undefined_opcode_bytes = sorted(
    opcode_byte
    for opcode_byte in range(256)
    if opcode_byte not in {op.int() for op in Op}
)


@pytest.mark.parametrize(
    "evm_bytes, python_opcodes",
    [
        (basic_vector[0], basic_vector[1]),
        (basic_vector[0][2:], basic_vector[1]),  # no "0x" prefix
        (complex_vector[0], complex_vector[1]),
        (complex_vector[0][2:], complex_vector[1]),  # no "0x" prefix
        pytest.param(
            repeating_vector[0], repeating_vector[1], id="repeating_jumpdest"
        ),
    ],
)
def test_evm_bytes(evm_bytes: str, python_opcodes: str) -> None:
    """Test evm_bytes using the basic and complex vectors."""
    assert process_evm_bytes_string(evm_bytes) == python_opcodes


@pytest.mark.parametrize(("evm_bytes", "python_opcodes"), edge_case_vectors)
def test_evm_bytes_edge_cases(evm_bytes: str, python_opcodes: str) -> None:
    """Cover decoding and simplification edge cases for evm_bytes."""
    assert process_evm_bytes_string(evm_bytes) == python_opcodes


@pytest.mark.parametrize(
    ("evm_bytes", "python_opcodes"), truncated_push_vectors
)
def test_evm_bytes_truncated_push_zero_padding(
    evm_bytes: str, python_opcodes: str
) -> None:
    """PUSH instructions right-pad missing immediate bytes with zeros."""
    assert process_evm_bytes_string(evm_bytes) == python_opcodes


def test_evm_bytes_assembly_output() -> None:
    """Assembly output keeps the opcode stream and line formatting intact."""
    assert (
        process_evm_bytes_string("0x005b00", assembly=True)
        == "stop\n\njumpdest\nstop"
    )


def test_evm_bytes_skip_simplify_output() -> None:
    """skip_simplify preserves repeated decoded instructions."""
    assert (
        process_evm_bytes_string("0x60606060", skip_simplify=True)
        == "Op.PUSH1[0x60] + Op.PUSH1[0x60]"
    )


def test_evm_bytes_push0_is_decoded_without_fork_context() -> None:
    """The decoder uses the global opcode table rather than a selected fork."""
    assert process_evm_bytes_string("0x5f") == "Op.PUSH0"


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


@pytest.mark.parametrize("evm_bytes", malformed_hex_strings)
def test_invalid_hex_string(evm_bytes: str) -> None:
    """Malformed hex strings are rejected before opcode decoding."""
    with pytest.raises(ValueError):
        process_evm_bytes_string(evm_bytes)


@pytest.mark.parametrize(
    "opcode_byte",
    undefined_opcode_bytes,
    ids=lambda opcode_byte: f"0x{opcode_byte:02x}",
)
def test_unknown_opcode(opcode_byte: int) -> None:
    """All bytes not present in Op are rejected as unknown opcodes."""
    with pytest.raises(ValueError):
        process_evm_bytes_string(f"0x{opcode_byte:02x}")
