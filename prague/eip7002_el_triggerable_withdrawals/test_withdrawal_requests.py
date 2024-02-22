"""
abstract: Tests [EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002)
    Test execution layer triggered exits [EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002)

"""  # noqa: E501

from typing import Dict, List

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Header,
    Macros,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import TestAddress, TestAddress2

from .helpers import (
    TestAccount2,
    WithdrawalRequest,
    WithdrawalRequestContract,
    WithdrawalRequestInteractionBase,
    WithdrawalRequestTransaction,
    get_n_fee_increment_blocks,
)
from .spec import Spec, ref_spec_7002

REFERENCE_SPEC_GIT_PATH = ref_spec_7002.git_path
REFERENCE_SPEC_VERSION = ref_spec_7002.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize(
    "blocks_withdrawal_requests",
    [
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=0,
                        ),
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa_insufficient_fee",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                            calldata_modifier=lambda x: x[:-1],
                            valid=False,
                        ),
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa_input_too_short",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                            calldata_modifier=lambda x: x + b"\x00",
                            valid=False,
                        ),
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_eoa_input_too_long",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x02,
                            amount=Spec.MAX_AMOUNT - 1,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_from_same_eoa",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x02,
                            amount=Spec.MAX_AMOUNT - 1,
                            fee=Spec.get_fee(0),
                        ),
                        sender_account=TestAccount2,
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_from_different_eoa",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=i + 1,
                            amount=0 if i % 2 == 0 else Spec.MAX_AMOUNT,
                            fee=Spec.get_fee(0),
                        ),
                    )
                    for i in range(Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK)
                ],
            ],
            id="single_block_max_withdrawal_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=0,
                        ),
                    ),
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x02,
                            amount=Spec.MAX_AMOUNT - 1,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_first_reverts",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x02,
                            amount=Spec.MAX_AMOUNT - 1,
                            fee=0,
                        ),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_last_reverts",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                            # Value obtained from trace minus one
                            gas_limit=114_247 - 1,
                            valid=False,
                        ),
                    ),
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x02,
                            amount=0,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_first_oog",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=0x02,
                            amount=0,
                            fee=Spec.get_fee(0),
                            # Value obtained from trace minus one
                            gas_limit=80_047 - 1,
                            valid=False,
                        ),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_request_last_oog",
        ),
        pytest.param(
            [
                # Block 1
                [
                    WithdrawalRequestTransaction(
                        request=WithdrawalRequest(
                            validator_public_key=i + 1,
                            amount=0 if i % 2 == 0 else Spec.MAX_AMOUNT,
                            fee=Spec.get_fee(0),
                        ),
                    )
                    for i in range(Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK * 2)
                ],
                # Block 2, no new withdrawal requests, but queued requests from previous block
                [],
                # Block 3, no new nor queued withdrawal requests
                [],
            ],
            id="multiple_block_above_max_withdrawal_requests_from_eoa",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestContract(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                        ),
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_from_contract",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestContract(
                        request=[
                            WithdrawalRequest(
                                validator_public_key=i + 1,
                                amount=Spec.MAX_AMOUNT - 1 if i % 2 == 0 else 0,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestContract(
                        request=[
                            WithdrawalRequest(
                                validator_public_key=1,
                                amount=Spec.MAX_AMOUNT,
                                fee=0,
                            )
                        ]
                        + [
                            WithdrawalRequest(
                                validator_public_key=i + 1,
                                amount=Spec.MAX_AMOUNT - 1 if i % 2 == 0 else 0,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(1, Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_first_reverts",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestContract(
                        request=[
                            WithdrawalRequest(
                                validator_public_key=i + 1,
                                amount=Spec.MAX_AMOUNT - 1 if i % 2 == 0 else 0,
                                fee=Spec.get_fee(0),
                            )
                            for i in range(Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK - 1)
                        ]
                        + [
                            WithdrawalRequest(
                                validator_public_key=Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK,
                                amount=Spec.MAX_AMOUNT - 1
                                if (Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK - 1) % 2 == 0
                                else 0,
                                fee=0,
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
                    WithdrawalRequestContract(
                        request=[
                            WithdrawalRequest(
                                validator_public_key=1,
                                amount=Spec.MAX_AMOUNT - 1,
                                gas_limit=100,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                        ]
                        + [
                            WithdrawalRequest(
                                validator_public_key=i + 1,
                                amount=Spec.MAX_AMOUNT - 1 if i % 2 == 0 else 0,
                                gas_limit=1_000_000,
                                fee=Spec.get_fee(0),
                                valid=True,
                            )
                            for i in range(1, Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK)
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_first_oog",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestContract(
                        request=[
                            WithdrawalRequest(
                                validator_public_key=i + 1,
                                amount=Spec.MAX_AMOUNT - 1 if i % 2 == 0 else 0,
                                fee=Spec.get_fee(0),
                                gas_limit=1_000_000,
                                valid=True,
                            )
                            for i in range(Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK)
                        ]
                        + [
                            WithdrawalRequest(
                                validator_public_key=Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK,
                                amount=Spec.MAX_AMOUNT - 1,
                                gas_limit=100,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_last_oog",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestContract(
                        request=[
                            WithdrawalRequest(
                                validator_public_key=i + 1,
                                amount=Spec.MAX_AMOUNT - 1 if i % 2 == 0 else 0,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                            for i in range(Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK)
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
                    WithdrawalRequestContract(
                        request=[
                            WithdrawalRequest(
                                validator_public_key=i + 1,
                                amount=Spec.MAX_AMOUNT - 1 if i % 2 == 0 else 0,
                                fee=Spec.get_fee(0),
                                valid=False,
                            )
                            for i in range(Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK)
                        ],
                        extra_code=Macros.OOG(),
                    ),
                ],
            ],
            id="single_block_multiple_withdrawal_requests_from_contract_caller_oog",
        ),
        pytest.param(
            # Test the first 50 fee increments
            get_n_fee_increment_blocks(50),
            id="multiple_block_fee_increments",
        ),
        pytest.param(
            [
                [
                    WithdrawalRequestContract(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                            valid=False,
                        ),
                        call_type=Op.DELEGATECALL,
                    ),
                    WithdrawalRequestContract(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                            valid=False,
                        ),
                        call_type=Op.STATICCALL,
                    ),
                    WithdrawalRequestContract(
                        request=WithdrawalRequest(
                            validator_public_key=0x01,
                            amount=0,
                            fee=Spec.get_fee(0),
                            valid=False,
                        ),
                        call_type=Op.CALLCODE,
                    ),
                ],
            ],
            id="single_block_single_withdrawal_request_delegatecall_staticcall_callcode",
        ),
    ],
)
def test_withdrawal_requests(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Dict[Address, Account],
):
    """
    Test making a withdrawal request to the beacon chain.
    """
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
                WithdrawalRequest(
                    validator_public_key=0x01,
                    amount=0,
                    source_address=Address(0),
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="no_withdrawals_non_empty_requests_list",
        ),
        pytest.param(
            [
                WithdrawalRequestTransaction(
                    request=WithdrawalRequest(
                        validator_public_key=0x01,
                        amount=0,
                        fee=Spec.get_fee(0),
                    ),
                ),
            ],
            [],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_empty_requests_list",
        ),
        pytest.param(
            [
                WithdrawalRequestTransaction(
                    request=WithdrawalRequest(
                        validator_public_key=0x01,
                        amount=0,
                        fee=Spec.get_fee(0),
                    ),
                ),
            ],
            [
                WithdrawalRequest(
                    validator_public_key=0x02,
                    amount=0,
                    source_address=TestAddress,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_public_key_mismatch",
        ),
        pytest.param(
            [
                WithdrawalRequestTransaction(
                    request=WithdrawalRequest(
                        validator_public_key=0x01,
                        amount=0,
                        fee=Spec.get_fee(0),
                    ),
                ),
            ],
            [
                WithdrawalRequest(
                    validator_public_key=0x01,
                    amount=1,
                    source_address=TestAddress,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_amount_mismatch",
        ),
        pytest.param(
            [
                WithdrawalRequestTransaction(
                    request=WithdrawalRequest(
                        validator_public_key=0x01,
                        amount=0,
                        fee=Spec.get_fee(0),
                    ),
                ),
            ],
            [
                WithdrawalRequest(
                    validator_public_key=0x01,
                    amount=0,
                    source_address=TestAddress2,
                )
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_request_source_address_mismatch",
        ),
        pytest.param(
            [
                WithdrawalRequestTransaction(
                    request=WithdrawalRequest(
                        validator_public_key=0x01,
                        amount=0,
                        fee=Spec.get_fee(0),
                    ),
                ),
                WithdrawalRequestTransaction(
                    request=WithdrawalRequest(
                        validator_public_key=0x02,
                        amount=0,
                        fee=Spec.get_fee(0),
                    ),
                ),
            ],
            [
                WithdrawalRequest(
                    validator_public_key=0x02,
                    amount=0,
                    source_address=TestAddress,
                ),
                WithdrawalRequest(
                    validator_public_key=0x01,
                    amount=0,
                    source_address=TestAddress,
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="two_withdrawal_requests_out_of_order",
        ),
        pytest.param(
            [
                WithdrawalRequestTransaction(
                    request=WithdrawalRequest(
                        validator_public_key=0x01,
                        amount=0,
                        fee=Spec.get_fee(0),
                    ),
                ),
            ],
            [
                WithdrawalRequest(
                    validator_public_key=0x01,
                    amount=0,
                    source_address=TestAddress,
                ),
                WithdrawalRequest(
                    validator_public_key=0x01,
                    amount=0,
                    source_address=TestAddress,
                ),
            ],
            BlockException.INVALID_REQUESTS,
            id="single_withdrawal_requests_duplicate_in_requests_list",
        ),
    ],
)
def test_withdrawal_requests_negative(
    blockchain_test: BlockchainTestFiller,
    requests: List[WithdrawalRequestInteractionBase],
    block_body_override_requests: List[WithdrawalRequest],
    exception: BlockException,
):
    """
    Test blocks where the requests list and the actual withdrawal requests that happened in the
    block's transactions do not match.
    """
    # No previous block so fee is the base
    fee = 1
    current_block_requests = []
    for w in requests:
        current_block_requests += w.valid_requests(fee)
    included_requests = current_block_requests[: Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK]

    pre: Dict[Address, Account] = {}
    for d in requests:
        d.update_pre(pre)

    address_nonce: Dict[Address, int] = {}
    txs = []
    for r in requests:
        nonce = 0
        if r.sender_account.address in address_nonce:
            nonce = address_nonce[r.sender_account.address]
        txs.append(r.transaction(nonce))
        address_nonce[r.sender_account.address] = nonce + 1
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(
                    requests_root=included_requests,
                ),
                requests=block_body_override_requests,
                exception=exception,
            )
        ],
    )
