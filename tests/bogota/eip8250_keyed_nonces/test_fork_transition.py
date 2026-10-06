"""
Tests for the EIP-8250 fork transition.

The fork installs the nonce manager before the first post-fork block's
transactions run. The pre-fork blocks run under the `amsterdam` spec
module and the fork block onwards under `bogota`. The installation is
not part of the fork block's access list.
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
            nonce_changes=[], code_changes=[], storage_changes=[]
        ),
    }
)
"""The nonce manager is read by a probe and records no change."""


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "pre_fork_nonce,pre_fork_balance",
    [
        pytest.param(None, None, id="absent_before_fork"),
        pytest.param(0, 1, id="balance_before_fork"),
        pytest.param(7, 1, id="nonce_and_balance_before_fork"),
    ],
)
def test_nonce_manager_initialized_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    pre_fork_nonce: int | None,
    pre_fork_balance: int | None,
) -> None:
    """
    Install the nonce manager code at the fork block, raise its nonce
    to at least one and keep its balance, with no block access list
    entry for the installation.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        Op.SSTORE(Op.NUMBER, Op.EXTCODESIZE(Spec.NONCE_MANAGER)) + Op.STOP
    )
    if pre_fork_nonce is not None and pre_fork_balance is not None:
        pre[Spec.NONCE_MANAGER] = Account(
            nonce=pre_fork_nonce, balance=pre_fork_balance
        )

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[
                Transaction(sender=sender, to=probe),
                # Before the fork the call is a plain transfer.
                Transaction(sender=sender, to=Spec.NONCE_MANAGER, value=1),
            ],
            expected_block_access_list=NONCE_MANAGER_UNTOUCHED,
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[Transaction(sender=sender, to=probe)],
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
        probe: Account(storage={1: 0, 2: code_size, 3: code_size}),
        Spec.NONCE_MANAGER: Account(
            nonce=max(pre_fork_nonce or 0, Spec.NONCE_MANAGER_NONCE),
            balance=(pre_fork_balance or 0) + 1,
            code=Spec.NONCE_MANAGER_CODE,
            storage={},
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_keyed_transaction_in_first_post_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Consume a key in the fork block, whose access list records the slot
    write and no installation.
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
