"""Fixtures for the EIP-7685 deposit tests."""

from typing import List, SupportsBytes

import pytest

from ethereum_test_tools import (
    Alloc,
    Block,
    BlockException,
    Bytes,
    EngineAPIError,
    Header,
    Requests,
)

from ..eip6110_deposits.helpers import DepositInteractionBase, DepositRequest
from ..eip7002_el_triggerable_withdrawals.helpers import (
    WithdrawalRequest,
    WithdrawalRequestInteractionBase,
)
from ..eip7251_consolidations.helpers import (
    ConsolidationRequest,
    ConsolidationRequestInteractionBase,
)


@pytest.fixture
def block_body_override_requests(
    request: pytest.FixtureRequest,
) -> List[DepositRequest | WithdrawalRequest | ConsolidationRequest] | None:
    """List of requests that overwrite the requests in the header. None by default."""
    if hasattr(request, "param"):
        return request.param
    return None


@pytest.fixture
def correct_requests_hash_in_header() -> bool:
    """
    Whether to include the correct requests hash in the header so the calculated
    block hash is correct, even though the requests in the new payload parameters might
    be wrong.
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
    block_body_override_requests_bytes = [bytes(r) for r in block_body_override_requests]
    if any(len(r) <= 1 for r in block_body_override_requests_bytes):
        return EngineAPIError.InvalidParams

    def is_monotonically_increasing(requests: List[bytes]) -> bool:
        return all(x[0] < y[0] for x, y in zip(requests, requests[1:], strict=False))

    if not is_monotonically_increasing(block_body_override_requests_bytes):
        return EngineAPIError.InvalidParams

    return None


@pytest.fixture
def blocks(
    pre: Alloc,
    requests: List[
        DepositInteractionBase
        | WithdrawalRequestInteractionBase
        | ConsolidationRequestInteractionBase
    ],
    block_body_override_requests: List[Bytes | SupportsBytes] | None,
    correct_requests_hash_in_header: bool,
    exception: BlockException | None,
    engine_api_error_code: EngineAPIError | None,
) -> List[Block]:
    """List of blocks that comprise the test."""
    valid_requests_list: List[DepositRequest | WithdrawalRequest | ConsolidationRequest] = []
    # Single block therefore base fee
    withdrawal_request_fee = 1
    consolidation_request_fee = 1
    for r in requests:
        r.update_pre(pre)
        if isinstance(r, DepositInteractionBase):
            valid_requests_list += r.valid_requests(10**18)
        elif isinstance(r, WithdrawalRequestInteractionBase):
            valid_requests_list += r.valid_requests(withdrawal_request_fee)
        elif isinstance(r, ConsolidationRequestInteractionBase):
            valid_requests_list += r.valid_requests(consolidation_request_fee)

    valid_requests = Requests(*valid_requests_list)

    rlp_modifier: Header | None = None
    if correct_requests_hash_in_header:
        rlp_modifier = Header(
            requests_hash=valid_requests,
        )
    return [
        Block(
            txs=sum((r.transactions() for r in requests), []),
            header_verify=Header(requests_hash=valid_requests),
            requests=block_body_override_requests,
            exception=exception,
            rlp_modifier=rlp_modifier,
            engine_api_error_code=engine_api_error_code,
        )
    ]
