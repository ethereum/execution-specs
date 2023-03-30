"""
Test Withdrawal system-level operation
"""

from typing import List

from ethereum_test_forks import Shanghai
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTest,
    TestAddress,
    Transaction,
    Withdrawal,
    Yul,
    compute_create_address,
    test_from,
    to_address,
    to_hash,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4895.md"
REFERENCE_SPEC_VERSION = "0966bbc3ff92127c0a729ce5455bbc35fd2075b8"

WITHDRAWALS_FORK = Shanghai

ONE_GWEI = 10**9

# Common contracts across withdrawals tests
SET_STORAGE = Yul(
    """
    {
        sstore(number(), 1)
    }
    """
)
"""
Contract that simply sets a storage value unconditionally on call
"""

SELFDESTRUCT = Yul(
    """
    {
        let addr := calldataload(0)
        selfdestruct(addr)
    }
    """
)
"""
Contract that selfdestructs and sends all funds to specified
account.
"""


def set_withdrawal_index(
    withdrawals: List[Withdrawal], start_index: int = 0
) -> None:
    """
    Automatically set the index of each withdrawal in a list in sequential
    order.
    """
    for i, w in enumerate(withdrawals):
        w.index = start_index + i


@test_from(WITHDRAWALS_FORK)
def test_use_value_in_tx(_):
    """
    Test sending a transaction from an address yet to receive a withdrawal
    """
    pre = {TestAddress: Account(balance=0)}

    tx = Transaction(
        # Transaction sent from the `TestAddress`, which has 0 balance at start
        nonce=0,
        gas_price=ONE_GWEI,
        gas_limit=21000,
        to=to_address(0x100),
        data="0x",
    )

    withdrawal = Withdrawal(
        index=0,
        validator=0,
        address=TestAddress,
        amount=tx.gas_limit + 1,
    )

    blocks = [
        Block(
            txs=[tx.with_error("intrinsic gas too low: have 0, want 21000")],
            withdrawals=[
                withdrawal,
            ],
            exception="Transaction without funds",
        )
    ]

    yield BlockchainTest(
        pre=pre,
        post={},
        blocks=blocks,
    )

    blocks = [
        Block(
            txs=[],
            withdrawals=[
                withdrawal,
            ],
        ),
        Block(
            txs=[tx],
            withdrawals=[],
        ),
    ]
    post = {
        TestAddress: Account(balance=ONE_GWEI),
    }

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
    )


@test_from(WITHDRAWALS_FORK)
def test_use_value_in_contract(_):
    """
    Test sending value from contract that has not received a withdrawal
    """
    SEND_ONE_GWEI = Yul(
        """
        {
            let ret := call(gas(), 0x200, 1000000000, 0, 0, 0, 0)
            sstore(number(), ret)
        }
        """
    )
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(balance=0, code=SEND_ONE_GWEI),
        to_address(0x200): Account(balance=0),
    }
    tx = Transaction(
        # Transaction sent from the `TestAddress`, which has 0 balance at start
        nonce=0,
        value=0,
        gas_price=10,
        gas_limit=100000,
        to=to_address(0x100),
        data="0x",
    )
    withdrawal = Withdrawal(
        index=0,
        validator=0,
        address=to_address(0x100),
        amount=1,
    )

    blocks = [
        Block(
            txs=[tx.with_nonce(0)],
            withdrawals=[withdrawal],
        ),
        Block(
            txs=[tx.with_nonce(1)],  # Same tx again, just increase nonce
        ),
    ]
    post = {
        to_address(0x100): Account(
            storage={
                0x1: 0x0,  # Call fails on the first attempt
                0x2: 0x1,  # Succeeds on the second attempt
            }
        ),
        to_address(0x200): Account(
            balance=ONE_GWEI,
        ),
    }

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
    )


@test_from(WITHDRAWALS_FORK)
def test_balance_within_block(_):
    """
    Test Withdrawal balance increase within the same block,
    inside contract call.
    """
    SAVE_BALANCE_ON_BLOCK_NUMBER = Yul(
        """
        {
            let addr := calldataload(0)
            sstore(number(), balance(addr))
        }
        """
    )
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(
            code=SAVE_BALANCE_ON_BLOCK_NUMBER,
        ),
        to_address(0x200): Account(
            balance=ONE_GWEI,
        ),
    }
    blocks = [
        Block(
            txs=[
                Transaction(
                    nonce=0,
                    gas_limit=100000,
                    to=to_address(0x100),
                    data=to_hash(0x200),
                )
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator=0,
                    address=to_address(0x200),
                    amount=1,
                )
            ],
        ),
        Block(
            txs=[
                Transaction(
                    nonce=1,
                    gas_limit=100000,
                    to=to_address(0x100),
                    data=to_hash(0x200),
                )
            ]
        ),
    ]

    post = {
        to_address(0x100): Account(
            storage={
                1: ONE_GWEI,
                2: 2 * ONE_GWEI,
            }
        )
    }

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
    )


@test_from(WITHDRAWALS_FORK)
def test_multiple_withdrawals_same_address(_):
    """
    Test Withdrawals can be done to the same address multiple times in
    the same block.
    """
    ADDRESSES = [
        to_address(0x0),  # Zero address
        to_address(0x1),  # Pre-compiles
        to_address(0x2),
        to_address(0x3),
        to_address(0x4),
        to_address(0x5),
        to_address(0x6),
        to_address(0x7),
        to_address(0x8),
        to_address(0x9),
        to_address(2**160 - 1),
    ]

    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
    }

    for addr in ADDRESSES:
        pre[addr] = Account(
            code=SET_STORAGE,
        )

    # Many repeating withdrawals of the same accounts in the same block.
    blocks = [
        Block(
            withdrawals=[
                Withdrawal(
                    index=i,
                    validator=0,
                    address=ADDRESSES[i % len(ADDRESSES)],
                    amount=1,
                )
                for i in range(len(ADDRESSES) * 16)
            ],
        ),
    ]

    post = {}

    for addr in ADDRESSES:
        post[addr] = Account(
            balance=16 * ONE_GWEI,
            storage={},
        )

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
    )

    # Similar test but now use multiple blocks each with multiple withdrawals
    # to the same withdrawal address.
    # Expected post is exactly the same.
    blocks = [
        Block(
            withdrawals=[
                Withdrawal(
                    index=i * 16 + j,
                    validator=i,
                    address=ADDRESSES[i],
                    amount=1,
                )
                for j in range(16)
            ],
        )
        for i in range(len(ADDRESSES))
    ]

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
        tag="multiple_blocks",
    )


@test_from(WITHDRAWALS_FORK)
def test_many_withdrawals(_):
    """
    Test Withdrawals with a count of N withdrawals in a single block where
    N is a high number not expected to be seen in mainnet.
    """
    N = 400
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
    }
    withdrawals = []
    post = {}
    for i in range(N):
        addr = to_address(0x100 * i)
        amount = i * 1
        pre[addr] = Account(
            code=SET_STORAGE,
        )
        withdrawals.append(
            Withdrawal(
                index=i,
                validator=i,
                address=addr,
                amount=amount,
            )
        )
        post[addr] = Account(
            code=SET_STORAGE,
            balance=amount * ONE_GWEI,
            storage={},
        )

    blocks = [
        Block(
            withdrawals=withdrawals,
        ),
    ]

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_self_destructing_account(_):
    """
    Test Withdrawals can be done to self-destructed accounts.
    Account `0x100` self-destructs and sends all its balance to `0x200`.
    Then, a withdrawal is received at `0x100` with 99 wei.
    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(
            code=SELFDESTRUCT,
            balance=(100 * ONE_GWEI),
        ),
        to_address(0x200): Account(
            balance=0,
        ),
    }

    tx_1 = Transaction(
        # Transaction sent from the `TestAddress`, that calls a
        # self-destructing contract.
        nonce=0,
        gas_price=10,
        gas_limit=100000,
        to=to_address(0x100),
        data=to_hash(0x200),
    )

    withdrawal = Withdrawal(
        index=0,
        validator=0,
        address=to_address(0x100),
        amount=(99),
    )

    block = Block(
        txs=[tx_1],
        withdrawals=[withdrawal],
    )

    post = {
        to_address(0x100): Account(
            code=None,
            balance=(99 * ONE_GWEI),
        ),
        to_address(0x200): Account(
            code=None,
            balance=(100 * ONE_GWEI),
        ),
    }

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=[block],
    )


@test_from(WITHDRAWALS_FORK)
def test_newly_created_contract(_):
    """
    Test Withdrawing to a newly created contract.
    """
    created_contract = compute_create_address(TestAddress, 0)

    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
    }

    initcode = Yul(
        """
        {
            return(0, 1)
        }
        """
    )

    tx = Transaction(
        # Transaction sent from the `TestAddress`, that creates a
        # new contract.
        nonce=0,
        gas_price=10,
        gas_limit=1000000,
        to=None,
        data=initcode,
    )

    withdrawal = Withdrawal(
        index=0,
        validator=0,
        address=created_contract,
        amount=1,
    )

    block = Block(
        txs=[tx],
        withdrawals=[withdrawal],
    )

    post = {
        created_contract: Account(
            code="0x00",
            balance=ONE_GWEI,
        ),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=[block])

    # Same test but include value in the contract creating transaction

    tx.value = ONE_GWEI
    post[created_contract].balance = 2 * ONE_GWEI

    yield BlockchainTest(
        pre=pre, post=post, blocks=[block], tag="with_tx_value"
    )


@test_from(WITHDRAWALS_FORK)
def test_no_evm_execution(_):
    """
    Test Withdrawals don't trigger EVM execution.
    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(
            code=SET_STORAGE,
        ),
        to_address(0x200): Account(
            code=SET_STORAGE,
        ),
        to_address(0x300): Account(
            code=SET_STORAGE,
        ),
        to_address(0x400): Account(
            code=SET_STORAGE,
        ),
    }
    blocks = [
        Block(
            txs=[
                Transaction(
                    nonce=0,
                    gas_limit=100000,
                    to=to_address(0x300),
                ),
                Transaction(
                    nonce=1,
                    gas_limit=100000,
                    to=to_address(0x400),
                ),
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator=0,
                    address=to_address(0x100),
                    amount=1,
                ),
                Withdrawal(
                    index=1,
                    validator=1,
                    address=to_address(0x200),
                    amount=1,
                ),
            ],
        ),
        Block(
            txs=[
                Transaction(
                    nonce=2,
                    gas_limit=100000,
                    to=to_address(0x100),
                ),
                Transaction(
                    nonce=3,
                    gas_limit=100000,
                    to=to_address(0x200),
                ),
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator=0,
                    address=to_address(0x300),
                    amount=1,
                ),
                Withdrawal(
                    index=1,
                    validator=1,
                    address=to_address(0x400),
                    amount=1,
                ),
            ],
        ),
    ]

    post = {
        to_address(0x100): Account(storage={2: 1}),
        to_address(0x200): Account(storage={2: 1}),
        to_address(0x300): Account(storage={1: 1}),
        to_address(0x400): Account(storage={1: 1}),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_zero_amount(_):
    """
    Test Withdrawals where one of the withdrawal has a zero amount.
    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(
            code="0x00",
            balance=0,
        ),
        to_address(0x200): Account(
            code="0x00",
            balance=0,
        ),
        to_address(0x300): Account(
            code="0x00",
            balance=0,
        ),
    }

    withdrawal_1 = Withdrawal(
        index=0,
        validator=0,
        address=to_address(0x100),
        amount=0,
    )

    block = Block(
        withdrawals=[withdrawal_1],
    )

    post = {
        to_address(0x100): Account(
            code="0x00",
            balance=0,
        ),
        to_address(0x200): Account(
            code="0x00",
            balance=0,
        ),
        to_address(0x300): Account(
            code="0x00",
            balance=0,
        ),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=[block])

    # Same test but add another withdrawal with positive amount in same
    # block.
    withdrawal_2 = Withdrawal(
        index=1,
        validator=0,
        address=to_address(0x200),
        amount=1,
    )
    block.withdrawals.append(withdrawal_2)
    post[to_address(0x200)].balance = ONE_GWEI
    yield BlockchainTest(
        pre=pre, post=post, blocks=[block], tag="with_extra_positive_amount"
    )

    # Same test but add another withdrawal with max amount in same
    # block.
    withdrawal_3 = Withdrawal(
        index=2,
        validator=0,
        address=to_address(0x300),
        amount=2**64 - 1,
    )
    block.withdrawals.append(withdrawal_3)
    post[to_address(0x300)].balance = (2**64 - 1) * ONE_GWEI

    yield BlockchainTest(
        pre=pre, post=post, blocks=[block], tag="with_extra_max_amount"
    )

    # Same test but reverse order of withdrawals.
    block.withdrawals.reverse()
    set_withdrawal_index(block.withdrawals)

    yield BlockchainTest(
        pre=pre, post=post, blocks=[block], tag="reverse_withdrawal_order"
    )


@test_from(WITHDRAWALS_FORK)
def test_large_amount(_):
    """
    Test Withdrawals that have a large gwei amount, so that (gwei * 1e9)
    could overflow uint64 but not uint256.
    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
    }

    withdrawals: List[Withdrawal] = []
    amounts: List[int] = [
        (2**35),
        (2**64) - 1,
        (2**63) + 1,
        (2**63),
        (2**63) - 1,
    ]

    post = {}

    for i, amount in enumerate(amounts):
        addr = to_address(0x100 * (i + 1))
        withdrawals.append(
            Withdrawal(
                index=i,
                validator=i,
                address=addr,
                amount=amount,
            )
        )
        post[addr] = Account(balance=(amount * ONE_GWEI))

    blocks = [
        Block(
            withdrawals=withdrawals,
        )
    ]
    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
    )
