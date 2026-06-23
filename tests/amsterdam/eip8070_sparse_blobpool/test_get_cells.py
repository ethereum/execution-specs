"""
Get cells engine endpoint tests.

Tests for the `engine_getBlobsV4` endpoint in [EIP-8070: eth/72 - Sparse
Blobpool](https://eips.ethereum.org/EIPS/eip-8070).

`engine_getBlobsV4` retrieves a custody-aligned subset of a blob's cells,
selected by a `uint128` `indices_bitarray` cell mask, and returns a partial
cell matrix with `null` entries for cells that were not requested or are not
held by the client.
"""

from hashlib import sha256
from typing import List

import pytest
from execution_testing import (
    Alloc,
    Blob,
    BlobsTestFiller,
    Fork,
    Hash,
    NetworkWrappedTransaction,
    Transaction,
)

from .spec import Spec, ref_spec_8070

REFERENCE_SPEC_GIT_PATH = ref_spec_8070.git_path
REFERENCE_SPEC_VERSION = ref_spec_8070.version

pytestmark = pytest.mark.valid_from("EIP8070")

CELLS = Spec.CELLS_PER_EXT_BLOB
ALL_CELLS_MASK = (1 << CELLS) - 1


def generate_blob_layouts(fork: Fork) -> List:
    """Return blob transaction layouts to exercise `getBlobsV4`."""
    max_blobs_per_tx = fork.max_blobs_per_tx()
    return [
        pytest.param(
            [[Blob.from_fork(fork)]],
            id="single_blob_transaction",
        ),
        pytest.param(
            [[Blob.from_fork(fork, s) for s in range(max_blobs_per_tx)]],
            id="max_blobs_per_tx",
        ),
    ]


def generate_cell_masks() -> List:
    """Return cell masks to exercise `getBlobsV4`."""
    return [
        pytest.param(ALL_CELLS_MASK, id="all_cells"),
        pytest.param((1 << Spec.RECONSTRUCTION_THRESHOLD) - 1, id="first_64"),
        pytest.param(0xFF, id="custody_aligned_8"),
        pytest.param(1, id="single_cell"),
        pytest.param(
            sum(1 << i for i in range(0, CELLS, 2)), id="alternating_cells"
        ),
    ]


@pytest.mark.parametrize(
    "cell_mask",
    generate_cell_masks(),
)
@pytest.mark.parametrize_by_fork("txs_blobs", generate_blob_layouts)
@pytest.mark.exception_test
def test_get_cells(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
    cell_mask: int,
) -> None:
    """
    Test that `getBlobsV4` returns exactly the cells selected by the mask.

    Requested cells (and their proofs) must match the locally computed values;
    non-requested cell indices must be `null` in the partial matrix.
    """
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=cell_mask,
    )


@pytest.mark.parametrize(
    "cell_mask",
    generate_cell_masks(),
)
@pytest.mark.parametrize_by_fork("txs_blobs", generate_blob_layouts)
@pytest.mark.exception_test
def test_get_cells_partial_and_missing(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
    cell_mask: int,
) -> None:
    """
    Test that `getBlobsV4` returns a partial response: existing blobs yield a
    cell matrix while non-existing versioned hashes yield `null` entries.
    """
    nonexisting_blob_hashes = [
        Hash(sha256(str(i).encode()).digest()) for i in range(5)
    ]
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=cell_mask,
        nonexisting_blob_hashes=nonexisting_blob_hashes,
    )


@pytest.mark.parametrize(
    "cell_mask",
    generate_cell_masks(),
)
@pytest.mark.parametrize("txs_blobs", [[]], ids=["no_blobs"])
@pytest.mark.exception_test
def test_get_cells_only_nonexisting(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    cell_mask: int,
) -> None:
    """
    Test that `getBlobsV4` returns an array of `null` entries (one per
    requested hash) when all requested blobs are non-existing.
    """
    nonexisting_blob_hashes = [
        Hash(sha256(str(i).encode()).digest()) for i in range(5)
    ]
    blobs_test(
        pre=pre,
        txs=[],
        get_blobs_version=4,
        cell_mask=cell_mask,
        nonexisting_blob_hashes=nonexisting_blob_hashes,
    )
