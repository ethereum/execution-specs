"""
Pytest (plugin) definitions local to EIP-4844 tests.
"""
import pytest

from ethereum_test_tools import Address, Block, Hash, TestPrivateKey2, Transaction, add_kzg_version

from .spec import BlockHeaderBlobGasFields, Spec


@pytest.fixture
def non_zero_blob_gas_used_genesis_block(
    parent_blobs: int,
    parent_excess_blob_gas: int,
    tx_max_fee_per_gas: int,
) -> Block | None:
    """
    For test cases with a non-zero blobGasUsed field in the
    original genesis block header we must instead utilize an
    intermediate block to act on its behalf.

    Genesis blocks with a non-zero blobGasUsed field are invalid as
    they do not have any blob txs.

    For the intermediate block to align with default genesis values,
    we must add TARGET_BLOB_GAS_PER_BLOCK to the excessBlobGas of the
    genesis value, expecting an appropriate drop to the intermediate block.
    Similarly, we must add parent_blobs to the intermediate block within
    a blob tx such that an equivalent blobGasUsed field is wrote.
    """
    if parent_blobs == 0:
        return None

    parent_excess_blob_gas += Spec.TARGET_BLOB_GAS_PER_BLOCK
    excess_blob_gas = Spec.calc_excess_blob_gas(
        BlockHeaderBlobGasFields(parent_excess_blob_gas, 0)
    )

    return Block(
        txs=[
            Transaction(
                ty=Spec.BLOB_TX_TYPE,
                nonce=0,
                to=Address(0x200),
                value=1,
                gas_limit=21000,
                max_fee_per_gas=tx_max_fee_per_gas,
                max_priority_fee_per_gas=0,
                max_fee_per_blob_gas=Spec.get_blob_gasprice(excess_blob_gas=excess_blob_gas),
                access_list=[],
                blob_versioned_hashes=add_kzg_version(
                    [Hash(x) for x in range(parent_blobs)],
                    Spec.BLOB_COMMITMENT_VERSION_KZG,
                ),
                secret_key=TestPrivateKey2,
            )
        ]
    )
