"""Test the request types that can be included in a block by the given fork."""

from typing import List

import pytest

from ethereum_test_exceptions import BlockException
from ethereum_test_forks import Fork
from ethereum_test_tools import Alloc, Block, BlockchainTestFiller, Environment

from ..eip6110_deposits.helpers import DepositInteractionBase, DepositRequest, DepositTransaction
from ..eip7002_el_triggerable_withdrawals.helpers import (
    WithdrawalRequest,
    WithdrawalRequestInteractionBase,
    WithdrawalRequestTransaction,
)
from ..eip7251_consolidations.helpers import (
    ConsolidationRequest,
    ConsolidationRequestInteractionBase,
    ConsolidationRequestTransaction,
)
from .spec import ref_spec_7685

REFERENCE_SPEC_GIT_PATH = ref_spec_7685.git_path
REFERENCE_SPEC_VERSION = ref_spec_7685.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.fixture
def block_body_extra_requests(fork: Fork, invalid_request_data: bytes) -> List[bytes]:
    """
    Create a request with an invalid type for the fork.

    This overrides the default fixture and its behavior defined in conftest.py.
    """
    invalid_request_type = fork.max_request_type() + 1
    return [bytes([invalid_request_type]) + invalid_request_data]


@pytest.fixture
def requests(
    fork: Fork,
    include_valid_requests: bool,
) -> List[
    DepositInteractionBase | WithdrawalRequestInteractionBase | ConsolidationRequestInteractionBase
]:
    """List of valid requests that are added along with the invalid request."""
    if not include_valid_requests:
        return []
    if fork.max_request_type() == 2:
        return [
            DepositTransaction(
                requests=[
                    DepositRequest(
                        pubkey=1,
                        withdrawal_credentials=2,
                        amount=1_000_000_000,
                        signature=3,
                        index=0,
                    )
                ]
            ),
            WithdrawalRequestTransaction(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=1,
                        amount=0,
                        fee=1,
                    )
                ]
            ),
            ConsolidationRequestTransaction(
                requests=[
                    ConsolidationRequest(
                        source_pubkey=2,
                        target_pubkey=5,
                        fee=1,
                    )
                ]
            ),
        ]
    raise NotImplementedError(f"Unsupported fork: {fork}")


@pytest.mark.parametrize(
    "include_valid_requests",
    [False, True],
)
@pytest.mark.parametrize(
    "invalid_request_data",
    [
        pytest.param(b"", id="no_data"),
        pytest.param(b"\0", id="single_byte"),
        pytest.param(b"\0" * 32, id="32_bytes"),
    ],
)
@pytest.mark.parametrize(
    "exception",
    [
        pytest.param(BlockException.INVALID_REQUESTS, id=""),
    ],
)
def test_invalid_request_type(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
):
    """Test sending a block with an invalid request type."""
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
