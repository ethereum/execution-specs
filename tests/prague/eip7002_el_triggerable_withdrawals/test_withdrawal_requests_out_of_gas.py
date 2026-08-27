"""
Out-of-gas withdrawal request tests.

Tests that withdrawal requests whose triggering call runs out of gas are not
included in the block, for
[EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002).

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

from .helpers import WithdrawalRequest
from .spec import Spec, ref_spec_7002

REFERENCE_SPEC_GIT_PATH = ref_spec_7002.git_path
REFERENCE_SPEC_VERSION = ref_spec_7002.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionMeasuredOutOfGasContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                fee=WithdrawalRequest.get_fee(0),
                            ),
                            WithdrawalRequest(
                                validator_pubkey=0x02,
                                amount=0,
                                fee=WithdrawalRequest.get_fee(0),
                            ),
                            WithdrawalRequest(
                                validator_pubkey=0x03,
                                amount=0,
                                fee=WithdrawalRequest.get_fee(0),
                                # Starved of gas by the relay contract.
                                valid=False,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_measured_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=1,
                                amount=Spec.MAX_AMOUNT - 1,
                                valid=False,
                            )
                        ]
                        + [
                            WithdrawalRequest(
                                validator_pubkey=i + 1,
                                amount=Spec.MAX_AMOUNT - 1
                                if i % 2 == 0
                                else 0,
                                valid=True,
                            )
                            for i in range(
                                1, Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK
                            )
                        ],
                        # Starve the first inner call of gas
                        gas_limits=[100]
                        + [None]
                        * (Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK - 1),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_first_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=i + 1,
                                amount=Spec.MAX_AMOUNT - 1
                                if i % 2 == 0
                                else 0,
                                valid=True,
                            )
                            for i in range(
                                Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK
                            )
                        ]
                        + [
                            WithdrawalRequest(
                                validator_pubkey=Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK,
                                amount=Spec.MAX_AMOUNT - 1,
                                valid=False,
                            )
                        ],
                        # Starve the last inner call of gas
                        gas_limits=[None]
                        * Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK
                        + [100],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_last_oog",
        ),
    ],
)
def test_withdrawal_requests_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """
    Test that a withdrawal request whose triggering call runs out of gas is
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
