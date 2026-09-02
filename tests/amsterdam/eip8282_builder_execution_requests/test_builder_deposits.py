"""
Builder deposit request tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderDepositRequest,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
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
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                # A top-up of more than the minimum stake.
                                amount=32 * MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_above_minimum",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            ),
                            BuilderDepositRequest(
                                pubkey=0x04,
                                withdrawal_credentials=0x05,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x06,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_same_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x04,
                                withdrawal_credentials=0x05,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x06,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_different_eoa",
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
                            )
                            for i in range(BuilderDepositRequest.max_per_block)
                        ],
                    ),
                ],
            ],
            id="single_block_max_builder_deposits_from_contract",
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
                            )
                            for i in range(
                                BuilderDepositRequest.max_per_block + 1
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_carry_over_builder_deposits_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                # One gwei below the minimum stake.
                                amount=MIN_DEPOSIT_GWEI - 1,
                                signature=0x03,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_below_minimum",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                # One wei short of `fee + amount * 1 gwei`.
                                extra_wei=-1,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_insufficient_value",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                calldata_modifier=lambda x: x[:-1],
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_input_too_short",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                calldata_modifier=lambda x: x + b"\x00",
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_input_too_long",
        ),
    ],
)
def test_builder_deposit_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """
    Test submitting valid builder deposit requests to the builder deposit
    predeploy and verifying they are dequeued into the block's requests.
    """
    blockchain_test(pre=pre, post={}, blocks=blocks)
