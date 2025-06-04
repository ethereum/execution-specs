"""Shared pytest definitions for EIP-7883 tests."""

from typing import Dict

import pytest

from ethereum_test_forks import Fork, Osaka
from ethereum_test_tools import Account, Address, Alloc, Storage, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .helpers import Vector
from .spec import Spec, Spec7883


@pytest.fixture
def call_opcode() -> Op:
    """Return default call used to call the precompile."""
    return Op.CALL


@pytest.fixture
def gas_measure_contract(pre: Alloc, call_opcode: Op, fork: Fork, vector: Vector) -> Address:
    """Deploys a contract that measures ModExp gas consumption."""
    call_code = call_opcode(
        address=Spec.MODEXP_ADDRESS,
        value=0,
        args_offset=0,
        args_size=Op.CALLDATASIZE,
    )
    gas_costs = fork.gas_costs()
    extra_gas = (
        gas_costs.G_WARM_ACCOUNT_ACCESS
        + (gas_costs.G_VERY_LOW * (len(call_opcode.kwargs) - 2))  # type: ignore
        + (gas_costs.G_BASE * 3)
    )
    measure_code = (
        Op.CALLDATACOPY(dest_offset=0, offset=0, size=Op.CALLDATASIZE)
        + Op.GAS  # [gas_start]
        + call_code  # [gas_start, call_result]
        + Op.GAS  # [gas_start, call_result, gas_end]
        + Op.SWAP1  # [gas_start, gas_end, call_result]
        + Op.PUSH1[0]  # [gas_start, gas_end, call_result, 0]
        + Op.SSTORE  # [gas_start, gas_end]
        + Op.PUSH2[extra_gas]  # [gas_start, gas_end, extra_gas]
        + Op.ADD  # [gas_start, gas_end + extra_gas]
        + Op.SWAP1  # [gas_end + extra_gas, gas_start]
        + Op.SUB  # [gas_start - (gas_end + extra_gas)]
        + Op.PUSH1[1]  # [gas_start - (gas_end + extra_gas), 1]
        + Op.SSTORE  # []
    )
    measure_code += Op.SSTORE(2, Op.RETURNDATASIZE())
    for i in range(len(vector.expected) // 32):
        measure_code += Op.RETURNDATACOPY(0, i * 32, 32)
        measure_code += Op.SSTORE(i + 3, Op.MLOAD(0))
    measure_code += Op.STOP()
    return pre.deploy_contract(measure_code)


@pytest.fixture
def precompile_gas(fork: Fork, vector: Vector) -> int:
    """Calculate gas cost for the ModExp precompile and verify it matches expected gas."""
    spec = Spec if fork < Osaka else Spec7883
    expected_gas = vector.gas_old if fork < Osaka else vector.gas_new
    calculated_gas = spec.calculate_gas_cost(
        len(vector.input.base),
        len(vector.input.modulus),
        len(vector.input.exponent),
        vector.input.exponent,
    )
    assert calculated_gas == expected_gas, (
        f"Calculated gas {calculated_gas} != Vector gas {expected_gas}"
    )
    return calculated_gas


@pytest.fixture
def tx(
    fork: Fork,
    pre: Alloc,
    gas_measure_contract: Address,
    vector: Vector,
    precompile_gas: int,
) -> Transaction:
    """Transaction to measure gas consumption of the ModExp precompile."""
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = intrinsic_gas_cost_calc(calldata=vector.input)
    memory_expansion_gas_calc = fork.memory_expansion_gas_calculator()
    memory_expansion_gas = memory_expansion_gas_calc(new_bytes=len(bytes(vector.input)))
    sstore_gas = fork.gas_costs().G_STORAGE_SET * (len(vector.expected) // 32)
    return Transaction(
        sender=pre.fund_eoa(),
        to=gas_measure_contract,
        data=vector.input,
        gas_limit=intrinsic_gas_cost
        + precompile_gas
        + memory_expansion_gas
        + sstore_gas
        + 100_000,
    )


@pytest.fixture
def post(
    gas_measure_contract: Address,
    precompile_gas: int,
    vector: Vector,
) -> Dict[Address, Account]:
    """Return expected post state with gas consumption check."""
    storage = Storage()
    storage[0] = 1
    storage[1] = precompile_gas
    storage[2] = len(vector.expected)
    for i in range(len(vector.expected) // 32):
        storage[i + 3] = vector.expected[i * 32 : (i + 1) * 32]
    return {gas_measure_contract: Account(storage=storage)}
