"""
Test Withdrawal system-level operation
"""

from typing import List

from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTest,
    TestAddress,
    Transaction,
    Withdrawal,
    Yul,
    test_from,
    to_address,
    to_hash,
)

WITHDRAWALS_FORK = "shanghai"

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
def test_withdrawals_use_value_in_tx(_):
    """
    Test sending a transaction from an address yet to receive a withdrawal
    """
    pre = {}

    tx = Transaction(
        # Transaction sent from the `TestAddress`, which has 0 balance at start
        nonce=0,
        gas_price=10,
        gas_limit=21000,
        to=to_address(0x100),
        data="0x",
    )

    withdrawal = Withdrawal(
        index=0,
        validator=0,
        address=TestAddress,
        amount=tx.gas_price * tx.gas_limit + 1,
    )

    blocks = [
        Block(
            txs=[tx.with_error("intrinsic gas too low: have 0, want 21000")],
            withdrawals=[
                withdrawal,
            ],
            exception="Transaction without funds",
        ),
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
        TestAddress: Account(balance=1),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_use_value_in_contract(_):
    """
    Test sending value from contract that has not received a withdrawal
    """
    SEND_ONE_WEI = Yul(
        """
        {
            let ret := call(gas(), 0x200, 1, 0, 0, 0, 0)
            sstore(number(), ret)
        }
        """
    )
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(balance=0, code=SEND_ONE_WEI),
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
            balance=1,
        ),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_balance_within_block(_):
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
            balance=1,
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
                    amount=10**9,
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
                1: 1,
                2: 10**9 + 1,
            }
        )
    }

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_multiple_withdrawals_same_address(_):
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
                    amount=10**9,
                )
                for i in range(len(ADDRESSES) * 16)
            ],
        ),
    ]

    post = {}

    for addr in ADDRESSES:
        post[addr] = Account(
            balance=16 * 10**9,
            storage={},
        )

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)

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
                    amount=10**9,
                )
                for j in range(16)
            ],
        )
        for i in range(len(ADDRESSES))
    ]

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_many_withdrawals(_):
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
        amount = i * 10**9
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
            balance=amount,
            storage={},
        )

    blocks = [
        Block(
            withdrawals=withdrawals,
        ),
    ]

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_self_destructing_account(_):
    """
    Test Withdrawals can be done to the same address multiple times in
    the same block.
    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(
            code=SELFDESTRUCT,
            balance=100,
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
        amount=99,
    )

    block = Block(
        txs=[tx_1],
        withdrawals=[withdrawal],
    )

    post = {
        to_address(0x100): Account(
            code=None,
            balance=99,
        ),
        to_address(0x200): Account(
            code=None,
            balance=100,
        ),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=[block])


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_newly_created_contract(_):
    """
    Test Withdrawals where one of the withdrawal has a zero amount.
    """
    created_contract = "0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"

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
            balance=1,
        ),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=[block])

    # Same test but include value in the contract creating transaction

    tx.value = 1
    post[created_contract].balance = 2

    yield BlockchainTest(pre=pre, post=post, blocks=[block])


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_no_evm_execution(_):
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
                    amount=10**9,
                ),
                Withdrawal(
                    index=1,
                    validator=1,
                    address=to_address(0x200),
                    amount=10**9,
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
                    amount=10**9,
                ),
                Withdrawal(
                    index=1,
                    validator=1,
                    address=to_address(0x400),
                    amount=10**9,
                ),
            ],
        ),
    ]

    post = {
        to_address(0x100): Account(
            storage={
                2: 1,
            }
        ),
        to_address(0x200): Account(
            storage={
                2: 1,
            }
        ),
        to_address(0x300): Account(
            storage={
                1: 1,
            }
        ),
        to_address(0x400): Account(
            storage={
                1: 1,
            }
        ),
    }

    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_zero_amount(_):
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
    post[to_address(0x200)].balance = 1
    yield BlockchainTest(pre=pre, post=post, blocks=[block])

    # Same test but reverse order of withdrawals.
    block.withdrawals.reverse()
    set_withdrawal_index(block.withdrawals)

    yield BlockchainTest(pre=pre, post=post, blocks=[block])


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_overflowing_balance(_):
    """
    Test Withdrawals that overflows an account.
    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        to_address(0x100): Account(
            balance=(2**256 - 1),
        ),
    }
    blocks = [
        Block(
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator=0,
                    address=to_address(0x100),
                    amount=1,
                )
            ],
            exception="invalid withdrawal",
        )
    ]
    post = {
        to_address(0x100): Account(
            balance=(2**256 - 1),
        ),
    }
    yield BlockchainTest(pre=pre, post=post, blocks=blocks)


@test_from(WITHDRAWALS_FORK)
def test_withdrawals_invalid_skip_indexes(_):
    """
    Test Withdrawal blocks starting from the incorrect index (!=0)
    or by skipping an index between blocks
    """
    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=0,
        ),
        to_address(0x100A): Account(
            code=SET_STORAGE,
        ),
        to_address(0x100B): Account(
            code=SET_STORAGE,
        ),
        to_address(0x200A): Account(
            code=SET_STORAGE,
        ),
        to_address(0x200B): Account(
            code=SET_STORAGE,
        ),
    }

    block_1_invalid = Block(
        # Skip start index
        txs=[
            Transaction(
                nonce=0,
                gas_limit=100000,
                to=to_address(0x100A),
            )
        ],
        withdrawals=[
            Withdrawal(
                index=1,
                validator=0,
                address=to_address(0x100A),
                amount=10**9,
            )
        ],
        exception="invalid withdrawal index",
    )
    block_1_valid = Block(
        # Correct start index
        txs=[
            Transaction(
                nonce=0,
                gas_limit=100000,
                to=to_address(0x100B),
            )
        ],
        withdrawals=[
            Withdrawal(
                index=0,
                validator=0,
                address=to_address(0x100B),
                amount=10**9,
            )
        ],
    )

    block_2_invalid = Block(
        # Skip withdrawal index
        txs=[
            Transaction(
                nonce=1,
                gas_limit=100000,
                to=to_address(0x200A),
            )
        ],
        withdrawals=[
            Withdrawal(
                index=2,
                validator=0,
                address=to_address(0x200A),
                amount=10**9,
            )
        ],
        exception="invalid withdrawal index",
    )
    block_2_valid = Block(
        # Correct sequential withdrawal index
        txs=[
            Transaction(
                nonce=1,
                gas_limit=100000,
                to=to_address(0x200B),
            )
        ],
        withdrawals=[
            Withdrawal(
                index=1,
                validator=0,
                address=to_address(0x200B),
                amount=10**9,
            )
        ],
    )

    post = {
        to_address(0x100A): Account(
            balance=None,
            storage=None,
        ),
        to_address(0x100B): Account(
            balance=10**9,
            storage={
                0x1: 0x1,
            },
        ),
        to_address(0x200A): Account(
            balance=None,
            storage=None,
        ),
        to_address(0x200B): Account(
            balance=10**9,
            storage={
                0x2: 0x1,
            },
        ),
    }

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=[block_1_invalid, block_1_valid, block_2_valid],
    )

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=[
            block_1_valid,
            block_2_invalid,
            block_2_valid,
        ],
    )


# @test_from(WITHDRAWALS_FORK)
# def test_withdrawals_inner_skip_index(_):
#     # TODO: This is not possible yet I think
#     pass
