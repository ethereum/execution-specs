"""
Tests for the EIP-8250 fork transition.

The fork installs the nonce manager at `Spec.NONCE_MANAGER` before the
first post-fork block's transactions run: its code, a nonce of at least
one, and any balance it already held. Every other EIP-8250 test starts
at a fork where the account is already in the genesis allocation.

The pre-fork blocks run under the `amsterdam` spec module and the fork
block onwards under `bogota`. As EIP-8250 is specified, the
initialization happens before the fork block runs and is not part of
that block's access list.
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
from .helpers import KEY_A, keyed_storage, nonce_slot
from .spec import Spec, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_at_transition_to("Bogota")

FORK_TIMESTAMP = 15_000
"""Timestamp at which the transition fork activates EIP-8250."""

NONCE_MANAGER_UNTOUCHED = BlockAccessListExpectation(
    account_expectations={
        Spec.NONCE_MANAGER: BalAccountExpectation.empty(),
    }
)
"""
The nonce manager is in the block access list, read by a transaction,
and records no change.
"""


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "pre_fork_nonce,pre_fork_balance",
    [
        pytest.param(None, None, id="absent_before_fork"),
        pytest.param(0, 1, id="balance_before_fork"),
        pytest.param(7, 1, id="nonce_and_balance_before_fork"),
    ],
)
def test_nonce_manager_installed_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    pre_fork_nonce: int | None,
    pre_fork_balance: int | None,
) -> None:
    """
    Install the nonce manager at the fork block.

    A probe records `EXTCODESIZE` of the address keyed by block number:
    no code in the pre-fork block, the runtime code from the fork block
    on. The account ends with a nonce of `max(existing_nonce, 1)`, its
    balance unchanged and empty storage. No block's access list records
    a change to it, the fork block included.
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
            txs=[Transaction(sender=sender, to=probe)],
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
            nonce=max(pre_fork_nonce or 0, 1),
            balance=pre_fork_balance or 0,
            code=Spec.NONCE_MANAGER_CODE,
            storage={},
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_keyed_frame_in_first_post_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Consume a keyed nonce in the block that activates the fork.

    The nonce manager is installed before the block's transactions run,
    so the keyed write lands in its storage. The block access list records
    the write at the transaction's index and nothing for the install.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        nonce=0,
        nonce_keys=[KEY_A],
        frames=[verify_frame()],
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
                        code_changes=[],
                        storage_changes=[
                            BalStorageSlot(
                                slot=nonce_slot(sender, KEY_A),
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
        sender: Account(nonce=0),
        Spec.NONCE_MANAGER: Account(
            nonce=1,
            code=Spec.NONCE_MANAGER_CODE,
            storage=keyed_storage(sender, {KEY_A: 1}),
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
