"""
Pytest (plugin) definitions local to EIP-4844 tests.
"""
import pytest

from ethereum_test_tools import (
    Block,
    TestPrivateKey2,
    Transaction,
    add_kzg_version,
    to_address,
    to_hash_bytes,
)

from .common import (
    BLOB_COMMITMENT_VERSION_KZG,
    TARGET_DATA_GAS_PER_BLOCK,
    calc_excess_data_gas,
    get_data_gasprice,
)


@pytest.fixture
def block_intermediate(
    parent_blobs: int,
    parent_excess_data_gas: int,
    tx_max_fee_per_gas: int,
) -> Block | None:
    """
    For test cases with a non-zero dataGasUsed field in the
    original genesis block header we must instead utilize an
    intermediate block to act on its behalf.

    Genesis blocks with a non-zero dataGasUsed field are invalid as
    they do not have any blob txs.

    For the intermediate block to align with default genesis values,
    we must add TARGET_DATA_GAS_PER_BLOCK to the excessDataGas of the
    genesis value, expecting an appropriate drop to the intermediate block.
    Similarly, we must add parent_blobs to the intermediate block within
    a blob tx such that an equivalent dataGasUsed field is wrote.
    """
    return (
        None
        if parent_blobs == 0
        else Block(
            txs=[
                Transaction(
                    ty=3,
                    nonce=0,
                    to=to_address(0x200),
                    value=1,
                    gas_limit=21000,
                    max_fee_per_gas=tx_max_fee_per_gas,
                    max_priority_fee_per_gas=0,
                    max_fee_per_data_gas=get_data_gasprice(
                        excess_data_gas=calc_excess_data_gas(
                            parent_excess_data_gas=(
                                parent_excess_data_gas + TARGET_DATA_GAS_PER_BLOCK
                            ),
                            parent_blobs=0,
                        ),
                    ),
                    access_list=[],
                    blob_versioned_hashes=add_kzg_version(
                        [to_hash_bytes(x) for x in range(parent_blobs)],
                        BLOB_COMMITMENT_VERSION_KZG,
                    ),
                    secret_key=TestPrivateKey2,
                )
            ]
        )
    )
