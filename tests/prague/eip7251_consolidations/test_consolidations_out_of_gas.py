"""
Out-of-gas consolidation request tests.

Tests that consolidation requests whose triggering call runs out of gas are
not included in the block, for
[EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).

The relay contract self-measures, at runtime, the gas its call to the
predeploy needs and then forwards one gas less to the request marked invalid,
so the out-of-gas boundary holds across forks without a hard-coded gas value.
The coarse starvation cases still pass their limits per request via the
interaction's `gas_limits` list.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    SystemContractInteractionContract,
    SystemContractInteractionMeasuredOutOfGasContract,
)

from .helpers import ConsolidationRequest
from .spec import Spec, ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionMeasuredOutOfGasContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=ConsolidationRequest.get_fee(0),
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=ConsolidationRequest.get_fee(0),
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x05,
                                target_pubkey=0x06,
                                fee=ConsolidationRequest.get_fee(0),
                                # Starved of gas by the relay contract.
                                valid=False,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_measured_oog",
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
                                Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5,
                            )
                        ],
                        # Starve the first inner call of gas
                        gas_limits=[100]
                        + [None]
                        * (Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5 - 1),
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
                                Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5
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
                        * (Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
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

    The relay contract self-measures the required gas and forwards one gas
    less than needed to the invalid request, so the out-of-gas holds across
    forks without any hard-coded gas value.
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
