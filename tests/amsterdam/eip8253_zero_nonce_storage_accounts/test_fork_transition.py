"""Fork-transition tests for EIP-8253."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Op,
    Transaction,
    compute_create_address,
)

from .spec import Spec, ref_spec_8253

REFERENCE_SPEC_GIT_PATH = ref_spec_8253.git_path
REFERENCE_SPEC_VERSION = ref_spec_8253.version

FORK_TIMESTAMP = 15_000


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
def test_nonce_bump_and_bal(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Bump exactly the targeted accounts once and preserve their state."""
    targets = tuple(Address(address) for address in Spec.TARGETED_ACCOUNTS)
    non_target = Address(0x1234)
    expected_accounts = {}

    for i, target in enumerate(targets):
        balance = i + 1
        storage = {i: i + 1}
        pre[target] = Account(nonce=0, balance=balance, storage=storage)
        expected_accounts[target] = Account(
            nonce=1,
            balance=balance,
            storage=storage,
        )

    pre[non_target] = Account(nonce=0, balance=1, storage={0: 1})

    transition_expectations = {
        target: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=0, post_nonce=1)]
        )
        for target in targets
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=FORK_TIMESTAMP - 1),
            Block(
                timestamp=FORK_TIMESTAMP,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=transition_expectations
                ),
            ),
            Block(
                timestamp=FORK_TIMESTAMP + 1,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=dict.fromkeys(targets)
                ),
            ),
        ],
        post={
            **expected_accounts,
            non_target: Account(nonce=0, balance=1, storage={0: 1}),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
def test_create_collision_in_first_fork_transaction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """The activation bump makes a historical CREATE destination collide."""
    creator = Address(Spec.HISTORICAL_CREATOR)
    target = Address(Spec.HISTORICAL_TARGET)
    assert (
        compute_create_address(
            address=creator,
            nonce=Spec.HISTORICAL_CREATOR_NONCE,
        )
        == target
    )

    pre[target] = Account(nonce=0, balance=7, storage={1: 2})
    pre[creator] = Account(
        nonce=Spec.HISTORICAL_CREATOR_NONCE,
        code=Op.SSTORE(0, Op.CREATE(0, 0, 0)),
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=FORK_TIMESTAMP - 1),
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=creator)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        target: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=0,
                                    post_nonce=1,
                                )
                            ]
                        )
                    }
                ),
            ),
        ],
        post={
            target: Account(nonce=1, balance=7, storage={1: 2}),
            creator: Account(
                nonce=Spec.HISTORICAL_CREATOR_NONCE + 1,
                code=Op.SSTORE(0, Op.CREATE(0, 0, 0)),
                storage={0: 0},
            ),
        },
    )
