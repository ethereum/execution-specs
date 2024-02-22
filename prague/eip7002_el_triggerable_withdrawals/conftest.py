"""
Fixtures for the EIP-7002 deposit tests.
"""
from typing import Dict, List

import pytest

from ethereum_test_tools import Account, Address, Block, Header

from .helpers import WithdrawalRequest, WithdrawalRequestInteractionBase
from .spec import Spec


@pytest.fixture
def included_requests(
    blocks_withdrawal_requests: List[List[WithdrawalRequestInteractionBase]],
) -> List[List[WithdrawalRequest]]:
    """
    Return the list of withdrawal requests that should be included in each block.
    """
    excess_withdrawal_requests = 0
    carry_over_requests: List[WithdrawalRequest] = []
    per_block_included_requests: List[List[WithdrawalRequest]] = []
    for block_withdrawal_requests in blocks_withdrawal_requests:
        # Get fee for the current block
        current_minimum_fee = Spec.get_fee(excess_withdrawal_requests)

        # With the fee, get the valid withdrawal requests for the current block
        current_block_requests = []
        for w in block_withdrawal_requests:
            current_block_requests += w.valid_requests(current_minimum_fee)

        # Get the withdrawal requests that should be included in the block
        pending_requests = carry_over_requests + current_block_requests
        per_block_included_requests.append(
            pending_requests[: Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK]
        )
        carry_over_requests = pending_requests[Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK :]

        # Update the excess withdrawal requests
        excess_withdrawal_requests = Spec.get_excess_withdrawal_requests(
            excess_withdrawal_requests,
            len(current_block_requests),
        )
    return per_block_included_requests


@pytest.fixture
def pre(
    blocks_withdrawal_requests: List[List[WithdrawalRequestInteractionBase]],
) -> Dict[Address, Account]:
    """
    Initial state of the accounts. Every withdrawal transaction defines their own pre-state
    requirements, and this fixture aggregates them all.
    """
    pre: Dict[Address, Account] = {}
    for requests in blocks_withdrawal_requests:
        for d in requests:
            d.update_pre(pre)
    return pre


@pytest.fixture
def blocks(
    blocks_withdrawal_requests: List[List[WithdrawalRequestInteractionBase]],
    included_requests: List[List[WithdrawalRequest]],
) -> List[Block]:
    """
    Return the list of blocks that should be included in the test.
    """
    blocks: List[Block] = []
    address_nonce: Dict[Address, int] = {}
    for i in range(len(blocks_withdrawal_requests)):
        txs = []
        for r in blocks_withdrawal_requests[i]:
            nonce = 0
            if r.sender_account.address in address_nonce:
                nonce = address_nonce[r.sender_account.address]
            txs.append(r.transaction(nonce))
            address_nonce[r.sender_account.address] = nonce + 1
        blocks.append(
            Block(
                txs=txs,
                header_verify=Header(
                    requests_root=included_requests[i],
                ),
            )
        )
    return blocks
