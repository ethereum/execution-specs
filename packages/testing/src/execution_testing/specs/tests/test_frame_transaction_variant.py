"""Tests for the frame-transaction state-test variant."""

from execution_testing.forks import Bogota
from execution_testing.test_types import Alloc, Environment, Transaction

from ..frame_transaction_variant import (
    convert_to_frame_transaction_variant,
)
from ..state import StateTest


def test_frame_transaction_variant_preserves_chain_id() -> None:
    """The frame transaction uses the state test's configured chain ID."""
    chain_id = 12345
    test = StateTest(
        fork=Bogota,
        pre=Alloc(),
        post=Alloc(),
        tx=Transaction(chain_id=chain_id),
        chain_id=chain_id,
    )

    variant = convert_to_frame_transaction_variant(test)

    assert variant.tx.chain_id == chain_id


def test_frame_transaction_variant_preserves_block_gas_limit() -> None:
    """Leave the observable block gas limit unchanged."""
    gas_limit = 4_000_000
    test = StateTest(
        fork=Bogota,
        env=Environment(gas_limit=gas_limit),
        pre=Alloc(),
        post=Alloc(),
        tx=Transaction(),
    )

    variant = convert_to_frame_transaction_variant(test)

    assert variant.env.gas_limit == gas_limit
