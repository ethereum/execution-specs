"""
abstract: Tests `excessBlobGas` and `blobGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844) at fork transition.
    Test `excessBlobGas` and `blobGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844) at fork
    transition.
"""  # noqa: E501

from typing import List, Mapping

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    EngineAPIError,
    Environment,
    Hash,
    Header,
    Transaction,
    add_kzg_version,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

# Timestamp of the fork
FORK_TIMESTAMP = 15_000
BASE_FEE_MAX_CHANGE_DENOMINATOR = 8


@pytest.fixture
def block_gas_limit(fork: Fork) -> int:  # noqa: D103
    gas_limit = int(Environment().gas_limit)
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    if tx_gas_limit_cap is not None:
        # Below transaction gas limit cap to reach gas limit easily
        gas_limit = min(gas_limit, tx_gas_limit_cap * 2)
    return gas_limit


@pytest.fixture
def genesis_environment(block_gas_limit: int, block_base_fee_per_gas: int) -> Environment:  # noqa: D103
    return Environment(
        base_fee_per_gas=(block_base_fee_per_gas * BASE_FEE_MAX_CHANGE_DENOMINATOR) // 7,
        gas_limit=block_gas_limit,
    )


@pytest.fixture
def pre_fork_blobs_per_block(fork: Fork) -> int:
    """Amount of blobs to produce with the pre-fork rules."""
    if fork.supports_blobs(timestamp=0):
        return fork.max_blobs_per_block(timestamp=0)
    return 0


@pytest.fixture
def post_fork_blobs_per_block(fork: Fork) -> int:
    """Amount of blobs to produce with the post-fork rules."""
    return fork.target_blobs_per_block(timestamp=FORK_TIMESTAMP) + 1


@pytest.fixture
def pre_fork_blocks(
    pre_fork_blobs_per_block: int,
    destination_account: Address,
    gas_spender_account: Address,
    sender: EOA,
    fork: Fork,
    block_base_fee_per_gas: int,
    block_gas_limit: int,
) -> List[Block]:
    """Generate blocks to reach the fork."""
    blocks = []

    for t in range(999, FORK_TIMESTAMP, 1_000):
        remaining_gas = block_gas_limit // 2
        if pre_fork_blobs_per_block == 0:
            blocks.append(
                Block(
                    txs=[
                        Transaction(
                            to=gas_spender_account,
                            value=0,
                            gas_limit=remaining_gas,
                            max_fee_per_gas=1_000_000,
                            max_priority_fee_per_gas=10,
                            sender=sender,
                        )
                    ],
                    timestamp=t,
                )
            )
            continue

        # Split into multi txs for forks where max per tx < max per block
        txs = []
        blob_index = 0
        remaining_blobs = pre_fork_blobs_per_block
        max_blobs_per_tx = fork.max_blobs_per_tx(timestamp=0)

        while remaining_blobs > 0:
            tx_blobs = min(remaining_blobs, max_blobs_per_tx)
            blob_tx_gas_limit = 21_000
            txs.append(
                Transaction(
                    ty=Spec.BLOB_TX_TYPE,
                    to=destination_account,
                    value=1,
                    gas_limit=blob_tx_gas_limit,
                    max_fee_per_gas=1_000_000,
                    max_priority_fee_per_gas=10,
                    max_fee_per_blob_gas=100,
                    access_list=[],
                    blob_versioned_hashes=add_kzg_version(
                        [Hash(blob_index + x) for x in range(tx_blobs)],
                        Spec.BLOB_COMMITMENT_VERSION_KZG,
                    ),
                    sender=sender,
                )
            )
            remaining_gas -= blob_tx_gas_limit
            blob_index += tx_blobs
            remaining_blobs -= tx_blobs
        txs.append(
            Transaction(
                to=gas_spender_account,
                value=0,
                gas_limit=remaining_gas,
                max_fee_per_gas=1_000_000,
                max_priority_fee_per_gas=10,
                sender=sender,
            )
        )
        block = Block(
            txs=txs, timestamp=t, header_verify=Header(base_fee_per_gas=block_base_fee_per_gas)
        )
        blocks.append(block)
    return blocks


@pytest.fixture
def pre_fork_excess_blobs(
    fork: Fork,
    pre_fork_blobs_per_block: int,
    pre_fork_blocks: List[Block],
) -> int:
    """
    Return the cumulative excess blobs up until the fork given the pre_fork_blobs_per_block
    and the target blobs in the fork prior.
    """
    if not fork.supports_blobs(timestamp=0):
        return 0

    target_blobs = fork.target_blobs_per_block(timestamp=0)
    if pre_fork_blobs_per_block > target_blobs:
        return (pre_fork_blobs_per_block - target_blobs) * (len(pre_fork_blocks) - 1)
    return 0


@pytest.fixture
def post_fork_block_count(fork: Fork) -> int:
    """Amount of blocks to produce with the post-fork rules."""
    return SpecHelpers.get_min_excess_blobs_for_blob_gas_price(fork=fork, blob_gas_price=2) // (
        fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP)
        - fork.target_blobs_per_block(timestamp=FORK_TIMESTAMP)
    )


@pytest.fixture
def destination_account(pre: Alloc) -> Address:  # noqa: D103
    # Empty account to receive the blobs
    return pre.fund_eoa(amount=0)


@pytest.fixture
def gas_spender_account(pre: Alloc) -> Address:  # noqa: D103
    # Account that when called consumes the entirety of the transaction's gas
    return pre.deploy_contract(code=Op.INVALID)


@pytest.fixture
def fork_block_excess_blob_gas(
    fork: Fork,
    pre_fork_excess_blobs: int,
    pre_fork_blobs_per_block: int,
    block_base_fee_per_gas: int,
) -> int:
    """Calculate the expected excess blob gas for the fork block."""
    if pre_fork_blobs_per_block == 0:
        return 0
    calc_excess_blob_gas_post_fork = fork.excess_blob_gas_calculator(timestamp=FORK_TIMESTAMP)
    return calc_excess_blob_gas_post_fork(
        parent_excess_blobs=pre_fork_excess_blobs,
        parent_blob_count=pre_fork_blobs_per_block,
        parent_base_fee_per_gas=block_base_fee_per_gas,
    )


@pytest.fixture
def post_fork_blocks(
    destination_account: Address,
    post_fork_block_count: int,
    post_fork_blobs_per_block: int,
    fork_block_excess_blob_gas: int,
    sender: EOA,
    pre_fork_blocks: List[Block],
    fork: Fork,
):
    """Generate blocks after the fork."""
    blocks = []

    for i in range(post_fork_block_count):
        if post_fork_blobs_per_block == 0:
            if i == 0:
                blocks.append(
                    Block(
                        txs=[],
                        header_verify=Header(
                            excess_blob_gas=fork_block_excess_blob_gas,
                        ),
                    )
                )
            else:
                blocks.append(Block(txs=[]))
            continue

        # Split into multi txs for forks where max per tx < max per block
        txs = []
        blob_index = 0
        remaining_blobs = post_fork_blobs_per_block
        max_blobs_per_tx = fork.max_blobs_per_tx(timestamp=FORK_TIMESTAMP)
        while remaining_blobs > 0:
            tx_blobs = min(remaining_blobs, max_blobs_per_tx)
            txs.append(
                Transaction(
                    ty=Spec.BLOB_TX_TYPE,
                    to=destination_account,
                    value=1,
                    gas_limit=100_000,
                    max_fee_per_gas=1_000_000,
                    max_priority_fee_per_gas=10,
                    max_fee_per_blob_gas=100,
                    blob_versioned_hashes=add_kzg_version(
                        [Hash(blob_index + x) for x in range(tx_blobs)],
                        Spec.BLOB_COMMITMENT_VERSION_KZG,
                    ),
                    sender=sender,
                )
            )
            blob_index += tx_blobs
            remaining_blobs -= tx_blobs

        if i == 0:
            blocks.append(
                Block(
                    txs=txs,
                    header_verify=Header(
                        excess_blob_gas=fork_block_excess_blob_gas,
                    ),
                )
            )
        else:
            blocks.append(Block(txs=txs))

    return blocks


@pytest.fixture
def post(  # noqa: D103
    pre_fork_blocks: List[Block],
    pre_fork_blobs_per_block: int,
    post_fork_block_count: int,
    post_fork_blobs_per_block: int,
    destination_account: Address,
    fork: Fork,
) -> Mapping[Address, Account]:
    pre_fork_tx_count_per_block = 0
    if pre_fork_blobs_per_block > 0:
        max_blobs_per_tx_pre = fork.max_blobs_per_tx(timestamp=0)
        pre_fork_tx_count_per_block = (
            pre_fork_blobs_per_block + max_blobs_per_tx_pre - 1
        ) // max_blobs_per_tx_pre

    post_fork_tx_count_per_block = 0
    if post_fork_blobs_per_block > 0:
        max_blobs_per_tx_post = fork.max_blobs_per_tx(timestamp=FORK_TIMESTAMP)
        post_fork_tx_count_per_block = (
            post_fork_blobs_per_block + max_blobs_per_tx_post - 1
        ) // max_blobs_per_tx_post

    pre_fork_value = len(pre_fork_blocks) * pre_fork_tx_count_per_block
    post_fork_value = post_fork_block_count * post_fork_tx_count_per_block
    total_value = pre_fork_value + post_fork_value

    if total_value == 0:
        return {}
    return {
        destination_account: Account(balance=total_value),
    }


@pytest.mark.valid_at_transition_to("Cancun", subsequent_forks=False)
@pytest.mark.parametrize(
    "excess_blob_gas_present,blob_gas_used_present",
    [
        (True, False),
        (False, True),
        (True, True),
    ],
)
@pytest.mark.exception_test
def test_invalid_pre_fork_block_with_blob_fields(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Alloc,
    pre_fork_blocks: List[Block],
    excess_blob_gas_present: bool,
    blob_gas_used_present: bool,
):
    """
    Test block rejection when `excessBlobGas` and/or `blobGasUsed` fields are present on a pre-fork
    block.

    Blocks sent by NewPayloadV2 (Shanghai) that contain `excessBlobGas` and `blobGasUsed` fields
    must be rejected with the appropriate `EngineAPIError.InvalidParams` error error.
    """
    header_modifier = Header(
        excess_blob_gas=0 if excess_blob_gas_present else None,
        blob_gas_used=0 if blob_gas_used_present else None,
    )
    blockchain_test(
        pre=pre,
        post={},
        blocks=pre_fork_blocks[:-1]
        + [
            Block(
                timestamp=(FORK_TIMESTAMP - 1),
                rlp_modifier=header_modifier,
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                engine_api_error_code=EngineAPIError.InvalidParams,
            )
        ],
        genesis_environment=env,
    )


@pytest.mark.valid_at_transition_to("Cancun", subsequent_forks=False)
@pytest.mark.parametrize(
    "excess_blob_gas_missing,blob_gas_used_missing",
    [
        (True, False),
        (False, True),
        (True, True),
    ],
)
@pytest.mark.exception_test
def test_invalid_post_fork_block_without_blob_fields(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Alloc,
    pre_fork_blocks: List[Block],
    excess_blob_gas_missing: bool,
    blob_gas_used_missing: bool,
):
    """
    Test block rejection when `excessBlobGas` and/or `blobGasUsed` fields are missing on a
    post-fork block.

    Blocks sent by NewPayloadV3 (Cancun) without `excessBlobGas` and `blobGasUsed` fields must be
    rejected with the appropriate `EngineAPIError.InvalidParams` error.
    """
    header_modifier = Header()
    if excess_blob_gas_missing:
        header_modifier.excess_blob_gas = Header.REMOVE_FIELD
    if blob_gas_used_missing:
        header_modifier.blob_gas_used = Header.REMOVE_FIELD
    blockchain_test(
        pre=pre,
        post={},
        blocks=pre_fork_blocks
        + [
            Block(
                timestamp=FORK_TIMESTAMP,
                rlp_modifier=header_modifier,
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                engine_api_error_code=EngineAPIError.InvalidParams,
            )
        ],
        genesis_environment=env,
    )


@pytest.mark.valid_at_transition_to("Cancun", subsequent_forks=False)
@pytest.mark.parametrize_by_fork(
    "post_fork_block_count,post_fork_blobs_per_block",
    lambda fork: [
        pytest.param(
            SpecHelpers.get_min_excess_blobs_for_blob_gas_price(fork=fork, blob_gas_price=2)
            // (
                fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP)
                - fork.target_blobs_per_block(timestamp=FORK_TIMESTAMP)
            )
            + 2,
            fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP),
            id="max_blobs",
        ),
        pytest.param(10, 0, id="no_blobs"),
        pytest.param(10, fork.target_blobs_per_block(timestamp=FORK_TIMESTAMP), id="target_blobs"),
    ],
)
def test_fork_transition_excess_blob_gas_at_blob_genesis(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Alloc,
    pre_fork_blocks: List[Block],
    post_fork_blocks: List[Block],
    post: Mapping[Address, Account],
):
    """
    Test `excessBlobGas` calculation in the header when the fork is activated.

    Also produce enough blocks to test the blob gas price increase when the block is full with
    `SpecHelpers.max_blobs_per_block()` blobs.
    """
    blockchain_test(
        pre=pre,
        post=post,
        blocks=pre_fork_blocks + post_fork_blocks,
        genesis_environment=env,
    )


@pytest.mark.valid_at_transition_to("Prague", subsequent_forks=True)
@pytest.mark.parametrize_by_fork(
    "post_fork_block_count,pre_fork_blobs_per_block,post_fork_blobs_per_block",
    lambda fork: [
        pytest.param(
            SpecHelpers.get_min_excess_blobs_for_blob_gas_price(fork=fork, blob_gas_price=2)
            // (
                fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP)
                - fork.target_blobs_per_block(timestamp=FORK_TIMESTAMP)
            )
            + 2,
            fork.max_blobs_per_block(timestamp=0),
            fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP),
            id="max_blobs_before_and_after",
        ),
        pytest.param(
            10,
            0,
            fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP),
            id="no_blobs_before_and_max_blobs_after",
        ),
        pytest.param(
            10,
            fork.max_blobs_per_block(timestamp=0),
            0,
            id="max_blobs_before_and_no_blobs_after",
        ),
        pytest.param(
            10,
            fork.target_blobs_per_block(timestamp=0),
            fork.target_blobs_per_block(timestamp=FORK_TIMESTAMP),
            id="target_blobs_before_and_after",
        ),
        pytest.param(
            10,
            1,
            fork.max_blobs_per_block(timestamp=FORK_TIMESTAMP),
            id="single_blob_before_and_max_blobs_after",
        ),
        pytest.param(
            10,
            fork.max_blobs_per_block(timestamp=0),
            1,
            id="max_blobs_before_and_single_blob_after",
        ),
    ],
)
@pytest.mark.parametrize("block_base_fee_per_gas", [7, 16, 23])
def test_fork_transition_excess_blob_gas_post_blob_genesis(
    blockchain_test: BlockchainTestFiller,
    genesis_environment: Environment,
    pre: Alloc,
    pre_fork_blocks: List[Block],
    post_fork_blocks: List[Block],
    post: Mapping[Address, Account],
):
    """Test `excessBlobGas` calculation in the header when the fork is activated."""
    blockchain_test(
        pre=pre,
        post=post,
        blocks=pre_fork_blocks + post_fork_blocks,
        genesis_environment=genesis_environment,
    )
