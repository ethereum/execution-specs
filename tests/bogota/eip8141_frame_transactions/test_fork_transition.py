"""
Tests for the EIP-8141 fork transition.

The expiry verifier is an ordinary contract that is part of the genesis
allocation in every EIP-8141 test, so EIP-8141's activation writes no
state. These tests cover what the first post-fork block accepts: a
frame transaction carrying an expiry frame executes in the block that
activates the fork.

The pre-fork blocks run under the `amsterdam` spec module, which has no
frame transactions, and the post-fork blocks under `bogota`, so the
transition tool applies each side's own rules. A frame transaction being
rejected before the fork is not covered here yet.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    FrameReceipt,
    Op,
    Transaction,
    TransactionReceipt,
)

from .helpers import expiry_frame, sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_at_transition_to("Bogota")

FORK_TIMESTAMP = 15_000
"""Timestamp at which the transition fork activates EIP-8141."""

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

VERIFIER_WITHOUT_CODE_CHANGE = BlockAccessListExpectation(
    account_expectations={
        Spec.EXPIRY_VERIFIER: BalAccountExpectation(code_changes=[]),
    }
)
"""
The verifier is in the block access list, reached by a transaction, and
records no code change.
"""


def test_expiry_frame_in_first_post_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Execute an expiry verifier frame in the block that activates the fork.

    The verifier is already deployed before the fork, so a frame
    transaction carrying an expiry frame in the activation block finds
    the contract in place and executes. The block's access list shows
    the verifier as executed code, not as a code change.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            expiry_frame(),
            sender_frame(target=target),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS) for _ in range(3)
            ],
        ),
    )
    blocks = [
        Block(timestamp=FORK_TIMESTAMP - 1),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[tx],
            expected_block_access_list=VERIFIER_WITHOUT_CODE_CHANGE,
        ),
    ]
    post = {
        target: Account(storage={SLOT_EXECUTED: 1}),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
