"""Shared helpers for the EIP-8198 tests."""

from typing import List

from execution_testing import (
    Address,
    Alloc,
    Fork,
    Hash,
    Op,
    Transaction,
    TransactionException,
    add_kzg_version,
)

from .spec import Spec

BLOCK_GAS_LIMIT = 30_000_000
"""
Block gas limit used by the base fee and gas limit tests.

Its gas target lies below the transaction gas limit cap, so a single
transaction can bring a block to its target, and two can fill it.
"""

MAX_FEE_PER_GAS = 10**12
"""Maximum fee per gas that covers every base fee the tests reach."""

BLOB_COUNT_ERRORS = [
    TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED,
    TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
]
"""Errors a block or transaction over the blob limit may be rejected with."""


def gas_spending_transactions(
    *,
    pre: Alloc,
    sender: Address,
    fork: Fork,
    gas: int,
) -> List[Transaction]:
    """
    Return transactions that together use exactly `gas`.

    Each transaction calls a contract that halts exceptionally, which consumes
    all of the transaction's gas.
    """
    if gas == 0:
        return []
    gas_spender = pre.deploy_contract(code=Op.INVALID)
    cap = fork.transaction_gas_limit_cap() or gas
    chunks = []
    remaining = gas
    while remaining > 0:
        chunk = min(remaining, cap)
        chunks.append(chunk)
        remaining -= chunk
    return [
        Transaction(
            to=gas_spender,
            gas_limit=chunk,
            max_fee_per_gas=MAX_FEE_PER_GAS,
            max_priority_fee_per_gas=0,
            sender=sender,
        )
        for chunk in chunks
    ]


def blob_transactions(
    *,
    sender: Address,
    destination: Address,
    fork: Fork,
    blob_count: int,
    max_fee_per_blob_gas: int,
    first_blob_index: int = 0,
    error: TransactionException | List[TransactionException] | None = None,
) -> List[Transaction]:
    """
    Return blob transactions carrying `blob_count` blobs in total, split so
    that no transaction exceeds the fork's per-transaction blob limit.

    When `error` is set, it is attached to the last transaction.
    """
    max_blobs_per_tx = fork.max_blobs_per_tx()
    counts = []
    remaining = blob_count
    while remaining > 0:
        counts.append(min(remaining, max_blobs_per_tx))
        remaining -= counts[-1]
    txs = []
    blob_index = first_blob_index
    for i, tx_blobs in enumerate(counts):
        txs.append(
            Transaction(
                ty=Spec.BLOB_TX_TYPE,
                to=destination,
                value=1,
                max_fee_per_gas=MAX_FEE_PER_GAS,
                max_priority_fee_per_gas=0,
                max_fee_per_blob_gas=max_fee_per_blob_gas,
                blob_versioned_hashes=add_kzg_version(
                    [Hash(blob_index + j) for j in range(tx_blobs)],
                    Spec.BLOB_COMMITMENT_VERSION_KZG,
                ),
                sender=sender,
                error=error if i == len(counts) - 1 else None,
            )
        )
        blob_index += tx_blobs
    return txs
