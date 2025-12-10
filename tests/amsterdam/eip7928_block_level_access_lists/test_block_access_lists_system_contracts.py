"""Tests for EIP-7928 using the consistent data class pattern."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Transaction,
    keccak256,
)

from ...cancun.eip4788_beacon_root.spec import Spec as Spec_eip4788
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def test_bal_4788_simple(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure system contract execution related addresses and changes are
    captured.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    charlie = pre.fund_eoa(amount=0)

    tx_alice = Transaction(
        sender=alice,
        to=charlie,
        value=10,
    )

    tx_bob = Transaction(
        sender=bob,
        to=charlie,
        value=10,
    )

    timestamp = 100
    parent_beacon_block_root = keccak256(
        int.to_bytes(timestamp, length=8, byteorder="big")
    )
    root_storage_slot = timestamp + Spec_eip4788.HISTORY_BUFFER_LENGTH

    block = Block(
        txs=[tx_alice, tx_bob],
        timestamp=timestamp,
        parent_beacon_block_root=parent_beacon_block_root,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                bob: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=2, post_nonce=1)],
                ),
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=10),
                        BalBalanceChange(tx_index=2, post_balance=20),
                    ],
                ),
                Spec_eip4788.SYSTEM_ADDRESS: BalAccountExpectation(
                    nonce_changes=[],
                    balance_changes=[],
                    code_changes=[],
                    storage_changes=[],
                    storage_reads=[],
                ),
                Spec_eip4788.BEACON_ROOTS_ADDRESS: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=timestamp,
                            slot_changes=[
                                BalStorageChange(
                                    tx_index=0,
                                    post_value=timestamp,
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=root_storage_slot,
                            slot_changes=[
                                BalStorageChange(
                                    tx_index=0,
                                    post_value=parent_beacon_block_root,
                                )
                            ],
                        ),
                    ]
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(nonce=1),
            charlie: Account(balance=20),
        },
    )
