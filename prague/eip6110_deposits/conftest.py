"""
Fixtures for the EIP-6110 deposit tests.
"""
from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import Alloc, Block, BlockException, Header, Requests, Transaction

from .helpers import DepositInteractionBase, DepositRequest


@pytest.fixture
def update_pre(pre: Alloc, requests: List[DepositInteractionBase]):
    """
    Initial state of the accounts. Every deposit transaction defines their own pre-state
    requirements, and this fixture aggregates them all.
    """
    for d in requests:
        d.update_pre(pre)


@pytest.fixture
def txs(
    requests: List[DepositInteractionBase],
    update_pre: None,  # Fixture is used for its side effects
) -> List[Transaction]:
    """List of transactions to include in the block."""
    txs = []
    for r in requests:
        txs += r.transactions()
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
    fork: Fork,
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
                requests_hash=Requests(
                    *included_requests,
                    max_request_type=fork.max_request_type(block_number=1, timestamp=1),
                ),
            ),
            requests=Requests(
                *block_body_override_requests,
                max_request_type=fork.max_request_type(block_number=1, timestamp=1),
            ).requests_list
            if block_body_override_requests is not None
            else None,
            exception=exception,
        )
    ]
