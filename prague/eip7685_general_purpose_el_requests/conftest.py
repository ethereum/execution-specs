"""
Fixtures for the EIP-7685 deposit tests.
"""

from typing import Dict, List

import pytest

from ethereum_test_tools import Account, Address, Block, BlockException, Header, Transaction

from ..eip6110_deposits.helpers import DepositInteractionBase, DepositRequest
from ..eip7002_el_triggerable_withdrawals.helpers import (
    WithdrawalRequest,
    WithdrawalRequestInteractionBase,
)


@pytest.fixture
def pre(
    requests: List[DepositInteractionBase | WithdrawalRequestInteractionBase],
) -> Dict[Address, Account]:
    """
    Initial state of the accounts. Every deposit transaction defines their own pre-state
    requirements, and this fixture aggregates them all.
    """
    pre: Dict[Address, Account] = {}
    for d in requests:
        d.update_pre(pre)
    return pre


@pytest.fixture
def txs(
    requests: List[DepositInteractionBase | WithdrawalRequestInteractionBase],
) -> List[Transaction]:
    """List of transactions to include in the block."""
    address_nonce: Dict[Address, int] = {}
    txs = []
    for r in requests:
        nonce = 0
        if r.sender_account.address in address_nonce:
            nonce = address_nonce[r.sender_account.address]
        txs.append(r.transaction(nonce))
        address_nonce[r.sender_account.address] = nonce + 1
    return txs


@pytest.fixture
def block_body_override_requests() -> List[DepositRequest] | None:
    """List of requests that overwrite the requests in the header. None by default."""
    return None


@pytest.fixture
def exception() -> BlockException | None:
    """Block exception expected by the tests. None by default."""
    return None


@pytest.fixture
def blocks(
    requests: List[DepositInteractionBase | WithdrawalRequestInteractionBase],
    block_body_override_requests: List[DepositRequest | WithdrawalRequest] | None,
    txs: List[Transaction],
    exception: BlockException | None,
) -> List[Block]:
    """List of blocks that comprise the test."""
    included_deposit_requests = []
    included_withdrawal_requests = []
    # Single block therefore base fee
    withdrawal_request_fee = 1
    for r in requests:
        if isinstance(r, DepositInteractionBase):
            included_deposit_requests += r.valid_requests(10**18)
        elif isinstance(r, WithdrawalRequestInteractionBase):
            included_withdrawal_requests += r.valid_requests(withdrawal_request_fee)

    return [
        Block(
            txs=txs,
            header_verify=Header(
                requests_root=included_deposit_requests + included_withdrawal_requests,
            ),
            requests=block_body_override_requests,
            exception=exception,
        )
    ]
