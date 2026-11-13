"""
Block blob limits shared by frame and EIP-4844 transactions, for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A blob-carrying frame transaction contributes
`len(blob_versioned_hashes) * GAS_PER_BLOB` to the block's `blob_gas_used`
and counts against the blob limits of the active fork, together with the
block's EIP-4844 transactions.
"""

from typing import List

import pytest
from execution_testing import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Header,
    Transaction,
    TransactionException,
    add_kzg_version,
)

from .helpers import sender_frame, verify_frame
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

BLOB_COMMITMENT_VERSION_KZG = 1
DESTINATION = Address(0x100)


def blob_txs(
    pre: Alloc,
    fork: Fork,
    total_blobs: int,
    last_is_frame_tx: bool,
    last_tx_error: TransactionException | None = None,
) -> List[Transaction]:
    """
    Return transactions carrying `total_blobs` blobs, each at most the
    per-transaction maximum, alternating between frame and EIP-4844
    transactions and ending with the kind `last_is_frame_tx` selects.
    """
    counts: List[int] = []
    remaining = total_blobs
    while remaining > 0:
        counts.append(min(remaining, fork.max_blobs_per_tx()))
        remaining -= counts[-1]

    txs: List[Transaction] = []
    first_hash = 0
    for index, count in enumerate(counts):
        blob_versioned_hashes = add_kzg_version(
            list(range(first_hash, first_hash + count)),
            BLOB_COMMITMENT_VERSION_KZG,
        )
        first_hash += count
        distance_from_last = len(counts) - 1 - index
        is_frame_tx = last_is_frame_tx == (distance_from_last % 2 == 0)
        error = last_tx_error if distance_from_last == 0 else None
        if is_frame_tx:
            txs.append(
                Transaction(
                    sender=pre.fund_eoa(),
                    frames=[verify_frame(), sender_frame(target=DESTINATION)],
                    blob_versioned_hashes=blob_versioned_hashes,
                    error=error,
                )
            )
        else:
            txs.append(
                Transaction(
                    ty=3,
                    sender=pre.fund_eoa(),
                    to=DESTINATION,
                    blob_versioned_hashes=blob_versioned_hashes,
                    error=error,
                )
            )
    return txs


@pytest.mark.parametrize(
    "extra_blobs",
    [
        pytest.param(0, id="at_limit"),
        pytest.param(1, id="above_limit", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.parametrize(
    "last_is_frame_tx",
    [True, False],
    ids=["frame_tx_last", "blob_tx_last"],
)
def test_frame_and_blob_txs_against_the_block_blob_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    last_is_frame_tx: bool,
    extra_blobs: int,
) -> None:
    """
    Accept a block whose frame and EIP-4844 transactions together carry
    exactly the fork's maximum blob count, with `blob_gas_used` counting
    the blobs of both kinds, and reject one carrying one blob more:
    whichever kind crosses the limit, the blobs of the other kind count
    against it.
    """
    total_blobs = fork.max_blobs_per_block() + extra_blobs
    header = Header(blob_gas_used=total_blobs * fork.blob_gas_per_blob())
    if extra_blobs:
        error = TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        block = Block(
            txs=blob_txs(
                pre, fork, total_blobs, last_is_frame_tx, last_tx_error=error
            ),
            exception=error,
            rlp_modifier=header,
        )
    else:
        block = Block(
            txs=blob_txs(pre, fork, total_blobs, last_is_frame_tx),
            header_verify=header,
        )
    blockchain_test(pre=pre, post={}, blocks=[block])
