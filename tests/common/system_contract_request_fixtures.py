"""
Shared pytest fixtures for system-contract request tests (EIP-6110, EIP-7002,
EIP-7251, and future forks).

These fixtures are request-type agnostic and track inclusion independently per
request type. For `FeeSystemContractRequest` types (e.g. withdrawals and
consolidations) they read the per-block dequeue cap (`max_per_block`), the fee
curve (`get_fee`) and the excess update (`get_excess`), tracking the excess
request count per type. Fee-less requests (e.g. deposits) are always included
with no per-block cap. A block may therefore mix request types, each accounted
for with its own rules.
"""

from collections import defaultdict
from dataclasses import replace
from itertools import zip_longest
from typing import Dict, List, Type

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockException,
    FeeSystemContractRequest,
    Fork,
    Header,
    Requests,
    SystemContractInteractionBase,
    SystemContractRequest,
    TransitionFork,
)

RequestType = Type[SystemContractRequest]


@pytest.fixture
def system_contract_interactions_per_block_copy(
    system_contract_interactions_per_block: List[
        List[SystemContractInteractionBase]
    ],
) -> List[List[SystemContractInteractionBase]]:
    """
    Return a copy of `system_contract_interactions_per_block` whose requests
    can be safely mutated by fixtures in the test.

    Each interaction's requests are copied because `included_requests` writes
    the per-block fee onto individual requests in place; sharing them would
    leak those mutations back into the parametrize value. A full `deepcopy` is
    avoided because relay-contract interactions embed opcode objects that are
    not copiable.
    """
    return [
        [
            replace(
                interaction,
                requests=[
                    request.model_copy() for request in interaction.requests
                ],
            )
            for interaction in block_interactions
        ]
        for block_interactions in system_contract_interactions_per_block
    ]


@pytest.fixture
def included_requests(
    pre: Alloc,
    system_contract_interactions_per_block_copy: List[
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

    for block_interactions in system_contract_interactions_per_block_copy:
        # Group this block's valid requests by type. Fee requests are kept only
        # if they meet their type's current (per-block) fee; fee-less requests
        # (e.g. deposits) are always included.
        current: Dict[RequestType, List[SystemContractRequest]] = defaultdict(
            list
        )
        for i in range(len(block_interactions)):
            # Update the fee in all interaction's requests
            for request in block_interactions[i].requests:
                request_type = type(request)
                if request_type not in seen_types:
                    seen_types.append(request_type)
                if isinstance(request, FeeSystemContractRequest):
                    current_excess = excess[request_type]
                    if request.excess_fee_processing == "call":
                        # The contract adds the requests already queued this
                        # block beyond the target onto the stored excess.
                        current_excess += max(
                            len(current[request_type])
                            - request.target_per_block,
                            0,
                        )
                    minimum_fee = request.get_fee(current_excess)
                    # Write the correct fee if unset regardless of validity
                    if "fee" not in request.model_fields_set:
                        request.fee = minimum_fee
                    if request.fee < minimum_fee and request.valid:
                        raise Exception(
                            "Invalid request marked as valid: "
                            f"{request.model_dump_json()}"
                        )
                if request.valid:
                    current[request_type].append(request)

            # With the correct fee, now update the pre.
            block_interactions[i] = block_interactions[i].update_pre(pre=pre)

            # Finally, set the source address in the valid requests
            source_address = block_interactions[i].request_source_address
            assert source_address is not None
            for request in block_interactions[i].requests:
                if not request.valid:
                    continue
                request.set_source_address(source_address)

        block_included: List[SystemContractRequest] = []
        for request_type in seen_types:
            pending = carry_over[request_type] + current[request_type]
            if issubclass(request_type, FeeSystemContractRequest):
                cap = request_type.max_per_block
                block_included += pending[:cap]
                carry_over[request_type] = pending[cap:]
                excess[request_type] = request_type.get_excess(
                    excess[request_type], len(current[request_type])
                )
            else:
                # Fee-less requests (e.g. deposits) have no per-block cap.
                block_included += pending
                carry_over[request_type] = []
        per_block_included.append(block_included)

    # Keep adding blocks until every type's queue is drained. Only fee requests
    # (which are capped per block) can ever carry over.
    while any(carry_over[request_type] for request_type in seen_types):
        block_included = []
        for request_type in seen_types:
            if not issubclass(request_type, FeeSystemContractRequest):
                continue
            queue = carry_over[request_type]
            cap = request_type.max_per_block
            block_included += queue[:cap]
            carry_over[request_type] = queue[cap:]
        per_block_included.append(block_included)

    return per_block_included


@pytest.fixture
def timestamp() -> int:
    """Return the timestamp for the first block."""
    return 1


@pytest.fixture
def blocks(
    fork: Fork | TransitionFork,
    system_contract_interactions_per_block_copy: List[
        List[SystemContractInteractionBase]
    ],
    included_requests: List[List[SystemContractRequest]],
    timestamp: int,
) -> List[Block]:
    """Return the list of blocks that should be included in the test."""
    blocks: List[Block] = []

    for block_interactions, block_included_requests in zip_longest(  # type: ignore
        system_contract_interactions_per_block_copy,
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


@pytest.fixture
def override_blocks(
    blocks: List[Block],
    block_body_override_requests: List[SystemContractRequest] | None,
    exception: BlockException | None,
) -> List[Block]:
    """
    Return a single block for negative tests where the requests in the block
    body do not match the requests that actually happened in the block's
    transactions.

    The transactions and expected requests hash are taken from the shared
    `blocks` fixture; only the block body's requests list is overridden with
    `block_body_override_requests` and the block is expected to fail with
    `exception`.
    """
    assert len(blocks) == 2
    requests_block = blocks[0]
    return [
        Block(
            txs=requests_block.txs,
            header_verify=requests_block.header_verify,
            requests=(
                Requests(*block_body_override_requests).requests_list
                if block_body_override_requests is not None
                else None
            ),
            exception=exception,
        )
    ]
