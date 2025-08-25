"""
abstract: Tests `MAX_BLOBS_PER_TX` limit for [EIP-7594: PeerDAS - Peer Data Availability Sampling](https://eips.ethereum.org/EIPS/eip-7594)
    Tests `MAX_BLOBS_PER_TX` limit for [EIP-7594: PeerDAS - Peer Data Availability Sampling](https://eips.ethereum.org/EIPS/eip-7594).
"""  # noqa: E501

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
    add_kzg_version,
)

from .spec import Spec, ref_spec_7594

REFERENCE_SPEC_GIT_PATH = ref_spec_7594.git_path
REFERENCE_SPEC_VERSION = ref_spec_7594.version

FORK_TIMESTAMP = 15_000


@pytest.fixture
def env() -> Environment:
    """Environment fixture."""
    return Environment()


@pytest.fixture
def sender(pre: Alloc):
    """Sender account with sufficient balance for blob transactions."""
    return pre.fund_eoa(amount=10**18)


@pytest.fixture
def destination(pre: Alloc):
    """Destination account for blob transactions."""
    return pre.fund_eoa(amount=0)


@pytest.fixture
def blob_gas_price(fork: Fork) -> int:
    """Blob gas price for transactions."""
    return fork.min_base_fee_per_blob_gas()


@pytest.fixture
def tx(
    sender: Address,
    destination: Address,
    blob_gas_price: int,
    blob_count: int,
):
    """Blob transaction fixture."""
    return Transaction(
        ty=3,
        sender=sender,
        to=destination,
        value=1,
        gas_limit=21_000,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=1,
        max_fee_per_blob_gas=blob_gas_price,
        access_list=[],
        blob_versioned_hashes=add_kzg_version(
            [Hash(i) for i in range(0, blob_count)],
            Spec.BLOB_COMMITMENT_VERSION_KZG,
        ),
    )


@pytest.mark.parametrize_by_fork(
    "blob_count",
    lambda fork: list(range(1, fork.max_blobs_per_tx() + 1)),
)
@pytest.mark.valid_from("Osaka")
def test_valid_max_blobs_per_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    tx: Transaction,
):
    """
    Test that transactions with blob count from 1 to MAX_BLOBS_PER_TX are accepted.
    Verifies that individual transactions can contain up to the maximum allowed
    number of blobs per transaction.
    """
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post={},
    )


@pytest.mark.parametrize_by_fork(
    "blob_count",
    lambda fork: [
        fork.max_blobs_per_tx() + 1,
        fork.max_blobs_per_tx() + 2,
        fork.max_blobs_per_block(),
        fork.max_blobs_per_block() + 1,
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.exception_test
def test_invalid_max_blobs_per_tx(
    fork: Fork,
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    tx: Transaction,
    blob_count: int,
):
    """
    Test that transactions exceeding MAX_BLOBS_PER_TX are rejected.
    Verifies that individual transactions cannot contain more than the maximum
    allowed number of blobs per transaction, even if the total would be within
    the block limit.
    """
    state_test(
        env=env,
        pre=pre,
        tx=tx.with_error(
            TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
            if blob_count > fork.max_blobs_per_block()
            else TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED
        ),
        post={},
    )


@pytest.mark.parametrize_by_fork(
    "blob_count",
    lambda fork: [
        fork.max_blobs_per_tx(timestamp=FORK_TIMESTAMP) + 1,
        fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP) + 1,
    ],
)
@pytest.mark.valid_at_transition_to("Osaka")
@pytest.mark.exception_test
def test_max_blobs_per_tx_fork_transition(
    fork: Fork,
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Alloc,
    tx: Transaction,
    blob_count: int,
):
    """Test `MAX_BLOBS_PER_TX` limit enforcement across fork transition."""
    expected_exception = (
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        if blob_count > fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP)
        else TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED
    )
    pre_fork_block = Block(
        txs=[
            tx
            if blob_count < fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP - 1)
            else tx.with_error(expected_exception)
        ],
        timestamp=FORK_TIMESTAMP - 1,
        exception=None
        if blob_count < fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP - 1)
        else [expected_exception],
    )
    fork_block = Block(
        txs=[tx.with_nonce(1).with_error(expected_exception)],
        timestamp=FORK_TIMESTAMP,
        exception=[expected_exception],
    )
    post_fork_block = Block(
        txs=[tx.with_nonce(2).with_error(expected_exception)],
        timestamp=FORK_TIMESTAMP + 1,
        exception=[expected_exception],
    )
    blockchain_test(
        pre=pre,
        post={},
        blocks=[pre_fork_block, fork_block, post_fork_block],
        genesis_environment=env,
    )
