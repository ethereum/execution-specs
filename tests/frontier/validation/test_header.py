"""Test the block header validations applied from Frontier."""

from typing import Generator

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Fork,
    Header,
    ParameterSet,
)
from execution_testing.base_types import ZeroPaddedHexNumber
from execution_testing.forks import Frontier

# Protocol minimum block gas limit, enforced since Frontier.
PROTOCOL_GAS_LIMIT_FLOOR = Frontier.minimum_block_gas_limit()


def gas_limit_cases_by_fork(
    fork: Fork,
) -> Generator[ParameterSet, None, None]:
    """Yield gas limit cases around the fork's minimum block gas limit."""
    minimum_block_gas_limit = fork.minimum_block_gas_limit()
    # The invalid cases pin the head's gas limit so low that no valid
    # child exists (a child's gas limit is bound to its parent's), so
    # the sync block the filler would append above these chains cannot
    # be built.
    invalid_case_marks = [
        pytest.mark.exception_test,
        pytest.mark.no_sync_block_state_context,
    ]
    yield pytest.param(
        0,
        id="zero",
        marks=invalid_case_marks,
    )
    yield pytest.param(
        1,
        id="one",
        marks=invalid_case_marks,
    )
    yield pytest.param(
        minimum_block_gas_limit - 1,
        id="minimum_minus_one",
        marks=invalid_case_marks,
    )
    yield pytest.param(minimum_block_gas_limit, id="minimum")


@pytest.mark.parametrize_by_fork("gas_limit", gas_limit_cases_by_fork)
def test_block_gas_limit_below_minimum(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_limit: int,
    env: Environment,
    fork: Fork,
) -> None:
    """
    Tests that a block with a gas limit below the minimum throws an error.
    """
    modified_fields = {"gas_limit": gas_limit}
    minimum_block_gas_limit = fork.minimum_block_gas_limit()
    env.gas_limit = ZeroPaddedHexNumber(minimum_block_gas_limit)

    block = Block(txs=[])

    if gas_limit < minimum_block_gas_limit:
        block.rlp_modifier = Header(**modified_fields)
        if gas_limit < PROTOCOL_GAS_LIMIT_FLOOR:
            block.exception = (
                [
                    BlockException.INVALID_GASLIMIT,
                    BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED,
                ]
                if fork.is_eip_enabled(7928)
                else BlockException.INVALID_GASLIMIT
            )
        else:
            block.exception = (
                BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED
            )

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)
