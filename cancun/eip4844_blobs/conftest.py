"""Pytest (plugin) definitions local to EIP-4844 tests."""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import Alloc, Block, Environment, Hash, Transaction, add_kzg_version

from .spec import Spec


@pytest.fixture
def block_base_fee_per_gas() -> int:
    """Return default max fee per gas for transactions sent during test."""
    return 7


@pytest.fixture
def target_blobs_per_block(fork: Fork) -> int:
    """Return default number of blobs to be included in the block."""
    return fork.target_blobs_per_block()


@pytest.fixture
def max_blobs_per_block(fork: Fork) -> int:
    """Return default number of blobs to be included in the block."""
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
    Return default data blobs of the parent blob.

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
def excess_blob_gas(
    fork: Fork,
    parent_excess_blobs: int | None,
    parent_blobs: int | None,
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
    )


@pytest.fixture
def correct_excess_blob_gas(
    fork: Fork,
    parent_excess_blobs: int | None,
    parent_blobs: int | None,
) -> int:
    """
    Calculate the correct excess blob gas of the block under test from the parent block.

    Should not be overloaded by a test case.
    """
    if parent_excess_blobs is None or parent_blobs is None:
        return 0
    excess_blob_gas = fork.excess_blob_gas_calculator()
    return excess_blob_gas(
        parent_excess_blobs=parent_excess_blobs,
        parent_blob_count=parent_blobs,
    )


@pytest.fixture
def block_fee_per_blob_gas(  # noqa: D103
    fork: Fork,
    correct_excess_blob_gas: int,
) -> int:
    get_blob_gas_price = fork.blob_gas_price_calculator()
    return get_blob_gas_price(excess_blob_gas=correct_excess_blob_gas)


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
def genesis_excess_blob_gas(
    parent_excess_blob_gas: int | None,
    parent_blobs: int,
    target_blobs_per_block: int,
    blob_gas_per_blob: int,
) -> int:
    """Return default excess blob gas for the genesis block."""
    excess_blob_gas = parent_excess_blob_gas if parent_excess_blob_gas else 0
    if parent_blobs:
        # We increase the excess blob gas of the genesis because
        # we cannot include blobs in the genesis, so the
        # test blobs are actually in block 1.
        excess_blob_gas += target_blobs_per_block * blob_gas_per_blob
    return excess_blob_gas


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
def tx_value() -> int:
    """
    Return default value contained by the transactions sent during test.

    Can be overloaded by a test case to provide a custom transaction value.
    """
    return 1


@pytest.fixture
def tx_calldata() -> bytes:
    """Return default calldata in transactions sent during test."""
    return b""


@pytest.fixture(autouse=True)
def tx_max_fee_per_gas(
    block_base_fee_per_gas: int,
) -> int:
    """
    Max fee per gas value used by all transactions sent during test.

    By default the max fee per gas is the same as the block fee per gas.

    Can be overloaded by a test case to test rejection of transactions where
    the max fee per gas is insufficient.
    """
    return block_base_fee_per_gas


@pytest.fixture
def tx_max_priority_fee_per_gas() -> int:
    """
    Return default max priority fee per gas for transactions sent during test.

    Can be overloaded by a test case to provide a custom max priority fee per
    gas.
    """
    return 0


@pytest.fixture
def tx_max_fee_per_blob_gas_multiplier() -> int:
    """
    Return default max fee per blob gas multiplier for transactions sent during test.

    Can be overloaded by a test case to provide a custom max fee per blob gas
    multiplier.
    """
    return 1


@pytest.fixture
def tx_max_fee_per_blob_gas_delta() -> int:
    """
    Return default max fee per blob gas delta for transactions sent during test.

    Can be overloaded by a test case to provide a custom max fee per blob gas
    delta.
    """
    return 0


@pytest.fixture
def tx_max_fee_per_blob_gas(  # noqa: D103
    blob_gas_price: int | None,
    tx_max_fee_per_blob_gas_multiplier: int,
    tx_max_fee_per_blob_gas_delta: int,
) -> int:
    """
    Return default max fee per blob gas for transactions sent during test.

    By default, it is set to the blob gas price of the block.

    Can be overloaded by a test case to test rejection of transactions where
    the max fee per blob gas is insufficient.
    """
    if blob_gas_price is None:
        # When fork transitioning, the default blob gas price is 1.
        return 1
    return (blob_gas_price * tx_max_fee_per_blob_gas_multiplier) + tx_max_fee_per_blob_gas_delta


@pytest.fixture
def non_zero_blob_gas_used_genesis_block(
    pre: Alloc,
    parent_blobs: int,
    fork: Fork,
    genesis_excess_blob_gas: int,
    parent_excess_blob_gas: int,
    tx_max_fee_per_gas: int,
    target_blobs_per_block: int,
) -> Block | None:
    """
    For test cases with a non-zero blobGasUsed field in the
    original genesis block header we must instead utilize an
    intermediate block to act on its behalf.

    Genesis blocks with a non-zero blobGasUsed field are invalid as
    they do not have any blob txs.

    For the intermediate block to align with default genesis values,
    we must add TARGET_BLOB_GAS_PER_BLOCK to the excessBlobGas of the
    genesis value, expecting an appropriate drop to the intermediate block.
    Similarly, we must add parent_blobs to the intermediate block within
    a blob tx such that an equivalent blobGasUsed field is wrote.
    """
    if parent_blobs == 0:
        return None

    excess_blob_gas_calculator = fork.excess_blob_gas_calculator(block_number=1)
    assert parent_excess_blob_gas == excess_blob_gas_calculator(
        parent_excess_blob_gas=genesis_excess_blob_gas,
        parent_blob_count=0,
    ), "parent excess blob gas is not as expected for extra block"

    sender = pre.fund_eoa(10**27)

    # Address that contains no code, nor balance and is not a contract.
    empty_account_destination = pre.fund_eoa(0)

    blob_gas_price_calculator = fork.blob_gas_price_calculator(block_number=1)

    return Block(
        txs=[
            Transaction(
                ty=Spec.BLOB_TX_TYPE,
                sender=sender,
                to=empty_account_destination,
                value=1,
                gas_limit=21_000,
                max_fee_per_gas=tx_max_fee_per_gas,
                max_priority_fee_per_gas=0,
                max_fee_per_blob_gas=blob_gas_price_calculator(
                    excess_blob_gas=parent_excess_blob_gas
                ),
                access_list=[],
                blob_versioned_hashes=add_kzg_version(
                    [Hash(x) for x in range(parent_blobs)],
                    Spec.BLOB_COMMITMENT_VERSION_KZG,
                ),
            )
        ]
    )
