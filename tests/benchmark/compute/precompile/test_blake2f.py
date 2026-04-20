"""Benchmark BLAKE2F precompile."""

import random

import pytest
from execution_testing import (
    Address,
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

from tests.istanbul.eip152_blake2.common import Blake2bInput
from tests.istanbul.eip152_blake2.spec import Spec as Blake2bSpec

from ..helpers import Precompile, concatenate_parameters


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            Blake2bSpec.BLAKE2_PRECOMPILE_ADDRESS,
            concatenate_parameters(
                [
                    Blake2bInput(
                        rounds=0xFFFF, f=True
                    ).create_blake2b_tx_data(),
                ]
            ),
            id="blake2f",
        ),
    ],
)
def test_blake2f(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark BLAKE2F precompile."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=Precompile.BLAKE2F,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("num_rounds", [1, 6, 12, 24])
def test_blake2f_benchmark(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    num_rounds: int,
) -> None:
    """Benchmark BLAKE2F precompile with varying number of rounds."""
    precompile_address = Blake2bSpec.BLAKE2_PRECOMPILE_ADDRESS
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    calldata = Blake2bInput(rounds=num_rounds, f=True).create_blake2b_tx_data()

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=Precompile.BLAKE2F,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("num_rounds", [1, 6, 12, 24])
def test_blake2f_uncachable(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    num_rounds: int,
) -> None:
    """
    Benchmark BLAKE2F with unique input per call.

    Each iteration writes the 64-byte output back to offset 4 in
    memory, overwriting the h[] state so every call receives a
    distinct input, avoiding precompile result caching in
    clients.
    """
    precompile_address = Blake2bSpec.BLAKE2_PRECOMPILE_ADDRESS
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()

    # BLAKE2F costs num_rounds gas.
    gsc = fork.gas_costs()
    precompile_cost = (
        num_rounds * gsc.PRECOMPILE_BLAKE2F_PER_ROUND
    ) + gsc.PRECOMPILE_BLAKE2F_BASE

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=precompile_address,
            args_size=Op.CALLDATASIZE,
            # override the h state
            ret_offset=4,
            ret_size=64,
            # gas accounting
            address_warm=True,
            inner_call_cost=precompile_cost,
        ),
    )

    # rounds: data[0:4] 4 bytes
    # h: data[4:68] 64 bytes
    # m: data[68:196] 128 bytes
    # t: data[196:212] 16 bytes
    # f: data[212:213] 1 byte
    setup = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        # gas accounting
        data_size=213,
        old_memory_size=0,
        new_memory_size=213,
    )
    setup_cost = setup.gas_cost(fork)

    loop = WhileGas(
        body=attack_block,
        fork=fork,
    )
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    iteration_cost = loop.gas_cost(fork)

    base_calldata = Blake2bInput(
        rounds=num_rounds, f=True
    ).create_blake2b_tx_data()

    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value
    rng = random.Random(42)

    expected_opcode_count = 0
    while remaining_gas > 0:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        h_state = rng.randbytes(64)

        calldata = Bytes(
            base_calldata[:4]  # rounds
            + h_state  # h
            + base_calldata[68:]  # m, t, f
        )

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

    benchmark_test(
        target_opcode=Op.STATICCALL,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        blocks=[Block(txs=txs)],
        expected_opcode_count=expected_opcode_count,
    )
