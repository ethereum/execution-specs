"""Test opcode gas costs."""

import pytest

from execution_testing.vm import Bytecode, Op

from ..forks.forks import Homestead, Osaka
from ..helpers import Fork


@pytest.mark.parametrize(
    "fork,opcode,expected_cost",
    [
        pytest.param(
            Osaka,
            Op.MSTORE(new_memory_size=1),
            Osaka.memory_expansion_gas_calculator()(new_bytes=1)
            + Osaka.gas_costs().G_VERY_LOW,
            id="mstore_memory_expansion",
        ),
        pytest.param(
            Osaka,
            Op.SSTORE,
            Osaka.gas_costs().G_STORAGE_SET + Osaka.gas_costs().G_COLD_SLOAD,
            id="sstore_defaults",
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=True),
            Osaka.gas_costs().G_STORAGE_SET,
            id="sstore_warm_key",
        ),
        # EXP tests
        pytest.param(
            Osaka,
            Op.EXP(exponent=0),
            Osaka.gas_costs().G_EXP,
            id="exp_zero_exponent",
        ),
        pytest.param(
            Osaka,
            Op.EXP(exponent=0xFFFFFF),  # 3 bytes
            Osaka.gas_costs().G_EXP + Osaka.gas_costs().G_EXP_BYTE * 3,
            id="exp_three_bytes",
        ),
        pytest.param(
            Osaka,
            Op.EXP(exponent=0x1FFFFFF),  # 3 bytes
            Osaka.gas_costs().G_EXP + Osaka.gas_costs().G_EXP_BYTE * 4,
            id="exp_three_bytes_plus_one_bit",
        ),
        # SHA3 tests
        pytest.param(
            Osaka,
            Op.SHA3(data_size=0),
            Osaka.gas_costs().G_KECCAK_256,
            id="sha3_zero_data",
        ),
        pytest.param(
            Osaka,
            Op.SHA3(data_size=64, new_memory_size=96),
            Osaka.gas_costs().G_KECCAK_256
            + Osaka.gas_costs().G_KECCAK_256_WORD * 2
            + Osaka.memory_expansion_gas_calculator()(new_bytes=96),
            id="sha3_with_data_and_memory",
        ),
        # BALANCE tests
        pytest.param(
            Osaka,
            Op.BALANCE(address_warm=False),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS,
            id="balance_cold_address",
        ),
        pytest.param(
            Osaka,
            Op.BALANCE(address_warm=True),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS,
            id="balance_warm_address",
        ),
        # CALLDATACOPY tests
        pytest.param(
            Osaka,
            Op.CALLDATACOPY(data_size=32, new_memory_size=32),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.gas_costs().G_COPY * 1
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="calldatacopy_one_word",
        ),
        pytest.param(
            Osaka,
            Op.CALLDATACOPY(
                data_size=64, new_memory_size=64, old_memory_size=32
            ),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.gas_costs().G_COPY * 2
            + Osaka.memory_expansion_gas_calculator()(
                new_bytes=64, previous_bytes=32
            ),
            id="calldatacopy_expansion",
        ),
        # CODECOPY tests
        pytest.param(
            Osaka,
            Op.CODECOPY(data_size=96, new_memory_size=96),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.gas_costs().G_COPY * 3
            + Osaka.memory_expansion_gas_calculator()(new_bytes=96),
            id="codecopy_three_words",
        ),
        # EXTCODESIZE tests
        pytest.param(
            Osaka,
            Op.EXTCODESIZE(address_warm=False),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS,
            id="extcodesize_cold",
        ),
        pytest.param(
            Osaka,
            Op.EXTCODESIZE(address_warm=True),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS,
            id="extcodesize_warm",
        ),
        # EXTCODECOPY tests
        pytest.param(
            Osaka,
            Op.EXTCODECOPY(
                address_warm=True, data_size=32, new_memory_size=32
            ),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS
            + Osaka.gas_costs().G_COPY * 1
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="extcodecopy_warm",
        ),
        pytest.param(
            Osaka,
            Op.EXTCODECOPY(
                address_warm=False, data_size=64, new_memory_size=64
            ),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS
            + Osaka.gas_costs().G_COPY * 2
            + Osaka.memory_expansion_gas_calculator()(new_bytes=64),
            id="extcodecopy_cold",
        ),
        # EXTCODEHASH tests
        pytest.param(
            Osaka,
            Op.EXTCODEHASH(address_warm=False),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS,
            id="extcodehash_cold",
        ),
        pytest.param(
            Osaka,
            Op.EXTCODEHASH(address_warm=True),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS,
            id="extcodehash_warm",
        ),
        # RETURNDATACOPY tests
        pytest.param(
            Osaka,
            Op.RETURNDATACOPY(data_size=32, new_memory_size=32),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.gas_costs().G_COPY * 1
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="returndatacopy",
        ),
        # MLOAD tests
        pytest.param(
            Osaka,
            Op.MLOAD(new_memory_size=32),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="mload_memory_expansion",
        ),
        # MSTORE8 tests
        pytest.param(
            Osaka,
            Op.MSTORE8(new_memory_size=1),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.memory_expansion_gas_calculator()(new_bytes=1),
            id="mstore8_memory_expansion",
        ),
        # SLOAD tests
        pytest.param(
            Osaka,
            Op.SLOAD(key_warm=False),
            Osaka.gas_costs().G_COLD_SLOAD,
            id="sload_cold",
        ),
        pytest.param(
            Osaka,
            Op.SLOAD(key_warm=True),
            Osaka.gas_costs().G_WARM_SLOAD,
            id="sload_warm",
        ),
        # MCOPY tests
        pytest.param(
            Osaka,
            Op.MCOPY(data_size=32, new_memory_size=32),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.gas_costs().G_COPY * 1
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="mcopy_one_word",
        ),
        pytest.param(
            Osaka,
            Op.MCOPY(data_size=96, new_memory_size=128, old_memory_size=64),
            Osaka.gas_costs().G_VERY_LOW
            + Osaka.gas_costs().G_COPY * 3
            + Osaka.memory_expansion_gas_calculator()(
                new_bytes=128, previous_bytes=64
            ),
            id="mcopy_expansion",
        ),
        # LOG0 tests
        pytest.param(
            Osaka,
            Op.LOG0(data_size=32, new_memory_size=32),
            Osaka.gas_costs().G_LOG
            + Osaka.gas_costs().G_LOG_DATA * 32
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="log0",
        ),
        # LOG1 tests
        pytest.param(
            Osaka,
            Op.LOG1(data_size=64, new_memory_size=64),
            Osaka.gas_costs().G_LOG
            + Osaka.gas_costs().G_LOG_DATA * 64
            + Osaka.gas_costs().G_LOG_TOPIC
            + Osaka.memory_expansion_gas_calculator()(new_bytes=64),
            id="log1",
        ),
        # LOG2 tests
        pytest.param(
            Osaka,
            Op.LOG2(data_size=128, new_memory_size=128),
            Osaka.gas_costs().G_LOG
            + Osaka.gas_costs().G_LOG_DATA * 128
            + Osaka.gas_costs().G_LOG_TOPIC * 2
            + Osaka.memory_expansion_gas_calculator()(new_bytes=128),
            id="log2",
        ),
        # LOG3 tests
        pytest.param(
            Osaka,
            Op.LOG3(data_size=256, new_memory_size=256),
            Osaka.gas_costs().G_LOG
            + Osaka.gas_costs().G_LOG_DATA * 256
            + Osaka.gas_costs().G_LOG_TOPIC * 3
            + Osaka.memory_expansion_gas_calculator()(new_bytes=256),
            id="log3",
        ),
        # LOG4 tests
        pytest.param(
            Osaka,
            Op.LOG4(data_size=512, new_memory_size=512),
            Osaka.gas_costs().G_LOG
            + Osaka.gas_costs().G_LOG_DATA * 512
            + Osaka.gas_costs().G_LOG_TOPIC * 4
            + Osaka.memory_expansion_gas_calculator()(new_bytes=512),
            id="log4",
        ),
        # CREATE tests
        pytest.param(
            Osaka,
            Op.CREATE(init_code_size=100, new_memory_size=100),
            Osaka.gas_costs().G_CREATE
            + Osaka.gas_costs().G_INITCODE_WORD * 4  # (100 + 31) // 32 = 4
            + Osaka.memory_expansion_gas_calculator()(new_bytes=100),
            id="create_with_initcode",
        ),
        # CREATE2 tests
        pytest.param(
            Osaka,
            Op.CREATE2(init_code_size=64, new_memory_size=64),
            Osaka.gas_costs().G_CREATE
            + Osaka.gas_costs().G_INITCODE_WORD * 2
            + Osaka.gas_costs().G_KECCAK_256_WORD * 2
            + Osaka.memory_expansion_gas_calculator()(new_bytes=64),
            id="create2_with_initcode_and_hash",
        ),
        # CALL tests
        pytest.param(
            Osaka,
            Op.CALL(
                address_warm=True, value_transfer=False, new_memory_size=64
            ),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS
            + Osaka.memory_expansion_gas_calculator()(new_bytes=64),
            id="call_warm_no_value",
        ),
        pytest.param(
            Osaka,
            Op.CALL(address_warm=False, delegated_address=True),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS
            + Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS,
            id="call_cold_delegated_address",
        ),
        pytest.param(
            Osaka,
            Op.CALL(
                address_warm=False,
                delegated_address=True,
                delegated_address_warm=True,
            ),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS
            + Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS,
            id="call_warm_delegated_address",
        ),
        pytest.param(
            Osaka,
            Op.CALL(address_warm=False, value_transfer=True, account_new=True),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS
            + Osaka.gas_costs().G_CALL_VALUE
            + Osaka.gas_costs().G_NEW_ACCOUNT,
            id="call_cold_account_new",
        ),
        pytest.param(
            Homestead,
            Op.CALL(address_warm=False, value_transfer=True, account_new=True),
            Homestead.gas_costs().G_COLD_ACCOUNT_ACCESS,
            id="call_cold_account_new_homestead",
        ),
        pytest.param(
            Osaka,
            Op.CALL(
                address_warm=False,
                value_transfer=True,
                account_new=False,
                new_memory_size=32,
            ),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS
            + Osaka.gas_costs().G_CALL_VALUE
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="call_cold_with_value",
        ),
        pytest.param(
            Osaka,
            Op.CALL(
                address_warm=False,
                value_transfer=True,
                account_new=True,
                new_memory_size=32,
            ),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS
            + Osaka.gas_costs().G_CALL_VALUE
            + Osaka.gas_costs().G_NEW_ACCOUNT
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="call_cold_new_account",
        ),
        # CALLCODE tests
        pytest.param(
            Osaka,
            Op.CALLCODE(
                address_warm=True, value_transfer=False, new_memory_size=32
            ),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="callcode_warm",
        ),
        # DELEGATECALL tests
        pytest.param(
            Osaka,
            Op.DELEGATECALL(address_warm=True, new_memory_size=32),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="delegatecall_warm",
        ),
        pytest.param(
            Osaka,
            Op.DELEGATECALL(address_warm=False, new_memory_size=64),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS
            + Osaka.memory_expansion_gas_calculator()(new_bytes=64),
            id="delegatecall_cold",
        ),
        # STATICCALL tests
        pytest.param(
            Osaka,
            Op.STATICCALL(address_warm=True, new_memory_size=32),
            Osaka.gas_costs().G_WARM_ACCOUNT_ACCESS
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="staticcall_warm",
        ),
        pytest.param(
            Osaka,
            Op.STATICCALL(address_warm=False, new_memory_size=0),
            Osaka.gas_costs().G_COLD_ACCOUNT_ACCESS,
            id="staticcall_cold_no_memory",
        ),
        # RETURN tests
        pytest.param(
            Osaka,
            Op.RETURN(new_memory_size=32),
            Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="return_no_deposit",
        ),
        pytest.param(
            Osaka,
            Op.RETURN(code_deposit_size=100, new_memory_size=32),
            Osaka.gas_costs().G_CODE_DEPOSIT_BYTE * 100
            + Osaka.memory_expansion_gas_calculator()(new_bytes=32),
            id="return_with_code_deposit",
        ),
        # REVERT tests
        pytest.param(
            Osaka,
            Op.REVERT(new_memory_size=64),
            Osaka.memory_expansion_gas_calculator()(new_bytes=64),
            id="revert_memory_expansion",
        ),
        # CLZ test (Osaka-specific)
        pytest.param(
            Osaka,
            Op.CLZ,
            Osaka.gas_costs().G_LOW,
            id="clz_osaka",
        ),
    ],
)
def test_opcode_gas_costs(fork: Fork, opcode: Op, expected_cost: int) -> None:  # noqa: D103
    op_gas_cost_calc = fork.opcode_gas_calculator()
    assert expected_cost == op_gas_cost_calc(opcode)


@pytest.mark.parametrize(
    "fork,bytecode,expected_cost",
    [
        pytest.param(
            Osaka,
            Op.ADD + Op.SUB,
            Osaka.gas_costs().G_VERY_LOW * 2,
            id="sum_of_opcodes",
        ),
        pytest.param(
            Osaka,
            Op.ADD(1, 1),
            Osaka.gas_costs().G_VERY_LOW * 3,
            id="opcode_with_args",
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(1, 2, key_warm=True),
            Osaka.gas_costs().G_STORAGE_SET + Osaka.gas_costs().G_VERY_LOW * 2,
            id="opcode_with_metadata",
        ),
    ],
)
def test_bytecode_gas_costs(  # noqa: D103
    fork: Fork, bytecode: Bytecode, expected_cost: int
) -> None:
    assert expected_cost == bytecode.gas_cost(fork)


@pytest.mark.parametrize(
    "fork,opcode,expected_refund",
    [
        pytest.param(
            Osaka,
            Op.SSTORE(original_value=0, new_value=0),
            0,
            id="sstore_no_refund_zero_to_zero",
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(original_value=1, new_value=1),
            0,
            id="sstore_no_refund_nonzero_to_nonzero",
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(original_value=1, new_value=0),
            Osaka.gas_costs().R_STORAGE_CLEAR,
            id="sstore_refund_clear_storage",
        ),
        pytest.param(
            Osaka,
            Op.ADD,
            0,
            id="add_no_refund",
        ),
        pytest.param(
            Osaka,
            Op.MSTORE,
            0,
            id="mstore_no_refund",
        ),
    ],
)
def test_opcode_refunds(fork: Fork, opcode: Op, expected_refund: int) -> None:  # noqa: D103
    op_refund_calc = fork.opcode_refund_calculator()
    assert expected_refund == op_refund_calc(opcode)


@pytest.mark.parametrize(
    "fork,bytecode,expected_refund",
    [
        pytest.param(
            Osaka,
            Op.SSTORE(original_value=1, new_value=0),
            Osaka.gas_costs().R_STORAGE_CLEAR,
            id="single_sstore_clear",
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(original_value=2, new_value=0)
            + Op.SSTORE(original_value=1, new_value=0),
            Osaka.gas_costs().R_STORAGE_CLEAR * 2,
            id="double_sstore_clear",
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(original_value=1, new_value=2)
            + Op.SSTORE(original_value=1, new_value=0),
            Osaka.gas_costs().R_STORAGE_CLEAR,
            id="mixed_sstore_one_clear",
        ),
        pytest.param(
            Osaka,
            Op.ADD + Op.SUB,
            0,
            id="no_refund_opcodes",
        ),
    ],
)
def test_bytecode_refunds(  # noqa: D103
    fork: Fork, bytecode: Bytecode, expected_refund: int
) -> None:
    assert expected_refund == bytecode.refund(fork)


@pytest.mark.parametrize(
    "fork,opcode,expected_cost",
    [
        # No-op: new == current (value_reset=True on clean slot)
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=True, original_value=0, new_value=0),
            Osaka.gas_costs().G_WARM_SLOAD,
            id="sstore_noop_zero_warm",  # 0 → 0
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=False, original_value=0, new_value=0),
            Osaka.gas_costs().G_COLD_SLOAD + Osaka.gas_costs().G_WARM_SLOAD,
            id="sstore_noop_zero_cold",  # 0 → 0
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=True, original_value=5, new_value=5),
            Osaka.gas_costs().G_WARM_SLOAD,
            id="sstore_noop_nonzero_warm",  # 5 → 5
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=False, original_value=5, new_value=5),
            Osaka.gas_costs().G_COLD_SLOAD + Osaka.gas_costs().G_WARM_SLOAD,
            id="sstore_noop_nonzero_cold",  # 5 → 5
        ),
        # Create storage: 0 → X (original == 0)
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=True, new_value=5),
            Osaka.gas_costs().G_STORAGE_SET,
            id="sstore_create_warm",  # 0 → 5
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=False, new_value=5),
            Osaka.gas_costs().G_COLD_SLOAD + Osaka.gas_costs().G_STORAGE_SET,
            id="sstore_create_cold",  # 0 → 5
        ),
        # Modify storage: X → Y (original != 0, new != 0, new != original)
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=True, original_value=5, new_value=7),
            Osaka.gas_costs().G_STORAGE_RESET,
            id="sstore_modify_warm",  # 5 → 7
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=False, original_value=5, new_value=7),
            Osaka.gas_costs().G_COLD_SLOAD + Osaka.gas_costs().G_STORAGE_RESET,
            id="sstore_modify_cold",  # 5 → 7
        ),
        # Clear storage: X → 0 (original != 0, new == 0)
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=True, original_value=5, new_value=0),
            Osaka.gas_costs().G_STORAGE_RESET,
            id="sstore_clear_warm",  # 5 → 0
        ),
        pytest.param(
            Osaka,
            Op.SSTORE(key_warm=False, original_value=5, new_value=0),
            Osaka.gas_costs().G_COLD_SLOAD + Osaka.gas_costs().G_STORAGE_RESET,
            id="sstore_clear_cold",  # 5 → 0
        ),
    ],
)
def test_sstore_gas_costs(fork: Fork, opcode: Op, expected_cost: int) -> None:
    """Test SSTORE gas costs for all single-SSTORE scenarios."""
    assert opcode.gas_cost(fork) == expected_cost
