"""Test the block header validations applied from Frontier."""

import pytest
from execution_testing.base_types.base_types import ZeroPaddedHexNumber
from execution_testing.base_types.composite_types import Alloc
from execution_testing.exceptions.exceptions import BlockException
from execution_testing.specs.blockchain import (
    Block,
    BlockchainTestFiller,
    Header,
)
from execution_testing.test_types.block_types import Environment


@pytest.mark.parametrize(
    "gas_limit",
    [
        pytest.param(0, marks=pytest.mark.exception_test),
        pytest.param(1, marks=pytest.mark.exception_test),
        pytest.param(4999, marks=pytest.mark.exception_test),
        5000,
    ],
)
def test_gas_limit_below_minimum(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_limit: int,
    env: Environment,
) -> None:
    """
    Tests that a block with a gas limit below limit throws an error.
    """
    modified_fields = {"gas_limit": gas_limit}
    env.gas_limit = ZeroPaddedHexNumber(5000)

    block = Block(
        txs=[],
        rlp_modifier=Header(**modified_fields),
        exception=BlockException.INVALID_GASLIMIT
        if gas_limit < 5000
        else None,
    )

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)
