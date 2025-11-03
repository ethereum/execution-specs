"""Test suite for OpcodeGasCalculator."""

import pytest

from execution_testing.forks.forks.forks import Osaka, Prague
from execution_testing import Bytecode, OpcodeGasCalculator, Op, Fork


@pytest.mark.parametrize(
    "fork,bytecode,expected_gas",
    [
        # Simple arithmetic
        pytest.param(
            Prague,
            Op.PUSH0 + Op.PUSH0 + Op.ADD,
            7,  # 2 + 2 + 3
            id="prague_simple_arithmetic",
        ),
        pytest.param(
            Osaka,
            Op.PUSH0 + Op.PUSH0 + Op.ADD,
            7,  # 2 + 2 + 3
            id="osaka_simple_arithmetic",
        ),
        # PUSH1 operations
        pytest.param(
            Prague,
            Op.PUSH1(42) + Op.PUSH1(43) + Op.MUL,
            11,  # 3 + 3 + 5
            id="prague_push1_mul",
        ),
        pytest.param(
            Osaka,
            Op.PUSH1(42) + Op.PUSH1(43) + Op.MUL,
            11,  # 3 + 3 + 5
            id="osaka_push1_mul",
        ),
        # Storage operations (base cost only)
        pytest.param(
            Prague,
            Op.PUSH1(42) + Op.PUSH0 + Op.SSTORE,
            105,  # 3 + 2 + 100
            id="prague_sstore",
        ),
        pytest.param(
            Osaka,
            Op.PUSH1(42) + Op.PUSH0 + Op.SSTORE,
            105,  # 3 + 2 + 100
            id="osaka_sstore",
        ),
        # Complex sequence
        pytest.param(
            Osaka,
            Op.PUSH1(42)
            + Op.PUSH1(43)
            + Op.ADD
            + Op.PUSH0
            + Op.MSTORE
            + Op.PUSH0
            + Op.PUSH0
            + Op.RETURN,
            18,  # 3 + 3 + 3 + 2 + 3 + 2 + 2 + 0
            id="complex_sequence",
        ),
        # DUP opcodes
        pytest.param(
            Osaka,
            Op.DUP1 + Op.DUP2 + Op.DUP16,
            9,  # 3 + 3 + 3
            id="dup_opcodes",
        ),
        # SWAP opcodes
        pytest.param(
            Osaka,
            Op.SWAP1 + Op.SWAP2 + Op.SWAP16,
            9,  # 3 + 3 + 3
            id="swap_opcodes",
        ),
        # LOG opcodes
        pytest.param(
            Osaka,
            Op.LOG0 + Op.LOG1 + Op.LOG4,
            1125,  # 375 + 375 + 375
            id="log_opcodes",
        ),
        # Various PUSH sizes
        pytest.param(
            Osaka,
            Op.PUSH0 + Op.PUSH1(0xFF) + Op.PUSH2(0xFFFF) + Op.PUSH32(0xFF),
            11,  # 2 + 3 + 3 + 3
            id="push_variants",
        ),
        # Empty bytecode
        pytest.param(
            Osaka,
            Bytecode(),
            0,
            id="empty_bytecode",
        ),
        # Single opcode
        pytest.param(
            Osaka,
            Op.STOP,
            0,
            id="stop_opcode",
        ),
        # Memory operations
        pytest.param(
            Osaka,
            Op.MLOAD + Op.MSTORE + Op.MSTORE8,
            9,  # 3 + 3 + 3
            id="memory_ops",
        ),
        # Comparison and bitwise
        pytest.param(
            Osaka,
            Op.LT + Op.GT + Op.EQ + Op.AND + Op.OR + Op.XOR + Op.NOT,
            21,  # 3 * 7
            id="comparison_bitwise",
        ),
        # Arithmetic operations
        pytest.param(
            Prague,
            Op.ADD + Op.SUB + Op.MUL + Op.DIV + Op.MOD,
            21,  # 3 + 3 + 5 + 5 + 5
            id="arithmetic_ops",
        ),
        # EXP operation
        pytest.param(
            Osaka,
            Op.EXP,
            10,
            id="exp_op",
        ),
        # CALL-like operations
        pytest.param(
            Osaka,
            Op.CALL + Op.DELEGATECALL + Op.STATICCALL,
            300,  # 100 + 100 + 100
            id="call_ops",
        ),
        # CREATE operations
        pytest.param(
            Osaka,
            Op.CREATE + Op.CREATE2,
            64000,  # 32000 + 32000
            id="create_ops",
        ),
        # SHA3/KECCAK256
        pytest.param(
            Osaka,
            Op.SHA3,
            30,
            id="sha3",
        ),
        # Block information opcodes
        pytest.param(
            Osaka,
            Op.BLOCKHASH + Op.COINBASE + Op.TIMESTAMP + Op.NUMBER,
            26,  # 20 + 2 + 2 + 2
            id="block_info",
        ),
        # Realistic constructor pattern
        pytest.param(
            Osaka,
            Op.PUSH1(0x80)
            + Op.PUSH1(0x40)
            + Op.MSTORE
            + Op.CALLVALUE
            + Op.DUP1
            + Op.ISZERO
            + Op.PUSH1(0x0F)
            + Op.JUMPI
            + Op.PUSH0
            + Op.DUP1
            + Op.REVERT,
            35,  # 3+3+3+2+3+3+3+10+2+3+0
            id="constructor_pattern",
        ),
    ],
)
def test_opcode_gas_calculator(
    fork: Fork, bytecode: Bytecode, expected_gas: int
) -> None:
    """Test that OpcodeGasCalculator correctly calculates base gas costs."""
    calc = OpcodeGasCalculator(fork)
    assert calc.calculate(bytecode) == expected_gas


def test_direct_op_cost() -> None:
    """Test using fork's op_cost method directly."""
    assert Prague.op_cost(Op.ADD) == 3
    assert Osaka.op_cost(Op.ADD) == 3
    assert Prague.op_cost(Op.MUL) == 5
    assert Osaka.op_cost(Op.MUL) == 5


def test_fork_consistency() -> None:
    """Test that Prague and Osaka have same base costs for common opcodes."""
    code = Op.PUSH1(0x01) + Op.PUSH1(0x02) + Op.ADD

    prague_calc = OpcodeGasCalculator(Prague)
    osaka_calc = OpcodeGasCalculator(Osaka)

    prague_gas = prague_calc.calculate(code)
    osaka_gas = osaka_calc.calculate(code)

    assert prague_gas == osaka_gas == 9  # 3 + 3 + 3
