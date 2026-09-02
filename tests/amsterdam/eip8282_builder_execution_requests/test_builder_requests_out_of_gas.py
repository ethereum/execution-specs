"""
Out-of-gas builder request tests.

Tests that builder deposit and exit requests whose triggering call runs out of
gas are not included in the block, for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).

"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderDepositRequest,
    BuilderExitRequest,
    SystemContractInteractionMeasuredOutOfGasContract,
)

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = pytest.mark.valid_from("Amsterdam")

MIN_DEPOSIT_GWEI = BuilderDepositRequest.min_deposit_wei // 10**9


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionMeasuredOutOfGasContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                fee=BuilderDepositRequest.get_fee(0),
                            ),
                            BuilderDepositRequest(
                                pubkey=0x04,
                                withdrawal_credentials=0x05,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x06,
                                fee=BuilderDepositRequest.get_fee(0),
                            ),
                            BuilderDepositRequest(
                                pubkey=0x07,
                                withdrawal_credentials=0x08,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x09,
                                fee=BuilderDepositRequest.get_fee(0),
                                # Starved of gas by the relay contract.
                                valid=False,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_builder_deposit_out_of_gas",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionMeasuredOutOfGasContract(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                fee=BuilderExitRequest.get_fee(0),
                            ),
                            BuilderExitRequest(
                                pubkey=0x02,
                                fee=BuilderExitRequest.get_fee(0),
                            ),
                            BuilderExitRequest(
                                pubkey=0x03,
                                fee=BuilderExitRequest.get_fee(0),
                                # Starved of gas by the relay contract.
                                valid=False,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_builder_exit_out_of_gas",
        ),
    ],
)
def test_builder_request_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """
    Test that a builder request whose triggering call runs out of gas is not
    included, while the other requests in the block are.

    The relay contract self-measures the required gas and forwards one gas less
    than needed to the invalid request, so the out-of-gas holds across forks
    without any hard-coded gas value.
    """
    blockchain_test(pre=pre, post={}, blocks=blocks)
