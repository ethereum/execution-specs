"""Test suite for `execution_testing.vm` module."""

import pytest

from execution_testing.base_types import Address
from execution_testing.forks.forks.forks import Prague

from ..opcodes import Bytecode
from ..opcodes import Macros as Om
from ..opcodes import Opcodes as Op


@pytest.mark.parametrize(
    "opcodes,expected",
    [
        pytest.param(Op.PUSH1(0x01), b"\x60\x01", id="PUSH1(0x01)"),
        pytest.param(Op.PUSH1[0x01], b"\x60\x01", id="PUSH1[0x01]"),
        pytest.param(Op.PUSH1("0x01"), b"\x60\x01", id="PUSH1('0x01')"),
        pytest.param(Op.PUSH1["0x01"], b"\x60\x01", id="PUSH1['0x01']"),
        pytest.param(Op.PUSH1(0xFF), b"\x60\xff", id="PUSH1(0xFF)"),
        pytest.param(Op.PUSH1(-1), b"\x60\xff", id="PUSH1(-1)"),
        pytest.param(Op.PUSH1[-1], b"\x60\xff", id="PUSH1[-1]"),
        pytest.param(Op.PUSH1(-2), b"\x60\xfe", id="PUSH1(-2)"),
        pytest.param(
            Op.PUSH20(0x01),
            b"\x73" + b"\x00" * 19 + b"\x01",
            id="PUSH20(0x01)",
        ),
        pytest.param(
            Op.PUSH20[0x01],
            b"\x73" + b"\x00" * 19 + b"\x01",
            id="PUSH20[0x01]",
        ),
        pytest.param(
            Op.PUSH32(0xFF),
            b"\x7f" + b"\x00" * 31 + b"\xff",
            id="PUSH32(0xFF)",
        ),
        pytest.param(Op.PUSH32(-1), b"\x7f" + b"\xff" * 32, id="PUSH32(-1)"),
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
            id="SSTORE(-1, CALL(GAS, ADDRESS, PUSH1(0x20), 0, 0, 0x20, 0x1234))",  # noqa: E501
        ),
        pytest.param(
            Op.CALL(Op.GAS, Op.PUSH20(0x1234), 0, 0, 0, 0, 32),
            b"\x60\x20\x60\x00\x60\x00\x60\x00\x60\x00\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x12\x34\x5a\xf1",
            id="CALL(GAS, PUSH20(0x1234), 0, 0, 0, 0, 32)",
        ),
        pytest.param(
            Op.CALL(Op.GAS, Address(0x1234), 0, 0, 0, 0, 32),
            b"\x60\x20\x60\x00\x60\x00\x60\x00\x60\x00\x61\x12\x34\x5a\xf1",
            id="CALL(GAS, Address(0x1234), 0, 0, 0, 0, 32)",
        ),
        pytest.param(
            Op.ADD(1, 2), bytes([0x60, 0x02, 0x60, 0x01, 0x01]), id="ADD(1, 2)"
        ),
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
            Op.STOP * 2,
            bytes(
                [
                    Op.STOP.int(),
                    Op.STOP.int(),
                ]
            ),
            id="STOP * 2",
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
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5a\xf1",
            id="Op.CALL(address=1)",
        ),
        pytest.param(
            Op.STATICCALL(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5a\xfa",
            id="Op.STATICCALL(address=1)",
        ),
        pytest.param(
            Op.CALLCODE(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5a\xf2",
            id="Op.CALLCODE(address=1)",
        ),
        pytest.param(
            Op.DELEGATECALL(address=1),
            b"\x60\x00\x60\x00\x60\x00\x60\x00\x60\x01\x5a\xf4",
            id="Op.DELEGATECALL(address=1)",
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
            bytes(
                Op.MSTORE(0, bytes(range(32)))
                + Op.MSTORE(32, bytes(range(32, 64)))
            ),
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
def test_opcodes(opcodes: bytes, expected: bytes) -> None:
    """Test that the `opcodes` are transformed into bytecode as expected."""
    assert bytes(opcodes) == expected


def test_opcodes_repr() -> None:
    """Test that the `repr` of an `Op` is the same as its name."""
    assert f"{Op.CALL}" == "CALL"
    assert f"{Op.DELEGATECALL}" == "DELEGATECALL"
    assert f"{Om.OOG}" == "OOG"
    assert str(Op.ADD) == "ADD"


def test_macros() -> None:
    """Test opcode and macros interaction."""
    assert (Op.PUSH1(1) + Om.OOG) == (Op.PUSH1(1) + Op.SHA3(0, 100000000000))
    for opcode in Op:
        assert opcode != Om.OOG


@pytest.mark.parametrize(
    "data,offset",
    [
        pytest.param(b"", 0, id="empty"),
        pytest.param(bytes(range(32)), 0, id="exactly_32_bytes_offset_0"),
        pytest.param(bytes(range(64)), 0, id="exactly_64_bytes_offset_0"),
        pytest.param(bytes(range(12)), 0, id="partial_12_bytes_offset_0"),
        pytest.param(bytes(range(33)), 0, id="33_bytes_offset_0"),
        pytest.param(bytes(range(63)), 0, id="63_bytes_offset_0"),
        pytest.param(bytes(range(32)), 32, id="exactly_32_bytes_offset_32"),
        pytest.param(bytes(range(12)), 64, id="partial_12_bytes_offset_64"),
    ],
)
def test_mstore_macro_memory_metadata(data: bytes, offset: int) -> None:
    """Test that Om.MSTORE sets memory size metadata on emitted opcodes."""
    bytecode = Om.MSTORE(data, offset)
    if len(data) == 0:
        assert len(bytecode.opcode_list) == 0
        return

    # Collect all memory metadata from the opcode list
    memory_opcodes = [
        op
        for op in bytecode.opcode_list
        if op.metadata.get("new_memory_size", 0) > 0
    ]

    # At least one opcode must carry memory expansion metadata
    assert len(memory_opcodes) > 0, "No opcodes with memory metadata found"

    # The maximum new_memory_size should reflect the full data stored
    num_chunks = (len(data) + 31) // 32
    expected_final_memory_size = offset + num_chunks * 32
    max_new_memory = max(
        op.metadata["new_memory_size"] for op in memory_opcodes
    )
    assert max_new_memory == expected_final_memory_size

    # First memory-expanding opcode should have old_memory_size=0
    assert memory_opcodes[0].metadata["old_memory_size"] == 0

    # Each subsequent memory opcode should chain: old = previous new
    for i in range(1, len(memory_opcodes)):
        assert (
            memory_opcodes[i].metadata["old_memory_size"]
            == memory_opcodes[i - 1].metadata["new_memory_size"]
        )


@pytest.mark.parametrize(
    "bytecode,expected_popped_items,expected_pushed_items,"
    "expected_max_stack_height,expected_min_stack_height",
    [
        pytest.param(Op.PUSH1 + Op.POP, 0, 0, 1, 0, id="PUSH1 + POP"),
        pytest.param(Op.PUSH1 + Op.PUSH1, 0, 2, 2, 0, id="PUSH1 + PUSH1"),
        pytest.param(Op.PUSH1 * 3, 0, 3, 3, 0, id="PUSH1 * 3"),
        pytest.param(Op.POP + Op.POP, 2, 0, 2, 2, id="POP + POP"),
        pytest.param(Op.POP * 3, 3, 0, 3, 3, id="POP * 3"),
        pytest.param(
            (Op.POP * 3) + Op.PUSH1, 3, 1, 3, 3, id="(POP * 3) + PUSH1"
        ),
        pytest.param(Op.SWAP2 + Op.POP * 3, 3, 0, 3, 3, id="SWAP2 + POP * 3"),
        pytest.param(
            Op.SWAP2 + Op.PUSH1 * 3, 0, 3, 6, 3, id="SWAP2 + PUSH1 * 3"
        ),
        pytest.param(Op.SWAP1 + Op.SWAP2, 0, 0, 3, 3, id="SWAP1 + SWAP2"),
        pytest.param(
            Op.POP * 2 + Op.PUSH1 + Op.POP * 2 + Op.PUSH1 * 3,
            3,
            3,
            3,
            3,
            id="POP * 2 + PUSH1 + POP * 2 + PUSH1 * 3",
        ),
        pytest.param(
            Op.CALL(1, 2, 3, 4, 5, 6, 7),
            0,
            1,
            7,
            0,
            id="CALL(1, 2, 3, 4, 5, 6, 7)",
        ),
        pytest.param(
            Op.POP(Op.CALL(1, 2, 3, 4, 5, 6, 7)),
            0,
            0,
            7,
            0,
            id="POP(CALL(1, 2, 3, 4, 5, 6, 7))",
        ),
        pytest.param(
            Op.PUSH0 * 2 + Op.PUSH0 + Op.ADD + Op.PUSH0 + Op.POP * 2,
            0,
            1,
            3,
            0,
            id="parens1",
        ),
        pytest.param(
            Op.PUSH0 * 2 + (Op.PUSH0 + Op.ADD + Op.PUSH0 + Op.POP * 2),
            0,
            1,
            3,
            0,
            id="parens2",
        ),
        pytest.param(
            Op.PUSH0 * 2 + Op.PUSH0 + (Op.ADD + Op.PUSH0 + Op.POP * 2),
            0,
            1,
            3,
            0,
            id="parens3",
        ),
        pytest.param(
            Op.PUSH0 * 2 + Op.PUSH0 + (Op.ADD + Op.PUSH0) + Op.POP * 2,
            0,
            1,
            3,
            0,
            id="parens4",
        ),
        pytest.param(
            Op.PUSH0 * 2 + (Op.PUSH0 + Op.ADD + Op.PUSH0) + Op.POP * 2,
            0,
            1,
            3,
            0,
            id="parens5",
        ),
    ],
)
def test_bytecode_properties(
    bytecode: Bytecode,
    expected_popped_items: int,
    expected_pushed_items: int,
    expected_max_stack_height: int,
    expected_min_stack_height: int,
) -> None:
    """Test that the properties of the bytecode are as expected."""
    assert bytecode.popped_stack_items == expected_popped_items, (
        "Popped stack items mismatch"
    )
    assert bytecode.pushed_stack_items == expected_pushed_items, (
        "Pushed stack items mismatch"
    )
    assert bytecode.max_stack_height == expected_max_stack_height, (
        "Max stack height mismatch"
    )
    assert bytecode.min_stack_height == expected_min_stack_height, (
        "Min stack height mismatch"
    )


def test_opcode_comparison() -> None:
    """Test that the opcodes are comparable."""
    assert Op.STOP < Op.ADD
    assert Op.ADD == Op.ADD
    assert Op.ADD != Op.STOP
    assert Op.ADD > Op.STOP


def test_bytecode_concatenation_with_bytes() -> None:
    """
    Test that the bytecode can be concatenated with bytes.
    Bytes work as verbatim code and don't affect the bytecode properties.
    """
    base = Op.PUSH1[0xFF] + Op.NOT
    assert str(base) == ""

    code = base + b"\x01\x02"
    assert code == bytes([0x60, 0xFF, 0x19, 0x01, 0x02])

    assert str(code) == ""
    assert code.popped_stack_items == base.popped_stack_items
    assert code.pushed_stack_items == base.pushed_stack_items
    assert code.max_stack_height == base.max_stack_height
    assert code.min_stack_height == base.min_stack_height
    assert code.terminating == base.terminating


def test_opcode_kwargs_validation() -> None:
    """Test that invalid keyword arguments raise ValueError."""
    # Test valid kwargs work
    Op.MSTORE(offset=0, value=1)
    Op.CALL(
        gas=1,
        address=2,
        value=3,
        args_offset=4,
        args_size=5,
        ret_offset=6,
        ret_size=7,
    )

    # Test invalid kwargs raise ValueError
    with pytest.raises(
        ValueError,
        match=r"Invalid keyword argument\(s\) \['offest'\] for opcode MSTORE",
    ):
        Op.MSTORE(offest=0, value=1)  # codespell:ignore offest

    with pytest.raises(
        ValueError,
        match=r"Invalid keyword argument\(s\) \['wrong_arg'\] for opcode MSTORE",  # noqa: E501
    ):
        Op.MSTORE(offset=0, value=1, wrong_arg=2)

    with pytest.raises(
        ValueError,
        match=r"Invalid keyword argument\(s\) \['addres'\] for opcode CALL",
    ):
        Op.CALL(
            gas=1,
            addres=2,  # codespell:ignore
            value=3,
            args_offset=4,
            args_size=5,
            ret_offset=6,
            ret_size=7,
        )

    # Test multiple invalid kwargs
    with pytest.raises(
        ValueError, match=r"Invalid keyword argument\(s\).*for opcode MSTORE"
    ):
        Op.MSTORE(offest=0, valu=1, extra=2)  # codespell:ignore offest,valu


def test_placeholder_requires_data_portion() -> None:
    """Test that a placeholder requires an opcode with a data portion."""
    with pytest.raises(
        ValueError,
        match="`data_placeholder` requires an opcode with data portion",
    ):
        Op.ADD(1, 2, data_placeholder="value")


@pytest.mark.parametrize(
    "placeholder_offsets,placeholder_sizes",
    [
        pytest.param({"value": 1}, None, id="offsets_only"),
        pytest.param(None, {"value": 2}, id="sizes_only"),
        pytest.param(
            {"value": 1, "other": 4}, {"value": 2}, id="length_mismatch"
        ),
    ],
)
def test_placeholder_incongruent_parameters(
    placeholder_offsets: dict[str, int] | None,
    placeholder_sizes: dict[str, int] | None,
) -> None:
    """Test that placeholder offsets and sizes must agree with each other."""
    with pytest.raises(Exception, match="incongruent parameters"):
        Bytecode(
            placeholder_offsets=placeholder_offsets,
            placeholder_sizes=placeholder_sizes,
        )


@pytest.mark.parametrize(
    "size,value",
    [
        pytest.param(1, 0x42, id="PUSH1"),
        pytest.param(2, 0x1234, id="PUSH2"),
        pytest.param(3, 0x123456, id="PUSH3"),
        pytest.param(4, 0x12345678, id="PUSH4"),
        pytest.param(8, 0xFF, id="PUSH8"),
        pytest.param(16, 0xABCD, id="PUSH16"),
        pytest.param(32, 0xDEADBEEF, id="PUSH32"),
    ],
)
def test_placeholder_substitute_basic(size: int, value: int) -> None:
    """Test basic placeholder substitution functionality."""
    push_op = getattr(Op, f"PUSH{size}")
    code = Op.POP(push_op(data_placeholder="value"))

    # The placeholder is sized after the opcode's data portion
    assert code._placeholder_sizes == {"value": size}

    # Substitute the actual value
    code.substitute(value=value)
    assert bytes(code) == bytes(Op.POP(push_op(value)))


@pytest.mark.parametrize(
    "size",
    [
        pytest.param(1, id="PUSH1"),
        pytest.param(2, id="PUSH2"),
        pytest.param(4, id="PUSH4"),
        pytest.param(8, id="PUSH8"),
        pytest.param(32, id="PUSH32"),
    ],
)
def test_placeholder_substitute_out_of_range(size: int) -> None:
    """Test that substitute rejects values that don't fit."""
    push_op = getattr(Op, f"PUSH{size}")
    code = Op.POP(push_op(data_placeholder="value"))

    for out_of_range in (-1, 256**size):
        with pytest.raises(ValueError, match="doesn't fit"):
            code.substitute(value=out_of_range)

    # Max value should work
    max_value = 256**size - 1
    code.substitute(value=max_value)
    assert bytes(code) == bytes(Op.POP(push_op(max_value)))


def test_placeholder_substitute_not_found() -> None:
    """Test that substitute raises error for an unknown placeholder."""
    code = Op.POP(Op.PUSH2(data_placeholder="value"))

    with pytest.raises(KeyError, match="not found in bytecode"):
        code.substitute(other_value=0x1234)


def test_placeholder_bytes_guard() -> None:
    """Test that bytecode with an open placeholder cannot become bytes."""
    code = Op.POP(Op.PUSH2(data_placeholder="value"))
    reference = Op.POP(Op.PUSH2(0))

    with pytest.raises(Exception, match="active placeholders"):
        bytes(code)

    with pytest.raises(Exception, match="active placeholders"):
        code.hex()

    with pytest.raises(Exception, match="active placeholders"):
        code.keccak256()

    # Length and gas cost remain available, which is what makes the
    # measure-then-substitute pattern possible
    assert len(code) == len(reference)
    assert code.gas_cost(Prague) == reference.gas_cost(Prague)

    # Once every slot is filled the conversion succeeds
    code.substitute(value=0x1234)
    filled = Op.POP(Op.PUSH2(0x1234))
    assert bytes(code) == bytes(filled)
    assert code.keccak256() == filled.keccak256()


def test_multiple_placeholders() -> None:
    """Test multiple placeholders in the same bytecode."""
    code = Op.ADD(
        Op.PUSH2(data_placeholder="first"),
        Op.PUSH1(data_placeholder="second"),
    )
    expected = bytes(Op.ADD(Op.PUSH2(0x1234), Op.PUSH1(0xAB)))

    assert code._placeholder_sizes == {"first": 2, "second": 1}

    # Substitute first placeholder, second should remain
    code.substitute(first=0x1234)
    assert "first" not in code._placeholder_offsets
    assert "second" in code._placeholder_offsets

    # Substitute second placeholder
    code.substitute(second=0xAB)
    assert not code._placeholder_offsets
    assert bytes(code) == expected


def test_placeholder_offset_after_concatenation() -> None:
    """Test that placeholder offsets are adjusted after concatenation."""
    prefix = Op.PUSH1(0xFF) + Op.POP
    suffix = Op.POP(Op.PUSH2(data_placeholder="value"))

    combined = prefix + suffix

    # The placeholder offset should account for the prefix length
    assert combined._placeholder_offsets["value"] == (
        len(prefix) + suffix._placeholder_offsets["value"]
    )
    assert combined._placeholder_sizes == suffix._placeholder_sizes

    # Substitution should still produce correct bytecode
    combined.substitute(value=0xBEEF)
    expected = prefix + Op.POP(Op.PUSH2(0xBEEF))
    assert bytes(combined) == bytes(expected)


def test_placeholder_conflicting_names_raise() -> None:
    """Test that concatenating a reused placeholder name raises."""
    code = Op.POP(Op.PUSH2(data_placeholder="value"))

    with pytest.raises(Exception, match="Conflicting data placeholders"):
        code + code

    # Distinct names concatenate without complaint
    other = Op.POP(Op.PUSH2(data_placeholder="other_value"))
    combined = code + other
    assert set(combined._placeholder_offsets) == {"value", "other_value"}


def test_placeholder_mul_raises() -> None:
    """Test that multiplying bytecode with placeholders raises."""
    code = Op.POP(Op.PUSH2(data_placeholder="value"))

    with pytest.raises(ValueError, match="Cannot multiply.*placeholders"):
        code * 3

    # Multiplying by 0 and 1 should still work
    assert bytes(code * 0) == b""
    assert len(code * 1) == len(code)
    assert "value" in (code * 1)._placeholder_offsets


def test_placeholder_in_opcode_list() -> None:
    """Test that placeholder PUSH opcode is included in opcode_list."""
    code = Op.POP(Op.PUSH2(data_placeholder="value"))

    # The opcode_list should contain the PUSH2 and POP opcodes
    assert len(code.opcode_list) == 2
    assert code.opcode_list[0] == Op.PUSH2
    assert code.opcode_list[1] == Op.POP


def test_placeholder_in_complex_bytecode() -> None:
    """Test placeholder in more complex bytecode constructions."""
    code = (
        Op.JUMPDEST
        + Op.PUSH1(1)
        + Op.ADD
        + Op.DUP1
        + Op.JUMPI(
            Op.GT(Op.GAS, Op.PUSH2(data_placeholder="loop_cost")),
            0,
        )
        + Op.STOP
    )

    # Placeholder should be tracked
    assert "loop_cost" in code._placeholder_offsets

    # Substitute and verify the bytecode is valid
    code.substitute(loop_cost=1000)
    assert "loop_cost" not in code._placeholder_offsets

    # Verify the value 1000 (0x03E8) appears in the bytecode
    assert b"\x03\xe8" in bytes(code)
