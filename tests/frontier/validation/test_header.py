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


@pytest.mark.parametrize(
    "number_offset",
    [
        pytest.param(-1, id="parent_number", marks=pytest.mark.exception_test),
        pytest.param(0, id="parent_number_plus_one"),
        pytest.param(
            1, id="parent_number_plus_two", marks=pytest.mark.exception_test
        ),
    ],
)
@pytest.mark.verify_sync
@pytest.mark.valid_from("Frontier")
def test_block_number(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    number_offset: int,
) -> None:
    """
    Test that a block's number must be its parent's number plus one.

    The first block is valid, so the block under test has a parent that is
    not the genesis block, and a sync test has a valid head to sync to.
    """
    parent = Block()
    child = Block()
    if number_offset != 0:
        # The parent is block 1, so the valid number is 2.
        child.rlp_modifier = Header(number=2 + number_offset)
        child.exception = BlockException.INVALID_BLOCK_NUMBER

    blockchain_test(pre=pre, post={}, blocks=[parent, child])
