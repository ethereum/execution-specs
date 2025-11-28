"""Test the validations applying after London."""

import pytest
from execution_testing.base_types.composite_types import Alloc
from execution_testing.exceptions.exceptions.block import BlockException
from execution_testing.specs.blockchain import (
    Block,
    BlockchainTestFiller,
    Header,
)


@pytest.mark.valid_from("London")
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "field,invalid_value,exception",
    [
        ("base_fee_per_gas", 1, BlockException.INVALID_BASEFEE_PER_GAS),
    ],
)
def test_invalid_header(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    field: str,
    invalid_value: int,
    exception: BlockException | list[BlockException],
) -> None:
    """
    Tests that a block with an invalid header (e.g. base_fee_per_gas) is
    rejected.
    """
    invalid_fields = {field: invalid_value}

    block = Block(
        txs=[], rlp_modifier=Header(**invalid_fields), exception=exception
    )

    blockchain_test(pre=pre, post={}, blocks=[block])
