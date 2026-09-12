"""
Tests for [EIP-8253: Bump nonce of zero-nonce storage accounts](https://eips.ethereum.org/EIPS/eip-8253).

The bump happens once, at the Amsterdam fork block. These transition tests
use the Mainnet address list with synthetic prestates, including listed
accounts with empty storage and accounts absent from the prestate.
"""

from typing import Tuple

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
    Bytecode,
    Initcode,
    Op,
    Storage,
    Transaction,
    TransitionFork,
    compute_create_address,
    keccak256,
)

from .helpers import (
    BALANCE_BASE,
    BUMP_EXPECTATION,
    FORK_TIMESTAMP,
    bumped_account,
    place_targeted_account,
    place_targeted_accounts,
)
from .spec import Spec, TargetedAccount, ref_spec_8253

REFERENCE_SPEC_GIT_PATH = ref_spec_8253.git_path
REFERENCE_SPEC_VERSION = ref_spec_8253.version

pytestmark = [
    pytest.mark.valid_at_transition_to("Amsterdam"),
    pytest.mark.pre_alloc_mutable,
]

INITCODE = Initcode(deploy_code=Op.STOP)
INITCODE_WORD = int.from_bytes(bytes(INITCODE).ljust(32, b"\0"), "big")


def deploy_creator(
    pre: Alloc, target: TargetedAccount, value: int = 0
) -> Tuple[Address, Bytecode, Storage, int]:
    """
    Deploy a synthetic factory at the historical creator address and nonce.

    Issue a `CREATE` of `INITCODE` sending `value` and store its result in
    the first slot; record completion in the second slot.

    Return the creator address, its code, its expected storage after a
    collision, and the slot that records completion.
    """
    creator = Address(target.creator)
    assert (
        compute_create_address(address=creator, nonce=target.creation_nonce)
        == target.address
    ), "test correctness: creator and nonce do not derive the target"

    creator_storage = Storage()
    result_slot = creator_storage.store_next(0, "create_result")
    executed_slot = creator_storage.store_next(1, "executed")
    creator_code = (
        Op.MSTORE(0, INITCODE_WORD)
        + Op.SSTORE(result_slot, Op.CREATE(value, 0, len(INITCODE)))
        + Op.SSTORE(executed_slot, 1)
        + Op.STOP
    )
    pre.deploy_contract(
        creator_code, address=creator, nonce=target.creation_nonce
    )
    return creator, creator_code, creator_storage, executed_slot


def executed_slot_change(
    executed_slot: int, block_access_index: int
) -> BalStorageSlot:
    """Return the BAL storage change of a creator that ran to completion."""
    return BalStorageSlot(
        slot=executed_slot,
        slot_changes=[
            BalStorageChange(
                block_access_index=block_access_index, post_value=1
            )
        ],
    )


@pytest.mark.parametrize("activation_delay", [0, 7])
def test_nonce_bump_at_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    activation_delay: int,
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
            timestamp=FORK_TIMESTAMP + activation_delay,
            txs=[Transaction(sender=sender, to=receiver, value=1)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations=dict.fromkeys(post, BUMP_EXPECTATION)
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP + activation_delay + 1,
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
    Target each listed address using its historical creator/nonce pair.

    A synthetic factory issues `CREATE` in the first fork-block transaction.
    The bumped nonce causes an EIP-684 collision and preserves the storage.
    The collision reads no target storage, unlike an EIP-7610 storage check.
    """
    address = place_targeted_account(pre, target)
    creator, creator_code, creator_storage, executed_slot = deploy_creator(
        pre, target
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
                            executed_slot_change(executed_slot, 1)
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
            address: bumped_account(target),
            creator: Account(
                nonce=target.creation_nonce + 1,
                code=creator_code,
                storage=creator_storage,
            ),
            receiver: Account(balance=1),
        },
    )


def test_create_collision_after_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Attempt creation through the synthetic factory after the fork block.

    The `CREATE` still collides, and the target appears in that block's BAL
    only as an accessed account: the bump is not replayed.
    """
    target = Spec.TARGETED_ACCOUNTS[0]
    address = place_targeted_account(pre, target)
    creator, creator_code, creator_storage, executed_slot = deploy_creator(
        pre, target
    )
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[Transaction(sender=sender, to=receiver, value=1)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={address: BUMP_EXPECTATION}
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP + 1,
            txs=[Transaction(sender=sender, to=creator)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    address: BalAccountExpectation.empty(),
                    creator: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(
                                block_access_index=1,
                                post_nonce=target.creation_nonce + 1,
                            )
                        ],
                        storage_changes=[
                            executed_slot_change(executed_slot, 1)
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
            address: bumped_account(target),
            creator: Account(
                nonce=target.creation_nonce + 1,
                code=creator_code,
                storage=creator_storage,
            ),
            receiver: Account(balance=1),
        },
    )


@pytest.mark.parametrize(
    "failure",
    ["insufficient_balance", "static_context", "out_of_gas"],
)
def test_create_early_failure_at_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    failure: str,
) -> None:
    """
    A `CREATE` from the original creator that fails before the target
    address is accessed leaves the target with only the bump in the fork
    block BAL. The creator does not increment its nonce.
    """
    amsterdam = fork.transitions_to()
    target = Spec.TARGETED_ACCOUNTS[0]
    address = place_targeted_account(pre, target)
    sender = pre.fund_eoa()

    # The creator has no balance, so a `CREATE` sending value fails its
    # preflight balance check.
    value = 1 if failure == "insufficient_balance" else 0
    creator, creator_code, creator_storage, executed_slot = deploy_creator(
        pre, target, value=value
    )
    # Only the failed balance check lets the creator's code run to its end.
    post = {
        address: bumped_account(target),
        creator: Account(
            nonce=target.creation_nonce,
            code=creator_code,
            storage=creator_storage
            if failure == "insufficient_balance"
            else {},
        ),
    }
    account_expectations = {
        address: BUMP_EXPECTATION,
        creator: BalAccountExpectation.empty(),
    }

    if failure == "insufficient_balance":
        tx = Transaction(sender=sender, to=creator)
        account_expectations[creator] = BalAccountExpectation(
            nonce_changes=[],
            storage_changes=[executed_slot_change(executed_slot, 1)],
        )
    elif failure == "static_context":
        wrapper_storage = Storage()
        wrapper_code = Op.SSTORE(
            wrapper_storage.store_next(0, "staticcall_result"),
            Op.STATICCALL(Op.GAS, creator, 0, 0, 0, 0),
        ) + Op.SSTORE(wrapper_storage.store_next(1, "executed"), 1)
        # Pre-set the result slot so the write of zero is a real change.
        wrapper = pre.deploy_contract(wrapper_code, storage={0: 0xDEAD})
        tx = Transaction(sender=sender, to=wrapper)
        post[wrapper] = Account(storage=wrapper_storage)
    elif failure == "out_of_gas":
        # Enough gas for everything up to the `CREATE`, one short of the
        # opcode's own charge, which comes before the target is accessed.
        before_target_access = Op.MSTORE(
            0, INITCODE_WORD, new_memory_size=32
        ) + Op.CREATE(
            0,
            0,
            len(INITCODE),
            init_code_size=len(INITCODE),
            old_memory_size=32,
            new_memory_size=32,
            account_new=False,
        )
        intrinsic_gas = amsterdam.transaction_intrinsic_cost_calculator()()
        tx = Transaction(
            sender=sender,
            to=creator,
            gas_limit=intrinsic_gas
            + before_target_access.gas_cost(amsterdam)
            - 1,
        )
    else:
        raise ValueError(f"Unhandled failure: {failure}")

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post,
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
    address = place_targeted_account(pre, target)
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
            address: bumped_account(target, BALANCE_BASE + 2 * value),
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
    including ones with the same shape as the targeted accounts, whether
    they are left alone or read during the block. The bump follows the
    fixed list, not the account shape.
    """
    place_targeted_accounts(pre)

    lookalike = pre.fund_eoa(amount=0)
    pre[lookalike] = Account(nonce=0, balance=1, code=b"", storage={0: 1})
    lookalike_read = pre.fund_eoa(amount=0)
    pre[lookalike_read] = Account(nonce=0, balance=1, code=b"", storage={0: 1})
    contract = pre.deploy_contract(Op.STOP, storage={0: 1})
    used_eoa = pre.fund_eoa(nonce=5)
    fresh_eoa = pre.fund_eoa(amount=1)

    reader = pre.deploy_contract(Op.SSTORE(0, Op.BALANCE(lookalike_read)))
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
                txs=[
                    Transaction(sender=sender, to=receiver, value=1),
                    Transaction(sender=sender, to=reader),
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        **dict.fromkeys(untouched),
                        lookalike_read: BalAccountExpectation.empty(),
                    }
                ),
            ),
        ],
        post={
            lookalike: Account(nonce=0, balance=1, code=b"", storage={0: 1}),
            lookalike_read: Account(
                nonce=0, balance=1, code=b"", storage={0: 1}
            ),
            contract: Account(nonce=1, code=Op.STOP, storage={0: 1}),
            used_eoa: Account(nonce=5),
            fresh_eoa: Account(nonce=0, balance=1),
            reader: Account(storage={0: 1}),
            receiver: Account(balance=2),
        },
    )


@pytest.mark.parametrize(
    "present", [False, True], ids=["absent", "empty-storage"]
)
def test_targeted_accounts_without_storage(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    present: bool,
) -> None:
    """
    Bump listed addresses even when their storage is empty or they are absent.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)
    targeted = [Address(target.address) for target in Spec.TARGETED_ACCOUNTS]
    balance = BALANCE_BASE if present else 0
    if present:
        for address in targeted:
            pre.deploy_contract(b"", address=address, nonce=0, balance=balance)

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
                address: Account(
                    nonce=1, balance=balance, code=b"", storage={}
                )
                for address in targeted
            },
            receiver: Account(balance=2),
        },
    )
