"""
Tests for the EIP-8141 fork transition.

The fork installs the expiry verifier's runtime code at
`Spec.EXPIRY_VERIFIER` when it activates. Every other EIP-8141 test
starts at a fork where the code is already in the genesis allocation, so
these tests are the only ones that exercise the install itself: what the
account looks like before the fork block, and what changes at it.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
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

pytestmark = pytest.mark.valid_at_transition_to("EIP8141")

FORK_TIMESTAMP = 15_000
"""Timestamp at which the transition fork activates EIP-8141."""

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "pre_fork_nonce,pre_fork_balance",
    [
        pytest.param(None, None, id="absent_before_fork"),
        pytest.param(0, 1, id="balance_before_fork"),
        pytest.param(7, 1, id="nonce_and_balance_before_fork"),
    ],
)
@pytest.mark.parametrize(
    "transfer_before_fork",
    [
        pytest.param(False, id="no_transfer"),
        pytest.param(True, id="transfer_before_fork"),
    ],
)
def test_expiry_verifier_installed_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    pre_fork_nonce: int | None,
    pre_fork_balance: int | None,
    transfer_before_fork: bool,
) -> None:
    """
    Install the expiry verifier's code at the fork block and nothing else.

    A probe contract records `EXTCODESIZE` of the verifier address keyed
    by block number, so each block's view is visible in the post-state:

    * block 1 (pre-fork): no code yet, and a transaction sent to the
      address runs nothing.
    * block 2 (transition): the runtime code is present from the first
      post-fork block.
    * block 3 (post-fork): the code stays.

    The account's other fields are left as they were before the fork. An
    address nobody touched ends with a zero nonce and balance; an account
    that already existed keeps its nonce and its balance, whether that
    balance was in the genesis allocation or arrived by a pre-fork
    transfer. The post-state pins all three fields, so an install that
    writes anything other than the code fails here.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        Op.SSTORE(Op.NUMBER, Op.EXTCODESIZE(Spec.EXPIRY_VERIFIER)) + Op.STOP
    )
    if pre_fork_nonce is not None and pre_fork_balance is not None:
        pre[Spec.EXPIRY_VERIFIER] = Account(
            nonce=pre_fork_nonce, balance=pre_fork_balance
        )

    pre_fork_txs = [
        Transaction(sender=sender, to=probe),
        # Before the fork there is no code at the address: the call is a
        # plain transfer of whatever value it carries.
        Transaction(
            sender=sender,
            to=Spec.EXPIRY_VERIFIER,
            value=1 if transfer_before_fork else 0,
        ),
    ]
    blocks = [
        Block(timestamp=FORK_TIMESTAMP - 1, txs=pre_fork_txs),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[Transaction(sender=sender, to=probe)],
        ),
        Block(
            timestamp=FORK_TIMESTAMP + 1,
            txs=[Transaction(sender=sender, to=probe)],
        ),
    ]

    code_size = len(Spec.EXPIRY_VERIFIER_CODE)
    expected_balance = (pre_fork_balance or 0) + (
        1 if transfer_before_fork else 0
    )
    post = {
        probe: Account(
            storage={
                1: 0,
                2: code_size,
                3: code_size,
            },
        ),
        Spec.EXPIRY_VERIFIER: Account(
            nonce=pre_fork_nonce or 0,
            balance=expected_balance,
            code=Spec.EXPIRY_VERIFIER_CODE,
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_expiry_frame_in_first_post_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Execute an expiry verifier frame in the block that activates the fork.

    The verifier's code is installed before the block's transactions run,
    so a frame transaction carrying an expiry frame in that same block
    finds the predeploy in place and executes.
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
        Block(timestamp=FORK_TIMESTAMP, txs=[tx]),
    ]
    post = {
        Spec.EXPIRY_VERIFIER: Account(
            nonce=0,
            code=Spec.EXPIRY_VERIFIER_CODE,
        ),
        target: Account(storage={SLOT_EXECUTED: 1}),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
