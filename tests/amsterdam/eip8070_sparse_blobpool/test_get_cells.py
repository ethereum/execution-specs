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
    add_kzg_version,
)

from .spec import Spec, ref_spec_8070

REFERENCE_SPEC_GIT_PATH = ref_spec_8070.git_path
REFERENCE_SPEC_VERSION = ref_spec_8070.version

pytestmark = pytest.mark.valid_from("EIP8070")

CELLS = Spec.CELLS_PER_EXT_BLOB
ALL_CELLS_MASK = (1 << CELLS) - 1


def generate_blob_layouts(fork: Fork) -> List:
    """Return blob transaction layouts to exercise `getBlobsV4`."""
    max_blobs_per_block = fork.max_blobs_per_block()
    max_blobs_per_tx = fork.max_blobs_per_tx()
    target_blobs_per_block = fork.target_blobs_per_block()

    # Ascending pattern (1, 2, 3... blobs per tx) capped at the target
    ascending_txs = []
    total_blobs = 0
    blob_offset = 0
    for tx_size in range(1, max_blobs_per_tx + 1):
        if total_blobs + tx_size > target_blobs_per_block:
            break
        ascending_txs.append(
            [Blob.from_fork(fork, blob_offset + j) for j in range(tx_size)]
        )
        total_blobs += tx_size
        blob_offset += tx_size

    two_tx_blobs = min(target_blobs_per_block // 2, max_blobs_per_tx)
    three_tx_blobs = min(target_blobs_per_block // 3, max_blobs_per_tx)

    return [
        pytest.param(
            [[Blob.from_fork(fork)]],
            id="single_blob_transaction",
        ),
        pytest.param(
            [[Blob.from_fork(fork, s) for s in range(max_blobs_per_tx)]],
            id="max_blobs_per_tx",
        ),
        pytest.param(
            [[Blob.from_fork(fork, s)] for s in range(max_blobs_per_block)],
            id="max_blobs_per_block",
        ),
        pytest.param(
            [[Blob.from_fork(fork, s)] for s in range(target_blobs_per_block)],
            id="target_blobs_per_block",
        ),
        pytest.param(
            [
                [Blob.from_fork(fork, s) for s in range(two_tx_blobs)],
                [
                    Blob.from_fork(fork, s + two_tx_blobs)
                    for s in range(two_tx_blobs)
                ],
            ],
            id="two_tx_equal_blobs",
        ),
        pytest.param(
            [
                [
                    Blob.from_fork(fork, s + i * three_tx_blobs)
                    for s in range(three_tx_blobs)
                ]
                for i in range(3)
            ],
            id="three_tx_equal_blobs",
        ),
        pytest.param(
            [[Blob.from_fork(fork, s) for s in range(max_blobs_per_tx)]]
            + [
                [Blob.from_fork(fork, max_blobs_per_tx + s)]
                for s in range(max_blobs_per_block - max_blobs_per_tx)
            ],
            id="mixed_max_tx_plus_singles",
        ),
        pytest.param(
            ascending_txs,
            id="ascending_blob_pattern",
        ),
    ]


def generate_nonexisting_blob_hashes(count: int) -> List[Hash]:
    """Return well-formed versioned hashes that match no pooled blob."""
    return add_kzg_version(
        [sha256(str(i).encode()).digest() for i in range(count)],
        Spec.BLOB_COMMITMENT_VERSION_KZG,
    )


def generate_single_blob_layout(fork: Fork) -> List:
    """Return a single-blob transaction layout."""
    return [
        pytest.param([[Blob.from_fork(fork)]], id="single_blob_transaction")
    ]


def generate_single_blob_txs_layout(fork: Fork) -> List:
    """Return a layout of three single-blob transactions."""
    return [
        pytest.param(
            [[Blob.from_fork(fork, s)] for s in range(3)],
            id="three_single_blob_txs",
        )
    ]


def generate_cell_masks() -> List:
    """Return cell masks to exercise `getBlobsV4`."""
    return [
        pytest.param(ALL_CELLS_MASK, id="all_cells"),
        pytest.param((1 << Spec.RECONSTRUCTION_THRESHOLD) - 1, id="first_64"),
        pytest.param(
            ALL_CELLS_MASK ^ ((1 << Spec.RECONSTRUCTION_THRESHOLD) - 1),
            id="top_64",
        ),
        pytest.param(0xFF, id="custody_aligned_8"),
        pytest.param(1, id="single_cell"),
        pytest.param(1 << (CELLS - 1), id="last_cell"),
        pytest.param(
            sum(1 << i for i in range(0, CELLS, 2)), id="alternating_cells"
        ),
        pytest.param(0, id="no_cells"),
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
    nonexisting_blob_hashes = generate_nonexisting_blob_hashes(5)
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
    nonexisting_blob_hashes = generate_nonexisting_blob_hashes(5)
    blobs_test(
        pre=pre,
        txs=[],
        get_blobs_version=4,
        cell_mask=cell_mask,
        nonexisting_blob_hashes=nonexisting_blob_hashes,
    )


@pytest.mark.parametrize(
    "cell_mask",
    [pytest.param(0xFF, id="custody_aligned_8")],
)
@pytest.mark.parametrize_by_fork("txs_blobs", generate_single_blob_layout)
@pytest.mark.exception_test
def test_get_cells_min_request_size(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
    cell_mask: int,
) -> None:
    """
    Test a request of 128 versioned hashes, the minimum request size a
    client must support for `getBlobsV4`.

    The response must hold one entry per requested hash: a cell matrix for
    the existing blob and `null` for each non-existing hash.
    """
    nonexisting_blob_hashes = generate_nonexisting_blob_hashes(
        Spec.MIN_SUPPORTED_REQUEST_SIZE - 1
    )
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=cell_mask,
        nonexisting_blob_hashes=nonexisting_blob_hashes,
    )


@pytest.mark.parametrize(
    "cell_mask",
    [
        pytest.param(ALL_CELLS_MASK, id="all_cells"),
        pytest.param(0xFF, id="custody_aligned_8"),
    ],
)
@pytest.mark.parametrize_by_fork("txs_blobs", generate_single_blob_txs_layout)
@pytest.mark.exception_test
def test_get_cells_interleaved_missing(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
    cell_mask: int,
) -> None:
    """
    Test that `null` entries appear at the exact request positions when
    non-existing hashes are interleaved with existing ones (leading,
    middle, and trailing positions of the request).
    """
    nonexisting_blob_hashes = generate_nonexisting_blob_hashes(5)
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=cell_mask,
        nonexisting_blob_hashes=nonexisting_blob_hashes,
        interleave_nonexisting_blob_hashes=True,
    )
