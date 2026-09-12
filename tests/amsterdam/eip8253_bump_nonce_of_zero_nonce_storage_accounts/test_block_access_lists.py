"""
Block access list tests for the fork block of
[EIP-8253: Bump nonce of zero-nonce storage accounts](https://eips.ethereum.org/EIPS/eip-8253).

The nonce change of a targeted account sits at block access index zero. The
tests check how it merges with what transactions, withdrawals, and the fee
recipient do to the same account in the fork block, and what the block
after the fork block records.
"""

from typing import Callable, Dict, List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Environment,
    Hash,
    Header,
    Op,
    RecipientType,
    Transaction,
    TransitionFork,
    Withdrawal,
)

from .helpers import (
    BALANCE_BASE,
    BUMP_EXPECTATION,
    FORK_TIMESTAMP,
    bump_expectation,
    bumped_account,
    place_targeted_account,
)
from .spec import Spec, ref_spec_8253

REFERENCE_SPEC_GIT_PATH = ref_spec_8253.git_path
REFERENCE_SPEC_VERSION = ref_spec_8253.version

pytestmark = [
    pytest.mark.valid_at_transition_to("Amsterdam"),
    pytest.mark.pre_alloc_mutable,
]

TARGET = Spec.TARGETED_ACCOUNTS[0]
GWEI = 10**9
GENESIS_BASE_FEE = 7


def fork_block_base_fee(fork: TransitionFork, genesis: Environment) -> int:
    """Return the base fee of a fork block that directly follows genesis."""
    return fork.transitions_to().base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis.gas_limit,
    )


def slot_written(slot: int, value: int) -> BalStorageSlot:
    """Return a single storage write by the first transaction."""
    return BalStorageSlot(
        slot=slot,
        slot_changes=[
            BalStorageChange(block_access_index=1, post_value=value)
        ],
    )


@pytest.mark.parametrize(
    "access",
    [
        pytest.param(lambda a: Op.BALANCE(a), id="balance"),
        pytest.param(lambda a: Op.EXTCODEHASH(a), id="extcodehash"),
        pytest.param(lambda a: Op.EXTCODESIZE(a), id="extcodesize"),
        pytest.param(lambda a: Op.CALL(Op.GAS, a, 0, 0, 0, 0, 0), id="call"),
        pytest.param(
            lambda a: Op.STATICCALL(Op.GAS, a, 0, 0, 0, 0), id="staticcall"
        ),
        pytest.param(
            lambda a: Op.DELEGATECALL(Op.GAS, a, 0, 0, 0, 0),
            id="delegatecall",
        ),
    ],
)
def test_bal_bump_and_read_only_access(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    access: Callable[[Address], Bytecode],
) -> None:
    """
    Reading a targeted account in the fork block adds nothing to its BAL
    entry: the account appears once, with only the nonce change.
    """
    address = place_targeted_account(pre, TARGET)
    reader = pre.deploy_contract(Op.POP(access(address)) + Op.SSTORE(0, 1))
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=reader)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: BUMP_EXPECTATION,
                        reader: BalAccountExpectation(
                            storage_changes=[slot_written(0, 1)]
                        ),
                    }
                ),
            )
        ],
        post={
            address: bumped_account(TARGET),
            reader: Account(storage={0: 1}),
        },
    )


@pytest.mark.parametrize("value", [0, 5], ids=["zero_value", "with_value"])
def test_bal_bump_and_transaction_to_targeted_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    value: int,
) -> None:
    """
    A transaction to a targeted account in the fork block adds a balance
    change at the transaction's index only if it carries value.
    """
    address = place_targeted_account(pre, TARGET)
    sender = pre.fund_eoa()
    balance = BALANCE_BASE + value
    balance_changes = (
        [BalBalanceChange(block_access_index=1, post_balance=balance)]
        if value
        else []
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=address, value=value)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: bump_expectation(balance_changes)
                    }
                ),
            )
        ],
        post={address: bumped_account(TARGET, balance)},
    )


@pytest.mark.parametrize("transfer", ["call", "selfdestruct"])
def test_bal_bump_and_reverted_transfer(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    transfer: str,
) -> None:
    """
    A value transfer to a targeted account inside a frame that reverts
    leaves no balance change, while the nonce change from before the
    transaction survives the revert.
    """
    address = place_targeted_account(pre, TARGET)
    sender = pre.fund_eoa()
    value = 5
    post: Dict[Address, Account] = {address: bumped_account(TARGET)}
    account_expectations: Dict[Address, BalAccountExpectation] = {
        address: BUMP_EXPECTATION
    }

    if transfer == "call":
        reverter = pre.deploy_contract(
            Op.POP(Op.CALL(Op.GAS, address, value, 0, 0, 0, 0))
            + Op.REVERT(0, 0),
            balance=value,
        )
        post[reverter] = Account(balance=value)
    elif transfer == "selfdestruct":
        victim_code = Op.SELFDESTRUCT(address)
        victim = pre.deploy_contract(victim_code, balance=value)
        reverter = pre.deploy_contract(
            Op.POP(Op.CALL(Op.GAS, victim, 0, 0, 0, 0, 0)) + Op.REVERT(0, 0)
        )
        post[victim] = Account(balance=value, code=victim_code)
        account_expectations[victim] = BalAccountExpectation.empty()
    else:
        raise ValueError(f"Unhandled transfer: {transfer}")
    account_expectations[reverter] = BalAccountExpectation.empty()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=reverter)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post,
    )


def test_bal_bump_and_oog_before_target_access(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    A `CALL` that runs out of gas before it reaches the targeted account
    records nothing for it, yet the account is present in the fork block
    BAL because of the bump.
    """
    amsterdam = fork.transitions_to()
    address = place_targeted_account(pre, TARGET)
    sender = pre.fund_eoa()

    call = Op.CALL(
        gas=0,
        address=address,
        value=0,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
        address_warm=False,
        value_transfer=False,
        account_new=False,
    )
    caller = pre.deploy_contract(call)
    intrinsic_gas = amsterdam.transaction_intrinsic_cost_calculator()()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[
                    Transaction(
                        sender=sender,
                        to=caller,
                        gas_limit=intrinsic_gas + call.gas_cost(amsterdam) - 1,
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: BUMP_EXPECTATION,
                        caller: BalAccountExpectation.empty(),
                    }
                ),
            )
        ],
        post={address: bumped_account(TARGET), caller: Account(code=call)},
    )


def test_bal_bump_and_access_list_entry(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Listing a targeted account and its storage slots in a transaction's
    EIP-2930 access list without touching them adds nothing to its BAL
    entry: the account is present because of the bump alone.
    """
    address = place_targeted_account(pre, TARGET)
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        ty=1,
        sender=sender,
        to=receiver,
        value=1,
        access_list=[
            AccessList(
                address=address,
                storage_keys=[Hash(key) for key in TARGET.storage_keys],
            )
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={address: BUMP_EXPECTATION}
                ),
            )
        ],
        post={address: bumped_account(TARGET), receiver: Account(balance=1)},
    )


@pytest.mark.parametrize(
    "victim_balance", [0, 100], ids=["zero_balance", "with_balance"]
)
def test_bal_bump_and_selfdestruct_beneficiary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    victim_balance: int,
) -> None:
    """
    A `SELFDESTRUCT` naming a targeted account as beneficiary adds a
    balance change only if it moves a non-zero balance.
    """
    address = place_targeted_account(pre, TARGET)
    sender = pre.fund_eoa()
    victim_code = Op.SELFDESTRUCT(address)
    victim = pre.deploy_contract(victim_code, balance=victim_balance)
    balance = BALANCE_BASE + victim_balance

    if victim_balance:
        target_expectation = bump_expectation(
            [BalBalanceChange(block_access_index=1, post_balance=balance)]
        )
        victim_expectation = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=0)
            ]
        )
    else:
        target_expectation = BUMP_EXPECTATION
        victim_expectation = BalAccountExpectation.empty()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=victim)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: target_expectation,
                        victim: victim_expectation,
                    }
                ),
            )
        ],
        post={
            address: bumped_account(TARGET, balance),
            # Not created in this transaction, so it survives.
            victim: Account(balance=0, code=victim_code),
        },
    )


@pytest.mark.parametrize(
    "scenario", ["empty_block", "zero_tip", "positive_tip"]
)
def test_bal_bump_of_fee_recipient(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    scenario: str,
) -> None:
    """
    A targeted account that is the fee recipient of the fork block is
    present in the BAL even when it earns nothing, which an untouched fee
    recipient otherwise is not; fees add a balance change at the
    transaction's index.
    """
    amsterdam = fork.transitions_to()
    address = place_targeted_account(pre, TARGET)
    genesis = Environment(base_fee_per_gas=GENESIS_BASE_FEE)
    base_fee = fork_block_base_fee(fork, genesis)

    txs: List[Transaction] = []
    balance = BALANCE_BASE
    if scenario != "empty_block":
        priority_fee = 1 if scenario == "positive_tip" else 0
        sender = pre.fund_eoa()
        receiver = pre.fund_eoa(amount=1)
        # No execution and no state growth, so the gas used is exactly the
        # intrinsic cost.
        gas_used = amsterdam.transaction_intrinsic_cost_calculator()()
        txs = [
            Transaction(
                sender=sender,
                to=receiver,
                gas_limit=gas_used,
                gas_price=base_fee + priority_fee,
            )
        ]
        balance += priority_fee * gas_used
    balance_changes = (
        [BalBalanceChange(block_access_index=1, post_balance=balance)]
        if balance != BALANCE_BASE
        else []
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=txs,
                fee_recipient=address,
                header_verify=Header(base_fee_per_gas=base_fee),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: bump_expectation(balance_changes)
                    }
                ),
            )
        ],
        post={address: bumped_account(TARGET, balance)},
        genesis_environment=genesis,
    )


def test_bal_bump_of_recipient_and_fee_recipient_in_one_transaction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    A targeted account that receives a transaction's value and its priority
    fee gets one balance change at that index holding the combined result,
    next to the nonce change at index zero.
    """
    amsterdam = fork.transitions_to()
    address = place_targeted_account(pre, TARGET)
    genesis = Environment(base_fee_per_gas=GENESIS_BASE_FEE)
    base_fee = fork_block_base_fee(fork, genesis)
    sender = pre.fund_eoa()
    value = 5
    priority_fee = 1

    gas_used = amsterdam.transaction_intrinsic_cost_calculator()(
        sends_value=True, recipient_type=RecipientType.EOA
    )
    tx = Transaction(
        sender=sender,
        to=address,
        value=value,
        gas_limit=gas_used,
        gas_price=base_fee + priority_fee,
    )
    balance = BALANCE_BASE + value + priority_fee * gas_used

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[tx],
                fee_recipient=address,
                header_verify=Header(base_fee_per_gas=base_fee),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: bump_expectation(
                            [
                                BalBalanceChange(
                                    block_access_index=1, post_balance=balance
                                )
                            ]
                        )
                    }
                ),
            )
        ],
        post={address: bumped_account(TARGET, balance)},
        genesis_environment=genesis,
    )


@pytest.mark.parametrize(
    "scenario", ["single", "zero_amount", "multiple", "after_transfer"]
)
def test_bal_bump_and_withdrawals(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """
    Withdrawals to a targeted account in the fork block add one balance
    change at the post-transaction index, holding the sum of all
    withdrawals, unless they move nothing.
    """
    address = place_targeted_account(pre, TARGET)
    txs: List[Transaction] = []
    balance_changes: List[BalBalanceChange] = []
    balance = BALANCE_BASE

    if scenario == "single":
        amounts = [10]
    elif scenario == "zero_amount":
        amounts = [0]
    elif scenario == "multiple":
        amounts = [5, 10, 15]
    elif scenario == "after_transfer":
        amounts = [10]
        sender = pre.fund_eoa()
        txs = [Transaction(sender=sender, to=address, value=5)]
        balance += 5
        balance_changes.append(
            BalBalanceChange(block_access_index=1, post_balance=balance)
        )
    else:
        raise ValueError(f"Unhandled scenario: {scenario}")

    withdrawn = sum(amounts) * GWEI
    if withdrawn:
        balance += withdrawn
        balance_changes.append(
            BalBalanceChange(
                block_access_index=len(txs) + 1, post_balance=balance
            )
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=txs,
                withdrawals=[
                    Withdrawal(
                        index=i, validator_index=i, address=address, amount=a
                    )
                    for i, a in enumerate(amounts)
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: bump_expectation(balance_changes)
                    }
                ),
            )
        ],
        post={address: bumped_account(TARGET, balance)},
    )


@pytest.mark.parametrize(
    "recipient_is_targeted",
    [
        pytest.param(True, id="targeted_recipient"),
        pytest.param(
            False, marks=pytest.mark.exception_test, id="other_recipient"
        ),
    ],
)
def test_bal_bump_size_limit_counts_targeted_address_once(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    recipient_is_targeted: bool,
) -> None:
    """
    With the block gas limit at the exact BAL budget of an empty fork
    block, a withdrawal to a targeted account fits because its address is
    already counted for the bump, while a withdrawal to any other account
    adds an item and exceeds the budget.
    """
    amsterdam = fork.transitions_to()
    address = place_targeted_account(pre, TARGET)
    min_gas_limit = (
        amsterdam.minimum_block_gas_limit()
        + len(amsterdam.zero_nonce_storage_accounts())
        * amsterdam.gas_costs().BLOCK_ACCESS_LIST_ITEM
    )
    amount = 10

    if recipient_is_targeted:
        recipient = address
        exception = None
        post = {address: bumped_account(TARGET, BALANCE_BASE + amount * GWEI)}
    else:
        recipient = pre.fund_eoa(amount=0)
        exception = BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED
        post = {}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[],
                withdrawals=[
                    Withdrawal(
                        index=0,
                        validator_index=0,
                        address=recipient,
                        amount=amount,
                    )
                ],
                exception=exception,
            )
        ],
        post=post,
        genesis_environment=Environment(gas_limit=min_gas_limit),
    )


def test_bal_access_to_bumped_account_after_fork_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    In the block after the fork block a targeted account that is only read
    appears as an accessed account with no changes: the nonce change is
    not repeated.
    """
    address = place_targeted_account(pre, TARGET)
    reader = pre.deploy_contract(Op.SSTORE(Op.NUMBER, Op.BALANCE(address)))
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=reader)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={address: BUMP_EXPECTATION}
                ),
            ),
            Block(
                timestamp=FORK_TIMESTAMP + 1,
                txs=[Transaction(sender=sender, to=reader)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        address: BalAccountExpectation.empty()
                    }
                ),
            ),
        ],
        post={
            address: bumped_account(TARGET),
            reader: Account(storage={1: BALANCE_BASE, 2: BALANCE_BASE}),
        },
    )
