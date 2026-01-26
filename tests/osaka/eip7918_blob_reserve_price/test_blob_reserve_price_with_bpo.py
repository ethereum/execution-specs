"""
[EIP-7918: Blob base fee bounded by execution
cost](https://eips.ethereum.org/EIPS/eip-7918).
"""

import pytest
from execution_testing import (
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
@pytest.mark.slow
def test_blob_base_fee_with_bpo_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
) -> None:
    """Test BPO1 transition with EIP-7918 reserve mechanism."""
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[Block(timestamp=15_000)],
        post={},
    )
