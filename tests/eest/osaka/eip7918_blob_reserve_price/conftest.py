"""
Pytest (plugin) definitions local to EIP-7918 tests.

Mostly a copy of `tests/cancun/eip4844_blobs/conftest.py`.
"""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import Environment

from .spec import Spec


@pytest.fixture
def target_blobs_per_block(fork: Fork) -> int:
    """Return default number of target blobs per block."""
    return fork.target_blobs_per_block()


@pytest.fixture
def max_blobs_per_block(fork: Fork) -> int:
    """Return default number of max blobs per block."""
    return fork.max_blobs_per_block()


@pytest.fixture
def blob_gas_per_blob(fork: Fork) -> int:
    """Return default blob gas cost per blob."""
    return fork.blob_gas_per_blob()


@pytest.fixture(autouse=True)
def parent_excess_blobs() -> int | None:
    """
    Return default excess blobs of the parent block.

    Can be overloaded by a test case to provide a custom parent excess blob
    count.
    """
    return 10  # Defaults to a blob gas price of 1.


@pytest.fixture(autouse=True)
def parent_blobs() -> int | None:
    """
    Return default data blobs of the parent block.

    Can be overloaded by a test case to provide a custom parent blob count.
    """
    return 0


@pytest.fixture
def parent_excess_blob_gas(
    parent_excess_blobs: int | None,
    blob_gas_per_blob: int,
) -> int | None:
    """Calculate the excess blob gas of the parent block from the excess blobs."""
    if parent_excess_blobs is None:
        return None
    assert parent_excess_blobs >= 0
    return parent_excess_blobs * blob_gas_per_blob


@pytest.fixture
def blobs_per_tx() -> int:
    """
    Total number of blobs per transaction.

    Can be overloaded by a test case to provide a custom blobs per transaction count.
    """
    return 1


@pytest.fixture
def block_base_fee_per_gas_delta() -> int:
    """Delta to add to the block base fee. Default is 0."""
    return 0


@pytest.fixture
def block_base_fee_per_gas(
    fork: Fork,
    parent_excess_blobs: int | None,
    block_base_fee_per_gas_delta: int,
) -> int:
    """Block base fee per gas. Default is 7 unless a delta is provided or overloaded."""
    if block_base_fee_per_gas_delta != 0:
        if parent_excess_blobs is None:
            blob_base_fee = 1
        else:
            excess_blob_gas = parent_excess_blobs * fork.blob_gas_per_blob()
            blob_gas_price_calculator = fork.blob_gas_price_calculator()
            blob_base_fee = blob_gas_price_calculator(excess_blob_gas=excess_blob_gas)
        boundary_base_fee = 8 * blob_base_fee
        return boundary_base_fee + block_base_fee_per_gas_delta
    return 7


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
    return fork.excess_blob_gas_calculator()(
        parent_excess_blobs=parent_excess_blobs,
        parent_blob_count=parent_blobs,
        parent_base_fee_per_gas=block_base_fee_per_gas,
    )


@pytest.fixture
def correct_excess_blob_gas(
    fork: Fork,
    parent_excess_blobs: int | None,
    parent_blobs: int | None,
    block_base_fee_per_gas: int,
) -> int:
    """
    Calculate the correct excess blob gas of the block under test from the parent block.

    Should not be overloaded by a test case.
    """
    if parent_excess_blobs is None or parent_blobs is None:
        return 0
    return fork.excess_blob_gas_calculator()(
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
def correct_blob_gas_used(
    fork: Fork,
    blobs_per_tx: int,
) -> int:
    """Correct blob gas used by the test transaction."""
    return fork.blob_gas_per_blob() * blobs_per_tx


@pytest.fixture
def reserve_price(
    block_base_fee_per_gas: int,
) -> int:
    """Calculate the blob base fee reserve price for the current base fee."""
    return Spec.get_reserve_price(block_base_fee_per_gas)


@pytest.fixture
def is_reserve_price_active(
    block_base_fee_per_gas: int,
    blob_gas_price: int,
) -> bool:
    """Check if the reserve price mechanism should be active."""
    return Spec.is_reserve_price_active(block_base_fee_per_gas, blob_gas_price)


@pytest.fixture
def genesis_excess_blob_gas(
    parent_excess_blob_gas: int | None,
) -> int:
    """Return default excess blob gas for the genesis block."""
    return parent_excess_blob_gas if parent_excess_blob_gas else 0


@pytest.fixture
def env(
    block_base_fee_per_gas: int,
    genesis_excess_blob_gas: int,
) -> Environment:
    """Prepare the environment of the genesis block for all blockchain tests."""
    return Environment(
        excess_blob_gas=genesis_excess_blob_gas,
        blob_gas_used=0,
        base_fee_per_gas=block_base_fee_per_gas,
    )


@pytest.fixture
def tx_max_fee_per_blob_gas(blob_gas_price: int | None) -> int:
    """Max fee per blob gas based on actual blob gas price."""
    if blob_gas_price is None:
        return 1
    return blob_gas_price
