"""
Mainnet marked execute checklist tests for
[EIP-8070: eth/72 - Sparse Blobpool](https://eips.ethereum.org/EIPS/eip-8070).
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

pytestmark = [pytest.mark.valid_at("EIP8070"), pytest.mark.mainnet]

CUSTODY_ALIGNED_MASK = (1 << Spec.SAMPLES_PER_SLOT) - 1


def generate_single_blob_layout(fork: Fork) -> List:
    """Return a single-blob transaction layout."""
    return [
        pytest.param([[Blob.from_fork(fork)]], id="single_blob_transaction")
    ]


@pytest.mark.parametrize_by_fork("txs_blobs", generate_single_blob_layout)
def test_sparse_blobpool_mainnet(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
) -> None:
    """
    Test that a custody-aligned `custodyColumns` update is accepted and
    that `getBlobsV4` then serves exactly the cells its mask selects.

    One blob carries both surfaces EIP-8070 adds, so a live-network run
    pays for the minimum blob gas the fork allows.
    """
    blobs_test(
        pre=pre,
        txs=txs,
        get_blobs_version=4,
        cell_mask=CUSTODY_ALIGNED_MASK,
        custody_columns_updates=[
            CUSTODY_ALIGNED_MASK.to_bytes(Spec.CUSTODY_BITMAP_BYTES, "little")
        ],
    )
