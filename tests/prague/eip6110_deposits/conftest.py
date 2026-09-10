"""Fixtures for the EIP-6110 deposit tests."""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockException,
    DepositRequest,
    Fork,
    Header,
    Requests,
    SystemContractInteractionBase,
    SystemContractRequest,
    Transaction,
)
from execution_testing.base_types import HexNumber


@pytest.fixture
def prepared_requests(
    pre: Alloc, requests: List[SystemContractInteractionBase]
) -> List[SystemContractInteractionBase]:
    """
    Allocate accounts/contracts for each request in `pre` and return copies
    with the allocated state populated. The parametrize value `requests` is
    not mutated, so it stays pristine across fixture format runs.
    """
    return [r.update_pre(pre) for r in requests]


@pytest.fixture
def txs(
    fork: Fork,
    prepared_requests: List[SystemContractInteractionBase],
) -> List[Transaction]:
    """List of transactions to include in the block."""
    floor_cost = fork.transaction_data_floor_cost_calculator()
    txs = []
    for r in prepared_requests:
        txs += r.transactions()
    for tx in txs:
        if "gas_limit" in tx.model_fields_set and tx.error is None:
            # Keep explicit limits above the fork's calldata floor
            # (EIP-8037 repricing). Error tests keep their exact limit.
            tx.gas_limit = HexNumber(
                max(int(tx.gas_limit), floor_cost(data=tx.data) + 1)
            )
    return txs


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
    prepared_requests: List[SystemContractInteractionBase],
) -> List[SystemContractRequest]:
    """
    Return the list of deposit requests that should be included in each block.

    A deposit is included only if it is marked valid and sends at least the
    minimum deposit value (1 ETH); deposits below the minimum revert in the
    deposit contract and never emit a log.
    """
    min_deposit_value = 10**18  # 1 ETH, the deposit contract's minimum

    included: List[SystemContractRequest] = []
    for d in prepared_requests:
        source = d.request_source_address
        assert source is not None, "Source address not initialized"
        included += [
            r.with_source_address(source)
            for r in d.requests
            if r.valid and r.value >= min_deposit_value
        ]
    return included


@pytest.fixture
def blocks(
    fork: Fork,
    included_requests: List[SystemContractRequest],
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
