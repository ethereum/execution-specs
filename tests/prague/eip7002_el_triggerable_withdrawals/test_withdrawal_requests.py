"""
Tests [EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002).
"""

from typing import List

import pytest
from execution_testing import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Macros,
    Op,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
    TestAddress,
    TestAddress2,
    WithdrawalRequest,
    fee_increment_blocks,
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
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                fee=0,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa_insufficient_fee",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                calldata_modifier=lambda x: x[:-1],
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa_input_too_short",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                calldata_modifier=lambda x: x + b"\x00",
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa_input_too_long",
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
                                amount=Spec.MAX_AMOUNT - 1,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_from_same_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            )
                        ],
                    ),
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x02,
                                amount=Spec.MAX_AMOUNT - 1,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_from_different_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=i + 1,
                                amount=0 if i % 2 == 0 else Spec.MAX_AMOUNT,
                            )
                            for i in range(WithdrawalRequest.max_per_block)
                        ],
                    )
                ],
            ],
            id="single_block_max_withdrawal_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                fee=0,
                                valid=False,
                            ),
                            WithdrawalRequest(
                                validator_pubkey=0x02,
                                amount=Spec.MAX_AMOUNT - 1,
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_first_reverts",
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
                                amount=Spec.MAX_AMOUNT - 1,
                                fee=0,
                                valid=False,
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_last_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=i + 1,
                                amount=0 if i % 2 == 0 else Spec.MAX_AMOUNT,
                            )
                            for i in range(WithdrawalRequest.max_per_block * 2)
                        ]
                    )
                ],
            ],
            id="multiple_block_above_max_withdrawal_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            ),
                        ],
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_contract_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            ),
                        ],
                        call_depth=264,
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_contract_call_depth_high",
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
                            )
                            for i in range(WithdrawalRequest.max_per_block)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=1,
                                amount=Spec.MAX_AMOUNT,
                                fee=0,
                                valid=False,
                            )
                        ]
                        + [
                            WithdrawalRequest(
                                validator_pubkey=i + 1,
                                amount=Spec.MAX_AMOUNT - 1
                                if i % 2 == 0
                                else 0,
                            )
                            for i in range(1, WithdrawalRequest.max_per_block)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_first_reverts",
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
                            )
                            for i in range(WithdrawalRequest.max_per_block - 1)
                        ]
                        + [
                            WithdrawalRequest(
                                validator_pubkey=WithdrawalRequest.max_per_block,
                                amount=(
                                    Spec.MAX_AMOUNT - 1
                                    if (WithdrawalRequest.max_per_block - 1)
                                    % 2
                                    == 0
                                    else 0
                                ),
                                fee=0,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_last_reverts",
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
                                valid=False,
                            )
                            for i in range(WithdrawalRequest.max_per_block)
                        ],
                        extra_code=Op.REVERT(0, 0),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_caller_reverts",
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
                                valid=False,
                            )
                            for i in range(WithdrawalRequest.max_per_block)
                        ],
                        extra_code=Macros.OOG(),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_caller_oog",
        ),
        pytest.param(
            # Test the first 50 fee increments
            fee_increment_blocks(WithdrawalRequest, 50),
            id="multiple_block_fee_increments",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.DELEGATECALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.STATICCALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.CALLCODE,
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_delegatecall_staticcall_callcode",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.DELEGATECALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.STATICCALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.CALLCODE,
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_delegatecall_staticcall_callcode_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.DELEGATECALL,
                        call_depth=1024,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.STATICCALL,
                        call_depth=1024,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                valid=False,
                            )
                        ],
                        call_type=Op.CALLCODE,
                        call_depth=1024,
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_delegatecall_staticcall_callcode_call_depth_high",
        ),
    ],
)
def test_withdrawal_requests(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """Test making a withdrawal request to the beacon chain."""
    blockchain_test(pre=pre, post={}, blocks=blocks)


@pytest.mark.parametrize(
    "system_contract_interactions_per_block,block_body_override_requests,exception",
    [
        pytest.param(
            [[]],
            [
                WithdrawalRequest(
                    validator_pubkey=0x01,
                    amount=0,
                    source_address=Address(0),
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="no_withdrawals_non_empty_requests_list",
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
                        ]
                    ),
                ]
            ],
            [],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_empty_requests_list",
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
                        ]
                    ),
                ]
            ],
            [
                WithdrawalRequest(
                    validator_pubkey=0x02,
                    amount=0,
                    source_address=TestAddress,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_public_key_mismatch",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            )
                        ],
                    ),
                ]
            ],
            [
                WithdrawalRequest(
                    validator_pubkey=0x01,
                    amount=1,
                    source_address=TestAddress,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_amount_mismatch",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            )
                        ],
                    ),
                ]
            ],
            [
                WithdrawalRequest(
                    validator_pubkey=0x01,
                    amount=0,
                    source_address=TestAddress2,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_source_address_mismatch",
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
                            ),
                        ],
                    ),
                ]
            ],
            [
                WithdrawalRequest(
                    validator_pubkey=0x02,
                    amount=0,
                    source_address=TestAddress,
                ),
                WithdrawalRequest(
                    validator_pubkey=0x01,
                    amount=0,
                    source_address=TestAddress,
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="two_withdrawal_requests_out_of_order",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                            )
                        ],
                    ),
                ]
            ],
            [
                WithdrawalRequest(
                    validator_pubkey=0x01,
                    amount=0,
                    source_address=TestAddress,
                ),
                WithdrawalRequest(
                    validator_pubkey=0x01,
                    amount=0,
                    source_address=TestAddress,
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_requests_duplicate_in_requests_list",
        ),
    ],
)
@pytest.mark.exception_test
def test_withdrawal_requests_negative(
    blockchain_test: BlockchainTestFiller,
    override_blocks: List[Block],
    pre: Alloc,
) -> None:
    """
    Test blocks where the requests list and the actual withdrawal requests that
    happened in the block's transactions do not match.
    """
    blockchain_test(pre=pre, post={}, blocks=override_blocks)
