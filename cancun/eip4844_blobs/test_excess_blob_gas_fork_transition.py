"""
abstract: Tests `excessBlobGas` and `blobGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844) at fork transition.
    Test `excessBlobGas` and `blobGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844) at fork
    transition.
"""  # noqa: E501
from typing import List, Mapping

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    BlockException,
    EngineAPIError,
    Environment,
    Hash,
    Header,
    TestAddress,
    Transaction,
    add_kzg_version,
)

from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

# All tests run on the transition fork from Shanghai to Cancun
pytestmark = pytest.mark.valid_at_transition_to("Cancun")


# Timestamp of the fork
FORK_TIMESTAMP = 15_000


@pytest.fixture
def env() -> Environment:  # noqa: D103
    return Environment()


@pytest.fixture
def pre() -> Mapping[Address, Account]:  # noqa: D103
    return {
        TestAddress: Account(balance=10**40),
    }


@pytest.fixture
def pre_fork_blocks():
    """
    Generates blocks to reach the fork.
    """
    return [Block(timestamp=t) for t in range(999, FORK_TIMESTAMP, 1_000)]


@pytest.fixture
def post_fork_block_count() -> int:
    """
    Amount of blocks to produce with the post-fork rules.
    """
    return SpecHelpers.get_min_excess_blobs_for_blob_gas_price(2) // (
        SpecHelpers.max_blobs_per_block() - SpecHelpers.target_blobs_per_block()
    )


@pytest.fixture
def blob_count_per_block() -> int:
    """
    Amount of blocks to produce with the post-fork rules.
    """
    return 4


@pytest.fixture
def destination_account() -> Address:  # noqa: D103
    return Address(0x100)


@pytest.fixture
def post_fork_blocks(
    destination_account: Address,
    post_fork_block_count: int,
    blob_count_per_block: int,
):
    """
    Generates blocks past the fork.
    """
    return [
        Block(
            txs=[
                Transaction(
                    ty=Spec.BLOB_TX_TYPE,
                    nonce=b,
                    to=destination_account,
                    value=1,
                    gas_limit=3000000,
                    max_fee_per_gas=1000000,
                    max_priority_fee_per_gas=10,
                    max_fee_per_blob_gas=100,
                    access_list=[],
                    blob_versioned_hashes=add_kzg_version(
                        [Hash(x) for x in range(blob_count_per_block)],
                        Spec.BLOB_COMMITMENT_VERSION_KZG,
                    ),
                )
                if blob_count_per_block > 0
                else Transaction(
                    ty=2,
                    nonce=b,
                    to=destination_account,
                    value=1,
                    gas_limit=3000000,
                    max_fee_per_gas=1000000,
                    max_priority_fee_per_gas=10,
                    access_list=[],
                )
            ],
        )
        for b in range(post_fork_block_count)
    ]


@pytest.fixture
def post(  # noqa: D103
    post_fork_block_count: int,
    destination_account: Address,
) -> Mapping[Address, Account]:
    return {
        destination_account: Account(balance=post_fork_block_count),
    }


@pytest.mark.parametrize(
    "excess_blob_gas_present,blob_gas_used_present",
    [
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_invalid_pre_fork_block_with_blob_fields(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
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
        tag="invalid_pre_fork_blob_fields",
    )


@pytest.mark.parametrize(
    "excess_blob_gas_missing,blob_gas_used_missing",
    [
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_invalid_post_fork_block_without_blob_fields(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
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
        tag="blob_fields_missing_post_fork",
    )


@pytest.mark.parametrize(
    "post_fork_block_count,blob_count_per_block",
    [
        (
            SpecHelpers.get_min_excess_blobs_for_blob_gas_price(2)
            // (SpecHelpers.max_blobs_per_block() - SpecHelpers.target_blobs_per_block())
            + 2,
            SpecHelpers.max_blobs_per_block(),
        ),
        (10, 0),
        (10, SpecHelpers.target_blobs_per_block()),
    ],
    ids=["max_blobs", "no_blobs", "target_blobs"],
)
def test_fork_transition_excess_blob_gas(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
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
        tag="correct_initial_blob_gas_calc",
    )
