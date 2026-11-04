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
    yield pytest.param(
        0,
        id="zero",
        marks=pytest.mark.exception_test,
    )
    yield pytest.param(
        1,
        id="one",
        marks=pytest.mark.exception_test,
    )
    yield pytest.param(
        minimum_block_gas_limit - 1,
        id="minimum_minus_one",
        marks=pytest.mark.exception_test,
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


def gas_limit_cases_at_maximum(
    fork: Fork,
) -> Generator[ParameterSet, None, None]:
    """Yield gas limit cases around the fork's maximum block gas limit."""
    maximum_block_gas_limit = fork.maximum_block_gas_limit()
    yield pytest.param(maximum_block_gas_limit, id="maximum")
    yield pytest.param(
        maximum_block_gas_limit + 1,
        id="maximum_plus_one",
        marks=pytest.mark.exception_test,
    )


@pytest.mark.parametrize_by_fork("gas_limit", gas_limit_cases_at_maximum)
def test_block_gas_limit_above_maximum(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_limit: int,
    env: Environment,
    fork: Fork,
) -> None:
    """
    Test that a block with a gas limit above the maximum is invalid.

    The parent sits at the maximum, so one more gas is well within the step
    a gas limit may move from its parent and only the maximum rejects it.
    """
    maximum_block_gas_limit = fork.maximum_block_gas_limit()
    env.gas_limit = ZeroPaddedHexNumber(maximum_block_gas_limit)

    if gas_limit == maximum_block_gas_limit:
        block = Block(txs=[], header_verify=Header(gas_limit=gas_limit))
    elif gas_limit == maximum_block_gas_limit + 1:
        block = Block(
            txs=[],
            rlp_modifier=Header(gas_limit=gas_limit),
            exception=BlockException.GASLIMIT_TOO_BIG,
        )
    else:
        raise ValueError(f"unexpected gas limit: {gas_limit}")

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)
