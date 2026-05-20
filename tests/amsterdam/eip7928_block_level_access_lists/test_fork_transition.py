"""Fork-transition tests for EIP-7928 (Block-level Access Lists)."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    EIPChecklist,
    Environment,
    Hash,
    Header,
    Transaction,
    TransitionFork,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

FORK_TIMESTAMP = 15_000


@EIPChecklist.BlockHeaderField.Test.ForkTransition.Initial()
@pytest.mark.valid_at_transition_to("Amsterdam")
def test_bal_fork_transition_happy_path(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify that a BAL is produced at the Amsterdam activation block.

    - Pre-fork block (timestamp < 15_000): no BAL hash, no BAL body.
    - Activation block (timestamp == 15_000): BAL hash and body are present
      and match the actual access activity in the block.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    pre_fork_tx = Transaction(sender=alice, to=bob, value=100, gas_price=10)
    post_fork_tx = Transaction(sender=alice, to=bob, value=100, gas_price=10)

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[pre_fork_tx],
            header_verify=Header(
                block_access_list_hash=Header.EMPTY_FIELD,
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[post_fork_tx],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    alice: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=1, post_nonce=2)
                        ],
                    ),
                    bob: BalAccountExpectation(
                        balance_changes=[
                            BalBalanceChange(
                                block_access_index=1, post_balance=200
                            ),
                        ],
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={bob: Account(balance=200)},
    )


@EIPChecklist.BlockHeaderField.Test.ForkTransition.Before()
@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.exception_test
def test_invalid_pre_fork_block_with_bal_hash_field(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a pre-Amsterdam block whose header carries
    `block_access_list_hash`.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(sender=sender, to=receiver, value=100, gas_price=10)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP - 1,
                txs=[tx],
                rlp_modifier=Header(block_access_list_hash=Hash(0)),
                exception=BlockException.INVALID_BLOCK_HASH,
            ),
        ],
    )


@EIPChecklist.BlockHeaderField.Test.ForkTransition.After()
@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.exception_test
def test_invalid_post_fork_block_without_bal_hash_field(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject an Amsterdam activation block whose header is missing
    `block_access_list_hash`.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(sender=sender, to=receiver, value=100, gas_price=10)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[tx],
                rlp_modifier=Header(
                    block_access_list_hash=Header.REMOVE_FIELD,
                ),
                exception=[
                    BlockException.INVALID_BAL_HASH,
                    BlockException.INVALID_BLOCK_HASH,
                ],
            ),
        ],
    )


@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.parametrize(
    "exceeds_limit_at_fork",
    [
        pytest.param(False, id="at_fork_within_budget"),
        pytest.param(
            True,
            marks=pytest.mark.exception_test,
            id="at_fork_over_budget",
        ),
    ],
)
def test_fork_transition_bal_size_constraint(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    exceeds_limit_at_fork: bool,
) -> None:
    """
    Verify the BAL size constraint applies only on/after Amsterdam.

    - Pre-fork block at a `gas_limit` that *would* fail the post-fork
      constraint is accepted (the constraint is not yet enforced).
    - Activation block at the exact budget is accepted.
    - Activation block one item over the budget is rejected with
      `BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED`.
    """
    amsterdam = fork.transitions_to()
    min_gas_limit = (
        amsterdam.empty_block_bal_item_count()
        * amsterdam.gas_costs().BLOCK_ACCESS_LIST_ITEM
    )
    over_budget_gas_limit = min_gas_limit - 1

    pre_fork_block = Block(
        timestamp=FORK_TIMESTAMP - 1,
        txs=[],
    )

    if exceeds_limit_at_fork:
        at_fork_block = Block(
            timestamp=FORK_TIMESTAMP,
            txs=[],
            exception=BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED,
        )
        block_gas_limit = over_budget_gas_limit
    else:
        at_fork_block = Block(
            timestamp=FORK_TIMESTAMP,
            txs=[],
        )
        block_gas_limit = min_gas_limit

    blockchain_test(
        pre=pre,
        post={},
        blocks=[pre_fork_block, at_fork_block],
        genesis_environment=Environment(gas_limit=block_gas_limit),
    )
