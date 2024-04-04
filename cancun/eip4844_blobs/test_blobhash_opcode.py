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

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    CodeGasMeasure,
    Hash,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import BlobhashScenario, blobhash_index_values, random_blob_hashes
from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

pytestmark = pytest.mark.valid_from("Cancun")


@pytest.fixture
def pre():  # noqa: D103
    return {
        TestAddress: Account(balance=10000000000000000000000),
    }


@pytest.fixture
def post():  # noqa: D103
    return {}


@pytest.fixture
def blocks():  # noqa: D103
    return []


@pytest.fixture
def template_tx():  # noqa: D103
    return Transaction(
        data=Hash(0),
        gas_limit=3000000,
        max_fee_per_gas=10,
    )


@pytest.fixture
def blob_tx(template_tx):
    """
    Blob transaction factory fixture.
    Used to define blob txs with a specified destination address, nonce & type.
    """

    def _blob_tx(address, type, nonce):
        return template_tx.copy(
            ty=type,
            nonce=nonce,
            to=address,
            gas_price=10 if type < 2 else None,
            access_list=[] if type >= 1 else None,
            max_priority_fee_per_gas=10,
            max_fee_per_blob_gas=10 if type >= 3 else None,
            blob_versioned_hashes=random_blob_hashes[0 : SpecHelpers.max_blobs_per_block()]
            if type >= 3
            else None,
        )

    return _blob_tx


@pytest.mark.parametrize("tx_type", [0, 1, 2, 3])
def test_blobhash_gas_cost(
    pre,
    template_tx,
    blocks,
    post,
    tx_type,
    blockchain_test: BlockchainTestFiller,
):
    """
    Tests `BLOBHASH` opcode gas cost using a variety of indexes.

    Asserts that the gas consumption of the `BLOBHASH` opcode is correct by ensuring
    it matches `HASH_OPCODE_GAS = 3`. Includes both valid and invalid random
    index sizes from the range `[0, 2**256-1]`, for tx types 2 and 3.
    """
    assert (
        Op.BLOBHASH.int() == Spec.HASH_OPCODE_BYTE
    ), "Opcodes blobhash byte doesn't match that defined in the spec"
    gas_measures_code = [
        CodeGasMeasure(
            code=Op.BLOBHASH(i),
            overhead_cost=3,
            extra_stack_items=1,
        )
        for i in blobhash_index_values
    ]
    for i, gas_code in enumerate(gas_measures_code):
        address = Address(0x100 + i * 0x100)
        pre[address] = Account(code=gas_code)
        blocks.append(
            Block(
                txs=[
                    template_tx.copy(
                        ty=tx_type,
                        nonce=i,
                        to=address,
                        gas_price=10 if tx_type < 2 else None,
                        access_list=[] if tx_type >= 1 else None,
                        max_fee_per_gas=10 if tx_type >= 2 else None,
                        max_priority_fee_per_gas=10 if tx_type >= 2 else None,
                        max_fee_per_blob_gas=10 if tx_type >= 3 else None,
                        blob_versioned_hashes=random_blob_hashes[
                            0 : SpecHelpers.target_blobs_per_block()
                        ]
                        if tx_type >= 3
                        else None,
                    )
                ]
            )
        )
        post[address] = Account(storage={0: Spec.HASH_GAS_COST})
    blockchain_test(
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
def test_blobhash_scenarios(
    pre,
    template_tx,
    blocks,
    post,
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
    for i in range(TOTAL_BLOCKS):
        address = Address(0x100 + i * 0x100)
        pre[address] = Account(code=blobhash_calls)
        blocks.append(
            Block(
                txs=[
                    template_tx.copy(
                        ty=Spec.BLOB_TX_TYPE,
                        nonce=i,
                        to=address,
                        access_list=[],
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
    pre,
    template_tx,
    blocks,
    post,
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
    for i in range(TOTAL_BLOCKS):
        address = Address(0x100 + i * 0x100)
        pre[address] = Account(code=blobhash_calls)
        blob_per_block = (i % SpecHelpers.max_blobs_per_block()) + 1
        blobs = [random_blob_hashes[blob] for blob in range(blob_per_block)]
        blocks.append(
            Block(
                txs=[
                    template_tx.copy(
                        ty=Spec.BLOB_TX_TYPE,
                        nonce=i,
                        to=address,
                        access_list=[],
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
    pre,
    blob_tx,
    post,
    blockchain_test: BlockchainTestFiller,
):
    """
    Tests that the `BLOBHASH` opcode returns the appropriate values when there
    is more than 1 blob tx type within a block (for tx types 2 and 3).

    Scenarios involve tx type 3 followed by tx type 2 running the same code
    within a block, including the opposite.
    """
    blobhash_bytecode = BlobhashScenario.generate_blobhash_bytecode("single_valid")
    pre = {
        **pre,
        **{
            Address(address): Account(code=blobhash_bytecode)
            for address in range(0x100, 0x500, 0x100)
        },
    }
    blocks = [
        Block(
            txs=[
                blob_tx(address=Address(0x100), type=3, nonce=0),
                blob_tx(address=Address(0x100), type=2, nonce=1),
            ]
        ),
        Block(
            txs=[
                blob_tx(address=Address(0x200), type=2, nonce=2),
                blob_tx(address=Address(0x200), type=3, nonce=3),
            ]
        ),
        Block(
            txs=[
                blob_tx(address=Address(0x300), type=2, nonce=4),
                blob_tx(address=Address(0x400), type=3, nonce=5),
            ],
        ),
    ]
    post = {
        Address(address): Account(
            storage={i: random_blob_hashes[i] for i in range(SpecHelpers.max_blobs_per_block())}
        )
        if address in (0x200, 0x400)
        else Account(storage={i: 0 for i in range(SpecHelpers.max_blobs_per_block())})
        for address in range(0x100, 0x500, 0x100)
    }
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
