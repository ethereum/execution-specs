"""Fixtures for the EIP-7685 request tests."""

from typing import List, SupportsBytes

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockException,
    Bytes,
    EngineAPIError,
    Header,
    Requests,
    SystemContractInteractionBase,
    SystemContractRequest,
)

from ...common.system_contract_request_fixtures import (
    blocks,  # noqa: F401
    included_requests,  # noqa: F401
    prepared_system_contract_interactions_per_block,  # noqa: F401
    timestamp,  # noqa: F401
)
from ..eip6110_deposits.helpers import DepositRequest
from ..eip7002_el_triggerable_withdrawals.helpers import WithdrawalRequest
from ..eip7251_consolidations.helpers import ConsolidationRequest


@pytest.fixture
def system_contract_interactions_per_block(
    requests: List[SystemContractInteractionBase],
) -> List[List[SystemContractInteractionBase]]:
    """
    Adapt the flat `requests` parametrization (one block's interactions) to the
    per-block shape consumed by the shared request fixtures (`blocks` etc.).
    """
    return [requests]


@pytest.fixture
def block_body_override_requests(
    request: pytest.FixtureRequest,
) -> List[DepositRequest | WithdrawalRequest | ConsolidationRequest] | None:
    """
    List of requests that overwrite the requests in the header. None by
    default.
    """
    if hasattr(request, "param"):
        return request.param
    return None


@pytest.fixture
def correct_requests_hash_in_header() -> bool:
    """
    Whether to include the correct requests hash in the header so the
    calculated block hash is correct, even though the requests in the new
    payload parameters might be wrong.
    """
    return False


@pytest.fixture
def exception() -> BlockException | None:
    """Block exception expected by the tests. None by default."""
    return None


@pytest.fixture
def engine_api_error_code(
    block_body_override_requests: List[Bytes | SupportsBytes] | None,
) -> EngineAPIError | None:
    """Engine API error code if any."""
    if block_body_override_requests is None:
        return None
    block_body_override_requests_bytes = [
        bytes(r) for r in block_body_override_requests
    ]
    if any(len(r) <= 1 for r in block_body_override_requests_bytes):
        return EngineAPIError.InvalidParams

    def is_monotonically_increasing(requests: List[bytes]) -> bool:
        return all(
            x[0] < y[0] for x, y in zip(requests, requests[1:], strict=False)
        )

    if not is_monotonically_increasing(block_body_override_requests_bytes):
        return EngineAPIError.InvalidParams

    return None


@pytest.fixture
def override_blocks(
    pre: Alloc,
    requests: List[SystemContractInteractionBase],
    block_body_override_requests: List[Bytes | SupportsBytes] | None,
    correct_requests_hash_in_header: bool,
    exception: BlockException | None,
    engine_api_error_code: EngineAPIError | None,
) -> List[Block]:
    """
    Single block whose request body / header can be overridden, used by the
    negative tests to inject invalid requests and expect a block exception.
    """
    valid_requests_list: List[SystemContractRequest] = []
    # Every request here is constructed with a sufficient value, so no fee
    # filter is needed: each interaction returns all of its `valid` requests.
    prepared = [r.update_pre(pre) for r in requests]
    for r in prepared:
        valid_requests_list += r.valid_requests()

    valid_requests = Requests(*valid_requests_list)

    rlp_modifier: Header | None = None
    if correct_requests_hash_in_header:
        rlp_modifier = Header(
            requests_hash=valid_requests,
        )
    return [
        Block(
            txs=sum((r.transactions() for r in prepared), []),
            header_verify=Header(requests_hash=valid_requests),
            requests=block_body_override_requests,
            exception=exception,
            rlp_modifier=rlp_modifier,
            engine_api_error_code=engine_api_error_code,
        )
    ]
