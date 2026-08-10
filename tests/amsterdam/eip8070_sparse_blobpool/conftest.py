"""Shared fixtures for building blob transactions in EIP-8070 tests."""

from typing import List, Optional

import pytest
from execution_testing import (
    Address,
    Alloc,
    Blob,
    Fork,
    NetworkWrappedTransaction,
    Transaction,
    TransactionException,
)


@pytest.fixture
def destination_account(pre: Alloc) -> Address:
    """Destination account for the blob transactions."""
    return pre.fund_eoa(amount=0)


@pytest.fixture
def tx_value() -> int:
    """Value contained by the transactions sent during test."""
    return 1


@pytest.fixture
def tx_gas(fork: Fork, tx_value: int) -> int:
    """Gas allocated to transactions sent during test."""
    return fork.transaction_intrinsic_cost_calculator()(
        sends_value=tx_value > 0
    )


@pytest.fixture
def block_base_fee_per_gas() -> int:
    """Return default max fee per gas for transactions sent during test."""
    return 7


@pytest.fixture
def tx_calldata() -> bytes:
    """Calldata in transactions sent during test."""
    return b""


@pytest.fixture(autouse=True)
def parent_excess_blobs() -> int:
    """Excess blobs of the parent block (defaults to a blob gas price of 1)."""
    return 10


@pytest.fixture(autouse=True)
def parent_blobs() -> int:
    """Blobs of the parent block."""
    return 0


@pytest.fixture
def excess_blob_gas(
    fork: Fork,
    parent_excess_blobs: int | None,
    parent_blobs: int | None,
    block_base_fee_per_gas: int,
) -> int | None:
    """Calculate the excess blob gas of the block under test."""
    if parent_excess_blobs is None or parent_blobs is None:
        return None
    excess_blob_gas = fork.excess_blob_gas_calculator()
    return excess_blob_gas(
        parent_excess_blobs=parent_excess_blobs,
        parent_blob_count=parent_blobs,
        parent_base_fee_per_gas=block_base_fee_per_gas,
    )


@pytest.fixture
def blob_gas_price(
    fork: Fork,
    excess_blob_gas: int | None,
) -> int | None:
    """Return blob gas price for the block of the test."""
    if excess_blob_gas is None:
        return None
    get_blob_gas_price = fork.blob_gas_price_calculator()
    return get_blob_gas_price(excess_blob_gas=excess_blob_gas)


@pytest.fixture
def txs_versioned_hashes(txs_blobs: List[List[Blob]]) -> List[List[bytes]]:
    """List of blob versioned hashes derived from the blobs."""
    return [[blob.versioned_hash for blob in blob_tx] for blob_tx in txs_blobs]


@pytest.fixture
def tx_max_fee_per_blob_gas(fork: Fork, blob_gas_price: Optional[int]) -> int:
    """Max fee per blob gas for transactions sent during test."""
    if blob_gas_price is None:
        return fork.min_base_fee_per_blob_gas()
    return blob_gas_price


@pytest.fixture
def tx_error() -> Optional[TransactionException]:
    """No transaction is expected to be rejected by the transition tool."""
    return None


@pytest.fixture(autouse=True)
def txs(
    pre: Alloc,
    destination_account: Optional[Address],
    tx_gas: int,
    tx_value: int,
    tx_calldata: bytes,
    tx_max_fee_per_blob_gas: int,
    txs_versioned_hashes: List[List[bytes]],
    tx_error: Optional[TransactionException],
    txs_blobs: List[List[Blob]],
    fork: Fork,
) -> List[NetworkWrappedTransaction | Transaction]:
    """Prepare the list of transactions that are sent during the test."""
    if len(txs_blobs) != len(txs_versioned_hashes):
        raise ValueError(
            "txs_blobs and txs_versioned_hashes should have the same length"
        )
    txs: List[NetworkWrappedTransaction | Transaction] = []
    for tx_blobs, tx_versioned_hashes in zip(
        txs_blobs, txs_versioned_hashes, strict=False
    ):
        tx = Transaction(
            sender=pre.fund_eoa(),
            to=destination_account,
            value=tx_value,
            gas_limit=tx_gas,
            data=tx_calldata,
            max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
            access_list=[],
            blob_versioned_hashes=tx_versioned_hashes,
            error=tx_error,
        )
        network_wrapped_tx = NetworkWrappedTransaction(
            tx=tx,
            blob_objects=tx_blobs,
            wrapper_version=fork.full_blob_tx_wrapper_version(),
        )
        txs.append(network_wrapped_tx)
    return txs
