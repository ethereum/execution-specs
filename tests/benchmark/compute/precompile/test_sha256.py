"""Benchmark SHA256 precompile."""

import math
import random

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytes,
    Fork,
    JumpLoopGenerator,
    Op,
    Transaction,
    WhileGas,
)

from ..helpers import Precompile, calculate_optimal_input_length


def test_sha256(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    tx_gas_limit: int,
) -> None:
    """Benchmark SHA256 precompile."""
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_available = tx_gas_limit - intrinsic_gas_calculator()

    gas_costs = fork.gas_costs()
    optimal_input_length = calculate_optimal_input_length(
        available_gas=gas_available,
        fork=fork,
        static_cost=gas_costs.PRECOMPILE_SHA256_BASE,
        per_word_dynamic_cost=gas_costs.PRECOMPILE_SHA256_PER_WORD,
        bytes_per_unit_of_work=64,
    )

    attack_block = Op.POP(
        Op.STATICCALL(
            Op.GAS, 0x02, Op.PUSH0, optimal_input_length, Op.PUSH0, Op.PUSH0
        )
    )

    benchmark_test(
        target_opcode=Precompile.SHA256,
        code_generator=JumpLoopGenerator(
            setup=Op.CODECOPY(0, 0, optimal_input_length),
            attack_block=attack_block,
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("size", [0, 32, 256, 1024])
def test_sha256_fixed_size(
    benchmark_test: BenchmarkTestFiller, size: int
) -> None:
    """Benchmark SHA256 with fixed size input."""
    attack_block = Op.POP(
        Op.STATICCALL(Op.GAS, 0x02, Op.PUSH0, size, Op.PUSH0, Op.PUSH0)
    )

    benchmark_test(
        target_opcode=Precompile.SHA256,
        code_generator=JumpLoopGenerator(
            setup=Op.CODECOPY(0, 0, size), attack_block=attack_block
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("size", [32, 256, 1024])
def test_sha256_uncachable(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    size: int,
) -> None:
    """Benchmark SHA256 with unique input per call."""
    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()

    precompile_cost = (
        # static cost
        gsc.PRECOMPILE_SHA256_BASE
        # dynamic cost
        + math.ceil(size / 32) * gsc.PRECOMPILE_SHA256_PER_WORD
    )
    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=0x02,
            args_size=size,
            ret_size=0x20,
            # gas accounting
            address_warm=True,
            inner_call_cost=precompile_cost,
        ),
    )

    setup = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        # gas accounting
        data_size=size,
        old_memory_size=0,
        new_memory_size=size,
    )
    setup_cost = setup.gas_cost(fork)

    loop = WhileGas(
        body=attack_block,
        fork=fork,
        extra_gas=precompile_cost,
    )
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    iteration_cost = loop.gas_cost(fork)

    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value
    rng = random.Random(42)
    expected_opcode_count = 0

    while remaining_gas > 0:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        calldata = Bytes(rng.randbytes(size))

        intrinsic = intrinsic_gas_calculator(
            calldata=calldata,
            return_cost_deducted_prior_execution=True,
        )
        gas_for_loop = per_tx_gas - intrinsic - setup_cost
        if gas_for_loop < iteration_cost:
            break
        expected_opcode_count += gas_for_loop // iteration_cost

        txs.append(
            Transaction(
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                gas_limit=per_tx_gas,
                data=calldata,
            )
        )
        remaining_gas -= per_tx_gas

    assert len(txs) != 0, "No transactions were added to the test."

    benchmark_test(
        target_opcode=Precompile.SHA256,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        blocks=[Block(txs=txs)],
        expected_opcode_count=expected_opcode_count,
    )
