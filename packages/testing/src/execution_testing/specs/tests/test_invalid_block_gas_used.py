"""
Test the header gas used given to blocks that are invalid because of one
of their transactions.
"""

from typing import List

import pytest

from execution_testing.base_types import Account, Address
from execution_testing.client_clis import TransitionTool
from execution_testing.exceptions import BlockException, TransactionException
from execution_testing.fixtures import (
    BaseFixture,
    BlockchainEngineFixture,
    BlockchainFixture,
    FixtureFormat,
)
from execution_testing.fixtures.blockchain import InvalidFixtureBlock
from execution_testing.forks import Shanghai
from execution_testing.test_types import Environment, Transaction

from ..blockchain import Block, BlockchainTest, Header

SENDER = "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b"
RECIPIENT = Address(0x100)
INSUFFICIENT_GAS_LIMIT = 20_999
VALID_GAS_LIMIT = 100_000
MODIFIED_GAS_USED = 12_345
INVALID_EXTRA_DATA = b"\x00" * 33


def insufficient_gas_tx() -> Transaction:
    """Return a transaction rejected for insufficient intrinsic gas."""
    return Transaction(
        to=RECIPIENT,
        gas_limit=INSUFFICIENT_GAS_LIMIT,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )


@pytest.mark.parametrize(
    "fixture_format",
    [BlockchainFixture, BlockchainEngineFixture],
    ids=["blockchain_test", "blockchain_test_engine"],
)
@pytest.mark.parametrize(
    "blocks,expected_gas_used",
    [
        pytest.param(
            [
                Block(
                    txs=[insufficient_gas_tx()],
                    exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
                )
            ],
            INSUFFICIENT_GAS_LIMIT,
            id="transaction_exception",
        ),
        pytest.param(
            [
                Block(
                    txs=[insufficient_gas_tx()],
                    exception=[TransactionException.INTRINSIC_GAS_TOO_LOW],
                )
            ],
            INSUFFICIENT_GAS_LIMIT,
            id="transaction_exception_list",
        ),
        pytest.param(
            [
                Block(
                    txs=[
                        Transaction(
                            to=RECIPIENT,
                            gas_limit=0,
                            error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                        )
                    ],
                    exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
                )
            ],
            1,
            id="transaction_exception_zero_gas_limit",
        ),
        pytest.param(
            [
                Block(
                    txs=[insufficient_gas_tx()],
                    rlp_modifier=Header(gas_used=MODIFIED_GAS_USED),
                    exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
                )
            ],
            MODIFIED_GAS_USED,
            id="transaction_exception_with_gas_used_modifier",
        ),
        pytest.param(
            [
                Block(
                    txs=[],
                    rlp_modifier=Header(extra_data=INVALID_EXTRA_DATA),
                    exception=BlockException.INCORRECT_BLOCK_FORMAT,
                )
            ],
            0,
            id="block_exception_without_transactions",
        ),
        pytest.param(
            [
                Block(
                    txs=[Transaction(to=RECIPIENT, gas_limit=VALID_GAS_LIMIT)],
                    rlp_modifier=Header(extra_data=INVALID_EXTRA_DATA),
                    exception=BlockException.INCORRECT_BLOCK_FORMAT,
                )
            ],
            21_000,
            id="block_exception_with_valid_transaction",
        ),
    ],
)
def test_invalid_block_header_gas_used(
    fixture_format: FixtureFormat,
    blocks: List[Block],
    expected_gas_used: int,
    default_t8n: TransitionTool,
) -> None:
    """
    Give a block that is invalid only because of a transaction the gas its
    transactions could have used, at least one gas for a zero limit, keep
    any explicit modifier, and leave blocks with block-level exceptions to
    the transition tool's value.
    """
    fixture: BaseFixture = (
        BlockchainTest(
            fork=Shanghai,
            pre={SENDER: Account(balance=10**18)},
            post={},
            blocks=blocks,
            genesis_environment=Environment(),
            is_exception_test=True,
        )
        .generate(t8n=default_t8n, fixture_format=fixture_format)
        .fixture
    )
    if isinstance(fixture, BlockchainFixture):
        block = fixture.blocks[0]
        assert isinstance(block, InvalidFixtureBlock)
        assert block.rlp_decoded is not None
        gas_used = int(block.rlp_decoded.header.gas_used)
    else:
        assert isinstance(fixture, BlockchainEngineFixture)
        payload = fixture.payloads[0]
        assert payload.validation_error is not None
        gas_used = int(payload.params[0].gas_used)
    assert gas_used == expected_gas_used
