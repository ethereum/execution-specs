"""
Tests [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).
"""

from typing import List

import pytest
from execution_testing import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    ConsolidationRequest,
    Macros,
    Op,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
    TestAddress,
    TestAddress2,
    fee_increment_blocks,
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
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x01,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_from_eoa_equal_pubkeys",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_from_eoa_max_pubkeys",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=0,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_from_eoa_insufficient_fee",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                calldata_modifier=lambda x: x[:-1],
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_from_eoa_input_too_short",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                calldata_modifier=lambda x: x + b"\x00",
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_from_eoa_input_too_long",
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
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_from_same_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                            )
                        ],
                    ),
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_from_different_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                            )
                            for i in range(ConsolidationRequest.max_per_block)
                        ],
                    )
                ],
            ],
            id="single_block_max_consolidation_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=0,
                                valid=False,
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_first_reverts",
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
                                fee=0,
                                valid=False,
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_last_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ]
                    )
                ],
            ],
            id="multiple_block_above_max_consolidation_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ],
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ],
                        call_depth=100,
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_call_depth_high",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x00,
                                target_pubkey=0x01,
                                fee=0,
                                valid=False,
                            )
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                            )
                            for i in range(
                                1,
                                ConsolidationRequest.max_per_block * 5,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_first_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                                fee=0,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_last_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                valid=False,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ],
                        extra_code=Op.REVERT(0, 0),
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_caller_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                valid=False,
                            )
                            for i in range(
                                ConsolidationRequest.max_per_block * 5
                            )
                        ],
                        extra_code=Macros.OOG(),
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_caller_oog",
        ),
        pytest.param(
            # Test the first 50 fee increments
            fee_increment_blocks(ConsolidationRequest, 50),
            id="multiple_block_fee_increments",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.DELEGATECALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.STATICCALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.CALLCODE,
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_delegatecall_staticcall_callcode",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.DELEGATECALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.STATICCALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.CALLCODE,
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_delegatecall_staticcall_callcode_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.DELEGATECALL,
                        call_depth=1024,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.STATICCALL,
                        call_depth=1024,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                valid=False,
                            )
                        ],
                        call_type=Op.CALLCODE,
                        call_depth=1024,
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_delegatecall_staticcall_callcode_call_depth_high",
        ),
    ],
)
def test_consolidation_requests(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """Test making a consolidation request to the beacon chain."""
    blockchain_test(pre=pre, post={}, blocks=blocks)


@pytest.mark.parametrize(
    "system_contract_interactions_per_block,block_body_override_requests,"
    "exception",
    [
        pytest.param(
            [[]],
            [
                ConsolidationRequest(
                    source_pubkey=0x01,
                    target_pubkey=0x02,
                    source_address=Address(0),
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="no_consolidations_non_empty_requests_list",
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
                        ]
                    ),
                ]
            ],
            [],
            BlockException.INVALID_REQUESTS,
            id="single_consolidation_request_empty_requests_list",
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
                        ]
                    ),
                ]
            ],
            [
                ConsolidationRequest(
                    source_pubkey=0x00,
                    target_pubkey=0x02,
                    source_address=TestAddress,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_consolidation_request_source_public_key_mismatch",
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
                        ]
                    ),
                ]
            ],
            [
                ConsolidationRequest(
                    source_pubkey=0x01,
                    target_pubkey=0x00,
                    source_address=TestAddress,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_consolidation_request_target_public_key_mismatch",
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
                        ]
                    ),
                ]
            ],
            [
                ConsolidationRequest(
                    source_pubkey=0x02,
                    target_pubkey=0x01,
                    source_address=TestAddress,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_consolidation_request_pubkeys_swapped",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                            )
                        ],
                    ),
                ]
            ],
            [
                ConsolidationRequest(
                    source_pubkey=0x01,
                    target_pubkey=0x02,
                    source_address=TestAddress2,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_consolidation_request_source_address_mismatch",
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
                            ),
                        ],
                    ),
                ]
            ],
            [
                ConsolidationRequest(
                    source_pubkey=0x03,
                    target_pubkey=0x04,
                    source_address=TestAddress,
                ),
                ConsolidationRequest(
                    source_pubkey=0x01,
                    target_pubkey=0x02,
                    source_address=TestAddress,
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="two_consolidation_requests_out_of_order",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                            )
                        ],
                    ),
                ]
            ],
            [
                ConsolidationRequest(
                    source_pubkey=0x01,
                    target_pubkey=0x02,
                    source_address=TestAddress,
                ),
                ConsolidationRequest(
                    source_pubkey=0x01,
                    target_pubkey=0x02,
                    source_address=TestAddress,
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="single_consolidation_requests_duplicate_in_requests_list",
        ),
    ],
)
@pytest.mark.exception_test
def test_consolidation_requests_negative(
    blockchain_test: BlockchainTestFiller,
    override_blocks: List[Block],
    pre: Alloc,
) -> None:
    """
    Test blocks where the requests list and the actual consolidation requests
    that happened in the block's transactions do not match.
    """
    blockchain_test(pre=pre, post={}, blocks=override_blocks)
