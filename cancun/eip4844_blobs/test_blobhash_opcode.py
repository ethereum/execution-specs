"""
abstract: Tests `BLOBHASH` opcode in [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test cases for the `BLOBHASH` opcode in
    [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

note: Adding a new test
    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test
    - pre
    - tx
    - post

    Additional custom `pytest.fixture` fixtures can be added and parametrized for new test cases.

    There is no specific structure to follow within this test module.

"""  # noqa: E501
from typing import List

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    CodeGasMeasure,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import BlobhashScenario, random_blob_hashes
from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

pytestmark = pytest.mark.valid_from("Cancun")


# Blobhash index values for test_blobhash_gas_cost
blobhash_index_values = [
    0x00,
    0x01,
    0x02,
    0x03,
    0x04,
    2**256 - 1,
    0xA12C8B6A8B11410C7D98D790E1098F1ED6D93CB7A64711481AAAB1848E13212F,
]


@pytest.mark.parametrize("blobhash_index", blobhash_index_values)
@pytest.mark.with_all_tx_types
def test_blobhash_gas_cost(
    pre: Alloc,
    tx_type: int,
    blobhash_index: int,
    state_test: StateTestFiller,
):
    """
    Tests `BLOBHASH` opcode gas cost using a variety of indexes.

    Asserts that the gas consumption of the `BLOBHASH` opcode is correct by ensuring
    it matches `HASH_OPCODE_GAS = 3`. Includes both valid and invalid random
    index sizes from the range `[0, 2**256-1]`, for tx types 2 and 3.
    """
    gas_measure_code = CodeGasMeasure(
        code=Op.BLOBHASH(blobhash_index),
        overhead_cost=3,
        extra_stack_items=1,
    )

    address = pre.deploy_contract(gas_measure_code)
    sender = pre.fund_eoa()

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=address,
        data=Hash(0),
        gas_limit=3_000_000,
        gas_price=10 if tx_type < 2 else None,
        access_list=[] if tx_type >= 1 else None,
        max_fee_per_gas=10 if tx_type >= 2 else None,
        max_priority_fee_per_gas=10 if tx_type >= 2 else None,
        max_fee_per_blob_gas=10 if tx_type == 3 else None,
        blob_versioned_hashes=random_blob_hashes[0 : SpecHelpers.target_blobs_per_block()]
        if tx_type == 3
        else None,
    )
    post = {address: Account(storage={0: Spec.HASH_GAS_COST})}

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
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
def test_blobhash_scenarios(
    pre: Alloc,
    scenario: str,
    blockchain_test: BlockchainTestFiller,
):
    """
    Tests that the `BLOBHASH` opcode returns the correct versioned hash for
    various valid indexes.

    Covers various scenarios with random `blob_versioned_hash` values within
    the valid range `[0, 2**256-1]`.
    """
    TOTAL_BLOCKS = 5
    b_hashes_list = BlobhashScenario.create_blob_hashes_list(length=TOTAL_BLOCKS)
    blobhash_calls = BlobhashScenario.generate_blobhash_bytecode(scenario)
    sender = pre.fund_eoa()

    blocks: List[Block] = []
    post = {}
    for i in range(TOTAL_BLOCKS):
        address = pre.deploy_contract(blobhash_calls)
        blocks.append(
            Block(
                txs=[
                    Transaction(
                        ty=Spec.BLOB_TX_TYPE,
                        sender=sender,
                        to=address,
                        data=Hash(0),
                        gas_limit=3_000_000,
                        access_list=[],
                        max_fee_per_gas=10,
                        max_priority_fee_per_gas=10,
                        max_fee_per_blob_gas=10,
                        blob_versioned_hashes=b_hashes_list[i],
                    )
                ]
            )
        )
        post[address] = Account(
            storage={
                index: b_hashes_list[i][index]
                for index in range(SpecHelpers.max_blobs_per_block())
            }
        )
    blockchain_test(
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
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    scenario,
):
    """
    Tests that the `BLOBHASH` opcode returns a zeroed `bytes32` value for invalid
    indexes.

    Includes cases where the index is negative (`index < 0`) or
    exceeds the maximum number of `blob_versioned_hash` values stored:
    (`index >= len(tx.message.blob_versioned_hashes)`).

    It confirms that the returned value is a zeroed `bytes32` for each case.
    """
    TOTAL_BLOCKS = 5
    blobhash_calls = BlobhashScenario.generate_blobhash_bytecode(scenario)
    sender = pre.fund_eoa()
    blocks: List[Block] = []
    post = {}
    for i in range(TOTAL_BLOCKS):
        address = pre.deploy_contract(blobhash_calls)
        blob_per_block = (i % SpecHelpers.max_blobs_per_block()) + 1
        blobs = [random_blob_hashes[blob] for blob in range(blob_per_block)]
        blocks.append(
            Block(
                txs=[
                    Transaction(
                        ty=Spec.BLOB_TX_TYPE,
                        sender=sender,
                        to=address,
                        gas_limit=3_000_000,
                        data=Hash(0),
                        access_list=[],
                        max_fee_per_gas=10,
                        max_priority_fee_per_gas=10,
                        max_fee_per_blob_gas=10,
                        blob_versioned_hashes=blobs,
                    )
                ]
            )
        )
        post[address] = Account(
            storage={
                index: (0 if index < 0 or index >= blob_per_block else blobs[index])
                for index in range(
                    -TOTAL_BLOCKS,
                    blob_per_block + (TOTAL_BLOCKS - (i % SpecHelpers.max_blobs_per_block())),
                )
            }
        )
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )


def test_blobhash_multiple_txs_in_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
):
    """
    Tests that the `BLOBHASH` opcode returns the appropriate values when there
    is more than 1 blob tx type within a block (for tx types 2 and 3).

    Scenarios involve tx type 3 followed by tx type 2 running the same code
    within a block, including the opposite.
    """
    blobhash_bytecode = BlobhashScenario.generate_blobhash_bytecode("single_valid")
    addresses = [pre.deploy_contract(blobhash_bytecode) for _ in range(4)]
    sender = pre.fund_eoa()

    def blob_tx(address: Address, type: int):
        return Transaction(
            ty=type,
            sender=sender,
            to=address,
            data=Hash(0),
            gas_limit=3_000_000,
            gas_price=10 if type < 2 else None,
            access_list=[] if type >= 1 else None,
            max_fee_per_gas=10,
            max_priority_fee_per_gas=10,
            max_fee_per_blob_gas=10 if type >= 3 else None,
            blob_versioned_hashes=random_blob_hashes[0 : SpecHelpers.max_blobs_per_block()]
            if type >= 3
            else None,
        )

    blocks = [
        Block(
            txs=[
                blob_tx(address=addresses[0], type=3),
                blob_tx(address=addresses[0], type=2),
            ]
        ),
        Block(
            txs=[
                blob_tx(address=addresses[1], type=2),
                blob_tx(address=addresses[1], type=3),
            ]
        ),
        Block(
            txs=[
                blob_tx(address=addresses[2], type=2),
                blob_tx(address=addresses[3], type=3),
            ],
        ),
    ]
    post = {
        Address(address): Account(
            storage={i: random_blob_hashes[i] for i in range(SpecHelpers.max_blobs_per_block())}
        )
        if address in (addresses[1], addresses[3])
        else Account(storage={i: 0 for i in range(SpecHelpers.max_blobs_per_block())})
        for address in addresses
    }
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
