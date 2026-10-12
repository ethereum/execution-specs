"""
Multi-transaction tests for
[EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).
"""  # noqa: E501

from typing import Dict, List, Optional

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from ..eip8141_frame_transactions.helpers import verify_frame
from .helpers import (
    NONCE_KEY,
    OTHER_KEY,
    nonce_manager_with_slots,
    used_key_slots,
    verify_only_tx_gas_used,
)
from .spec import Spec, keyed_nonce_slot, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")


def test_sequence_progression(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Use one key at consecutive sequences in a block, paying the first
    use once, with each write in the block access list at its index.
    """
    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[NONCE_KEY],
            nonce=seq,
        )
        for seq in (0, 1)
    ]
    first_gas = verify_only_tx_gas_used(fork, txs[0], first_uses=1)
    second_gas = verify_only_tx_gas_used(fork, txs[1], first_uses=0)
    txs[0].expected_receipt = TransactionReceipt(cumulative_gas_used=first_gas)
    txs[1].expected_receipt = TransactionReceipt(
        cumulative_gas_used=first_gas + second_gas
    )
    nonce_manager_writes = BalAccountExpectation(
        nonce_changes=[],
        balance_changes=[],
        code_changes=[],
        storage_changes=[
            BalStorageSlot(
                slot=keyed_nonce_slot(sender, NONCE_KEY),
                slot_changes=[
                    BalStorageChange(block_access_index=1, post_value=1),
                    BalStorageChange(block_access_index=2, post_value=2),
                ],
            )
        ],
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        Spec.NONCE_MANAGER: nonce_manager_writes,
                    }
                ),
            )
        ],
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 2}
            ),
            sender: Account(nonce=0),
        },
    )


def test_sequences_are_per_sender(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Use one key at sequence zero from two senders in a block, each
    writing its own slot.
    """
    senders = [pre.fund_eoa(), pre.fund_eoa()]
    txs = [
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[NONCE_KEY],
            nonce=0,
        )
        for sender in senders
    ]
    slot_writes = sorted(
        (
            BalStorageSlot(
                slot=keyed_nonce_slot(sender, NONCE_KEY),
                slot_changes=[
                    BalStorageChange(block_access_index=index, post_value=1)
                ],
            )
            for index, sender in enumerate(senders, start=1)
        ),
        key=lambda write: int(write.slot),
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        Spec.NONCE_MANAGER: BalAccountExpectation(
                            nonce_changes=[],
                            balance_changes=[],
                            code_changes=[],
                            storage_changes=slot_writes,
                        ),
                    }
                ),
            )
        ],
        post={
            Spec.NONCE_MANAGER: Account(
                storage={
                    keyed_nonce_slot(sender, NONCE_KEY): 1
                    for sender in senders
                }
            ),
            **{sender: Account(nonce=0) for sender in senders},
        },
    )


def test_disjoint_keys_replay_independent(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Include two transactions from one sender on disjoint keys, both at
    sequence zero.
    """
    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[key],
            nonce=0,
        )
        for key in (NONCE_KEY, OTHER_KEY)
    ]
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post={
            Spec.NONCE_MANAGER: Account(
                storage={
                    keyed_nonce_slot(sender, NONCE_KEY): 1,
                    keyed_nonce_slot(sender, OTHER_KEY): 1,
                }
            ),
            sender: Account(nonce=0),
        },
    )


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "first_keys,second_keys",
    [
        pytest.param([NONCE_KEY], [NONCE_KEY, OTHER_KEY], id="superset_keys"),
        pytest.param([NONCE_KEY], [NONCE_KEY], id="same_key"),
        pytest.param([NONCE_KEY, OTHER_KEY], [OTHER_KEY], id="subset_key"),
        pytest.param(
            [NONCE_KEY, OTHER_KEY],
            [OTHER_KEY, OTHER_KEY + 1],
            id="partly_overlapping_keys",
        ),
    ],
)
def test_overlapping_keys_same_sequence_rejected(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    first_keys: List[int],
    second_keys: List[int],
) -> None:
    """
    Reject a block whose second transaction shares a key, at the same
    sequence, with the first.
    """
    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=first_keys,
            nonce=0,
        ),
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=second_keys,
            nonce=0,
            error=TransactionException.NONCE_MISMATCH_TOO_LOW,
        ),
    ]
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                exception=TransactionException.NONCE_MISMATCH_TOO_LOW,
            )
        ],
        post={
            Spec.NONCE_MANAGER: Account(storage={}),
            sender: Account(nonce=0),
        },
    )


def test_overlapping_keys_next_sequence(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Advance one key of a consumed two-key set at the next sequence in
    the same block, leaving the other key behind.
    """
    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[NONCE_KEY, OTHER_KEY],
            nonce=0,
        ),
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[OTHER_KEY],
            nonce=1,
        ),
    ]
    slot_writes = {
        NONCE_KEY: [BalStorageChange(block_access_index=1, post_value=1)],
        OTHER_KEY: [
            BalStorageChange(block_access_index=1, post_value=1),
            BalStorageChange(block_access_index=2, post_value=2),
        ],
    }
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        Spec.NONCE_MANAGER: BalAccountExpectation(
                            nonce_changes=[],
                            balance_changes=[],
                            code_changes=[],
                            storage_changes=sorted(
                                (
                                    BalStorageSlot(
                                        slot=keyed_nonce_slot(sender, key),
                                        slot_changes=changes,
                                    )
                                    for key, changes in slot_writes.items()
                                ),
                                key=lambda write: int(write.slot),
                            ),
                        ),
                    }
                ),
            )
        ],
        post={
            Spec.NONCE_MANAGER: Account(
                storage={
                    keyed_nonce_slot(sender, NONCE_KEY): 1,
                    keyed_nonce_slot(sender, OTHER_KEY): 2,
                }
            ),
            sender: Account(nonce=0),
        },
    )


def test_keyed_then_legacy_from_one_sender(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Interleave keyed and legacy-keyed transactions from one sender in a
    block, neither advancing the other's domain.
    """
    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[NONCE_KEY],
            nonce=0,
        ),
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[0],
            nonce=0,
        ),
        Transaction(
            sender=sender,
            frames=[verify_frame()],
            nonce_keys=[NONCE_KEY],
            nonce=1,
        ),
    ]
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 2}
            ),
            sender: Account(nonce=1),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_keys,nonce_seq,used_keys",
    [
        pytest.param([NONCE_KEY], 0, {}, id="fresh_key"),
        pytest.param([NONCE_KEY], 1, {NONCE_KEY: 1}, id="used_key"),
        pytest.param(
            [NONCE_KEY, OTHER_KEY],
            1,
            {NONCE_KEY: 1, OTHER_KEY: 1},
            id="two_used_keys",
        ),
        pytest.param([NONCE_KEY, OTHER_KEY], 0, {}, id="two_fresh_keys"),
        pytest.param([0], 0, {}, id="legacy_key_set"),
    ],
)
def test_block_access_list(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: list[int],
    nonce_seq: int,
    used_keys: Dict[int, int],
) -> None:
    """
    Record each keyed write as a nonce manager storage change at the
    transaction's index, with the written sequence and never among the
    storage reads, with no sender nonce change, and leave the nonce
    manager out of the list for the legacy key set.
    """
    sender = pre.fund_eoa()
    if used_keys:
        nonce_manager_with_slots(pre, used_key_slots(sender, used_keys))
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
    )
    nonce_manager_expectation: Optional[BalAccountExpectation]
    if nonce_keys == [0]:
        nonce_manager_expectation = None
        sender_expectation = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)]
        )
        post_slots = {}
        sender_nonce = 1
    else:
        written_slots = sorted(
            keyed_nonce_slot(sender, key) for key in nonce_keys
        )
        nonce_manager_expectation = BalAccountExpectation(
            nonce_changes=[],
            balance_changes=[],
            code_changes=[],
            storage_changes=[
                BalStorageSlot(
                    slot=slot,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1, post_value=nonce_seq + 1
                        )
                    ],
                )
                for slot in written_slots
            ],
            storage_reads=[],
        )
        sender_expectation = BalAccountExpectation(nonce_changes=[])
        post_slots = dict.fromkeys(written_slots, nonce_seq + 1)
        sender_nonce = 0
    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                Spec.NONCE_MANAGER: nonce_manager_expectation,
                sender: sender_expectation,
            }
        ),
    )
    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            Spec.NONCE_MANAGER: Account(storage=post_slots),
            sender: Account(nonce=sender_nonce),
        },
    )
