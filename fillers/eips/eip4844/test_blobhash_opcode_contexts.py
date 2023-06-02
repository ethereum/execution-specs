"""
Test EIP-4844: BLOBHASH Opcode Contexts
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""


import pytest

from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    TestAddress,
    Transaction,
    to_hash_bytes,
)

from .blobhash_util import BlobhashContext, simple_blob_hashes

pytestmark = pytest.mark.valid_from("Cancun")

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"


# Blob transaction template
tx_type_3 = Transaction(
    ty=3,
    data=to_hash_bytes(0),
    gas_limit=3000000,
    max_fee_per_gas=10,
    max_priority_fee_per_gas=10,
    max_fee_per_data_gas=10,
    access_list=[],
    blob_versioned_hashes=simple_blob_hashes,
)


def create_opcode_context(pre, tx, post):
    """
    Generates an opcode context based on the key provided by the
    opcode_contexts dictionary.
    """
    return {
        "pre": {TestAddress: Account(balance=1000000000000000000000), **pre},
        "tx": tx,
        "post": post,
    }


# Dictionary of BLOBHASH opcode use cases. Each context is given a
# pre state, tx & post state respectively, and utilized
# directly within the context pytest fixture.
opcode_contexts = [
    (
        "on_top_level_call_stack",
        create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.with_fields(
                to=BlobhashContext.address("blobhash_sstore"),
                blob_versioned_hashes=simple_blob_hashes[:1],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={0: simple_blob_hashes[0]}
                ),
            },
        ),
    ),
    (
        "on_max_value",
        create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.with_fields(
                data=to_hash_bytes(2**256 - 1) + to_hash_bytes(2**256 - 1),
                to=BlobhashContext.address("blobhash_sstore"),
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={}
                ),
            },
        ),
    ),
    (
        "on_CALL",
        create_opcode_context(
            {
                BlobhashContext.address("call"): Account(
                    code=BlobhashContext.code("call")
                ),
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.with_fields(
                data=to_hash_bytes(1) + to_hash_bytes(1),
                to=BlobhashContext.address("call"),
                blob_versioned_hashes=simple_blob_hashes[:2],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={1: simple_blob_hashes[1]}
                ),
            },
        ),
    ),
    (
        "on_DELEGATECALL",
        create_opcode_context(
            {
                BlobhashContext.address("delegatecall"): Account(
                    code=BlobhashContext.code("delegatecall")
                ),
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.with_fields(
                data=to_hash_bytes(0) + to_hash_bytes(3),
                to=BlobhashContext.address("delegatecall"),
            ),
            {
                BlobhashContext.address("delegatecall"): Account(
                    storage={
                        k: v
                        for (k, v) in zip(
                            range(len(simple_blob_hashes)), simple_blob_hashes
                        )
                    }
                ),
            },
        ),
    ),
    (
        "on_STATICCALL",
        create_opcode_context(
            {
                BlobhashContext.address("staticcall"): Account(
                    code=BlobhashContext.code("staticcall")
                ),
                BlobhashContext.address("blobhash_return"): Account(
                    code=BlobhashContext.code("blobhash_return")
                ),
            },
            tx_type_3.with_fields(
                data=to_hash_bytes(0) + to_hash_bytes(3),
                to=BlobhashContext.address("staticcall"),
            ),
            {
                BlobhashContext.address("staticcall"): Account(
                    storage={
                        k: v
                        for (k, v) in zip(
                            range(len(simple_blob_hashes)), simple_blob_hashes
                        )
                    }
                ),
            },
        ),
    ),
    (
        "on_CALLCODE",
        create_opcode_context(
            {
                BlobhashContext.address("callcode"): Account(
                    code=BlobhashContext.code("callcode")
                ),
                BlobhashContext.address("blobhash_return"): Account(
                    code=BlobhashContext.code("blobhash_return")
                ),
            },
            tx_type_3.with_fields(
                data=to_hash_bytes(0) + to_hash_bytes(3),
                to=BlobhashContext.address("callcode"),
            ),
            {
                BlobhashContext.address("callcode"): Account(
                    storage={
                        k: v
                        for (k, v) in zip(
                            range(len(simple_blob_hashes)), simple_blob_hashes
                        )
                    }
                ),
            },
        ),
    ),
    (
        "on_INITCODE",
        create_opcode_context(
            {},
            tx_type_3.with_fields(
                data=BlobhashContext.code("initcode"),
                to=None,
            ),
            {
                BlobhashContext.created_contract(
                    "tx_created_contract"
                ): Account(
                    storage={
                        k: v
                        for (k, v) in zip(
                            range(len(simple_blob_hashes)), simple_blob_hashes
                        )
                    }
                ),
            },
        ),
    ),
    (
        "on_CREATE",
        create_opcode_context(
            {
                BlobhashContext.address("create"): Account(
                    code=BlobhashContext.code("create")
                ),
            },
            tx_type_3.with_fields(
                data=BlobhashContext.code("initcode"),
                to=BlobhashContext.address("create"),
            ),
            {
                BlobhashContext.created_contract("create"): Account(
                    storage={
                        k: v
                        for (k, v) in zip(
                            range(len(simple_blob_hashes)), simple_blob_hashes
                        )
                    }
                ),
            },
        ),
    ),
    (
        "on_CREATE2",
        create_opcode_context(
            {
                BlobhashContext.address("create2"): Account(
                    code=BlobhashContext.code("create2")
                ),
            },
            tx_type_3.with_fields(
                data=BlobhashContext.code("initcode"),
                to=BlobhashContext.address("create2"),
            ),
            {
                BlobhashContext.created_contract("create2"): Account(
                    storage={
                        k: v
                        for (k, v) in zip(
                            range(len(simple_blob_hashes)), simple_blob_hashes
                        )
                    }
                ),
            },
        ),
    ),
    (
        "on_type_2_tx",
        create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            Transaction(
                ty=2,
                data=to_hash_bytes(0),
                to=BlobhashContext.address("blobhash_sstore"),
                gas_limit=3000000,
                max_fee_per_gas=10,
                max_priority_fee_per_gas=10,
                access_list=[],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={0: 0}
                ),
            },
        ),
    ),
    (
        "on_type_1_tx",
        create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            Transaction(
                ty=1,
                data=to_hash_bytes(0),
                to=BlobhashContext.address("blobhash_sstore"),
                gas_limit=3000000,
                gas_price=10,
                access_list=[],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={0: 0}
                ),
            },
        ),
    ),
    (
        "on_type_0_tx",
        create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            Transaction(
                ty=0,
                data=to_hash_bytes(0),
                to=BlobhashContext.address("blobhash_sstore"),
                gas_limit=3000000,
                gas_price=10,
                access_list=[],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={0: 0}
                ),
            },
        ),
    ),
]


@pytest.fixture(params=opcode_contexts, ids=[op[0] for op in opcode_contexts])
def context(request):
    """
    Fixture that is parameterized to each value of the opcode_contexts
    list of tuples, with the first item in each tuple set as the test ID.
    """
    return request.param[1]


def test_blobhash_opcode_contexts(
    context, blockchain_test: BlockchainTestFiller
):
    """
    Tests that the BLOBHASH opcode functions correctly when called in different
    contexts including:

    - BLOBHASH opcode on the top level of the call stack.
    - BLOBHASH opcode on the max value.
    - BLOBHASH opcode on `CALL`, `DELEGATECALL`, `STATICCALL`, and `CALLCODE`.
    - BLOBHASH opcode on Initcode.
    - BLOBHASH opcode on `CREATE` and `CREATE2`.
    - BLOBHASH opcode on transaction types 0, 1 and 2.
    """
    blockchain_test(
        pre=context.get("pre"),
        blocks=[Block(txs=[context.get("tx")])],
        post=context.get("post"),
    )
