"""
Benchmark transaction context instructions.

Supported Opcodes:
- ORIGIN
- GASPRICE
- BLOBHASH
"""

import math

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    ExtCallGenerator,
    Fork,
    Op,
    TransactionType,
    add_kzg_version,
)

from tests.cancun.eip4844_blobs.spec import Spec as BlobsSpec


@pytest.mark.repricing
@pytest.mark.parametrize(
    "opcode",
    [
        Op.ORIGIN,
        Op.GASPRICE,
    ],
)
def test_call_frame_context_ops(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
) -> None:
    """Benchmark call zero-parameter instructions."""
    benchmark_test(
        target_opcode=opcode,
        code_generator=ExtCallGenerator(attack_block=opcode),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "blob_present",
    [
        pytest.param(0, id="no_blobs"),
        pytest.param(1, id="one_blob"),
    ],
)
def test_blobhash(
    fork: Fork,
    benchmark_test: BenchmarkTestFiller,
    blob_present: int,
    fixed_opcode_count: int | None,
    gas_benchmark_value: int,
) -> None:
    """Benchmark BLOBHASH instruction."""
    tx_kwargs: dict = {}
    if blob_present:
        cap = fork.transaction_gas_limit_cap()
        if fixed_opcode_count is None and cap is not None:
            # Check if blob tx splits would exceed block blob limit
            required_splits = math.ceil(gas_benchmark_value / cap)
            max_blobs = fork.max_blobs_per_block()
            if required_splits > max_blobs:
                pytest.skip(
                    f"Blob tx needs {required_splits} splits but fork allows "
                    f"{max_blobs} blobs/block"
                )
        tx_kwargs = {
            "ty": TransactionType.BLOB_TRANSACTION,
            "max_fee_per_blob_gas": fork.min_base_fee_per_blob_gas(),
            "blob_versioned_hashes": add_kzg_version(
                [i.to_bytes(32, "big") for i in range(blob_present)],
                BlobsSpec.BLOB_COMMITMENT_VERSION_KZG,
            ),
        }

    benchmark_test(
        target_opcode=Op.BLOBHASH,
        code_generator=ExtCallGenerator(
            attack_block=Op.BLOBHASH(Op.PUSH0),
            tx_kwargs=tx_kwargs,
        ),
    )
