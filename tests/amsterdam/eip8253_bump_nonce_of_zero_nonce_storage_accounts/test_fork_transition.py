"""
Tests for [EIP-8253: Bump nonce of zero-nonce storage accounts](https://eips.ethereum.org/EIPS/eip-8253).

The bump happens once, at the Amsterdam fork block, so every test is a
fork-transition test. The targeted accounts are placed in the pre-state the
way they look on Mainnet: empty code, zero nonce, non-empty storage.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Initcode,
    Op,
    Storage,
    Transaction,
    compute_create_address,
    keccak256,
)

from .spec import Spec, TargetedAccount, ref_spec_8253

REFERENCE_SPEC_GIT_PATH = ref_spec_8253.git_path
REFERENCE_SPEC_VERSION = ref_spec_8253.version

pytestmark = [
    pytest.mark.valid_at_transition_to("Amsterdam"),
    pytest.mark.pre_alloc_mutable,
]

FORK_TIMESTAMP = 15_000

# Distinct non-zero balances per targeted account, so a balance that is
# zeroed or attributed to the wrong account is caught.
BALANCE_BASE = 10**15

BUMP_EXPECTATION = BalAccountExpectation(
    nonce_changes=[BalNonceChange(block_access_index=0, post_nonce=1)],
    balance_changes=[],
    code_changes=[],
    storage_changes=[],
    storage_reads=[],
)
"""The only BAL entry a targeted account gets from the bump."""


def targeted_storage(target: TargetedAccount) -> Storage:
    """Return a non-zero value in each Mainnet storage slot of `target`."""
    storage = Storage()
    for key in target.storage_keys:
        storage[key] = 1
    return storage


def place_targeted_accounts(pre: Alloc) -> Dict[Address, Account]:
    """
    Add every targeted account to the pre-state as it looks on Mainnet and
    return the accounts expected after the bump.
    """
    post: Dict[Address, Account] = {}
    for index, target in enumerate(Spec.TARGETED_ACCOUNTS):
        address = Address(target.address)
        balance = BALANCE_BASE + index
        storage = targeted_storage(target)
        pre[address] = Account(
            nonce=0, balance=balance, code=b"", storage=storage
        )
        post[address] = Account(
            nonce=1, balance=balance, code=b"", storage=storage
        )
    return post


def test_nonce_bump_at_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Every targeted account gets nonce one at the fork block and keeps its
    balance, storage, and empty code. The fork block BAL holds exactly one
    nonce change per account at block access index zero; the blocks before
    and after leave the accounts untouched.
    """
    post = place_targeted_accounts(pre)
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    # A balance change before the fork must survive the bump.
    first = Address(Spec.TARGETED_ACCOUNTS[0].address)
    transfer = 7
    post[first] = Account(
        nonce=1,
        balance=int(post[first].balance) + transfer,
        code=b"",
        storage=post[first].storage,
    )

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[Transaction(sender=sender, to=first, value=transfer)],
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[Transaction(sender=sender, to=receiver, value=1)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations=dict.fromkeys(post, BUMP_EXPECTATION)
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP + 1,
            txs=[Transaction(sender=sender, to=receiver, value=1)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations=dict.fromkeys(post)
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={**post, receiver: Account(balance=2)},
    )


@pytest.mark.parametrize(
    "target",
    Spec.TARGETED_ACCOUNTS,
    ids=[f"{target.address:#042x}" for target in Spec.TARGETED_ACCOUNTS],
)
def test_create_collision_at_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    target: TargetedAccount,
) -> None:
    """
    Replay the Mainnet creation of a targeted account as the first
    transaction of the fork block: a `CREATE` from the original creator at
    the original nonce. It collides under EIP-684 because the nonce is now
    one, so no code is deployed and the storage survives.
    """
    address = Address(target.address)
    creator = Address(target.creator)
    assert (
        compute_create_address(address=creator, nonce=target.creation_nonce)
        == address
    ), "test correctness: creator and nonce do not derive the target"

    storage = targeted_storage(target)
    pre[address] = Account(
        nonce=0, balance=BALANCE_BASE, code=b"", storage=storage
    )

    initcode = Initcode(deploy_code=Op.STOP)
    creator_storage = Storage()
    result_slot = creator_storage.store_next(0, "create_result")
    executed_slot = creator_storage.store_next(1, "executed")
    creator_code = (
        Op.MSTORE(0, int.from_bytes(bytes(initcode).ljust(32, b"\0"), "big"))
        + Op.SSTORE(result_slot, Op.CREATE(0, 0, len(initcode)))
        + Op.SSTORE(executed_slot, 1)
        + Op.STOP
    )
    pre.deploy_contract(
        creator_code, address=creator, nonce=target.creation_nonce
    )

    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[Transaction(sender=sender, to=receiver, value=1)],
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[Transaction(sender=sender, to=creator)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    address: BUMP_EXPECTATION,
                    creator: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(
                                block_access_index=1,
                                post_nonce=target.creation_nonce + 1,
                            )
                        ],
                        storage_changes=[
                            BalStorageSlot(
                                slot=executed_slot,
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

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            address: Account(
                nonce=1, balance=BALANCE_BASE, code=b"", storage=storage
            ),
            creator: Account(
                nonce=target.creation_nonce + 1,
                code=creator_code,
                storage=creator_storage,
            ),
            receiver: Account(balance=1),
        },
    )


def test_call_to_bumped_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A `CALL` with value to a targeted account behaves the same before and at
    the fork block: it succeeds, the account still has no code, and its
    balance grows. In the fork block the BAL pairs the nonce change at index
    zero with the balance change at index one.
    """
    target = Spec.TARGETED_ACCOUNTS[0]
    address = Address(target.address)
    storage = targeted_storage(target)
    pre[address] = Account(
        nonce=0, balance=BALANCE_BASE, code=b"", storage=storage
    )
    value = 5

    def deploy_caller(balance_after_call: int) -> tuple[Address, Storage]:
        caller_storage = Storage()
        code = (
            Op.SSTORE(
                caller_storage.store_next(1, "call_success"),
                Op.CALL(Op.GAS, address, value, 0, 0, 0, 0),
            )
            + Op.SSTORE(
                caller_storage.store_next(keccak256(b""), "extcodehash"),
                Op.EXTCODEHASH(address),
            )
            + Op.SSTORE(
                caller_storage.store_next(0, "extcodesize"),
                Op.EXTCODESIZE(address),
            )
            + Op.SSTORE(
                caller_storage.store_next(balance_after_call, "balance"),
                Op.BALANCE(address),
            )
            + Op.STOP
        )
        return pre.deploy_contract(code, balance=value), caller_storage

    caller_before, storage_before = deploy_caller(BALANCE_BASE + value)
    caller_at_fork, storage_at_fork = deploy_caller(BALANCE_BASE + 2 * value)
    sender = pre.fund_eoa()

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[Transaction(sender=sender, to=caller_before)],
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[Transaction(sender=sender, to=caller_at_fork)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    address: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=0, post_nonce=1)
                        ],
                        balance_changes=[
                            BalBalanceChange(
                                block_access_index=1,
                                post_balance=BALANCE_BASE + 2 * value,
                            )
                        ],
                        code_changes=[],
                        storage_changes=[],
                        storage_reads=[],
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            address: Account(
                nonce=1,
                balance=BALANCE_BASE + 2 * value,
                code=b"",
                storage=storage,
            ),
            caller_before: Account(balance=0, storage=storage_before),
            caller_at_fork: Account(balance=0, storage=storage_at_fork),
        },
    )


def test_non_targeted_accounts_unaffected(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Accounts that are not on the list keep their nonce at the fork block,
    including one with the same shape as the targeted accounts.
    """
    place_targeted_accounts(pre)

    lookalike = pre.fund_eoa(amount=0)
    pre[lookalike] = Account(nonce=0, balance=1, code=b"", storage={0: 1})
    contract = pre.deploy_contract(Op.STOP, storage={0: 1})
    used_eoa = pre.fund_eoa(nonce=5)
    fresh_eoa = pre.fund_eoa(amount=1)

    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    untouched = [lookalike, contract, used_eoa, fresh_eoa]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP - 1,
                txs=[Transaction(sender=sender, to=receiver, value=1)],
            ),
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=receiver, value=1)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=dict.fromkeys(untouched)
                ),
            ),
        ],
        post={
            lookalike: Account(nonce=0, balance=1, code=b"", storage={0: 1}),
            contract: Account(nonce=1, code=Op.STOP, storage={0: 1}),
            used_eoa: Account(nonce=5),
            fresh_eoa: Account(nonce=0, balance=1),
            receiver: Account(balance=2),
        },
    )


def test_targeted_accounts_absent_from_pre_state(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    The bump is unconditional: a targeted account missing from the state is
    created at the fork block with nonce one, zero balance, and no code.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)
    targeted = [Address(target.address) for target in Spec.TARGETED_ACCOUNTS]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP - 1,
                txs=[Transaction(sender=sender, to=receiver, value=1)],
            ),
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=receiver, value=1)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=dict.fromkeys(
                        targeted, BUMP_EXPECTATION
                    )
                ),
            ),
        ],
        post={
            **{
                address: Account(nonce=1, balance=0, code=b"", storage={})
                for address in targeted
            },
            receiver: Account(balance=2),
        },
    )
