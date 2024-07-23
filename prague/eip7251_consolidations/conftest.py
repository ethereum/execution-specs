"""
Fixtures for the EIP-7251 consolidations tests.
"""
from itertools import zip_longest
from typing import List

import pytest

from ethereum_test_tools import Alloc, Block, Header

from .helpers import ConsolidationRequest, ConsolidationRequestInteractionBase
from .spec import Spec


@pytest.fixture
def update_pre(
    pre: Alloc,
    blocks_consolidation_requests: List[List[ConsolidationRequestInteractionBase]],
):
    """
    Initial state of the accounts. Every deposit transaction defines their own pre-state
    requirements, and this fixture aggregates them all.
    """
    for requests in blocks_consolidation_requests:
        for r in requests:
            r.update_pre(pre)


@pytest.fixture
def included_requests(
    update_pre: None,  # Fixture is used for its side effects
    blocks_consolidation_requests: List[List[ConsolidationRequestInteractionBase]],
) -> List[List[ConsolidationRequest]]:
    """
    Return the list of consolidation requests that should be included in each block.
    """
    excess_consolidation_requests = 0
    carry_over_requests: List[ConsolidationRequest] = []
    per_block_included_requests: List[List[ConsolidationRequest]] = []
    for block_consolidation_requests in blocks_consolidation_requests:
        # Get fee for the current block
        current_minimum_fee = Spec.get_fee(excess_consolidation_requests)

        # With the fee, get the valid consolidation requests for the current block
        current_block_requests = []
        for w in block_consolidation_requests:
            current_block_requests += w.valid_requests(current_minimum_fee)

        # Get the consolidation requests that should be included in the block
        pending_requests = carry_over_requests + current_block_requests
        per_block_included_requests.append(
            pending_requests[: Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK]
        )
        carry_over_requests = pending_requests[Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK :]

        # Update the excess consolidation requests
        excess_consolidation_requests = Spec.get_excess_consolidation_requests(
            excess_consolidation_requests,
            len(current_block_requests),
        )

    while carry_over_requests:
        # Keep adding blocks until all consolidation requests are included
        per_block_included_requests.append(
            carry_over_requests[: Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK]
        )
        carry_over_requests = carry_over_requests[Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK :]

    return per_block_included_requests


@pytest.fixture
def blocks(
    update_pre: None,  # Fixture is used for its side effects
    blocks_consolidation_requests: List[List[ConsolidationRequestInteractionBase]],
    included_requests: List[List[ConsolidationRequest]],
) -> List[Block]:
    """
    Return the list of blocks that should be included in the test.
    """
    return [  # type: ignore
        Block(
            txs=sum((r.transactions() for r in block_requests), []),
            header_verify=Header(requests_root=block_included_requests),
        )
        for block_requests, block_included_requests in zip_longest(
            blocks_consolidation_requests,
            included_requests,
            fillvalue=[],
        )
    ] + [
        Block(header_verify=Header(requests_root=[]))
    ]  # Add an empty block at the end to verify that no more consolidation requests are included
