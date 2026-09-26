"""
Custody columns forkchoice tests.

Tests for the `custodyColumns` parameter of `engine_forkchoiceUpdatedV4`
in [EIP-8070: eth/72 - Sparse Blobpool](
https://eips.ethereum.org/EIPS/eip-8070).

`custodyColumns` is an optional 16-byte bitmap informing the execution
client of the blob columns it must custody. A well-formed bitmap must be
accepted (custody set update errors must not affect the forkchoice flow);
a `null` value or a bitmap identical to the current set is a blobpool
no-op and must also be accepted; a bitmap of any other length must be
rejected with `-32602: Invalid params`. Blob serving via
`engine_getBlobsV4` must be unaffected either way, since the client
holds the full blobs.

Each test sends its `custodyColumns` values in order, one forkchoice
update each, before requesting the blobs. The custody set itself only
steers devp2p sampling of peer-announced transactions and is not
observable through the Engine API, so these tests pin acceptance and
unaffected blob serving, not the resulting custody set.
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
CUSTODY_ALIGNED_8 = ((1 << Spec.SAMPLES_PER_SLOT) - 1).to_bytes(
    BITMAP_BYTES, "little"
)


def generate_single_blob_layout(fork: Fork) -> List:
    """Return a single-blob transaction layout."""
    return [
        pytest.param([[Blob.from_fork(fork)]], id="single_blob_transaction")
    ]


@pytest.mark.parametrize(
    "custody_columns",
    [
        pytest.param(b"\xff" * BITMAP_BYTES, id="all_columns"),
        pytest.param(CUSTODY_ALIGNED_8, id="custody_aligned_8"),
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
        custody_columns_updates=[custody_columns],
    )


@pytest.mark.parametrize(
    "custody_columns_updates",
    [
        pytest.param([None], id="fresh"),
        pytest.param([CUSTODY_ALIGNED_8, None], id="after_custody_set"),
    ],
)
@pytest.mark.parametrize_by_fork("txs_blobs", generate_single_blob_layout)
@pytest.mark.exception_test
def test_fcu_custody_columns_null(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
    custody_columns_updates: List[bytes | None],
) -> None:
    """
    Test that `engine_forkchoiceUpdatedV4` accepts a `null`
    `custodyColumns` with a VALID payload status, both on a client with no
    custody set and after one was configured, and that `getBlobsV4` still
    serves every cell of the pending transaction afterwards.
    """
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=ALL_CELLS_MASK,
        custody_columns_updates=custody_columns_updates,
    )


@pytest.mark.parametrize_by_fork("txs_blobs", generate_single_blob_layout)
@pytest.mark.exception_test
def test_fcu_custody_columns_identical(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
) -> None:
    """
    Test that resending the current custody set, the other no-op case the
    EIP lists alongside `null`, is accepted with a VALID payload status
    and that `getBlobsV4` still serves every cell afterwards.
    """
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=ALL_CELLS_MASK,
        custody_columns_updates=[CUSTODY_ALIGNED_8, CUSTODY_ALIGNED_8],
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
        custody_columns_updates=[custody_columns],
    )
