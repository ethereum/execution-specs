"""
Out-of-gas withdrawal request tests.

Tests that withdrawal requests whose triggering call runs out of gas are not
included in the block, for
[EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002).

The gas limits are supplied per-request via the interaction's `gas_limits`
list rather than being baked into the withdrawal request descriptor, keeping
the gas concern isolated to these dedicated tests.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
    WithdrawalRequest,
)

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
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            ),
                            WithdrawalRequest(
                                validator_pubkey=0x02,
                                amount=0,
                            ),
                        ],
                        # Value obtained from trace minus one
                        gas_limits=[114_247 - 1, None],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_first_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            ),
                            WithdrawalRequest(
                                validator_pubkey=0x02,
                                amount=0,
                                valid=False,
                            ),
                        ],
                        # Value obtained from trace minus one
                        gas_limits=[None, 80_047 - 1],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_last_oog",
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
                            for i in range(1, WithdrawalRequest.max_per_block)
                        ],
                        # Starve the first inner call of gas
                        gas_limits=[100]
                        + [None] * (WithdrawalRequest.max_per_block - 1),
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
                            for i in range(WithdrawalRequest.max_per_block)
                        ]
                        + [
                            WithdrawalRequest(
                                validator_pubkey=WithdrawalRequest.max_per_block,
                                amount=Spec.MAX_AMOUNT - 1,
                                valid=False,
                            )
                        ],
                        # Starve the last inner call of gas
                        gas_limits=[None] * WithdrawalRequest.max_per_block
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

    The gas limits are supplied per-request via the interaction's `gas_limits`
    list rather than being baked into the withdrawal request descriptor,
    keeping the gas concern isolated to these dedicated tests.
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
