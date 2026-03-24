"""Conftest for EIP-7823 tests."""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Fork,
    Op,
    Storage,
    Transaction,
    keccak256,
)
from execution_testing.forks import Osaka

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput
from ..eip7883_modexp_gas_increase.spec import Spec


@pytest.fixture
def call_contract_post_storage() -> Storage:
    """
    Storage of the test contract after the transaction is executed. Note:
    Fixture `call_contract_code` fills the actual expected storage values.
    """
    return Storage()


@pytest.fixture
def call_succeeds(
    total_gas_used: int,
    fork: Fork,
    env: Environment,
    modexp_input: ModExpInput,
) -> bool:
    """
    By default, depending on the expected output, we can deduce if the call is
    expected to succeed or fail.
    """
    # Transaction gas limit exceeded
    tx_gas_limit_cap = fork.transaction_gas_limit_cap() or env.gas_limit
    if total_gas_used > tx_gas_limit_cap:
        return False

    # Input length exceeded
    base_length, exp_length, mod_length = modexp_input.get_declared_lengths()
    if (
        base_length > Spec.MAX_LENGTH_BYTES
        or exp_length > Spec.MAX_LENGTH_BYTES
        or mod_length > Spec.MAX_LENGTH_BYTES
    ) and fork >= Osaka:
        return False

    return True


@pytest.fixture
def gas_measure_contract(
    pre: Alloc,
    fork: Fork,
    modexp_expected: bytes,
    precompile_gas: int,
    call_contract_post_storage: Storage,
    call_succeeds: bool,
) -> Address:
    """
    Deploy a contract that calls ModExp and checks the result.

    Pre-Osaka (gas measurement):
      storage[0]: precompile call success
      storage[1]: return data length from precompile
      storage[2]: gas consumed by precompile (only if call succeeds)
      storage[3]: hash of return data from precompile (only if call succeeds)

    Osaka+ (correctness only):
      storage[0]: call success
      storage[1]: return data length
      storage[2]: hash of return data (only if call succeeds)
    """
    call_code = Op.CALL(
        precompile_gas,
        Spec.MODEXP_ADDRESS,
        0,
        0,
        Op.CALLDATASIZE(),
        0,
        0,
    )

    if fork >= Osaka:
        # Simplified: correctness only, no gas measurement
        code = (
            Op.CALLDATACOPY(dest_offset=0, offset=0, size=Op.CALLDATASIZE)
            + Op.SSTORE(
                call_contract_post_storage.store_next(call_succeeds),
                call_code,
            )
            + Op.SSTORE(
                call_contract_post_storage.store_next(
                    len(modexp_expected) if call_succeeds else 0
                ),
                Op.RETURNDATASIZE(),
            )
        )
        if call_succeeds:
            code += Op.RETURNDATACOPY(
                dest_offset=0, offset=0, size=Op.RETURNDATASIZE()
            )
            code += Op.SSTORE(
                call_contract_post_storage.store_next(
                    keccak256(bytes(modexp_expected))
                ),
                Op.SHA3(0, Op.RETURNDATASIZE()),
            )
        return pre.deploy_contract(code)

    # Pre-Osaka: full gas measurement
    extra_gas = (
        Op.CALL(
            precompile_gas,
            Spec.MODEXP_ADDRESS,
            0,
            0,
            Op.CALLDATASIZE(),
            0,
            0,
            address_warm=True,
        ).gas_cost(fork)
        + Op.GAS.gas_cost(fork)  # second GAS in measurement
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
        + Op.SSTORE(
            call_contract_post_storage.store_next(call_succeeds),
            call_result_measurement,
        )
        + Op.SSTORE(
            call_contract_post_storage.store_next(
                len(modexp_expected) if call_succeeds else 0
            ),
            Op.RETURNDATASIZE(),
        )
    )

    if call_succeeds:
        code += Op.SSTORE(
            call_contract_post_storage.store_next(precompile_gas),
            gas_calculation,
        )
        code += Op.RETURNDATACOPY(
            dest_offset=0, offset=0, size=Op.RETURNDATASIZE()
        )
        code += Op.SSTORE(
            call_contract_post_storage.store_next(
                keccak256(bytes(modexp_expected))
            ),
            Op.SHA3(0, Op.RETURNDATASIZE()),
        )
    return pre.deploy_contract(code)


@pytest.fixture
def precompile_gas(fork: Fork, modexp_input: ModExpInput) -> int:
    """
    Calculate gas cost for the ModExp precompile and verify it matches expected
    gas.
    """
    if fork >= Osaka:
        return 1_000_000  # Generous gas; no formula for EVM contract
    try:
        calculated_gas = Spec.calculate_gas_cost(modexp_input)
        return calculated_gas
    except Exception:
        # Used for `test_modexp_invalid_inputs` we expect the call to not
        # succeed. Return is for completeness.
        return 200


@pytest.fixture
def tx(
    pre: Alloc,
    gas_measure_contract: Address,
    modexp_input: ModExpInput,
    tx_gas_limit: int,
) -> Transaction:
    """Transaction to measure gas consumption of the ModExp precompile."""
    return Transaction(
        ty=0x02,
        sender=pre.fund_eoa(),
        to=gas_measure_contract,
        data=bytes(modexp_input),
        gas_limit=tx_gas_limit,
    )


@pytest.fixture
def total_gas_used(
    fork: Fork,
    modexp_expected: bytes,
    modexp_input: ModExpInput,
    precompile_gas: int,
) -> int:
    """
    Transaction gas limit used for the test (Can be overridden in the test).
    """
    if fork >= Osaka:
        return 10_000_000  # Generous gas for EVM contract
    intrinsic_gas_cost_calculator = (
        fork.transaction_intrinsic_cost_calculator()
    )
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    extra_gas = 500_000

    total_gas = (
        extra_gas
        + intrinsic_gas_cost_calculator(calldata=bytes(modexp_input))
        + memory_expansion_gas_calculator(new_bytes=len(bytes(modexp_input)))
        + precompile_gas
    )

    return total_gas


@pytest.fixture
def tx_gas_limit(total_gas_used: int, fork: Fork, env: Environment) -> int:
    """
    Transaction gas limit used for the test (Can be overridden in the test).
    """
    tx_gas_limit_cap = fork.transaction_gas_limit_cap() or env.gas_limit
    return min(tx_gas_limit_cap, total_gas_used)


@pytest.fixture
def post(
    gas_measure_contract: Address,
    call_contract_post_storage: Storage,
) -> Dict[Address, Account]:
    """Return expected post state with gas consumption check."""
    return {
        gas_measure_contract: Account(storage=call_contract_post_storage),
    }
