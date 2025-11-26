"""
Benchmark transaction context instructions.

Supported Opcodes:
- ORIGIN
- GASPRICE
- BLOBHASH
"""

from typing import Any, Dict

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
        code_generator=ExtCallGenerator(attack_block=opcode),
    )


@pytest.mark.repricing(blob_index=0, blobs_present=0)
@pytest.mark.parametrize(
    "blob_index, blobs_present",
    [
        pytest.param(0, 0, id="no blobs"),
        pytest.param(0, 1, id="one blob and accessed"),
        pytest.param(1, 1, id="one blob but access non-existent index"),
        pytest.param(5, 6, id="six blobs, access latest"),
    ],
)
def test_blobhash(
    fork: Fork,
    benchmark_test: BenchmarkTestFiller,
    blob_index: int,
    blobs_present: bool,
) -> None:
    """Benchmark BLOBHASH instruction."""
    tx_kwargs: Dict[str, Any] = {}
    if blobs_present > 0:
        tx_kwargs["ty"] = TransactionType.BLOB_TRANSACTION
        tx_kwargs["max_fee_per_blob_gas"] = fork.min_base_fee_per_blob_gas()
        tx_kwargs["blob_versioned_hashes"] = add_kzg_version(
            [i.to_bytes() * 32 for i in range(blobs_present)],
            BlobsSpec.BLOB_COMMITMENT_VERSION_KZG,
        )

    benchmark_test(
        code_generator=ExtCallGenerator(
            attack_block=Op.BLOBHASH(blob_index),
            tx_kwargs=tx_kwargs,
        ),
    )
