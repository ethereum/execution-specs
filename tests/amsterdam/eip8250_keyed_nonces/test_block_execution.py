"""
Block execution tests for
[EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).

Stateful nonce validity is evaluated against each transaction's actual
pre-state in block order, so frame transactions from one sender on
disjoint key sets, or on one key at consecutive sequences, share a
block, while a second use of an already consumed key invalidates it.
Keyed nonce writes are state changes of the nonce manager and appear in
the block access list; the legacy key set never touches it.
"""

from typing import Dict, List, Tuple

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Transaction,
    TransactionException,
)

from ..eip8141_frame_transactions.helpers import verify_frame
from .helpers import KEY_A, KEY_B, keyed_storage, nonce_manager, nonce_slot
from .spec import Spec, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")

TxNonce = Tuple[List[int], int]
"""A transaction's nonce key set and nonce sequence."""


def keyed_tx(
    sender: EOA, nonce_keys: List[int], nonce_seq: int
) -> Transaction:
    """Return a minimal frame transaction with the given nonce fields."""
    return Transaction(
        sender=sender,
        nonce=nonce_seq,
        nonce_keys=nonce_keys,
        frames=[verify_frame()],
    )


def expected_access_list(
    sender: EOA, txs: List[TxNonce]
) -> BlockAccessListExpectation:
    """
    Return the block access list entries of the sender and the nonce
    manager after the given transactions, each at its block position.
    """
    nonce_changes: List[BalNonceChange] = []
    slot_changes: Dict[int, List[BalStorageChange]] = {}
    legacy_nonce = 0
    for index, (nonce_keys, nonce_seq) in enumerate(txs, start=1):
        if nonce_keys == [0]:
            legacy_nonce += 1
            nonce_changes.append(
                BalNonceChange(
                    block_access_index=index, post_nonce=legacy_nonce
                )
            )
            continue
        for key in nonce_keys:
            slot_changes.setdefault(nonce_slot(sender, key), []).append(
                BalStorageChange(
                    block_access_index=index, post_value=nonce_seq + 1
                )
            )
    return BlockAccessListExpectation(
        account_expectations={
            sender: BalAccountExpectation(nonce_changes=nonce_changes),
            Spec.NONCE_MANAGER: (
                BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(slot=slot, slot_changes=changes)
                        for slot, changes in sorted(slot_changes.items())
                    ]
                )
                if slot_changes
                else None
            ),
        }
    )


@pytest.mark.parametrize(
    "txs,final_nonce,final_keys",
    [
        pytest.param(
            [([KEY_A], 0), ([KEY_B], 0)],
            0,
            {KEY_A: 1, KEY_B: 1},
            id="disjoint_keys",
        ),
        pytest.param(
            [([KEY_A], 0), ([KEY_A], 1)],
            0,
            {KEY_A: 2},
            id="consecutive_seqs",
        ),
        pytest.param(
            [([KEY_A, KEY_B], 0), ([KEY_B], 1)],
            0,
            {KEY_A: 1, KEY_B: 2},
            id="overlapping_keys_advance",
        ),
        pytest.param(
            [([0], 0), ([KEY_A], 0), ([0], 1)],
            2,
            {KEY_A: 1},
            id="legacy_and_keyed",
        ),
        pytest.param(
            [([0], 0), ([0], 1)],
            2,
            {},
            id="legacy_only",
        ),
    ],
)
def test_sender_transactions_in_one_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    txs: List[TxNonce],
    final_nonce: int,
    final_keys: Dict[int, int],
) -> None:
    """
    Include several frame transactions from one sender in one block.

    Each transaction's nonce check sees the writes of the ones before
    it. The block access list records every keyed write at its
    transaction's position under the nonce manager, every legacy
    increment under the sender, and nothing under the nonce manager when
    only the legacy key set is used.
    """
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[keyed_tx(sender, keys, seq) for keys, seq in txs],
                expected_block_access_list=expected_access_list(sender, txs),
            )
        ],
        post={
            sender: Account(nonce=final_nonce),
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(sender, final_keys)
            ),
        },
    )


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "second_keys",
    [
        pytest.param([KEY_A], id="same_key"),
        pytest.param([KEY_B], id="subset_key"),
        pytest.param([KEY_B, KEY_B + 1], id="partly_overlapping_keys"),
    ],
)
def test_consumed_key_replay_in_one_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    second_keys: List[int],
) -> None:
    """
    Reject a block whose second transaction reuses, at the same
    sequence, a key the first one consumed.
    """
    sender = pre.fund_eoa()
    first_keys = [KEY_A] if second_keys == [KEY_A] else [KEY_A, KEY_B]
    replay = keyed_tx(sender, second_keys, 0)
    replay.error = TransactionException.NONCE_MISMATCH_TOO_LOW

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[keyed_tx(sender, first_keys, 0), replay],
                exception=TransactionException.NONCE_MISMATCH_TOO_LOW,
            )
        ],
        post={Spec.NONCE_MANAGER: nonce_manager()},
    )
