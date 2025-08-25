"""
abstract:  [EIP-7918: Blob base fee bounded by execution cost](https://eips.ethereum.org/EIPS/eip-7918)
    Test the blob base fee reserve price mechanism for [EIP-7918: Blob base fee bounded by execution cost](https://eips.ethereum.org/EIPS/eip-7918).

"""  # noqa: E501

import pytest

from ethereum_test_tools import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
)

from .spec import ref_spec_7918

REFERENCE_SPEC_GIT_PATH = ref_spec_7918.git_path
REFERENCE_SPEC_VERSION = ref_spec_7918.version


@pytest.mark.valid_at_transition_to("BPO1")
@pytest.mark.valid_for_bpo_forks()
@pytest.mark.parametrize("parent_excess_blobs", [27])
@pytest.mark.parametrize("block_base_fee_per_gas", [17])
def test_blob_base_fee_with_bpo_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
):
    """Test BPO1 transition with EIP-7918 reserve mechanism."""
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[Block(timestamp=15_000)],
        post={},
    )
