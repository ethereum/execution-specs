"""
Shared pytest fixtures for system-contract request tests that use the
excess-based fee dynamic (EIP-7002, EIP-7251, and future forks).

These fixtures are request-type agnostic: they read the per-block dequeue cap
(`max_per_block`), the fee curve (`get_fee`) and the excess update
(`get_excess`) from each `FeeSystemContractRequest` subclass, and track the
excess request count independently per request type. A block may therefore mix
request types, each accounted for with its own fee and queue.
"""

from collections import defaultdict
from itertools import zip_longest
from typing import Dict, List, Type

import pytest
from execution_testing import (
    Alloc,
    Block,
    FeeSystemContractRequest,
    Fork,
    Header,
    Requests,
    SystemContractInteractionBase,
    SystemContractRequest,
    TransitionFork,
)

RequestType = Type[FeeSystemContractRequest]


@pytest.fixture
def prepared_system_contract_interactions_per_block(
    pre: Alloc,
    system_contract_interactions_per_block: List[
        List[SystemContractInteractionBase]
    ],
) -> List[List[SystemContractInteractionBase]]:
    """
    Allocate accounts/contracts for each interaction in `pre` and return copies
    with the allocated state populated. The parametrize value
    `system_contract_interactions_per_block` is not mutated, so it stays
    pristine across fixture format runs.
    """
    return [
        [r.update_pre(pre) for r in block_interactions]
        for block_interactions in system_contract_interactions_per_block
    ]


@pytest.fixture
def included_requests(
    prepared_system_contract_interactions_per_block: List[
        List[SystemContractInteractionBase]
    ],
) -> List[List[SystemContractRequest]]:
    """
    Return the requests that should be included in each block, tracking the
    excess request count independently per request type.
    """
    excess: Dict[RequestType, int] = defaultdict(int)
    carry_over: Dict[RequestType, List[SystemContractRequest]] = defaultdict(
        list
    )
    seen_types: List[RequestType] = []
    per_block_included: List[List[SystemContractRequest]] = []

    for block_interactions in prepared_system_contract_interactions_per_block:
        # Group this block's valid requests by type, keeping only those that
        # meet their type's current (per-block) minimum fee.
        current: Dict[RequestType, List[SystemContractRequest]] = defaultdict(
            list
        )
        for interaction in block_interactions:
            for request in interaction.valid_requests():
                assert isinstance(request, FeeSystemContractRequest)
                request_type = type(request)
                if request_type not in seen_types:
                    seen_types.append(request_type)
                if request.value >= request_type.get_fee(excess[request_type]):
                    current[request_type].append(request)

        block_included: List[SystemContractRequest] = []
        for request_type in seen_types:
            pending = carry_over[request_type] + current[request_type]
            block_included += pending[: request_type.max_per_block]
            carry_over[request_type] = pending[request_type.max_per_block :]
            excess[request_type] = request_type.get_excess(
                excess[request_type], len(current[request_type])
            )
        per_block_included.append(block_included)

    # Keep adding blocks until every type's queue is drained.
    while any(carry_over[request_type] for request_type in seen_types):
        block_included = []
        for request_type in seen_types:
            queue = carry_over[request_type]
            block_included += queue[: request_type.max_per_block]
            carry_over[request_type] = queue[request_type.max_per_block :]
        per_block_included.append(block_included)

    return per_block_included


@pytest.fixture
def timestamp() -> int:
    """Return the timestamp for the first block."""
    return 1


@pytest.fixture
def blocks(
    fork: Fork | TransitionFork,
    prepared_system_contract_interactions_per_block: List[
        List[SystemContractInteractionBase]
    ],
    included_requests: List[List[SystemContractRequest]],
    timestamp: int,
) -> List[Block]:
    """Return the list of blocks that should be included in the test."""
    blocks: List[Block] = []

    for block_interactions, block_included_requests in zip_longest(  # type: ignore
        prepared_system_contract_interactions_per_block,
        included_requests,
        fillvalue=[],
    ):
        block_fork = fork.fork_at(
            block_number=len(blocks) + 1,
            timestamp=timestamp,
        )
        header_verify: Header | None = None
        if block_fork.header_requests_required():
            header_verify = Header(
                requests_hash=Requests(
                    *block_included_requests,
                )
            )
        else:
            assert not block_included_requests
        blocks.append(
            Block(
                txs=sum((r.transactions() for r in block_interactions), []),
                header_verify=header_verify,
                timestamp=timestamp,
            )
        )
        timestamp += 1

    return blocks + [
        # Add an empty block at the end to verify that no more requests are
        # included.
        Block(
            header_verify=Header(requests_hash=Requests()),
            timestamp=timestamp,
        )
    ]
