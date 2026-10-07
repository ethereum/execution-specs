"""
Tests for the EIP-8250 fork transition.

The nonce manager is an ordinary contract that must already be in the
state when the fork activates, here through the genesis allocation.
Activation changes no state, so the fork block's access list records
nothing for the installation. The pre-fork blocks run under the
`amsterdam` spec module and the fork block onwards under `bogota`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from ..eip8141_frame_transactions.helpers import verify_frame
from .helpers import NONCE_KEY
from .spec import Spec, keyed_nonce_slot, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_at_transition_to("Bogota")

FORK_TIMESTAMP = 15_000
"""Timestamp at which the transition fork activates EIP-8250."""

NONCE_MANAGER_UNTOUCHED = BlockAccessListExpectation(
    account_expectations={
        Spec.NONCE_MANAGER: BalAccountExpectation(
            nonce_changes=[],
            balance_changes=[],
            code_changes=[],
            storage_changes=[],
        ),
    }
)
"""The nonce manager is read by a probe and records no change."""


def test_nonce_manager_unchanged_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Keep the nonce manager unchanged across the fork, with no block
    access list entry for activation, while ordinary calls to it revert
    on both sides of the fork.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        Op.SSTORE(Op.NUMBER, Op.EXTCODESIZE(Spec.NONCE_MANAGER)) + Op.STOP
    )

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[
                Transaction(sender=sender, to=probe),
                Transaction(sender=sender, to=Spec.NONCE_MANAGER, value=1),
            ],
            expected_block_access_list=NONCE_MANAGER_UNTOUCHED,
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[
                Transaction(sender=sender, to=probe),
                Transaction(sender=sender, to=Spec.NONCE_MANAGER, value=1),
            ],
            expected_block_access_list=NONCE_MANAGER_UNTOUCHED,
        ),
        Block(
            timestamp=FORK_TIMESTAMP + 1,
            txs=[Transaction(sender=sender, to=probe)],
            expected_block_access_list=NONCE_MANAGER_UNTOUCHED,
        ),
    ]

    code_size = len(Spec.NONCE_MANAGER_CODE)
    post = {
        probe: Account(storage={1: code_size, 2: code_size, 3: code_size}),
        Spec.NONCE_MANAGER: Account(
            nonce=Spec.NONCE_MANAGER_NONCE,
            balance=0,
            code=Spec.NONCE_MANAGER_CODE,
            storage={},
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.pre_alloc_mutable
def test_missing_nonce_manager_not_installed_at_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept the fork block on a chain whose state lacks the nonce
    manager, and install nothing at activation.
    """
    # Remove the nonce manager from the genesis allocation.
    pre[Spec.NONCE_MANAGER] = Account(nonce=0, balance=0, code=b"")
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        Op.SSTORE(Op.NUMBER, Op.EXTCODESIZE(Spec.NONCE_MANAGER)) + Op.STOP
    )

    blocks = [
        Block(
            timestamp=timestamp,
            txs=[Transaction(sender=sender, to=probe)],
            expected_block_access_list=NONCE_MANAGER_UNTOUCHED,
        )
        for timestamp in (
            FORK_TIMESTAMP - 1,
            FORK_TIMESTAMP,
            FORK_TIMESTAMP + 1,
        )
    ]
    post = {
        probe: Account(storage={1: 0, 2: 0, 3: 0}),
        Spec.NONCE_MANAGER: Account.NONEXISTENT,
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_keyed_transaction_in_first_post_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Consume a key in the fork block, whose access list records only the
    slot write.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=[NONCE_KEY],
        nonce=0,
    )
    blocks = [
        Block(timestamp=FORK_TIMESTAMP - 1),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[tx],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    Spec.NONCE_MANAGER: BalAccountExpectation(
                        nonce_changes=[],
                        balance_changes=[],
                        code_changes=[],
                        storage_changes=[
                            BalStorageSlot(
                                slot=keyed_nonce_slot(sender, NONCE_KEY),
                                slot_changes=[
                                    BalStorageChange(
                                        block_access_index=1, post_value=1
                                    )
                                ],
                            )
                        ],
                    ),
                }
            ),
        ),
    ]
    post = {
        Spec.NONCE_MANAGER: Account(
            nonce=Spec.NONCE_MANAGER_NONCE,
            code=Spec.NONCE_MANAGER_CODE,
            storage={keyed_nonce_slot(sender, NONCE_KEY): 1},
        ),
        sender: Account(nonce=0),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
