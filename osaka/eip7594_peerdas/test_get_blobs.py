"""
abstract: Tests get blobs engine endpoint for [EIP-7594: PeerDAS - Peer Data Availability Sampling](https://eips.ethereum.org/EIPS/eip-7594)
    Test get blobs engine endpoint for [EIP-7594: PeerDAS - Peer Data Availability Sampling](https://eips.ethereum.org/EIPS/eip-7594).
"""  # noqa: E501

from typing import List, Optional

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Address,
    Alloc,
    Blob,
    BlobsTestFiller,
    NetworkWrappedTransaction,
    Transaction,
    TransactionException,
)
from pytest_plugins.logging import get_logger

from .spec import ref_spec_7594

REFERENCE_SPEC_GIT_PATH = ref_spec_7594.git_path
REFERENCE_SPEC_VERSION = ref_spec_7594.version

logger = get_logger(__name__)


@pytest.fixture
def destination_account(pre: Alloc) -> Address:
    """Destination account for the blob transactions."""
    return pre.fund_eoa(amount=0)


@pytest.fixture
def tx_value() -> int:
    """
    Value contained by the transactions sent during test.

    Can be overloaded by a test case to provide a custom transaction value.
    """
    return 1


@pytest.fixture
def tx_gas() -> int:
    """Gas allocated to transactions sent during test."""
    return 21_000


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
    """
    Excess blobs of the parent block.

    Can be overloaded by a test case to provide a custom parent excess blob
    count.
    """
    return 10  # Defaults to a blob gas price of 1.


@pytest.fixture(autouse=True)
def parent_blobs() -> int:
    """
    Blobs of the parent blob.

    Can be overloaded by a test case to provide a custom parent blob count.
    """
    return 0


@pytest.fixture
def excess_blob_gas(
    fork: Fork,
    parent_excess_blobs: int | None,
    parent_blobs: int | None,
    block_base_fee_per_gas: int,
) -> int | None:
    """
    Calculate the excess blob gas of the block under test from the parent block.

    Value can be overloaded by a test case to provide a custom excess blob gas.
    """
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
    return get_blob_gas_price(
        excess_blob_gas=excess_blob_gas,
    )


@pytest.fixture
def txs_versioned_hashes(txs_blobs: List[List[Blob]]) -> List[List[bytes]]:
    """List of blob versioned hashes derived from the blobs."""
    return [[blob.versioned_hash for blob in blob_tx] for blob_tx in txs_blobs]


@pytest.fixture
def tx_max_fee_per_blob_gas(  # noqa: D103
    blob_gas_price: Optional[int],
) -> int:
    """
    Max fee per blob gas for transactions sent during test.

    By default, it is set to the blob gas price of the block.

    Can be overloaded by a test case to test rejection of transactions where
    the max fee per blob gas is insufficient.
    """
    if blob_gas_price is None:
        # When fork transitioning, the default blob gas price is 1.
        return 1
    return blob_gas_price


@pytest.fixture
def tx_error() -> Optional[TransactionException]:
    """
    Even though the final block we are producing in each of these tests is invalid, and some of the
    transactions will be invalid due to the format in the final block, none of the transactions
    should be rejected by the transition tool because they are being sent to it with the correct
    format.
    """
    return None


@pytest.fixture(autouse=True)
def txs(  # noqa: D103
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
        raise ValueError("txs_blobs and txs_versioned_hashes should have the same length")
    txs: List[NetworkWrappedTransaction | Transaction] = []
    for tx_blobs, tx_versioned_hashes in zip(txs_blobs, txs_versioned_hashes, strict=False):
        tx = Transaction(
            # type=3,
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


def generate_valid_blob_tests(
    fork: Fork,
) -> List:
    """
    Return a list of the 8 most important tests for valid blob transactions
    parametrized for each different fork.
    """
    max_blobs_per_block = fork.max_blobs_per_block()
    max_blobs_per_tx = fork.max_blobs_per_tx()
    target_blobs_per_block = fork.target_blobs_per_block()

    logger.debug(f"MAX_BLOBS_PER_BLOCK value for fork {fork}: {max_blobs_per_block}")
    logger.debug(f"MAX_BLOBS_PER_TX value for fork {fork}: {max_blobs_per_tx}")
    logger.debug(f"TARGET_BLOBS_PER_BLOCK value for fork {fork}: {target_blobs_per_block}")

    # Calculate ascending pattern that fits within target_blobs_per_block
    ascending_txs = []
    total_blobs = 0
    blob_offset = 0

    for tx_size in range(1, max_blobs_per_tx + 1):
        if total_blobs + tx_size <= target_blobs_per_block:
            ascending_txs.append([Blob.from_fork(fork, blob_offset + j) for j in range(tx_size)])
            total_blobs += tx_size
            blob_offset += tx_size
        else:
            break

    return [
        # Basic single blob transaction
        pytest.param(
            [  # Txs
                [  # Blobs per transaction
                    Blob.from_fork(fork),
                ]
            ],
            id="single_blob_transaction",
        ),
        # Max blobs per transaction (single tx with max blobs)
        pytest.param(
            [[Blob.from_fork(fork, s) for s in range(max_blobs_per_tx)]],
            id="max_blobs_per_tx",
        ),
        # Max blobs per block distributed across multiple txs
        pytest.param(
            [
                [
                    Blob.from_fork(fork, s),
                ]
                for s in range(max_blobs_per_block)
            ],
            id="max_blobs_per_block",
        ),
        # Target blobs per block distributed across multiple txs
        pytest.param(
            [
                [
                    Blob.from_fork(fork, s),
                ]
                for s in range(target_blobs_per_block)
            ],
            id="target_blobs_per_block",
        ),
        # Two transactions with equal blob distribution
        pytest.param(
            [
                [Blob.from_fork(fork, s) for s in range(target_blobs_per_block // 2)],
                [
                    Blob.from_fork(fork, s + target_blobs_per_block // 2)
                    for s in range(target_blobs_per_block // 2)
                ],
            ],
            id="two_tx_equal_blobs",
        ),
        # Three transactions with equal blob distribution
        pytest.param(
            [
                [Blob.from_fork(fork, s) for s in range(target_blobs_per_block // 3)],
                [
                    Blob.from_fork(fork, s + target_blobs_per_block // 3)
                    for s in range(target_blobs_per_block // 3)
                ],
                [
                    Blob.from_fork(fork, s + 2 * (target_blobs_per_block // 3))
                    for s in range(target_blobs_per_block // 3)
                ],
            ],
            id="three_tx_equal_blobs",
        ),
        # Mixed distribution: one max tx + remaining as singles
        pytest.param(
            [  # Txs
                [  # First tx with max blobs
                    Blob.from_fork(fork, s) for s in range(max_blobs_per_tx)
                ]
            ]
            + [
                [  # Remaining txs with 1 blob each
                    Blob.from_fork(fork, max_blobs_per_tx + s),
                ]
                for s in range(max_blobs_per_block - max_blobs_per_tx)
            ],
            id="mixed_max_tx_plus_singles",
        ),
        # Ascending pattern: 1, 2, 3... blobs per tx
        pytest.param(
            ascending_txs,
            id="ascending_blob_pattern",
        ),
    ]


@pytest.mark.parametrize_by_fork(
    "txs_blobs",
    generate_valid_blob_tests,
)
@pytest.mark.exception_test
@pytest.mark.valid_from("Cancun")
def test_get_blobs(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    txs: List[NetworkWrappedTransaction | Transaction],
):
    """
    Test valid blob combinations where one or more txs in the block
    serialized version contain a full blob (network version) tx.
    """
    blobs_test(
        pre=pre,
        txs=txs,
    )
