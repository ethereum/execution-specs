"""
Shared pytest definitions for the ModExp precompile tests.

The gas measurement fixtures live here, with the Byzantium pricing, because
every later repricing of the precompile reuses them: a directory testing a
repricing EIP overrides the `modexp_spec` fixture with its own gas formula.
"""

from typing import Dict, Type

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    Op,
    Storage,
    Transaction,
    keccak256,
)
from execution_testing.forks import Berlin

from .helpers import ModExpInput
from .spec import ModExpGasSpec, modexp_gas_spec

CALL_GAS_BEFORE_BERLIN = 700
"""Gas charged by EIP-150 for a call to an existing account."""


@pytest.fixture
def modexp_spec(fork: Fork) -> Type[ModExpGasSpec]:
    """Return the ModExp gas specification in effect at the given fork."""
    return modexp_gas_spec(fork)


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
    fork: Fork,
    modexp_input: ModExpInput,
    precompile_gas: int,
) -> int:
    """Calculate total tx gas needed for the transaction."""
    intrinsic_gas_cost_calculator = (
        fork.transaction_intrinsic_cost_calculator()
    )
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    sstore_gas = Op.SSTORE(key_warm=False).gas_cost(fork) * 4
    precompile_gas_with_margin = precompile_gas * 64 // 63
    extra_gas = 100_000
    if fork.is_eip_enabled(8037):
        extra_gas = 500_000

    return (
        extra_gas
        + intrinsic_gas_cost_calculator(calldata=bytes(modexp_input))
        + memory_expansion_gas_calculator(new_bytes=len(bytes(modexp_input)))
        + precompile_gas_with_margin
        + sstore_gas
    )


@pytest.fixture
def exceeds_tx_gas_cap(
    total_tx_gas_needed: int,
    fork: Fork,
    env: Environment,
    precompile_gas: int,
) -> bool:
    """Determine if total gas requirements exceed transaction gas cap."""
    if fork.is_eip_enabled(8037):
        # EIP-8037: tx.gas can exceed TX_MAX_GAS_LIMIT; excess fills
        # state_gas_reservoir. But regular gas is still capped at
        # TX_MAX_GAS_LIMIT, so if the precompile alone needs more regular gas
        # than the budget, the call will fail.
        cap = fork.transaction_gas_limit_cap()
        return cap is not None and precompile_gas > cap
    tx_gas_limit_cap = fork.transaction_gas_limit_cap() or env.gas_limit
    return total_tx_gas_needed > tx_gas_limit_cap


@pytest.fixture
def expected_tx_cap_fail() -> bool:
    """Whether this test is expected to fail due to transaction gas cap."""
    return False


@pytest.fixture
def call_succeeds(
    exceeds_tx_gas_cap: bool, expected_tx_cap_fail: bool
) -> bool:
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
    modexp_spec: Type[ModExpGasSpec],
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
    assert call_opcode in [
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
    ]
    value = [0] if call_opcode in [Op.CALL, Op.CALLCODE] else []

    gas_used = (
        precompile_gas + precompile_gas_modifier
        if precompile_gas_modifier != float("inf")
        else Environment().gas_limit
    )

    call_code = call_opcode(
        gas_used,
        modexp_spec.MODEXP_ADDRESS,
        *value,
        0,
        Op.CALLDATASIZE(),
        0,
        0,
    )

    gas_costs = fork.gas_costs()
    # A precompile is always warm, so EIP-2929 charges the warm access cost
    # for the call. Before Berlin the charge is the flat EIP-150 call cost,
    # which `gas_costs()` does not carry.
    call_gas = (
        gas_costs.WARM_ACCESS if fork >= Berlin else CALL_GAS_BEFORE_BERLIN
    )
    extra_gas = (
        call_gas
        + (gas_costs.VERY_LOW * (len(call_opcode.kwargs) - 1))
        + gas_costs.BASE  # CALLDATASIZE
        + gas_costs.BASE  # GAS
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
                keccak256(Bytes(modexp_expected))
            ),
            Op.SHA3(0, Op.RETURNDATASIZE()),
        )
    return pre.deploy_contract(code)


@pytest.fixture
def precompile_gas(
    fork: Fork,
    modexp_spec: Type[ModExpGasSpec],
    modexp_input: ModExpInput,
    gas_old: int | None,
    gas_new: int | None,
) -> int:
    """
    Calculate gas cost for the ModExp precompile and verify it matches expected
    gas.
    """
    try:
        calculated_gas = modexp_spec.calculate_gas_cost(modexp_input)
        if gas_old is not None and gas_new is not None:
            expected_gas = (
                gas_old if not fork.is_eip_enabled(7883) else gas_new
            )
            base_len = len(modexp_input.base)
            exp_len = len(modexp_input.exponent)
            mod_len = len(modexp_input.modulus)
            exp_int = int.from_bytes(modexp_input.exponent, byteorder="big")
            error_msg = (
                f"Calculated gas {calculated_gas} != "
                f"Vector gas {expected_gas}\n"
                f"Lengths: base: {hex(base_len)} ({base_len}), "
                f"exponent: {hex(exp_len)} ({exp_len}), "
                f"modulus: {hex(mod_len)} ({mod_len})\n"
                f"Exponent: {modexp_input.exponent} ({exp_int})"
            )
            assert calculated_gas == expected_gas, error_msg
        return calculated_gas
    except Exception:
        # Used for `test_modexp_invalid_inputs` we expect the call to not
        # succeed. Return is for completeness.
        return modexp_spec.MIN_GAS


@pytest.fixture
def precompile_gas_modifier() -> int:
    """Return the gas modifier for the ModExp precompile."""
    return 0


@pytest.fixture
def tx(
    pre: Alloc,
    gas_measure_contract: Address,
    modexp_input: ModExpInput,
) -> Transaction:
    """Transaction to measure gas consumption of the ModExp precompile."""
    return Transaction(
        sender=pre.fund_eoa(),
        to=gas_measure_contract,
        data=bytes(modexp_input),
    )


@pytest.fixture
def post(
    gas_measure_contract: Address,
    call_contract_post_storage: Storage,
) -> Dict[Address, Account]:
    """Return expected post state with gas consumption check."""
    return {
        gas_measure_contract: Account(storage=call_contract_post_storage),
    }
