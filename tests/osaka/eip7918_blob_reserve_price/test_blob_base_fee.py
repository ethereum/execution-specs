"""
[EIP-7918: Blob base fee bounded by execution cost](https://eips.ethereum.org/EIPS/eip-7918).

Test the blob base fee reserve price mechanism for
[EIP-7918: Blob base fee bounded by execution cost](https://eips.ethereum.org/EIPS/eip-7918).
"""

from typing import Any, Dict, Iterator, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Hash,
    Header,
    Op,
    Transaction,
    add_kzg_version,
)

from .spec import Spec, ref_spec_7918

REFERENCE_SPEC_GIT_PATH = ref_spec_7918.git_path
REFERENCE_SPEC_VERSION = ref_spec_7918.version

pytestmark = pytest.mark.valid_from("Osaka")


@pytest.fixture
def sender(pre: Alloc) -> Address:
    """Sender account with enough balance for tests."""
    return pre.fund_eoa(10**18)


@pytest.fixture
def destination_account(pre: Alloc) -> Address:
    """Contract that stores the blob base fee for verification."""
    code = Op.SSTORE(0, Op.BLOBBASEFEE)
    return pre.deploy_contract(code)


@pytest.fixture
def tx_gas() -> int:
    """Gas limit for transactions sent during test."""
    return 100_000


@pytest.fixture
def tx_value() -> int:
    """Value for transactions sent during test."""
    return 1


@pytest.fixture
def blob_hashes_per_tx(blobs_per_tx: int) -> List[Hash]:
    """Blob hashes for the transaction."""
    return add_kzg_version(
        [Hash(x) for x in range(blobs_per_tx)],
        Spec.BLOB_COMMITMENT_VERSION_KZG,
    )


@pytest.fixture
def tx(
    sender: Address,
    destination_account: Address,
    tx_gas: int,
    tx_value: int,
    blob_hashes_per_tx: List[Hash],
    block_base_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
) -> Transaction:
    """Blob transaction for the block."""
    return Transaction(
        ty=Spec.BLOB_TX_TYPE,
        sender=sender,
        to=destination_account,
        value=tx_value,
        gas_limit=tx_gas,
        max_fee_per_gas=block_base_fee_per_gas,
        max_priority_fee_per_gas=0,
        max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
        access_list=[],
        blob_versioned_hashes=blob_hashes_per_tx,
    )


@pytest.fixture
def block(
    tx: Transaction,
    fork: Fork,
    parent_excess_blobs: int,
    parent_blobs: int,
    block_base_fee_per_gas: int,
    blob_gas_per_blob: int,
) -> Block:
    """Single block fixture."""
    blob_count = (
        len(tx.blob_versioned_hashes) if tx.blob_versioned_hashes else 0
    )
    excess_blob_gas_calculator = fork.excess_blob_gas_calculator()
    expected_excess_blob_gas = excess_blob_gas_calculator(
        parent_excess_blobs=parent_excess_blobs,
        parent_blob_count=parent_blobs,
        parent_base_fee_per_gas=block_base_fee_per_gas,
    )
    return Block(
        txs=[tx],
        header_verify=Header(
            excess_blob_gas=expected_excess_blob_gas,
            blob_gas_used=blob_count * blob_gas_per_blob,
        ),
    )


@pytest.fixture
def post(
    destination_account: Address,
    blob_gas_price: int,
    tx_value: int,
) -> Dict[Address, Account]:
    """Post state storing the effective blob base fee."""
    return {
        destination_account: Account(
            storage={0: blob_gas_price},
            balance=tx_value,
        )
    }


@pytest.mark.parametrize(
    "block_base_fee_per_gas",
    [1, 7, 15, 16, 17, 100, 1000, 10000],
)
@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs",
    lambda fork: range(0, fork.target_blobs_per_block() + 1),
)
def test_reserve_price_various_base_fee_scenarios(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Alloc,
    block: Block,
    post: Dict[Address, Account],
) -> None:
    """
    Test reserve price mechanism across various block base fee and excess blob
    gas scenarios.
    """
    blockchain_test(
        pre=pre,
        post=post,
        blocks=[block],
        genesis_environment=env,
    )


def get_excess_blobs_for_blob_gas_price(fork: Fork, target_price: int) -> int:
    """Find minimum excess blobs to achieve a target blob gas price."""
    blob_gas_price_calculator = fork.blob_gas_price_calculator()
    gas_per_blob = fork.blob_gas_per_blob()
    excess_blobs = 0
    while True:
        excess_blob_gas = excess_blobs * gas_per_blob
        current_price = blob_gas_price_calculator(
            excess_blob_gas=excess_blob_gas
        )
        if current_price >= target_price:
            return excess_blobs
        excess_blobs += 1


def get_boundary_scenarios(fork: Fork) -> Iterator[Any]:
    """
    Generate boundary test scenarios including both low and high
    blob gas prices.

    The reserve price condition from EIP-7918 is:
        BLOB_BASE_COST * base_fee > GAS_PER_BLOB * blob_gas_price
        8192 * base_fee > 131072 * blob_gas_price
        base_fee > 16 * blob_gas_price

    The conftest calculates block_base_fee_per_gas as:
        base_fee = 8 * blob_gas_price + delta

    For equality (base_fee = 16 * blob_gas_price):
        8 * blob_gas_price + delta = 16 * blob_gas_price
        delta = 8 * blob_gas_price

    Tests the reserve price boundary at:
    - blob_gas_price = 1 (low excess blobs, various deltas around boundary)
    - blob_gas_price = 2, 3, 5, 10 (high excess blobs, delta set to hit exact
        equality where reserve_price == blob_gas_price)
    """
    # blob_gas_price = 1
    for excess_blobs in [
        0,
        3,
        fork.target_blobs_per_block(),
        fork.max_blobs_per_block(),
    ]:
        for delta in [-2, -1, 0, 1, 10, 100]:
            yield pytest.param(excess_blobs, delta)

    # blob_gas_price > 1
    for blob_target_price in [
        2,
        3,
        5,
        10,
        10**9,  # 1 Gwei
        10**11,  # 100 Gwei
    ]:
        excess_blobs = get_excess_blobs_for_blob_gas_price(
            fork, blob_target_price
        )
        blob_gas_price_calculator = fork.blob_gas_price_calculator()
        gas_per_blob = fork.blob_gas_per_blob()
        actual_price = blob_gas_price_calculator(
            excess_blob_gas=excess_blobs * gas_per_blob
        )
        delta = 8 * actual_price
        yield pytest.param(excess_blobs, delta)


@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs,block_base_fee_per_gas_delta",
    get_boundary_scenarios,
)
def test_reserve_price_boundary(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Alloc,
    block: Block,
    post: Dict[Address, Account],
) -> None:
    """
    Tests the reserve price boundary mechanism.

    The block base fee per gas is calculated as (8 * blob_base_fee) + delta,
    where 8 * blob_base_fee is the boundary at which reserve_price equals
    blob_gas_price.

    Tests include:
    - Low excess blob scenarios (blob_gas_price = 1) with various deltas
    - High blob gas price scenarios (2, 3, 5, 10) at exact equality boundary

    Example scenarios:
    - delta < 0: reserve inactive, effective_fee = blob_gas_price
    - delta = 0: equality boundary, reserve inactive (uses > not >=)
    - delta > 0: reserve active, effective_fee = reserve_price
    """
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[block],
        post=post,
    )
