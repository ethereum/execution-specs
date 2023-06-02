"""
Test EIP-4844: BLOBHASH Opcode
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""

import itertools

import pytest

from ethereum_test_forks import Cancun, forks_from
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    CodeGasMeasure,
    Environment,
    TestAddress,
    Transaction,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .blobhash_util import (
    BLOBHASH_GAS_COST,
    MAX_BLOB_PER_BLOCK,
    TARGET_BLOB_PER_BLOCK,
    BlobhashScenario,
    blobhash_index_values,
    random_blob_hashes,
)

pytestmark = pytest.mark.parametrize("fork", forks_from(Cancun))

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"


@pytest.fixture(params=blobhash_index_values, ids=lambda x: f"index={hex(x)}")
def blobhash_index(request):
    """
    Fixture that provides a set of parameterized blobhash index values.
    Display in hex format for better readability.
    """
    return request.param


@pytest.fixture
def env():  # noqa: D103
    return Environment()


@pytest.fixture
def pre():  # noqa: D103
    return {TestAddress: Account(balance=10000000000000000000000)}


@pytest.fixture
def post():  # noqa: D103
    return {}


@pytest.fixture
def blocks():  # noqa: D103
    return []


@pytest.fixture
def template_tx():  # noqa: D103
    return Transaction(
        data=to_hash_bytes(0),
        gas_limit=3000000,
        max_fee_per_gas=10,
        max_fee_per_data_gas=10,
    )


@pytest.fixture
def blob_tx(template_tx):
    """
    Blob transaction factory fixture.
    Used to define blob txs with a specified to address, nonce & type.
    """

    def _blob_tx(address, type, nonce):
        return template_tx.with_fields(
            ty=type,
            nonce=nonce,
            to=address,
            access_list=[],
            max_priority_fee_per_gas=10,
            blob_versioned_hashes=random_blob_hashes[0:MAX_BLOB_PER_BLOCK],
        )

    return _blob_tx


@pytest.mark.parametrize("tx_type", [0, 1, 2, 3])
def test_blobhash_gas_cost(
    env,
    pre,
    template_tx,
    blocks,
    post,
    tx_type,
    blobhash_index,
    blockchain_test: BlockchainTestFiller,
):
    """
    Test BLOBHASH opcode gas cost using a variety of indexes.

    Asserts the gas consumption of the BLOBHASH opcode is correct by ensuring
    it matches `HASH_OPCODE_GAS = 3`. Includes both valid and invalid random
    index sizes from the range `[0, 2**256-1]`, for tx types 2 and 3.
    """
    gas_measures_code = CodeGasMeasure(
        code=Op.BLOBHASH(blobhash_index),
        overhead_cost=3,
        extra_stack_items=1,
    )
    address = to_address(0x100)
    pre[address] = Account(code=gas_measures_code)
    blocks.append(
        Block(
            txs=[
                template_tx.with_fields(
                    ty=tx_type,
                    nonce=i,
                    to=address,
                    gas_price=10 if tx_type < 2 else None,
                    access_list=[] if tx_type >= 2 else None,
                    max_priority_fee_per_gas=10 if tx_type >= 2 else None,
                    blob_versioned_hashes=random_blob_hashes[
                        i:TARGET_BLOB_PER_BLOCK
                    ]
                    if tx_type >= 3
                    else None,
                )
                for i in range(TARGET_BLOB_PER_BLOCK)
            ]
        )
    )
    post[address] = Account(storage={0: BLOBHASH_GAS_COST})
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=blocks,
        post=post,
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "single_valid",
        "repeated_valid",
        "valid_invalid",
        "varied_valid",
    ],
)
def test_blobhash_versioned_hash(
    env,
    pre,
    template_tx,
    blocks,
    post,
    scenario: str,
    blockchain_test: BlockchainTestFiller,
):
    """
    Tests that the BLOBHASH opcode returns the correct versioned hash for
    various valid indexes.

    Covers various scenarios with random blob_versioned_hash values within
    the valid range `[0, 2**256-1]`.
    """
    TOTAL_BLOCKS = 10

    # Create an arbitrary repeated list of blob hashes
    # with length MAX_BLOB_PER_BLOCK * TOTAL_BLOCKS
    b_hashes = list(
        itertools.islice(
            itertools.cycle(random_blob_hashes),
            MAX_BLOB_PER_BLOCK * TOTAL_BLOCKS,
        )
    )
    for i in range(TOTAL_BLOCKS):
        blobhash_calls = BlobhashScenario.generate_blobhash_calls(scenario)
        address = to_address(0x100 + i * 0x100)
        pre[address] = Account(code=blobhash_calls)
        blocks.append(
            Block(
                txs=[
                    template_tx.with_fields(
                        ty=3,
                        nonce=i,
                        to=address,
                        access_list=[],
                        max_priority_fee_per_gas=10,
                        blob_versioned_hashes=b_hashes[
                            (i * MAX_BLOB_PER_BLOCK) : (i + 1)
                            * MAX_BLOB_PER_BLOCK
                        ],
                    )
                ]
            )
        )
        post[address] = Account(
            storage={
                index: b_hashes[i * MAX_BLOB_PER_BLOCK + index]
                for index in range(MAX_BLOB_PER_BLOCK)
            }
        )
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=blocks,
        post=post,
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "invalid_calls",
    ],
)
def test_blobhash_invalid_blob_index(
    env,
    pre,
    template_tx,
    blocks,
    post,
    blockchain_test: BlockchainTestFiller,
    scenario,
):
    """
    Tests that the BLOBHASH opcode returns a zeroed `bytes32` value for invalid
    indexes.

    Includes cases where the index is negative (`index < 0`) or
    exceeds the maximum number of `blob_versioned_hash` values stored:
    (`index >= len(tx.message.blob_versioned_hashes)`).

    It confirms that the returned value is a zeroed `bytes32 for each case.
    """
    INVALID_DEPTH_FACTOR = 5
    TOTAL_BLOCKS = 5

    for i in range(TOTAL_BLOCKS):
        blobhash_calls = BlobhashScenario.generate_blobhash_calls(scenario)
        address = to_address(0x100 + i * 0x100)
        pre[address] = Account(code=blobhash_calls)
        blob_per_block = (i % MAX_BLOB_PER_BLOCK) + 1
        blobs = [random_blob_hashes[blob] for blob in range(blob_per_block)]
        blocks.append(
            Block(
                txs=[
                    template_tx.with_fields(
                        ty=3,
                        nonce=i,
                        to=address,
                        access_list=[],
                        max_priority_fee_per_gas=10,
                        blob_versioned_hashes=blobs,
                    )
                ]
            )
        )
        post[address] = Account(
            storage={
                index: (
                    0 if index < 0 or index >= blob_per_block else blobs[index]
                )
                for index in range(
                    -INVALID_DEPTH_FACTOR,
                    blob_per_block
                    + (INVALID_DEPTH_FACTOR - (i % MAX_BLOB_PER_BLOCK)),
                )
            }
        )
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=blocks,
        post=post,
    )


def test_blobhash_multiple_txs_in_block(
    env,
    pre,
    blob_tx,
    post,
    blockchain_test: BlockchainTestFiller,
):
    """
    Tests that the BLOBHASH opcode returns the appropriate values when there
    is more than 1 blob tx type within a block (for tx types 2 and 3).

    Scenarios involve tx type 3 followed by tx type 2 running the same code
    within a block, including the opposite.
    """
    blobhash_calls = BlobhashScenario.generate_blobhash_calls("single_valid")
    pre = {
        **pre,
        **{
            to_address(address): Account(code=blobhash_calls)
            for address in range(0x100, 0x500, 0x100)
        },
    }
    blocks = [
        Block(
            txs=[
                blob_tx(address=to_address(0x100), type=3, nonce=0),
                blob_tx(address=to_address(0x100), type=2, nonce=1),
            ]
        ),
        Block(
            txs=[
                blob_tx(address=to_address(0x200), type=2, nonce=2),
                blob_tx(address=to_address(0x200), type=3, nonce=3),
            ]
        ),
        Block(
            txs=[
                blob_tx(address=to_address(0x300), type=2, nonce=4),
                blob_tx(address=to_address(0x400), type=3, nonce=5),
            ],
        ),
    ]
    post = {
        to_address(address): Account(
            storage={
                i: random_blob_hashes[i] for i in range(MAX_BLOB_PER_BLOCK)
            }
        )
        if address in (0x200, 0x400)
        else Account(storage={i: 0 for i in range(MAX_BLOB_PER_BLOCK)})
        for address in range(0x100, 0x500, 0x100)
    }
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=blocks,
        post=post,
    )
