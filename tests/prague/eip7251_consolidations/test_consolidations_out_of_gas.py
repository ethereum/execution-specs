"""
Out-of-gas consolidation request tests.

Tests that consolidation requests whose triggering call runs out of gas are
not included in the block, for
[EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).

The gas limits are supplied per-request via the interaction's `gas_limits`
list rather than being baked into the consolidation request descriptor,
keeping the gas concern isolated to these dedicated tests.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    ConsolidationRequest,
    Environment,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
)

from .spec import ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                            ),
                        ],
                        gas_limits=[136_534 - 1, None],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_first_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                valid=False,
                            ),
                        ],
                        gas_limits=[None, 102_334 - 1],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_last_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                                valid=False,
                            )
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                valid=True,
                            )
                            for i in range(
                                1,
                                ConsolidationRequest.max_per_block * 5,
                            )
                        ],
                        # Starve the first inner call of gas
                        gas_limits=[100]
                        + [None]
                        * (ConsolidationRequest.max_per_block * 5 - 1),
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_first_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                valid=True,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                                valid=False,
                            )
                        ],
                        # Starve the last inner call of gas
                        gas_limits=[None]
                        * (ConsolidationRequest.max_per_block * 5)
                        + [100],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_last_oog",
        ),
    ],
)
def test_consolidation_requests_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """
    Test that a consolidation request whose triggering call runs out of gas is
    not included, while the other requests in the block are.

    The gas limits are supplied per-request via the interaction's `gas_limits`
    list rather than being baked into the consolidation request descriptor,
    keeping the gas concern isolated to these dedicated tests.
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
