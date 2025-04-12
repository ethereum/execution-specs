"""
abstract: Tests [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251)
    Test execution layer triggered consolidations [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).

"""  # noqa: E501

from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Header,
    Macros,
    Requests,
    TestAddress,
    TestAddress2,
)
from ethereum_test_tools import Opcodes as Op

from .helpers import (
    ConsolidationRequest,
    ConsolidationRequestContract,
    ConsolidationRequestInteractionBase,
    ConsolidationRequestTransaction,
    get_n_fee_increment_blocks,
)
from .spec import Spec, ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize(
    "blocks_consolidation_requests",
    [
        pytest.param(
            [
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x01,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                            )
                        ],
                    ),
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK)
                        ],
                    )
                ],
            ],
            marks=pytest.mark.skip(
                reason="duplicate test due to MAX_CONSOLIDATION_REQUESTS_PER_BLOCK==1"
            ),
            id="single_block_max_consolidation_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=0,
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=0,
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
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                                gas_limit=136_534 - 1,
                                valid=False,
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=Spec.get_fee(0),
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_first_oog",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                            ),
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=Spec.get_fee(0),
                                gas_limit=102_334 - 1,
                                valid=False,
                            ),
                        ]
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_request_last_oog",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
                        ]
                    )
                ],
            ],
            id="multiple_block_above_max_consolidation_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
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
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x00,
                                target_pubkey=0x01,
                                fee=0,
                            )
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(1, Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_first_reverts",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                                fee=0,
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
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                                gas_limit=100,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                gas_limit=1_000_000,
                                fee=Spec.get_fee(0),
                                valid=True,
                            )
                            for i in range(1, Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_first_oog",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                                gas_limit=1_000_000,
                                valid=True,
                            )
                            for i in range(Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
                        ]
                        + [
                            ConsolidationRequest(
                                source_pubkey=-1,
                                target_pubkey=-2,
                                gas_limit=100,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_last_oog",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                            for i in range(Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
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
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=i * 2,
                                target_pubkey=i * 2 + 1,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                            for i in range(Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK * 5)
                        ],
                        extra_code=Macros.OOG(),
                    ),
                ],
            ],
            id="single_block_multiple_consolidation_requests_from_contract_caller_oog",
        ),
        pytest.param(
            # Test the first 50 fee increments
            get_n_fee_increment_blocks(50),
            id="multiple_block_fee_increments",
        ),
        pytest.param(
            [
                [
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                        ],
                        call_type=Op.DELEGATECALL,
                    ),
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                        ],
                        call_type=Op.STATICCALL,
                    ),
                    ConsolidationRequestContract(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                        ],
                        call_type=Op.CALLCODE,
                    ),
                ],
            ],
            id="single_block_single_consolidation_request_delegatecall_staticcall_callcode",
        ),
    ],
)
def test_consolidation_requests(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
):
    """Test making a consolidation request to the beacon chain."""
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.parametrize(
    "requests,block_body_override_requests,exception",
    [
        pytest.param(
            [],
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
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        ),
                    ]
                ),
            ],
            [],
            BlockException.INVALID_REQUESTS,
            id="single_consolidation_request_empty_requests_list",
        ),
        pytest.param(
            [
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        ),
                    ]
                ),
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
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        ),
                    ]
                ),
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
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        ),
                    ]
                ),
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
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        )
                    ],
                ),
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
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        ),
                        ConsolidationRequest(
                            source_pubkey=0x03,
                            target_pubkey=0x04,
                            fee=Spec.get_fee(0),
                        ),
                    ],
                ),
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
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        )
                    ],
                ),
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
    pre: Alloc,
    fork: Fork,
    blockchain_test: BlockchainTestFiller,
    requests: List[ConsolidationRequestInteractionBase],
    block_body_override_requests: List[ConsolidationRequest],
    exception: BlockException,
):
    """
    Test blocks where the requests list and the actual consolidation requests that happened in the
    block's transactions do not match.
    """
    for d in requests:
        d.update_pre(pre)

    # No previous block so fee is the base
    fee = 1
    current_block_requests = []
    for w in requests:
        current_block_requests += w.valid_requests(fee)
    included_requests = current_block_requests[: Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK]

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=sum((r.transactions() for r in requests), []),
                header_verify=Header(
                    requests_hash=Requests(*included_requests),
                ),
                requests=(
                    Requests(*block_body_override_requests).requests_list
                    if block_body_override_requests is not None
                    else None
                ),
                exception=exception,
            )
        ],
    )
