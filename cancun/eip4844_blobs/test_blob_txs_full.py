"""
abstract: Tests full blob type transactions for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test full blob type transactions for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

"""  # noqa: E501

from typing import List, Optional

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Header,
    NetworkWrappedTransaction,
    Transaction,
    TransactionException,
)

from .common import INF_POINT, Blob
from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version


@pytest.fixture
def destination_account() -> Address:
    """Destination account for the blob transactions."""
    return Address(0x100)


@pytest.fixture
def tx_value() -> int:
    """
    Value contained by the transactions sent during test.

    Can be overloaded by a test case to provide a custom transaction value.
    """
    return 1


@pytest.fixture
def tx_gas() -> int:
    """Gas allocated to transactions sent during test."""
    return 21_000


@pytest.fixture
def tx_calldata() -> bytes:
    """Calldata in transactions sent during test."""
    return b""


@pytest.fixture(autouse=True)
def parent_excess_blobs() -> int:
    """
    Excess blobs of the parent block.

    Can be overloaded by a test case to provide a custom parent excess blob
    count.
    """
    return 10  # Defaults to a blob gas price of 1.


@pytest.fixture(autouse=True)
def parent_blobs() -> int:
    """
    Blobs of the parent blob.

    Can be overloaded by a test case to provide a custom parent blob count.
    """
    return 0


@pytest.fixture
def tx_max_priority_fee_per_gas() -> int:
    """
    Max priority fee per gas for transactions sent during test.

    Can be overloaded by a test case to provide a custom max priority fee per
    gas.
    """
    return 0


@pytest.fixture
def txs_versioned_hashes(txs_blobs: List[List[Blob]]) -> List[List[bytes]]:
    """List of blob versioned hashes derived from the blobs."""
    return [[blob.versioned_hash() for blob in blob_tx] for blob_tx in txs_blobs]


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
def tx_max_fee_per_blob_gas(  # noqa: D103
    blob_gas_price: Optional[int],
) -> int:
    """
    Max fee per blob gas for transactions sent during test.

    By default, it is set to the blob gas price of the block.

    Can be overloaded by a test case to test rejection of transactions where
    the max fee per blob gas is insufficient.
    """
    if blob_gas_price is None:
        # When fork transitioning, the default blob gas price is 1.
        return 1
    return blob_gas_price


@pytest.fixture
def tx_error() -> Optional[TransactionException]:
    """
    Even though the final block we are producing in each of these tests is invalid, and some of the
    transactions will be invalid due to the format in the final block, none of the transactions
    should be rejected by the transition tool because they are being sent to it with the correct
    format.
    """
    return None


@pytest.fixture(autouse=True)
def txs(  # noqa: D103
    pre: Alloc,
    destination_account: Optional[Address],
    tx_gas: int,
    tx_value: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    tx_max_priority_fee_per_gas: int,
    txs_versioned_hashes: List[List[bytes]],
    tx_error: Optional[TransactionException],
    txs_blobs: List[List[Blob]],
    txs_wrapped_blobs: List[bool],
) -> List[Transaction]:
    """Prepare the list of transactions that are sent during the test."""
    if len(txs_blobs) != len(txs_versioned_hashes) or len(txs_blobs) != len(txs_wrapped_blobs):
        raise ValueError("txs_blobs and txs_versioned_hashes should have the same length")
    txs: List[Transaction] = []
    sender = pre.fund_eoa()
    for tx_blobs, tx_versioned_hashes, tx_wrapped_blobs in zip(
        txs_blobs, txs_versioned_hashes, txs_wrapped_blobs, strict=False
    ):
        tx = Transaction(
            ty=Spec.BLOB_TX_TYPE,
            sender=sender,
            to=destination_account,
            value=tx_value,
            gas_limit=tx_gas,
            data=tx_calldata,
            max_fee_per_gas=tx_max_fee_per_gas,
            max_priority_fee_per_gas=tx_max_priority_fee_per_gas,
            max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
            access_list=[],
            blob_versioned_hashes=tx_versioned_hashes,
            error=tx_error,
            wrapped_blob_transaction=tx_wrapped_blobs,
        )
        if tx_wrapped_blobs:
            blobs_info = Blob.blobs_to_transaction_input(tx_blobs)
            network_wrapped_tx = NetworkWrappedTransaction(
                tx=tx,
                blobs=blobs_info[0],
                blob_kzg_commitments=blobs_info[1],
                blob_kzg_proofs=blobs_info[2],
            )
            tx.rlp_override = network_wrapped_tx.rlp()
        txs.append(tx)
    return txs


@pytest.fixture
def env(
    parent_excess_blob_gas: int,
) -> Environment:
    """Prepare the environment for all test cases."""
    return Environment(
        excess_blob_gas=parent_excess_blob_gas,
        blob_gas_used=0,
    )


@pytest.fixture
def blocks(
    txs: List[Transaction],
    txs_wrapped_blobs: List[bool],
    blob_gas_per_blob: int,
) -> List[Block]:
    """Prepare the list of blocks for all test cases."""
    header_blob_gas_used = 0
    block_error = None
    if any(txs_wrapped_blobs):
        # This is a block exception because the invalid block is only created in the RLP version,
        # not in the transition tool.
        block_error = [
            BlockException.RLP_STRUCTURES_ENCODING,
            TransactionException.TYPE_3_TX_WITH_FULL_BLOBS,
        ]
    if len(txs) > 0:
        header_blob_gas_used = (
            sum(
                [
                    len(tx.blob_versioned_hashes)
                    for tx in txs
                    if tx.blob_versioned_hashes is not None
                ]
            )
            * blob_gas_per_blob
        )
    return [
        Block(
            txs=txs, exception=block_error, rlp_modifier=Header(blob_gas_used=header_blob_gas_used)
        )
    ]


def generate_full_blob_tests(
    fork: Fork,
) -> List:
    """
    Return a list of tests for invalid blob transactions due to insufficient max fee per blob gas
    parametrized for each different fork.
    """
    blob_size = Spec.FIELD_ELEMENTS_PER_BLOB * SpecHelpers.BYTES_PER_FIELD_ELEMENT
    max_blobs = fork.max_blobs_per_block()
    return [
        pytest.param(
            [  # Txs
                [  # Blobs per transaction
                    Blob(
                        blob=bytes(blob_size),
                        kzg_commitment=INF_POINT,
                        kzg_proof=INF_POINT,
                    ),
                ]
            ],
            [True],
            id="one_full_blob_one_tx",
        ),
        pytest.param(
            [  # Txs
                [  # Blobs per transaction
                    Blob(
                        blob=bytes(blob_size),
                        kzg_commitment=INF_POINT,
                        kzg_proof=INF_POINT,
                    )
                ]
                for _ in range(max_blobs)
            ],
            [True] + ([False] * (max_blobs - 1)),
            id="one_full_blob_max_txs",
        ),
        pytest.param(
            [  # Txs
                [  # Blobs per transaction
                    Blob(
                        blob=bytes(blob_size),
                        kzg_commitment=INF_POINT,
                        kzg_proof=INF_POINT,
                    )
                ]
                for _ in range(max_blobs)
            ],
            ([False] * (max_blobs - 1)) + [True],
            id="one_full_blob_at_the_end_max_txs",
        ),
    ]


@pytest.mark.parametrize_by_fork(
    "txs_blobs,txs_wrapped_blobs",
    generate_full_blob_tests,
)
@pytest.mark.exception_test
@pytest.mark.valid_from("Cancun")
def test_reject_valid_full_blob_in_block_rlp(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    blocks: List[Block],
):
    """
    Test valid blob combinations where one or more txs in the block
    serialized version contain a full blob (network version) tx.
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )
