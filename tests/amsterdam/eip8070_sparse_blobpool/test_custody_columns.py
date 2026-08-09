"""
Custody columns forkchoice tests.

Tests for the `custodyColumns` parameter of `engine_forkchoiceUpdatedV4`
in [EIP-8070: eth/72 - Sparse Blobpool](
https://eips.ethereum.org/EIPS/eip-8070).

`custodyColumns` is an optional 16-byte bitmap informing the execution
client of the blob columns it must custody. A well-formed bitmap must be
accepted (custody set update errors must not affect the forkchoice flow);
a bitmap of any other length must be rejected with `-32602: Invalid
params`. Blob serving via `engine_getBlobsV4` must be unaffected either
way, since the client holds the full blobs.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Blob,
    BlobsTestFiller,
    Fork,
    NetworkWrappedTransaction,
    Transaction,
)

from .spec import Spec, ref_spec_8070

REFERENCE_SPEC_GIT_PATH = ref_spec_8070.git_path
REFERENCE_SPEC_VERSION = ref_spec_8070.version

pytestmark = pytest.mark.valid_from("EIP8070")

CELLS = Spec.CELLS_PER_EXT_BLOB
ALL_CELLS_MASK = (1 << CELLS) - 1
BITMAP_BYTES = Spec.CUSTODY_BITMAP_BYTES


def generate_single_blob_layout(fork: Fork) -> List:
    """Return a single-blob transaction layout."""
    return [
        pytest.param([[Blob.from_fork(fork)]], id="single_blob_transaction")
    ]


@pytest.mark.parametrize(
    "custody_columns",
    [
        pytest.param(b"\xff" * BITMAP_BYTES, id="all_columns"),
        pytest.param(
            ((1 << Spec.SAMPLES_PER_SLOT) - 1).to_bytes(
                BITMAP_BYTES, "little"
            ),
            id="custody_aligned_8",
        ),
        pytest.param(b"\x00" * BITMAP_BYTES, id="no_columns"),
    ],
)
@pytest.mark.parametrize_by_fork("txs_blobs", generate_single_blob_layout)
@pytest.mark.exception_test
def test_fcu_custody_columns(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
    custody_columns: bytes,
) -> None:
    """
    Test that `engine_forkchoiceUpdatedV4` accepts a 16-byte
    `custodyColumns` bitmap with a VALID payload status and that blob
    serving via `getBlobsV4` is unaffected by the custody update.
    """
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=ALL_CELLS_MASK,
        custody_columns=custody_columns,
    )


@pytest.mark.parametrize(
    "custody_columns",
    [
        pytest.param(b"\xff" * (BITMAP_BYTES - 1), id="fifteen_bytes"),
        pytest.param(b"\xff" * (BITMAP_BYTES + 1), id="seventeen_bytes"),
        pytest.param(b"", id="empty"),
    ],
)
@pytest.mark.parametrize_by_fork("txs_blobs", generate_single_blob_layout)
@pytest.mark.exception_test
def test_fcu_custody_columns_invalid_length(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
    custody_columns: bytes,
) -> None:
    """
    Test that a malformed-length `custodyColumns` bitmap is rejected with
    `-32602: Invalid params` and does not affect subsequent blob serving.
    """
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=ALL_CELLS_MASK,
        custody_columns=custody_columns,
    )
