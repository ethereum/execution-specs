"""Fixtures for the EIP-6110 deposit tests."""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockException,
    Fork,
    Header,
    Requests,
    Transaction,
)

from .helpers import DepositInteractionBase, DepositRequest


@pytest.fixture
def prepared_requests(
    pre: Alloc, requests: List[DepositInteractionBase]
) -> List[DepositInteractionBase]:
    """
    Allocate accounts/contracts for each request in `pre` and return copies
    with the allocated state populated. The parametrize value `requests` is
    not mutated, so it stays pristine across fixture format runs.
    """
    return [r.update_pre(pre) for r in requests]


@pytest.fixture
def txs(
    fork: Fork,
    prepared_requests: List[DepositInteractionBase],
) -> List[Transaction]:
    """List of transactions to include in the block."""
    txs = []
    for r in prepared_requests:
        txs += r.transactions()
    # EIP-7976 (enabled with EIP-8037 on Amsterdam) raises calldata
    # floor cost, pushing the intrinsic above the hardcoded
    # tx_gas_limit of the large-calldata OOG fixtures. Lift each
    # tx's gas_limit to the new intrinsic only when it falls below;
    # the tx still OOGs on its first execution opcode, preserving
    # the fixture's no-deposits-applied outcome.
    if not (fork.is_eip_enabled(7976) and fork.is_eip_enabled(8037)):
        return txs
    current_calc = fork.transaction_intrinsic_cost_calculator()
    bumped: List[Transaction] = []
    for tx in txs:
        current_intrinsic = current_calc(calldata=tx.data)
        if tx.gas_limit < current_intrinsic:
            bumped.append(tx.copy(gas_limit=current_intrinsic))
        else:
            bumped.append(tx)
    return bumped


@pytest.fixture
def block_body_override_requests() -> List[DepositRequest] | None:
    """
    List of requests that overwrite the requests in the header. None by
    default.
    """
    return None


@pytest.fixture
def exception() -> BlockException | None:
    """Block exception expected by the tests. None by default."""
    return None


@pytest.fixture
def included_requests(
    prepared_requests: List[DepositInteractionBase],
) -> List[DepositRequest]:
    """
    Return the list of deposit requests that should be included in each block.
    """
    valid_requests: List[DepositRequest] = []

    for d in prepared_requests:
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
                ),
            ),
            requests=Requests(
                *block_body_override_requests,
            ).requests_list
            if block_body_override_requests is not None
            else None,
            exception=exception,
        )
    ]
