"""
Fixtures for the EIP-6110 deposit tests.
"""
from typing import Dict, List

import pytest

from ethereum_test_tools import Account, Address, Block, BlockException, Header, Transaction

from .helpers import DepositInteractionBase, DepositRequest


@pytest.fixture
def pre(requests: List[DepositInteractionBase]) -> Dict[Address, Account]:
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
    requests: List[DepositInteractionBase],
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
def included_requests(
    requests: List[DepositInteractionBase],
) -> List[DepositRequest]:
    """
    Return the list of deposit requests that should be included in each block.
    """
    valid_requests: List[DepositRequest] = []

    for d in requests:
        valid_requests += d.valid_requests(10**18)

    return valid_requests


@pytest.fixture
def blocks(
    included_requests: List[DepositRequest],
    block_body_override_requests: List[DepositRequest] | None,
    txs: List[Transaction],
    exception: BlockException | None,
) -> List[Block]:
    """List of blocks that comprise the test."""
    return [
        Block(
            txs=txs,
            header_verify=Header(
                requests_root=included_requests,
            ),
            requests=block_body_override_requests,
            exception=exception,
        )
    ]
