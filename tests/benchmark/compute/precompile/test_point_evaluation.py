"""Benchmark POINT EVALUATION precompile."""

import math

import ckzg  # type: ignore
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
    While,
)
from execution_testing.test_types.blob_types import Blob

from tests.cancun.eip4844_blobs.spec import Spec as BlobsSpec

from ..helpers import Precompile, concatenate_parameters

INPUT_SIZE = 192


@pytest.mark.repricing
@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            BlobsSpec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            concatenate_parameters(
                [
                    "01E798154708FE7789429634053CBF9F99B619F9F084048927333FCE637F549B",
                    "564C0A11A0F704F4FC3E8ACFE0F8245F0AD1347B378FBF96E206DA11A5D36306",
                    "24D25032E67A7E6A4910DF5834B8FE70E6BCFEEAC0352434196BDF4B2485D5A1",
                    "8F59A8D2A1A625A17F3FEA0FE5EB8C896DB3764F3185481BC22F91B4AAFFCCA25F26936857BC3A7C2539EA8EC3A952B7",
                    "873033E038326E87ED3E1276FD140253FA08E9FC25FB2D9A98527FC22A2C9612FBEAFDAD446CBC7BCDBDCD780AF2C16A",
                ]
            ),
            id="point_evaluation",
        ),
    ],
)
def test_point_evaluation(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark POINT EVALUATION precompile."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=precompile_address,
            args_size=Op.CALLDATASIZE,
        ),
    )

    benchmark_test(
        target_opcode=Precompile.POINT_EVALUATION,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


def _generate_point_evaluation_input(
    *,
    blob_data: bytes,
    commitment: bytes,
    versioned_hash: bytes,
    z: int,
    trusted_setup: object,
) -> bytes:
    """Generate a valid 192-byte point evaluation precompile input."""
    z_bytes = z.to_bytes(32, "big")
    proof_bytes, y_bytes = ckzg.compute_kzg_proof(
        blob_data, z_bytes, trusted_setup
    )
    return versioned_hash + z_bytes + y_bytes + commitment + proof_bytes


@pytest.mark.repricing
@pytest.mark.parametrize(
    "precompile_address",
    [
        pytest.param(
            BlobsSpec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            id="point_evaluation",
        ),
    ],
)
def test_point_evaluation_uncachable(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    precompile_address: Address,
) -> None:
    """Benchmark POINT EVALUATION with unique valid input per call."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    mem_exp = fork.memory_expansion_gas_calculator()
    precompile_cost = gsc.PRECOMPILE_POINT_EVALUATION

    # Each iteration: STATICCALL point_evaluation at advancing calldata
    # offset, then advance offset at MEM[CALLDATASIZE].
    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=precompile_address,
            args_offset=Op.MLOAD(Op.CALLDATASIZE),
            args_size=INPUT_SIZE,
            # gas accounting
            address_warm=True,
            inner_call_cost=precompile_cost,
        ),
    ) + Op.MSTORE(
        Op.CALLDATASIZE,
        Op.ADD(Op.MLOAD(Op.CALLDATASIZE), INPUT_SIZE),
    )

    setup = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    loop = While(
        body=attack_block,
        condition=Op.GT(Op.CALLDATASIZE, Op.MLOAD(Op.CALLDATASIZE)),
    )
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    iteration_cost = loop.gas_cost(fork)
    setup_cost = setup.gas_cost(fork)

    # Conservative per-variant estimate: one iteration + calldata
    # intrinsic + CALLDATACOPY copy and linear memory expansion.
    words_per_variant = math.ceil(INPUT_SIZE / 32)
    per_variant_gas = (
        iteration_cost
        + INPUT_SIZE * gsc.TX_DATA_TOKEN_FLOOR
        + words_per_variant * (gsc.OPCODE_COPY_PER_WORD + gsc.MEMORY_PER_WORD)
    )
    empty_intrinsic = intrinsic_gas_calculator(
        calldata=[], return_cost_deducted_prior_execution=True
    )
    fixed_overhead = empty_intrinsic + setup_cost + mem_exp(new_bytes=32)

    # Generate valid point evaluation inputs from a blob, each
    # with a unique evaluation point z.
    blob = Blob.from_fork(fork, seed=0)
    trusted_setup = Blob.trusted_setup()
    versioned_hash = BlobsSpec.kzg_to_versioned_hash(blob.commitment)

    seed_offset = 0
    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value
    expected_opcode_count = 0

    while remaining_gas > 0:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        per_tx_variants = max(
            1, (per_tx_gas - fixed_overhead) // per_variant_gas
        )

        points = [
            _generate_point_evaluation_input(
                blob_data=blob.data,
                commitment=blob.commitment,
                versioned_hash=versioned_hash,
                z=seed_offset + i + 1,
                trusted_setup=trusted_setup,
            )
            for i in range(per_tx_variants)
        ]
        calldata = Bytes(b"".join(points))
        while True:
            execution_intrinsic = intrinsic_gas_calculator(
                calldata=calldata,
                return_cost_deducted_prior_execution=True,
            )
            gas_for_loop = (
                per_tx_gas
                - execution_intrinsic
                - setup_cost
                - math.ceil(len(calldata) / 32) * gsc.OPCODE_COPY_PER_WORD
                - mem_exp(new_bytes=len(calldata) + 32)
            )

            if gas_for_loop >= per_tx_variants * iteration_cost:
                break
            per_tx_variants -= 1
            if not per_tx_variants:
                raise Exception("Unable to find correct variants.")
            calldata = Bytes(b"".join(points[:per_tx_variants]))

        expected_opcode_count += per_tx_variants

        assert len(calldata) != 0, "No valid calldata found for test"

        txs.append(
            Transaction(
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                gas_limit=per_tx_gas,
                data=calldata,
            )
        )
        remaining_gas -= per_tx_gas
        seed_offset += per_tx_variants
    assert len(txs) != 0, "No transactions were added to the test."
    benchmark_test(
        target_opcode=Precompile.POINT_EVALUATION,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        expected_opcode_count=expected_opcode_count,
        blocks=[Block(txs=txs)],
    )
