"""
Out-of-gas consolidation request tests.

Tests that consolidation requests whose triggering call runs out of gas are
not included in the block, for
[EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    ConsolidationRequest,
    Environment,
    Fork,
    Op,
    ParameterSet,
    SystemContractInteractionContract,
    SystemContractInteractionMeasuredOutOfGasContract,
    SystemContractInteractionTransaction,
)

from .spec import ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = pytest.mark.valid_from("Prague")


def out_of_gas_cases(fork: Fork) -> List[ParameterSet]:
    """Return the out-of-gas cases, deriving the starved gas from `fork`."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()

    def transactions_starving(
        index: int,
    ) -> List[List[SystemContractInteractionTransaction]]:
        requests = [
            ConsolidationRequest(
                source_pubkey=i * 2 + 1, target_pubkey=i * 2 + 2
            )
            for i in range(2)
        ]
        requests[index].valid = False
        # The intrinsic cost alone leaves the predeploy too little gas to
        # enqueue anything. The transaction pays the request fee as value.
        gas_limits: List[int | None] = [None, None]
        gas_limits[index] = intrinsic_cost(
            calldata=requests[index].calldata, sends_value=True
        )
        return [
            [
                SystemContractInteractionTransaction(
                    requests=requests, gas_limits=gas_limits
                )
            ]
        ]

    # The predeploy ends with a warm SSTORE, which EIP-2200 rejects unless
    # more than the call stipend remains, so the requirement exceeds the
    # measured consumption by that sentry.
    warm_sstore = Op.SSTORE(
        key_warm=True, original_value=0, current_value=1, new_value=2
    ).gas_cost(fork)
    sentry_margin = fork.call_value_stipend() - warm_sstore + 1
    # The relay measures the requirement on the second request, then forwards
    # one gas less to the third and exactly the requirement to the fourth.
    boundary_requests = [
        ConsolidationRequest(source_pubkey=i * 2 + 1, target_pubkey=i * 2 + 2)
        for i in range(4)
    ]
    boundary_requests[2].valid = False

    return [
        pytest.param(
            transactions_starving(0),
            id="single_block_multiple_consolidation_request_first_oog",
        ),
        pytest.param(
            transactions_starving(1),
            id="single_block_multiple_consolidation_request_last_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionMeasuredOutOfGasContract(
                        requests=boundary_requests,
                        exact_gas_indices=[3],
                        exact_gas_margin=sentry_margin,
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_gas_boundary",
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
    ]


@pytest.mark.parametrize_by_fork(
    "system_contract_interactions_per_block", out_of_gas_cases
)
def test_consolidation_requests_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """
    Test that a consolidation request whose triggering call runs out of gas is
    not included, while the other requests in the block are.
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
