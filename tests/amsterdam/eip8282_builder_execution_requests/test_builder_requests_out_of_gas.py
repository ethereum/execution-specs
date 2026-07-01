"""
Out-of-gas builder request tests.

Tests that builder deposit and exit requests whose triggering call runs out of
gas are not included in the block, for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).

The gas limits are supplied per-request via the interaction's `gas_limits`
list rather than being baked into the request descriptor, keeping the gas
concern isolated to these dedicated tests. Only the contract-driven starvation
variants (a single tiny inner-call gas limit) are exercised here; the
EOA-driven variants of EIP-7002 rely on trace-derived exact gas values that are
predeploy-specific and not yet available for the draft builder contracts.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    SystemContractInteractionContract,
)

from .helpers import BuilderDepositRequest, BuilderExitRequest
from .spec import Spec, ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = pytest.mark.valid_from("Amsterdam")

MIN_DEPOSIT_GWEI = Spec.BUILDER_MIN_DEPOSIT // 10**9

# Builder deposits have a large per-block cap (256); a modest count keeps the
# fixture small while still exercising the out-of-gas exclusion path.
DEPOSIT_OOG_COUNT = 4


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=1,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                valid=False,
                            )
                        ]
                        + [
                            BuilderDepositRequest(
                                pubkey=i + 1,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                valid=True,
                            )
                            for i in range(1, DEPOSIT_OOG_COUNT)
                        ],
                        # Starve the first inner call of gas.
                        gas_limits=[100] + [None] * (DEPOSIT_OOG_COUNT - 1),
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_contract_first_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=i + 1,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                valid=True,
                            )
                            for i in range(DEPOSIT_OOG_COUNT)
                        ]
                        + [
                            BuilderDepositRequest(
                                pubkey=DEPOSIT_OOG_COUNT + 1,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                valid=False,
                            )
                        ],
                        # Starve the last inner call of gas.
                        gas_limits=[None] * DEPOSIT_OOG_COUNT + [100],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_contract_last_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[BuilderExitRequest(pubkey=1, valid=False)]
                        + [
                            BuilderExitRequest(pubkey=i + 1, valid=True)
                            for i in range(1, Spec.MAX_EXIT_REQUESTS_PER_BLOCK)
                        ],
                        # Starve the first inner call of gas.
                        gas_limits=[100]
                        + [None] * (Spec.MAX_EXIT_REQUESTS_PER_BLOCK - 1),
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_contract_first_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=i + 1, valid=True)
                            for i in range(Spec.MAX_EXIT_REQUESTS_PER_BLOCK)
                        ]
                        + [
                            BuilderExitRequest(
                                pubkey=Spec.MAX_EXIT_REQUESTS_PER_BLOCK + 1,
                                valid=False,
                            )
                        ],
                        # Starve the last inner call of gas.
                        gas_limits=[None] * Spec.MAX_EXIT_REQUESTS_PER_BLOCK
                        + [100],
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_contract_last_oog",
        ),
    ],
)
def test_builder_requests_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """
    Test that a builder request whose triggering call runs out of gas is not
    included, while the other requests in the block are.

    The gas limits are supplied per-request via the interaction's `gas_limits`
    list rather than being baked into the request descriptor, keeping the gas
    concern isolated to these dedicated tests.
    """
    blockchain_test(pre=pre, post={}, blocks=blocks)
