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
    add_kzg_version,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .blobhash_util import BlobhashScenario

pytestmark = pytest.mark.parametrize("fork", forks_from(Cancun))

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"

BLOBHASH_GAS_COST = 3
TARGET_BLOB_PER_BLOCK = 2
MAX_BLOB_PER_BLOCK = 4
BLOB_COMMITMENT_VERSION_KZG = bytes([0x01])

# Random fixed list of blob versioned hashes
blob_hashes = add_kzg_version(
    [
        "0x00b8c5b09810b5fc07355d3da42e2c3a3e200c1d9a678491b7e8e256fc50cc4f",
        "0x005b4c8cc4f86aa2d2cf9e9ce97fca704a11a6c20f6b1d6c00a6e15f6d60a6df",
        "0x00878f80eaf10be1a6f618e6f8c071b10a6c14d9b89a3bf2a3f3cf2db6c5681d",
        "0x004eb72b108d562c639faeb6f8c6f366a28b0381c7d30431117ec8c7bb89f834",
        "0x00a9b2a6c3f3f0675b768d49b5f5dc5b5d988f88d55766247ba9e40b125f16bb",
        "0x00a4d4cde4aa01e57fb2c880d1d9c778c33bdf85e48ef4c4d4b4de51abccf4ed",
        "0x0071c9b8a0c72d38f5e5b5d08e5cb5ce5e23fb1bc5d75f9c29f7b94df0bceeb7",
        "0x002c8b6a8b11410c7d98d790e1098f1ed6d93cb7a64711481aaab1848e13212f",
        "0x00d78c25f8a1d6aa04d0e2e2a71cf8dfaa4239fa0f301eb57c249d1e6bfe3c3d",
        "0x00c778eb1348a73b9c30c7b1d282a5f8b2c5b5a12d5c5e4a4a35f9c5f639b4a4",
    ],
    BLOB_COMMITMENT_VERSION_KZG,
)


@pytest.fixture
def env():
    return Environment()


@pytest.fixture
def pre():
    return {TestAddress: Account(balance=10000000000000000000000)}


@pytest.fixture
def post():
    return {}


@pytest.fixture
def blocks():
    return []


@pytest.fixture
def tx():
    tx = Transaction(
        data=to_hash_bytes(0),
        gas_limit=3000000,
        max_fee_per_gas=10,
        max_fee_per_data_gas=10,
    )
    return tx


blobhash_index_values = [
    0x00,
    0x01,
    0x02,
    0x03,
    0x04,
    2**256 - 1,
    0x30A9B2A6C3F3F0675B768D49B5F5DC5B5D988F88D55766247BA9E40B125F16BB,
    0x4FA4D4CDE4AA01E57FB2C880D1D9C778C33BDF85E48EF4C4D4B4DE51ABCCF4ED,
    0x7871C9B8A0C72D38F5E5B5D08E5CB5CE5E23FB1BC5D75F9C29F7B94DF0BCEEB7,
    0xA12C8B6A8B11410C7D98D790E1098F1ED6D93CB7A64711481AAAB1848E13212F,
]


@pytest.fixture(params=blobhash_index_values, ids=lambda x: f"index={hex(x)}")
def blobhash_index(request):
    return request.param


@pytest.mark.parametrize("tx_type", [0, 1, 2, 3])
def test_blobhash_gas_cost(
    env,
    pre,
    tx,
    blocks,
    post,
    tx_type,
    blobhash_index,
    blockchain_test: BlockchainTestFiller,
):
    """
    Test BLOBHASH opcode gas cost using a variety of indexes.
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
                tx.with_fields(
                    ty=tx_type,
                    nonce=i,
                    to=address,
                    gas_price=10 if tx_type < 2 else None,
                    access_list=[] if tx_type >= 2 else None,
                    max_priority_fee_per_gas=10 if tx_type >= 2 else None,
                    blob_versioned_hashes=blob_hashes[i:TARGET_BLOB_PER_BLOCK]
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
    tx,
    blocks,
    post,
    scenario: str,
    blockchain_test: BlockchainTestFiller,
):
    TOTAL_BLOCKS = 10

    # Create an arbitrary repeated list of blob hashes
    # with length MAX_BLOB_PER_BLOCK * TOTAL_BLOCKS
    b_hashes = list(
        itertools.islice(
            itertools.cycle(blob_hashes),
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
                    tx.with_fields(
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
        post=post,
        blocks=blocks,
        tag=scenario,
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
    tx,
    blocks,
    post,
    blockchain_test: BlockchainTestFiller,
    scenario,
):
    """
    Tests that the `BLOBHASH` opcode returns a zeroed bytes32 value
    for invalid indexes.
    """
    INVALID_DEPTH_FACTOR = 5
    TOTAL_BLOCKS = 5

    for i in range(TOTAL_BLOCKS):
        blobhash_calls = BlobhashScenario.generate_blobhash_calls(scenario)
        address = to_address(0x100 + i * 0x100)
        pre[address] = Account(code=blobhash_calls)
        blob_per_block = (i % MAX_BLOB_PER_BLOCK) + 1
        blobs = [blob_hashes[blob] for blob in range(blob_per_block)]
        blocks.append(
            Block(
                txs=[
                    tx.with_fields(
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
        post=post,
        blocks=blocks,
        tag=scenario,
    )


def generate_base_tx(tx):
    transaction = tx
    return transaction.with_fields(
        access_list=[],
        max_priority_fee_per_gas=10,
        blob_versioned_hashes=blob_hashes[0:MAX_BLOB_PER_BLOCK],
    )


# block_params = [
#     (3, to_address(0x100), 2, to_address(0x100)),
#     (2, to_address(0x200), 3, to_address(0x200)),
#     (2, to_address(0x300), 3, to_address(0x400)),
# ]


# @pytest.mark.parametrize(
#     "block",
#     [
#         Block(
#             txs=[
#                 generate_base_tx(tx).with_fields(ty=ty1, nonce=0, to=to1),
#                 generate_base_tx(tx).with_fields(ty=ty2, nonce=1, to=to2),
#             ]
#         )
#         for ty1, to1, ty2, to2 in block_params
#     ],
#     ids=[f"Block {i}" for i in range(1, len(block_params) + 1)],
# )
# def test_blobhash_multiple_txs_in_block(
#     env,
#     pre,
#     block,
#     post,
#     blockchain_test: BlockchainTestFiller,
# ):
#     """
#     Tests that the `BLOBHASH` opcode returns the appropriate values
#     when there is more than one blob tx type within a block.
#     """
#     blobhash_calls = generate_blobhash_calls(
#         "single_valid", MAX_BLOB_PER_BLOCK
#     )
#     pre = {
#         **pre,
#         **{
#             to_address(address): Account(code=blobhash_calls)
#             for address in range(0x100, 0x500, 0x100)
#         },
#     }

#     post = {
#         to_address(address): Account(
#             storage={i: blob_hashes[i] for i in range(MAX_BLOB_PER_BLOCK)}
#         )
#         if address in (0x200, 0x400)
#         else Account(storage={i: 0 for i in range(MAX_BLOB_PER_BLOCK)})
#         for address in range(0x100, 0x500, 0x100)
#     }

#     blockchain_test(
#         genesis_environment=env,
#         pre=pre,
#         post=post,
#         blocks=[block],
#     )
