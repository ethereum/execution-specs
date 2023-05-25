"""
Test EIP-4844: Shard Blob Transactions (BLOBHASH Opcode)
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""

from typing import List

import pytest
from blobhash_context_util import BlobhashContext

from ethereum_test_forks import Cancun, forks_from
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    Environment,
    TestAddress,
    Transaction,
    add_kzg_version,
    to_hash_bytes,
)

pytestmark = pytest.mark.parametrize("fork", forks_from(Cancun))

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"

MAX_BLOB_PER_BLOCK = 4
BLOB_COMMITMENT_VERSION_KZG = bytes([0x01])

# Blob versioned hashes ranging from 1-4
b_hashes: List[bytes] = add_kzg_version(
    [(1 << x) for x in range(MAX_BLOB_PER_BLOCK)],
    BLOB_COMMITMENT_VERSION_KZG,
)

# Blob transaction template
tx_type_3 = Transaction(
    ty=3,
    data=to_hash_bytes(0),
    gas_limit=3000000,
    max_fee_per_gas=10,
    max_priority_fee_per_gas=10,
    max_fee_per_data_gas=10,
    access_list=[],
    blob_commitment_version_kzg=BLOB_COMMITMENT_VERSION_KZG,
    blob_versioned_hashes=b_hashes,
)


def create_opcode_context(pre, tx, post):
    pre = {TestAddress: Account(balance=1000000000000000000000), **pre}
    return {"pre": pre, "tx": tx, "post": post}


opcode_contexts = {
    "BLOBHASH_on_top_level_call_stack": create_opcode_context(
        {
            BlobhashContext.address("blobhash_sstore"): Account(
                code=BlobhashContext.code("blobhash_sstore")
            ),
        },
        tx_type_3.with_fields(
            to=BlobhashContext.address("blobhash_sstore"),
            blob_versioned_hashes=b_hashes[:1],
        ),
        {
            BlobhashContext.address("blobhash_sstore"): Account(
                storage={0: b_hashes[0]}
            ),
        },
    ),
    "BLOBHASH_on_max_value": create_opcode_context(
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
            BlobhashContext.address("blobhash_sstore"): Account(storage={}),
        },
    ),
    "BLOBHASH_on_CALL": create_opcode_context(
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
            blob_versioned_hashes=b_hashes[:2],
        ),
        {
            BlobhashContext.address("blobhash_sstore"): Account(
                storage={1: b_hashes[1]}
            ),
        },
    ),
    "BLOBHASH_on_DELEGATECALL": create_opcode_context(
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
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    "BLOBHASH_on_STATICCALL": create_opcode_context(
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
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    "BLOBHASH_on_CALLCODE": create_opcode_context(
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
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    "BLOBHASH_on_INITCODE": create_opcode_context(
        {},
        tx_type_3.with_fields(
            data=BlobhashContext.code("initcode"),
            to=None,
        ),
        {
            BlobhashContext.created_contract("tx_created_contract"): Account(
                storage={
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    "BLOBHASH_on_CREATE": create_opcode_context(
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
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    "BLOBHASH_on_CREATE2": create_opcode_context(
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
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    "BLOBHASH_on_type_2_tx": create_opcode_context(
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
    "BLOBHASH_on_type_1_tx": create_opcode_context(
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
    "BLOBHASH_on_type_0_tx": create_opcode_context(
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
}


@pytest.fixture
def env():
    """
    Fixture for environment setup.
    """
    return Environment(
        coinbase="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=300000000,
        number=1,
        timestamp=1000,
    )


@pytest.fixture(params=opcode_contexts.values(), ids=opcode_contexts.keys())
def context(request):
    """
    Fixture that is parameterized to each value of the opcode_contexts
    dictionary, with each key being used as the test ID.
    """
    return request.param


@pytest.fixture
def pre(context):
    """
    Fixture for the pre state of the given context.
    """
    return context["pre"]


@pytest.fixture
def tx(context):
    """
    Fixture of the transaction for the given context.
    """
    return context["tx"]


@pytest.fixture
def post(context):
    """
    Fixture for the post state of the given context.
    """
    return context["post"]


def test_blobhash_opcode_contexts(
    pre, tx, post, env: Environment, blockchain_test: BlockchainTestFiller
):
    """
    Test function for each opcode context, in the opcode_contexts dictionary.
    """
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[Block(txs=[tx])],
        post=post,
    )
