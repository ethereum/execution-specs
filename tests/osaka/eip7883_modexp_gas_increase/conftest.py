"""Shared pytest definitions for EIP-7883 tests."""

from typing import Dict

import pytest

from ethereum_test_forks import Fork, Osaka
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Storage,
    Transaction,
    keccak256,
)
from ethereum_test_vm import Opcodes as Op

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput
from .spec import Spec, Spec7883


@pytest.fixture
def gas_old() -> int | None:
    """Get old gas cost from the test vector if any."""
    return None


@pytest.fixture
def gas_new() -> int | None:
    """Get new gas cost from the test vector if any."""
    return None


@pytest.fixture
def call_opcode() -> Op:
    """Return call operation used to call the precompile."""
    return Op.CALL


@pytest.fixture
def call_contract_post_storage() -> Storage:
    """
    Storage of the test contract after the transaction is executed. Note:
    Fixture `call_contract_code` fills the actual expected storage values.
    """
    return Storage()


@pytest.fixture
def total_tx_gas_needed(
    fork: Fork, modexp_expected: bytes, modexp_input: ModExpInput, precompile_gas: int
) -> int:
    """Calculate total tx gas needed for the transaction."""
    intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    sstore_gas = fork.gas_costs().G_STORAGE_SET * (len(modexp_expected) // 32)
    extra_gas = 100_000

    return (
        extra_gas
        + intrinsic_gas_cost_calculator(calldata=bytes(modexp_input))
        + memory_expansion_gas_calculator(new_bytes=len(bytes(modexp_input)))
        + precompile_gas
        + sstore_gas
    )


@pytest.fixture
def exceeds_tx_gas_cap(total_tx_gas_needed: int, fork: Fork, env: Environment) -> bool:
    """Determine if total gas requirements exceed transaction gas cap."""
    tx_gas_limit_cap = fork.transaction_gas_limit_cap() or env.gas_limit
    return total_tx_gas_needed > tx_gas_limit_cap


@pytest.fixture
def expected_tx_cap_fail() -> bool:
    """Whether this test is expected to fail due to transaction gas cap."""
    return False


@pytest.fixture
def call_succeeds(exceeds_tx_gas_cap: bool, expected_tx_cap_fail: bool) -> bool:
    """
    Determine whether the ModExp precompile call should succeed or fail. By
    default, depending on the expected output, we assume it succeeds. Under
    EIP-7825, transactions requiring more gas than the cap should fail only if
    unexpected.
    """
    if exceeds_tx_gas_cap and not expected_tx_cap_fail:
        pytest.fail(
            "Test unexpectedly exceeds tx gas cap. "
            "Either mark with `expected_tx_cap_fail=True` or adjust inputs."
        )
    return not exceeds_tx_gas_cap


@pytest.fixture
def gas_measure_contract(
    pre: Alloc,
    call_opcode: Op,
    fork: Fork,
    modexp_expected: bytes,
    precompile_gas: int,
    precompile_gas_modifier: int,
    call_contract_post_storage: Storage,
    call_succeeds: bool,
) -> Address:
    """
    Deploys a contract that measures ModExp gas consumption and execution
    result.

    Always stored:
      storage[0]: precompile call success
      storage[1]: return data length from precompile

    Only if the precompile call succeeds:
      storage[2]: gas consumed by precompile
      storage[3]: hash of return data from precompile
    """
    assert call_opcode in [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL]
    value = [0] if call_opcode in [Op.CALL, Op.CALLCODE] else []

    gas_used = (
        precompile_gas + precompile_gas_modifier
        if precompile_gas_modifier != float("inf")
        else Environment().gas_limit
    )

    call_code = call_opcode(
        gas_used,
        Spec.MODEXP_ADDRESS,
        *value,
        0,
        Op.CALLDATASIZE(),
        0,
        0,
    )

    gas_costs = fork.gas_costs()
    extra_gas = (
        gas_costs.G_WARM_ACCOUNT_ACCESS
        + (gas_costs.G_VERY_LOW * (len(call_opcode.kwargs) - 1))
        + gas_costs.G_BASE  # CALLDATASIZE
        + gas_costs.G_BASE  # GAS
    )

    # Build the gas measurement contract code
    # Stack operations:
    # [gas_start]
    # [gas_start, call_result]
    # [gas_start, call_result, gas_end]
    # [gas_start, gas_end, call_result]
    call_result_measurement = Op.GAS + call_code + Op.GAS + Op.SWAP1

    # Calculate gas consumed: gas_start - (gas_end + extra_gas)
    # Stack Operation:
    # [gas_start, gas_end]
    # [gas_start, gas_end, extra_gas]
    # [gas_start, gas_end + extra_gas]
    # [gas_end + extra_gas, gas_start]
    # [gas_consumed]
    gas_calculation = Op.PUSH2[extra_gas] + Op.ADD + Op.SWAP1 + Op.SUB

    code = (
        Op.CALLDATACOPY(dest_offset=0, offset=0, size=Op.CALLDATASIZE)
        + Op.SSTORE(call_contract_post_storage.store_next(call_succeeds), call_result_measurement)
        + Op.SSTORE(
            call_contract_post_storage.store_next(len(modexp_expected) if call_succeeds else 0),
            Op.RETURNDATASIZE(),
        )
    )

    if call_succeeds:
        code += Op.SSTORE(call_contract_post_storage.store_next(precompile_gas), gas_calculation)
        code += Op.RETURNDATACOPY(dest_offset=0, offset=0, size=Op.RETURNDATASIZE())
        code += Op.SSTORE(
            call_contract_post_storage.store_next(keccak256(Bytes(modexp_expected))),
            Op.SHA3(0, Op.RETURNDATASIZE()),
        )
    return pre.deploy_contract(code)


@pytest.fixture
def precompile_gas(
    fork: Fork, modexp_input: ModExpInput, gas_old: int | None, gas_new: int | None
) -> int:
    """
    Calculate gas cost for the ModExp precompile and verify it matches expected
    gas.
    """
    spec = Spec if fork < Osaka else Spec7883
    try:
        calculated_gas = spec.calculate_gas_cost(modexp_input)
        if gas_old is not None and gas_new is not None:
            expected_gas = gas_old if fork < Osaka else gas_new
            assert calculated_gas == expected_gas, (
                f"Calculated gas {calculated_gas} != Vector gas {expected_gas}\n"
                f"Lengths: base: {hex(len(modexp_input.base))} ({len(modexp_input.base)}), "
                f"exponent: {hex(len(modexp_input.exponent))} ({len(modexp_input.exponent)}), "
                f"modulus: {hex(len(modexp_input.modulus))} ({len(modexp_input.modulus)})\n"
                f"Exponent: {modexp_input.exponent} "
                f"({int.from_bytes(modexp_input.exponent, byteorder='big')})"
            )
        return calculated_gas
    except Exception:
        # Used for `test_modexp_invalid_inputs` we expect the call to not
        # succeed. Return is for completeness.
        return 500 if fork >= Osaka else 200


@pytest.fixture
def precompile_gas_modifier() -> int:
    """Return the gas modifier for the ModExp precompile."""
    return 0


@pytest.fixture
def tx(
    pre: Alloc,
    gas_measure_contract: Address,
    modexp_input: ModExpInput,
    tx_gas_limit: int,
) -> Transaction:
    """Transaction to measure gas consumption of the ModExp precompile."""
    return Transaction(
        sender=pre.fund_eoa(),
        to=gas_measure_contract,
        data=bytes(modexp_input),
        gas_limit=tx_gas_limit,
    )


@pytest.fixture
def tx_gas_limit(total_tx_gas_needed: int, fork: Fork, env: Environment) -> int:
    """
    Transaction gas limit used for the test (Can be overridden in the test).
    """
    tx_gas_limit_cap = fork.transaction_gas_limit_cap() or env.gas_limit
    return min(tx_gas_limit_cap, total_tx_gas_needed)


@pytest.fixture
def post(
    gas_measure_contract: Address,
    call_contract_post_storage: Storage,
) -> Dict[Address, Account]:
    """Return expected post state with gas consumption check."""
    return {
        gas_measure_contract: Account(storage=call_contract_post_storage),
    }
