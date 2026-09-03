"""Tests for the frame-transaction state-test variant."""

from execution_testing.base_types import Address
from execution_testing.forks import Bogota
from execution_testing.test_types import (
    Account,
    Alloc,
    Environment,
    GasFee,
    Tip,
    Transaction,
)

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


def test_frame_transaction_variant_strips_gas_balance_terms() -> None:
    """
    Drop balance changes built from gas-pinning terms, keeping the
    account's other expectations and untouched accounts as they are.
    """
    tx = Transaction()
    assert tx.sender is not None
    coinbase = Address(0x100)
    recipient = Address(0x200)
    test = StateTest(
        fork=Bogota,
        pre=Alloc(),
        post=Alloc(
            {
                tx.sender: Account(
                    nonce=1, balance_change=-1 - GasFee(tx, gas=21_000)
                ),
                coinbase: Account(balance_change=Tip(tx, gas=21_000)),
                recipient: Account(balance_change=1),
            }
        ),
        tx=tx,
    )

    variant = convert_to_frame_transaction_variant(test)

    sender_post = variant.post[tx.sender]
    assert sender_post is not None
    assert sender_post.model_fields_set == {"nonce"}
    assert sender_post.nonce == 1
    coinbase_post = variant.post[coinbase]
    assert coinbase_post is not None
    assert coinbase_post.model_fields_set == set()
    assert variant.post[recipient] is test.post[recipient]


def test_frame_transaction_variant_keeps_post_without_gas_terms() -> None:
    """Leave the post-state object alone when nothing pins gas."""
    recipient = Address(0x200)
    test = StateTest(
        fork=Bogota,
        pre=Alloc(),
        post=Alloc({recipient: Account(balance_change=1)}),
        tx=Transaction(),
    )

    variant = convert_to_frame_transaction_variant(test)

    assert variant.post is test.post
