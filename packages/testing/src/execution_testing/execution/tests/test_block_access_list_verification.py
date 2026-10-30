"""Test the block access list verification of the transaction-post format."""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.test_types import (
    EOA,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BlockAccessListExpectation,
    Transaction,
)
from execution_testing.test_types.block_access_list import (
    BlockAccessListValidationError,
)

from ..transaction_post import TransactionPost

SENDER = EOA(key=1)
ACCOUNT = Address(0xA)
BLOCK_HASH = Hash(0xB1)


class FakeEthRPC:
    """Land a transaction at a given index and serve one access list."""

    def __init__(
        self,
        *,
        transaction_index: int,
        block_access_list: List[Dict[str, Any]],
    ) -> None:
        """Serve `block_access_list` for the block holding the sent tx."""
        self.transaction_index = transaction_index
        self.block_access_list = block_access_list
        self.receipt_requests: List[Hash] = []
        self.block_access_list_requests: List[Hash] = []

    def get_transaction_receipt(self, tx_hash: Hash) -> Dict[str, Any]:
        """Return the receipt of `tx_hash`."""
        self.receipt_requests.append(tx_hash)
        return {
            "transactionIndex": hex(self.transaction_index),
            "blockHash": str(BLOCK_HASH),
        }

    def get_block_access_list(self, block_hash: Hash) -> List[Dict[str, Any]]:
        """Return the access list of the block `block_hash`."""
        self.block_access_list_requests.append(block_hash)
        return self.block_access_list


def nonce_change_at(index: int, post_nonce: int) -> List[Dict[str, Any]]:
    """Return the access list a node serves for one nonce change."""
    return [
        {
            "address": str(ACCOUNT),
            "storageChanges": [],
            "storageReads": [],
            "balanceChanges": [],
            "nonceChanges": [{"index": hex(index), "value": hex(post_nonce)}],
            "codeChanges": [],
        }
    ]


def expecting(index: int, post_nonce: int) -> BlockAccessListExpectation:
    """Return the expectation a test pins for a block of its own."""
    return BlockAccessListExpectation(
        account_expectations={
            ACCOUNT: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(
                        block_access_index=index, post_nonce=post_nonce
                    )
                ]
            )
        }
    )


def transaction_post(
    expectation: BlockAccessListExpectation | None,
) -> tuple[TransactionPost, Transaction]:
    """Return the format of a single transaction expecting `expectation`."""
    tx = Transaction(
        sender=SENDER, nonce=0, gas_limit=21_000
    ).with_signature_and_sender()
    return (
        TransactionPost(
            blocks=[[tx]],
            post=Alloc(),
            expected_block_access_list=expectation,
        ),
        tx,
    )


def test_expected_index_follows_the_transaction() -> None:
    """Test that the pinned index moves to where the network packed it."""
    test, tx = transaction_post(expecting(1, 5))
    rpc = FakeEthRPC(
        transaction_index=7, block_access_list=nonce_change_at(8, 5)
    )

    test.verify_block_access_list(rpc, [[tx]])  # type: ignore[arg-type]

    assert rpc.receipt_requests == [tx.hash]
    assert rpc.block_access_list_requests == [BLOCK_HASH]


def test_index_left_where_the_test_pinned_it_fails() -> None:
    """Test that a node leaving the change at the pinned index is caught."""
    test, tx = transaction_post(expecting(1, 5))
    rpc = FakeEthRPC(
        transaction_index=7, block_access_list=nonce_change_at(1, 5)
    )

    with pytest.raises(BlockAccessListValidationError):
        test.verify_block_access_list(rpc, [[tx]])  # type: ignore[arg-type]


def test_system_operations_keep_their_index() -> None:
    """Test that index zero stays with the block's system operations."""
    test, tx = transaction_post(expecting(0, 5))
    rpc = FakeEthRPC(
        transaction_index=7, block_access_list=nonce_change_at(0, 5)
    )

    test.verify_block_access_list(rpc, [[tx]])  # type: ignore[arg-type]


def test_index_past_the_transaction_is_not_supported() -> None:
    """Test that an index no live block can place is refused."""
    test, tx = transaction_post(expecting(2, 5))
    rpc = FakeEthRPC(
        transaction_index=7, block_access_list=nonce_change_at(3, 5)
    )

    with pytest.raises(NotImplementedError, match="cannot be located"):
        test.verify_block_access_list(rpc, [[tx]])  # type: ignore[arg-type]


def test_without_an_expectation_nothing_is_requested() -> None:
    """Test that a test pinning no access list asks the node for none."""
    test, tx = transaction_post(None)
    rpc = FakeEthRPC(
        transaction_index=7, block_access_list=nonce_change_at(8, 5)
    )

    test.verify_block_access_list(rpc, [[tx]])  # type: ignore[arg-type]

    assert rpc.receipt_requests == []
    assert rpc.block_access_list_requests == []
