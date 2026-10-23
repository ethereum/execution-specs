"""
Blob-carrying frame transactions submitted in their network wrapper, for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame transaction with non-empty `blob_versioned_hashes` travels with its
blob sidecar exactly as an EIP-4844 transaction does, wrapped per EIP-7594 as
`rlp([tx_payload_body, wrapper_version, blobs, commitments, cell_proofs])`,
while a block body carries its plain payload. These tests submit such
transactions through `eth_sendRawTransaction` and check that the client serves
their blobs through `engine_getBlobsV*`, and check that a block carrying the
wrapper instead of the plain payload is rejected.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Blob,
    BlobsTestFiller,
    Block,
    BlockchainTestFiller,
    BlockException,
    Fork,
    Header,
    NetworkWrappedTransaction,
    Transaction,
    TransactionException,
)

from .helpers import sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


def network_wrapped(
    tx: Transaction, blobs: List[Blob], fork: Fork
) -> NetworkWrappedTransaction:
    """Return `tx` wrapped with the sidecar of `blobs`."""
    return NetworkWrappedTransaction(
        tx=tx,
        blob_objects=blobs,
        wrapper_version=fork.full_blob_tx_wrapper_version(),
    )


def frame_tx_with_blobs(pre: Alloc, blobs: List[Blob]) -> Transaction:
    """
    Return a frame transaction from a fresh EOA carrying `blobs`.

    The `VERIFY` frame approves execution and payment against the sender's
    default code. Its execution budget leaves room for the signature
    verification that counts against the same `MAX_VERIFY_GAS`, so the
    transaction is admissible to a public mempool.
    """
    return Transaction(
        sender=pre.fund_eoa(),
        frames=[
            verify_frame(gas_limit=Spec.MAX_VERIFY_GAS // 2),
            sender_frame(target=pre.fund_eoa(amount=0)),
        ],
        blob_versioned_hashes=[blob.versioned_hash for blob in blobs],
    )


def frame_blob_cases(fork: Fork) -> List:
    """Return blob distributions across frame transactions."""
    max_blobs_per_tx = fork.max_blobs_per_tx()
    return [
        pytest.param([[Blob.from_fork(fork)]], id="single_blob"),
        pytest.param(
            [[Blob.from_fork(fork, s) for s in range(max_blobs_per_tx)]],
            id="max_blobs_per_tx",
        ),
        pytest.param(
            [[Blob.from_fork(fork, s)] for s in range(2)],
            id="two_txs",
        ),
    ]


@pytest.mark.parametrize_by_fork("txs_blobs", frame_blob_cases)
def test_get_blobs_of_frame_txs(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    fork: Fork,
    txs_blobs: List[List[Blob]],
) -> None:
    """
    Submit blob-carrying frame transactions in their network wrapper and
    retrieve their blobs and cell proofs by versioned hash.
    """
    txs: List[NetworkWrappedTransaction | Transaction] = [
        network_wrapped(frame_tx_with_blobs(pre, blobs), blobs, fork)
        for blobs in txs_blobs
    ]
    blobs_test(pre=pre, txs=txs)


def test_get_blobs_of_frame_and_blob_txs(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Submit an EIP-4844 transaction and a blob-carrying frame transaction
    and retrieve the blobs of both in one request: the client serves frame
    transaction blobs from the same pool as EIP-4844 ones.
    """
    blob_tx_blobs = [Blob.from_fork(fork, 0)]
    frame_tx_blobs = [Blob.from_fork(fork, 1)]
    blob_tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.fund_eoa(amount=0),
        blob_versioned_hashes=[blob.versioned_hash for blob in blob_tx_blobs],
    )
    txs: List[NetworkWrappedTransaction | Transaction] = [
        network_wrapped(blob_tx, blob_tx_blobs, fork),
        network_wrapped(
            frame_tx_with_blobs(pre, frame_tx_blobs), frame_tx_blobs, fork
        ),
    ]
    blobs_test(pre=pre, txs=txs)


@pytest.mark.exception_test
def test_reject_frame_tx_network_wrapper_in_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reject a block whose body carries a blob-carrying frame transaction in
    its network wrapper: block bodies use the plain transaction payload, as
    for EIP-4844 transactions.
    """
    blobs = [Blob.from_fork(fork)]
    tx = frame_tx_with_blobs(pre, blobs).with_signature_and_sender()
    tx.rlp_override = network_wrapped(tx, blobs, fork).rlp()
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[tx],
                # The transition tool executes the plain transaction; only
                # the block's RLP carries the wrapper. A client rejects it
                # while decoding the body or, as for an EIP-4844
                # transaction, once it finds blobs attached to the decoded
                # transaction.
                exception=[
                    BlockException.RLP_STRUCTURES_ENCODING,
                    TransactionException.TYPE_3_TX_WITH_FULL_BLOBS,
                ],
                rlp_modifier=Header(
                    blob_gas_used=len(blobs) * fork.blob_gas_per_blob()
                ),
            )
        ],
    )
