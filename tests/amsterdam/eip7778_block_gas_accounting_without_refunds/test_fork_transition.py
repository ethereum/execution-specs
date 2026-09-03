"""
Fork-transition tests for
[EIP-7778 Block Gas Accounting without Refunds](https://eips.ethereum.org/EIPS/eip-7778).

Before the fork a transaction contributes its post-refund gas to the
block, afterwards it contributes its pre-refund gas. Both observables of
that switch are pinned here: the gas the block header reports, and the
admission of a trailing transaction whose room in the block depends on
which accumulator the client keeps.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    EIPChecklist,
    Environment,
    RefundTypes,
    Transaction,
    TransactionException,
    TransitionFork,
)
from execution_testing.vm import Op

from .helpers import RefundTransaction
from .spec import ref_spec_7778

REFERENCE_SPEC_GIT_PATH = ref_spec_7778.git_path
REFERENCE_SPEC_VERSION = ref_spec_7778.version

pytestmark = pytest.mark.valid_at_transition_to("EIP7778")

# Transition forks switch at timestamp 15_000.
PRE_FORK_TIMESTAMP = 14_999
POST_FORK_TIMESTAMP = 15_000

INITIAL_FUND = 10**18
REFUNDS_COUNT = 10


@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.parametrize(
    "timestamp,block_gas_limit_delta,block_is_invalid",
    [
        pytest.param(PRE_FORK_TIMESTAMP, -1, False, id="accepted_before_fork"),
        pytest.param(POST_FORK_TIMESTAMP, 0, False, id="accepted_after_fork"),
        pytest.param(
            POST_FORK_TIMESTAMP,
            -1,
            True,
            marks=pytest.mark.exception_test,
            id="rejected_after_fork",
        ),
    ],
)
def test_trailing_tx_admission_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    timestamp: int,
    block_gas_limit_delta: int,
    block_is_invalid: bool,
) -> None:
    """
    Pin the block gas allowance flip across the activation boundary.

    The block gas limit leaves room for the trailing transaction only
    when the refund is credited back to the accumulator, so the same
    shape is accepted before the fork and rejected after it.
    """
    sub_fork = fork.fork_at(timestamp=timestamp)

    refund_tx = RefundTransaction.build(
        fork=sub_fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={RefundTypes.STORAGE_CLEAR},
        refunds_count=REFUNDS_COUNT,
    )
    refund_tx.set_pre(pre)

    receipt_gas_used = refund_tx.expected_receipt.gas_used
    assert receipt_gas_used is not None
    # Without a refund the two accumulators coincide and the boundary is
    # unobservable.
    assert refund_tx.block_execution() > receipt_gas_used, (
        "Parametrization must produce a refund; without one pre- and "
        "post-refund accounting agree"
    )

    stop_address = pre.deterministic_deploy_contract(deploy_code=Op.STOP)
    intrinsic_cost_calc = sub_fork.transaction_intrinsic_cost_calculator()
    # Slack so a post-refund gate admits the trailing tx and still keeps
    # the block within its gas limit, instead of being caught by the
    # header gas_used check.
    trailing_tx_gas_limit = 2 * intrinsic_cost_calc(calldata=b"")
    trailing_tx = Transaction(
        to=stop_address,
        gas_limit=trailing_tx_gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED
        if block_is_invalid
        else None,
    )

    # Sized against the post-refund accumulator, which only the
    # post-fork rules exceed.
    block_gas_limit = (
        refund_tx.block_execution()
        + trailing_tx_gas_limit
        + block_gas_limit_delta
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=timestamp,
                txs=[refund_tx, trailing_tx],
                gas_limit=block_gas_limit,
                exception=[
                    BlockException.GAS_USED_OVERFLOW,
                    TransactionException.GAS_ALLOWANCE_EXCEEDED,
                ]
                if block_is_invalid
                else None,
            )
        ],
        post=refund_tx.post(pre, block_is_invalid=block_is_invalid),
        genesis_environment=Environment(gas_limit=block_gas_limit),
    )


@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedAfterFork()
def test_block_gas_used_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Pin the gas a block reports on each side of the activation boundary.

    The same refunding transaction shape is sent in a pre-fork and a
    post-fork block, each with its own sender so the receipt and balance
    pins stay per-fork. The header reports post-refund gas before the
    fork and pre-refund gas after it, while the sender is charged the
    post-refund amount on both sides.
    """
    blocks = []
    post: Dict[Address, Account | None] = {}

    for timestamp in (PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP):
        sub_fork = fork.fork_at(timestamp=timestamp)

        refund_tx = RefundTransaction.build(
            fork=sub_fork,
            sender=pre.fund_eoa(INITIAL_FUND),
            refund_types={RefundTypes.STORAGE_CLEAR},
            refunds_count=REFUNDS_COUNT,
        )
        refund_tx.set_pre(pre)

        receipt_gas_used = refund_tx.expected_receipt.gas_used
        assert receipt_gas_used is not None
        assert refund_tx.block_execution() > receipt_gas_used, (
            "Parametrization must produce a refund; without one pre- and "
            "post-refund accounting agree"
        )

        # EIP-7778 switches the block from the post-refund charge to the
        # pre-refund one; the sender pays the post-refund amount either
        # way.
        expected_gas_used: int
        if timestamp < POST_FORK_TIMESTAMP:
            expected_gas_used = receipt_gas_used
        else:
            expected_gas_used = refund_tx.block_execution()

        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[refund_tx],
                expected_gas_used=expected_gas_used,
            )
        )
        post.update(dict(refund_tx.post(pre).items()))

    blockchain_test(pre=pre, blocks=blocks, post=post)
