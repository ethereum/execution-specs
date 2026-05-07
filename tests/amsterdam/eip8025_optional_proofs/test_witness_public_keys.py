"""Stateless input transaction public-key tests."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Transaction,
)
from execution_testing.test_types.execution_witness.modifiers import (
    replace_public_key_at,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_stateless_input_public_keys_are_constructed(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A public key is included for each payload transaction."""
    recipient = pre.fund_eoa()
    sender_a = pre.fund_eoa()
    sender_b = pre.fund_eoa()
    tx_a = Transaction(
        sender=sender_a,
        to=recipient,
        value=0,
        gas_limit=500_000,
    )
    tx_b = Transaction(
        sender=sender_b,
        to=recipient,
        value=0,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx_a, tx_b],
                # The filler automatically verifies stateless input public
                # keys against the recovered payload transaction keys.
                expected_stateless_validation_success=True,
            )
        ],
        post={
            sender_a: Account(nonce=1),
            sender_b: Account(nonce=1),
        },
    )


def test_stateless_input_invalid_public_key_is_rejected(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A wrong but SSZ-valid public key fails stateless validation."""
    recipient = pre.fund_eoa()
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        gas_limit=500_000,
    )
    invalid_public_key = Bytes(b"\x04" + b"\x00" * 64)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                stateless_input_public_keys_modifier=(
                    replace_public_key_at(0, invalid_public_key)
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )
