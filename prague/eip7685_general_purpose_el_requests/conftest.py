"""
Fixtures for the EIP-7685 deposit tests.
"""

from typing import List

import pytest

from ethereum_test_tools import Alloc, Block, BlockException, Header

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
def block_body_override_requests() -> List[
    DepositRequest | WithdrawalRequest | ConsolidationRequest
] | None:
    """List of requests that overwrite the requests in the header. None by default."""
    return None


@pytest.fixture
def exception() -> BlockException | None:
    """Block exception expected by the tests. None by default."""
    return None


@pytest.fixture
def blocks(
    pre: Alloc,
    requests: List[
        DepositInteractionBase
        | WithdrawalRequestInteractionBase
        | ConsolidationRequestInteractionBase
    ],
    block_body_override_requests: List[DepositRequest | WithdrawalRequest | ConsolidationRequest]
    | None,
    exception: BlockException | None,
) -> List[Block]:
    """List of blocks that comprise the test."""
    included_deposit_requests = []
    included_withdrawal_requests = []
    included_consolidation_requests = []
    # Single block therefore base fee
    withdrawal_request_fee = 1
    consolidation_request_fee = 1
    for r in requests:
        r.update_pre(pre)
        if isinstance(r, DepositInteractionBase):
            included_deposit_requests += r.valid_requests(10**18)
        elif isinstance(r, WithdrawalRequestInteractionBase):
            included_withdrawal_requests += r.valid_requests(withdrawal_request_fee)
        elif isinstance(r, ConsolidationRequestInteractionBase):
            included_consolidation_requests += r.valid_requests(consolidation_request_fee)

    return [
        Block(
            txs=sum((r.transactions() for r in requests), []),
            header_verify=Header(
                requests_root=included_deposit_requests
                + included_withdrawal_requests
                + included_consolidation_requests,
            ),
            requests=block_body_override_requests,
            exception=exception,
        )
    ]
