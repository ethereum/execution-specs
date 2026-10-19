"""Test the mempool test spec's block rule and validators."""

from typing import List

import pytest

from execution_testing.exceptions import TransactionException
from execution_testing.forks import Cancun, Prague
from execution_testing.test_types import (
    EOA,
    Alloc,
    Blob,
    MempoolTransaction,
    NetworkWrappedTransaction,
    Transaction,
)

from ..mempool import MempoolTest

ALICE = EOA(key=1)
BOB = EOA(key=2)


def tx(sender: EOA, nonce: int, **kwargs: int) -> Transaction:
    """Return a transfer from `sender` at `nonce`."""
    return Transaction(sender=sender, nonce=nonce, gas_limit=21_000, **kwargs)


def mempool_test(entries: List[MempoolTransaction]) -> MempoolTest:
    """Return a mempool test sending `entries`."""
    return MempoolTest(pre=Alloc(), txs=entries, fork=Prague)


def test_block_holds_every_independent_transaction() -> None:
    """Test that transactions of distinct senders all land, in order."""
    rejected = tx(ALICE, 0)
    accepted = tx(BOB, 0)
    test = mempool_test(
        [
            MempoolTransaction(tx=rejected, accepted=False),
            MempoolTransaction(tx=accepted, accepted=True),
        ]
    )
    assert test.block_transactions() == [rejected, accepted]


def test_block_holds_the_last_admitted_replacement() -> None:
    """Test that only the surviving replacement of a nonce lands."""
    original = tx(ALICE, 0, gas_price=10)
    underpriced = tx(ALICE, 0, gas_price=10)
    replacement = tx(ALICE, 0, gas_price=11)
    test = mempool_test(
        [
            MempoolTransaction(tx=original, accepted=True),
            MempoolTransaction(tx=underpriced, accepted=False),
            MempoolTransaction(tx=replacement, accepted=True),
        ]
    )
    assert test.block_transactions() == [replacement]


def test_block_holds_the_first_of_rejected_alternatives() -> None:
    """Test that a nonce no transaction is admitted for lands once."""
    first = tx(ALICE, 0, gas_price=10)
    second = tx(ALICE, 0, gas_price=11)
    test = mempool_test(
        [
            MempoolTransaction(tx=first, accepted=False),
            MempoolTransaction(tx=second, accepted=False),
        ]
    )
    assert test.block_transactions() == [first]


def test_block_placement_overrides() -> None:
    """Test that `in_block` picks or drops a transaction explicitly."""
    original = tx(ALICE, 0, gas_price=10)
    replacement = tx(ALICE, 0, gas_price=11)
    dropped = tx(BOB, 0)
    test = mempool_test(
        [
            MempoolTransaction(tx=original, accepted=True, in_block=True),
            MempoolTransaction(tx=replacement, accepted=True),
            MempoolTransaction(tx=dropped, accepted=False, in_block=False),
        ]
    )
    assert test.block_transactions() == [original]


def test_rejects_consensus_errors() -> None:
    """Test that a transaction invalid in a block is refused."""
    invalid = tx(ALICE, 0).with_error(TransactionException.NONCE_IS_MAX)
    with pytest.raises(ValueError, match="consensus error"):
        mempool_test([MempoolTransaction(tx=invalid, accepted=False)])


def test_rejects_two_explicit_block_transactions_per_nonce() -> None:
    """Test that one nonce cannot place two transactions in the block."""
    with pytest.raises(ValueError, match="second transaction"):
        mempool_test(
            [
                MempoolTransaction(
                    tx=tx(ALICE, 0, gas_price=10), accepted=True, in_block=True
                ),
                MempoolTransaction(
                    tx=tx(ALICE, 0, gas_price=11), accepted=True, in_block=True
                ),
            ]
        )


def test_rejects_nonce_gaps() -> None:
    """Test that a nonce after a rejected transaction is refused."""
    mempool_test(
        [
            MempoolTransaction(tx=tx(ALICE, 0), accepted=True),
            MempoolTransaction(tx=tx(ALICE, 1), accepted=False),
        ]
    )
    with pytest.raises(ValueError, match="nonce gap"):
        mempool_test(
            [
                MempoolTransaction(tx=tx(ALICE, 0), accepted=False),
                MempoolTransaction(tx=tx(ALICE, 1), accepted=True),
            ]
        )


def test_block_holds_the_payload_of_a_wrapped_tx() -> None:
    """Test that a blob tx lands in the block without its sidecar."""
    payload = Transaction(
        ty=3,
        sender=ALICE,
        nonce=0,
        gas_limit=21_000,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[Blob.from_fork(Cancun).versioned_hash],
    )
    wrapped = NetworkWrappedTransaction(
        tx=payload, blob_objects=[Blob.from_fork(Cancun)]
    )
    test = mempool_test([MempoolTransaction(tx=wrapped, accepted=True)])
    assert test.block_transactions() == [payload]


def test_rejects_policy_verdicts() -> None:
    """Test that a mempool test states the verdict of every transaction."""
    with pytest.raises(ValueError, match="mempool policy"):
        mempool_test([MempoolTransaction(tx=tx(ALICE, 0), accepted=None)])
