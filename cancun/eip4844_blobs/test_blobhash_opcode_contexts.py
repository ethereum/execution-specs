"""
abstract: Tests `BLOBHASH` opcode in [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test case for `BLOBHASH` opcode calls across different contexts
    in [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

"""  # noqa: E501

from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    Hash,
    TestAddress,
    Transaction,
    YulCompiler,
    add_kzg_version,
)

from .common import BlobhashContext
from .spec import Spec, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

pytestmark = pytest.mark.valid_from("Cancun")


def create_opcode_context(pre, tx, post):
    """Generate opcode context based on the key provided by the opcode_contexts dictionary."""
    return {
        "pre": {TestAddress: Account(balance=1000000000000000000000), **pre},
        "tx": tx,
        "post": post,
    }


@pytest.fixture()
def simple_blob_hashes(
    max_blobs_per_block: int,
) -> List[bytes]:
    """Return a simple list of blob versioned hashes ranging from bytes32(1 to 4)."""
    return add_kzg_version(
        [(1 << x) for x in range(max_blobs_per_block)],
        Spec.BLOB_COMMITMENT_VERSION_KZG,
    )


@pytest.fixture()
def tx_type_3(
    fork: Fork,
    simple_blob_hashes: List[bytes],
) -> Transaction:
    """Blob transaction template."""
    return Transaction(
        ty=Spec.BLOB_TX_TYPE,
        data=Hash(0),
        gas_limit=3000000,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=10,
        max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas() * 10,
        access_list=[],
        blob_versioned_hashes=simple_blob_hashes,
    )


@pytest.fixture(
    params=[
        "on_top_level_call_stack",
        "on_max_value",
        "on_CALL",
        "on_DELEGATECALL",
        "on_STATICCALL",
        "on_CALLCODE",
        "on_CREATE",
        "on_CREATE2",
        "on_type_2_tx",
        "on_type_1_tx",
        "on_type_0_tx",
    ]
)
def opcode_context(
    yul: YulCompiler,
    request,
    max_blobs_per_block: int,
    simple_blob_hashes: List[bytes],
    tx_type_3: Transaction,
):
    """
    Fixture that is parameterized by each BLOBHASH opcode test case
    in order to return the corresponding constructed opcode context.

    Each context is given a pre state, tx & post state respectively.
    """
    BlobhashContext.yul_compiler = yul
    test_case = request.param
    if test_case == "on_top_level_call_stack":
        return create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.copy(
                to=BlobhashContext.address("blobhash_sstore"),
                blob_versioned_hashes=simple_blob_hashes[:1],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={0: simple_blob_hashes[0]}
                ),
            },
        )
    elif test_case == "on_max_value":
        return create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.copy(
                data=Hash(2**256 - 1) + Hash(2**256 - 1),
                to=BlobhashContext.address("blobhash_sstore"),
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(storage={}),
            },
        )
    elif test_case == "on_CALL":
        return create_opcode_context(
            {
                BlobhashContext.address("call"): Account(code=BlobhashContext.code("call")),
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.copy(
                data=Hash(1) + Hash(1),
                to=BlobhashContext.address("call"),
                blob_versioned_hashes=simple_blob_hashes[:2],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    storage={1: simple_blob_hashes[1]}
                ),
            },
        )
    elif test_case == "on_DELEGATECALL":
        return create_opcode_context(
            {
                BlobhashContext.address("delegatecall"): Account(
                    code=BlobhashContext.code("delegatecall")
                ),
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            tx_type_3.copy(
                data=Hash(0) + Hash(max_blobs_per_block - 1),
                to=BlobhashContext.address("delegatecall"),
            ),
            {
                BlobhashContext.address("delegatecall"): Account(
                    storage=dict(
                        zip(
                            range(len(simple_blob_hashes)),
                            simple_blob_hashes,
                            strict=False,
                        )
                    )
                ),
            },
        )
    elif test_case == "on_STATICCALL":
        return create_opcode_context(
            {
                BlobhashContext.address("staticcall"): Account(
                    code=BlobhashContext.code("staticcall")
                ),
                BlobhashContext.address("blobhash_return"): Account(
                    code=BlobhashContext.code("blobhash_return")
                ),
            },
            tx_type_3.copy(
                data=Hash(0) + Hash(max_blobs_per_block - 1),
                to=BlobhashContext.address("staticcall"),
            ),
            {
                BlobhashContext.address("staticcall"): Account(
                    storage=dict(
                        zip(range(len(simple_blob_hashes)), simple_blob_hashes, strict=False)
                    )
                ),
            },
        )
    elif test_case == "on_CALLCODE":
        return create_opcode_context(
            {
                BlobhashContext.address("callcode"): Account(
                    code=BlobhashContext.code("callcode")
                ),
                BlobhashContext.address("blobhash_return"): Account(
                    code=BlobhashContext.code("blobhash_return")
                ),
            },
            tx_type_3.copy(
                data=Hash(0) + Hash(max_blobs_per_block - 1),
                to=BlobhashContext.address("callcode"),
            ),
            {
                BlobhashContext.address("callcode"): Account(
                    storage=dict(
                        zip(range(len(simple_blob_hashes)), simple_blob_hashes, strict=False)
                    )
                ),
            },
        )
    elif test_case == "on_CREATE":
        return create_opcode_context(
            {
                BlobhashContext.address("create"): Account(code=BlobhashContext.code("create")),
            },
            tx_type_3.copy(
                data=BlobhashContext.code("initcode"),
                to=BlobhashContext.address("create"),
            ),
            {
                BlobhashContext.created_contract("create"): Account(
                    storage=dict(
                        zip(range(len(simple_blob_hashes)), simple_blob_hashes, strict=False)
                    )
                ),
            },
        )
    elif test_case == "on_CREATE2":
        return create_opcode_context(
            {
                BlobhashContext.address("create2"): Account(code=BlobhashContext.code("create2")),
            },
            tx_type_3.copy(
                data=BlobhashContext.code("initcode"),
                to=BlobhashContext.address("create2"),
            ),
            {
                BlobhashContext.created_contract("create2"): Account(
                    storage=dict(
                        zip(range(len(simple_blob_hashes)), simple_blob_hashes, strict=False)
                    )
                ),
            },
        )
    elif test_case == "on_type_2_tx":
        return create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            Transaction(
                ty=2,
                data=Hash(0),
                to=BlobhashContext.address("blobhash_sstore"),
                gas_limit=3000000,
                max_fee_per_gas=10,
                max_priority_fee_per_gas=10,
                access_list=[],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(storage={0: 0}),
            },
        )
    elif test_case == "on_type_1_tx":
        return create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            Transaction(
                ty=1,
                data=Hash(0),
                to=BlobhashContext.address("blobhash_sstore"),
                gas_limit=3000000,
                gas_price=10,
                access_list=[],
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(storage={0: 0}),
            },
        )
    elif test_case == "on_type_0_tx":
        return create_opcode_context(
            {
                BlobhashContext.address("blobhash_sstore"): Account(
                    code=BlobhashContext.code("blobhash_sstore")
                ),
            },
            Transaction(
                ty=0,
                data=Hash(0),
                to=BlobhashContext.address("blobhash_sstore"),
                gas_limit=3000000,
                gas_price=10,
            ),
            {
                BlobhashContext.address("blobhash_sstore"): Account(storage={0: 0}),
            },
        )
    else:
        raise Exception(f"Unknown test case {test_case}")


@pytest.mark.compile_yul_with("Shanghai")
def test_blobhash_opcode_contexts(opcode_context, blockchain_test: BlockchainTestFiller):
    """
    Tests that the `BLOBHASH` opcode functions correctly when called in different contexts.

    - `BLOBHASH` opcode on the top level of the call stack.
    - `BLOBHASH` opcode on the max value.
    - `BLOBHASH` opcode on `CALL`, `DELEGATECALL`, `STATICCALL`, and `CALLCODE`.
    - `BLOBHASH` opcode on Initcode.
    - `BLOBHASH` opcode on `CREATE` and `CREATE2`.
    - `BLOBHASH` opcode on transaction types 0, 1 and 2.
    """
    blockchain_test(
        pre=opcode_context.get("pre"),
        blocks=[Block(txs=[opcode_context.get("tx")])],
        post=opcode_context.get("post"),
    )
