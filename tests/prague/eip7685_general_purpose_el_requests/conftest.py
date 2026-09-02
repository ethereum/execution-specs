"""Fixtures for the EIP-7685 request tests."""

from typing import List, SupportsBytes

import pytest
from execution_testing import (
    Block,
    BlockException,
    Bytes,
    ConsolidationRequest,
    DepositRequest,
    EngineAPIError,
    Header,
    SystemContractInteractionBase,
    WithdrawalRequest,
)

from ...common.system_contract_request_fixtures import (
    blocks,  # noqa: F401
    included_requests,  # noqa: F401
    system_contract_interactions_per_block_copy,  # noqa: F401
    timestamp,  # noqa: F401
)


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
    blocks: List[Block],  # noqa: F811
    block_body_override_requests: List[Bytes | SupportsBytes] | None,
    correct_requests_hash_in_header: bool,
    exception: BlockException | None,
    engine_api_error_code: EngineAPIError | None,
) -> List[Block]:
    """
    Single block whose request body / header can be overridden, used by the
    negative tests to inject invalid requests and expect a block exception.

    The block's transactions and expected requests hash are taken from the
    shared `blocks` fixture; only the block body requests / header are
    overridden here.
    """
    assert len(blocks) == 2
    requests_block = blocks[0]
    rlp_modifier: Header | None = None
    if correct_requests_hash_in_header:
        rlp_modifier = requests_block.header_verify
    return [
        Block(
            txs=requests_block.txs,
            header_verify=requests_block.header_verify,
            requests=block_body_override_requests,
            exception=exception,
            rlp_modifier=rlp_modifier,
            engine_api_error_code=engine_api_error_code,
        )
    ]
