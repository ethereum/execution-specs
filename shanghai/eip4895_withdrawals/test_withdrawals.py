"""
abstract: Tests [EIP-4895: Beacon chain withdrawals](https://eips.ethereum.org/EIPS/eip-4895)
    Test cases for [EIP-4895: Beacon chain push withdrawals as
    operations](https://eips.ethereum.org/EIPS/eip-4895).
"""

from enum import Enum, unique
from typing import Dict, List, Mapping

import pytest

from ethereum_test_forks import Cancun, Fork
from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    Hash,
    TestAddress,
    Transaction,
    TransactionException,
    Withdrawal,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from evm_transition_tool import TransitionTool

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4895.md"
REFERENCE_SPEC_VERSION = "81af3b60b632bc9c03513d1d137f25410e3f4d34"

pytestmark = pytest.mark.valid_from("Shanghai")

ONE_GWEI = 10**9


@pytest.mark.parametrize(
    "test_case",
    ["tx_in_withdrawals_block", "tx_after_withdrawals_block"],
    ids=lambda x: x,
)
class TestUseValueInTx:
    """
    Test that the value from a withdrawal can be used in a transaction:

    1. `tx_in_withdrawals_block`: Test that the withdrawal value can not be used by a transaction
        in the same block as the withdrawal.

    2. `tx_after_withdrawals_block`: Test that the withdrawal value can be used by a transaction
        in the subsequent block.
    """

    @pytest.fixture
    def tx(self):  # noqa: D102
        # Transaction sent from the `TestAddress`, which has 0 balance at start
        return Transaction(
            nonce=0,
            gas_price=ONE_GWEI,
            gas_limit=21000,
            to=Address(0x100),
            data="0x",
        )

    @pytest.fixture
    def withdrawal(self, tx: Transaction):  # noqa: D102
        return Withdrawal(
            index=0,
            validator_index=0,
            address=TestAddress,
            amount=tx.gas_limit + 1,
        )

    @pytest.fixture
    def blocks(self, tx: Transaction, withdrawal: Withdrawal, test_case):  # noqa: D102
        if test_case == "tx_in_withdrawals_block":
            return [
                Block(
                    txs=[tx.with_error(TransactionException.INSUFFICIENT_ACCOUNT_FUNDS)],
                    withdrawals=[
                        withdrawal,
                    ],
                    exception=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                )
            ]
        if test_case == "tx_after_withdrawals_block":
            return [
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
        raise Exception("Invalid test case.")

    @pytest.fixture
    def post(self, test_case: str) -> Dict:  # noqa: D102
        if test_case == "tx_in_withdrawals_block":
            return {}
        if test_case == "tx_after_withdrawals_block":
            return {TestAddress: Account(balance=ONE_GWEI + 1)}
        raise Exception("Invalid test case.")

    def test_use_value_in_tx(
        self,
        blockchain_test: BlockchainTestFiller,
        post: dict,
        blocks: List[Block],
    ):
        """
        Test sending withdrawal value in a transaction.
        """
        pre = {TestAddress: Account(balance=1)}
        blockchain_test(pre=pre, post=post, blocks=blocks)


def test_use_value_in_contract(blockchain_test: BlockchainTestFiller):
    """
    Test sending value from contract that has not received a withdrawal
    """
    SEND_ONE_GWEI = Op.SSTORE(
        Op.NUMBER,
        Op.CALL(Op.GAS, 0x200, 1000000000, 0, 0, 0, 0),
    )

    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        Address(0x100): Account(balance=0, code=SEND_ONE_GWEI),
        Address(0x200): Account(balance=1),
    }
    tx = Transaction(
        # Transaction sent from the `TestAddress`, which has 0 balance at start
        nonce=0,
        value=0,
        gas_price=10,
        gas_limit=100000,
        to=Address(0x100),
        data="0x",
    )
    withdrawal = Withdrawal(
        index=0,
        validator_index=0,
        address=Address(0x100),
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
        Address(0x100): Account(
            storage={
                0x1: 0x0,  # Call fails on the first attempt
                0x2: 0x1,  # Succeeds on the second attempt
            }
        ),
        Address(0x200): Account(
            balance=ONE_GWEI + 1,
        ),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)


def test_balance_within_block(blockchain_test: BlockchainTestFiller):
    """
    Test Withdrawal balance increase within the same block,
    inside contract call.
    """
    SAVE_BALANCE_ON_BLOCK_NUMBER = Op.SSTORE(
        Op.NUMBER,
        Op.BALANCE(Op.CALLDATALOAD(0)),
    )
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        Address(0x100): Account(
            code=SAVE_BALANCE_ON_BLOCK_NUMBER,
        ),
        Address(0x200): Account(
            balance=ONE_GWEI,
        ),
    }
    blocks = [
        Block(
            txs=[
                Transaction(
                    nonce=0,
                    gas_limit=100000,
                    to=Address(0x100),
                    data=Hash(0x200),
                )
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=Address(0x200),
                    amount=1,
                )
            ],
        ),
        Block(
            txs=[
                Transaction(
                    nonce=1,
                    gas_limit=100000,
                    to=Address(0x100),
                    data=Hash(0x200),
                )
            ]
        ),
    ]

    post = {
        Address(0x100): Account(
            storage={
                1: ONE_GWEI,
                2: 2 * ONE_GWEI,
            }
        )
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)


@pytest.mark.parametrize("test_case", ["single_block", "multiple_blocks"])
class TestMultipleWithdrawalsSameAddress:
    """
    Test that multiple withdrawals can be sent to the same address in:

    1. A single block.

    2. Multiple blocks.
    """

    ADDRESSES = [
        Address(0x0),  # Zero address
        Address(0x1),  # Pre-compiles
        Address(0x2),
        Address(0x3),
        Address(0x4),
        Address(0x5),
        Address(0x6),
        Address(0x7),
        Address(0x8),
        Address(0x9),
        Address(2**160 - 1),
    ]

    @pytest.fixture
    def blocks(self, test_case: str):  # noqa: D102
        if test_case == "single_block":
            # Many repeating withdrawals of the same accounts in the same
            # block.
            return [
                Block(
                    withdrawals=[
                        Withdrawal(
                            index=i,
                            validator_index=i,
                            address=self.ADDRESSES[i % len(self.ADDRESSES)],
                            amount=1,
                        )
                        for i in range(len(self.ADDRESSES) * 16)
                    ],
                ),
            ]
        if test_case == "multiple_blocks":
            # Similar test but now use multiple blocks each with multiple
            # withdrawals to the same withdrawal address.
            return [
                Block(
                    withdrawals=[
                        Withdrawal(
                            index=i * 16 + j,
                            validator_index=i,
                            address=self.ADDRESSES[i],
                            amount=1,
                        )
                        for j in range(16)
                    ],
                )
                for i in range(len(self.ADDRESSES))
            ]
        raise Exception("Invalid test case.")

    def test_multiple_withdrawals_same_address(
        self,
        blockchain_test: BlockchainTestFiller,
        test_case: str,
        blocks: List[Block],
    ):
        """
        Test Withdrawals can be done to the same address multiple times in
        the same block.
        """
        pre = {
            TestAddress: Account(balance=1000000000000000000000, nonce=0),
        }
        for addr in self.ADDRESSES:
            pre[addr] = Account(
                # set a storage value unconditionally on call
                code=Op.SSTORE(Op.NUMBER, 1),
            )

        # Expected post is the same for both test cases.
        post = {}
        for addr in self.ADDRESSES:
            post[addr] = Account(
                balance=16 * ONE_GWEI,
                storage={},
            )

        blockchain_test(pre=pre, post=post, blocks=blocks, tag=test_case)


def test_many_withdrawals(blockchain_test: BlockchainTestFiller):
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
        addr = Address(0x100 * i)
        amount = i * 1
        pre[addr] = Account(
            code=Op.SSTORE(Op.NUMBER, 1),
        )
        withdrawals.append(
            Withdrawal(
                index=i,
                validator_index=i,
                address=addr,
                amount=amount,
            )
        )
        post[addr] = Account(
            code=Op.SSTORE(Op.NUMBER, 1),
            balance=amount * ONE_GWEI,
            storage={},
        )

    blocks = [
        Block(
            withdrawals=withdrawals,
        ),
    ]

    blockchain_test(pre=pre, post=post, blocks=blocks)


def test_self_destructing_account(blockchain_test: BlockchainTestFiller, fork: Fork):
    """
    Test withdrawals can be done to self-destructed accounts.
    Account `0x100` self-destructs and sends all its balance to `0x200`.
    Then, a withdrawal is received at `0x100` with 99 wei.
    """
    self_destruct_code = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        Address(0x100): Account(
            code=self_destruct_code,
            balance=(100 * ONE_GWEI),
        ),
        Address(0x200): Account(
            balance=1,
        ),
    }

    tx_1 = Transaction(
        # Transaction sent from the `TestAddress`, that calls a
        # self-destructing contract.
        nonce=0,
        gas_price=10,
        gas_limit=100000,
        to=Address(0x100),
        data=Hash(0x200),
    )

    withdrawal = Withdrawal(
        index=0,
        validator_index=0,
        address=Address(0x100),
        amount=(99),
    )

    block = Block(
        txs=[tx_1],
        withdrawals=[withdrawal],
    )

    post = {
        Address(0x100): Account(
            code=self_destruct_code if fork >= Cancun else b"",
            balance=(99 * ONE_GWEI),
        ),
        Address(0x200): Account(
            code=b"",
            balance=(100 * ONE_GWEI) + 1,
        ),
    }

    blockchain_test(pre=pre, post=post, blocks=[block])


@pytest.mark.parametrize(
    "include_value_in_tx",
    [False, True],
    ids=["without_tx_value", "with_tx_value"],
)
def test_newly_created_contract(
    blockchain_test: BlockchainTestFiller,
    include_value_in_tx: bool,
    request,
):
    """
    Test Withdrawing to a newly created contract.
    """
    created_contract = compute_create_address(TestAddress, 0)

    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
    }

    initcode = Op.RETURN(0, 1)

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
        validator_index=0,
        address=created_contract,
        amount=1,
    )

    created_contract_balance = ONE_GWEI
    if include_value_in_tx:
        tx = tx.copy(value=ONE_GWEI)
        created_contract_balance = 2 * ONE_GWEI

    post = {
        created_contract: Account(
            code="0x00",
            balance=created_contract_balance,
        ),
    }

    block = Block(
        txs=[tx],
        withdrawals=[withdrawal],
    )

    tag = request.node.callspec.id.split("-")[0]  # remove fork; brittle
    blockchain_test(pre=pre, post=post, blocks=[block], tag=tag)


def test_no_evm_execution(blockchain_test: BlockchainTestFiller):
    """
    Test Withdrawals don't trigger EVM execution.
    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        Address(0x100): Account(
            code=Op.SSTORE(Op.NUMBER, 1),
        ),
        Address(0x200): Account(
            code=Op.SSTORE(Op.NUMBER, 1),
        ),
        Address(0x300): Account(
            code=Op.SSTORE(Op.NUMBER, 1),
        ),
        Address(0x400): Account(
            code=Op.SSTORE(Op.NUMBER, 1),
        ),
    }
    blocks = [
        Block(
            txs=[
                Transaction(
                    nonce=0,
                    gas_limit=100000,
                    to=Address(0x300),
                ),
                Transaction(
                    nonce=1,
                    gas_limit=100000,
                    to=Address(0x400),
                ),
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=Address(0x100),
                    amount=1,
                ),
                Withdrawal(
                    index=1,
                    validator_index=1,
                    address=Address(0x200),
                    amount=1,
                ),
            ],
        ),
        Block(
            txs=[
                Transaction(
                    nonce=2,
                    gas_limit=100000,
                    to=Address(0x100),
                ),
                Transaction(
                    nonce=3,
                    gas_limit=100000,
                    to=Address(0x200),
                ),
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=Address(0x300),
                    amount=1,
                ),
                Withdrawal(
                    index=1,
                    validator_index=1,
                    address=Address(0x400),
                    amount=1,
                ),
            ],
        ),
    ]

    post = {
        Address(0x100): Account(storage={2: 1}),
        Address(0x200): Account(storage={2: 1}),
        Address(0x300): Account(storage={1: 1}),
        Address(0x400): Account(storage={1: 1}),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)


@unique
class ZeroAmountTestCases(Enum):  # noqa: D101
    TWO_ZERO = "two_withdrawals_no_value"
    THREE_ONE_WITH_VALUE = "three_withdrawals_one_with_value"
    FOUR_ONE_WITH_MAX = "four_withdrawals_one_with_value_one_with_max"
    FOUR_ONE_WITH_MAX_REVERSED = "four_withdrawals_one_with_value_one_with_max_reversed_order"


@pytest.mark.parametrize(
    "test_case",
    [case for case in ZeroAmountTestCases],
    ids=[case.value for case in ZeroAmountTestCases],
)
def test_zero_amount(
    blockchain_test: BlockchainTestFiller,
    test_case: ZeroAmountTestCases,
):
    """
    Test withdrawals with zero amount for the following cases, all withdrawals
    are included in one block:

    1. Two withdrawals of zero amount to two different addresses; one to an
       untouched account, one to an account with a balance.
    2. As 1., but with an additional withdrawal with positive value.
    3. As 2., but with an additional withdrawal containing the maximum value
       possible.
    4. As 3., but with order of withdrawals in the block reversed.

    """
    pre = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
        Address(0x200): Account(
            code="0x00",
            balance=0,
        ),
    }

    all_withdrawals = [
        # No value, untouched account
        Withdrawal(
            index=0,
            validator_index=0,
            address=Address(0x100),
            amount=0,
        ),
        # No value, touched account
        Withdrawal(
            index=0,
            validator_index=0,
            address=Address(0x200),
            amount=0,
        ),
        # Withdrawal with value
        Withdrawal(
            index=1,
            validator_index=0,
            address=Address(0x300),
            amount=1,
        ),
        # Withdrawal with maximum amount
        Withdrawal(
            index=2,
            validator_index=0,
            address=Address(0x400),
            amount=2**64 - 1,
        ),
    ]
    all_post = {
        Address(0x100): Account.NONEXISTENT,
        Address(0x200): Account(code="0x00", balance=0),
        Address(0x300): Account(balance=ONE_GWEI),
        Address(0x400): Account(balance=(2**64 - 1) * ONE_GWEI),
    }

    withdrawals: List[Withdrawal] = []
    post: Mapping[Address, Account | object] = {}
    if test_case == ZeroAmountTestCases.TWO_ZERO:
        withdrawals = all_withdrawals[0:2]
        post = {
            account: all_post[account]
            for account in post
            if account in [Address(0x100), Address(0x200)]
        }
    elif test_case == ZeroAmountTestCases.THREE_ONE_WITH_VALUE:
        withdrawals = all_withdrawals[0:3]
        post = {
            account: all_post[account]
            for account in post
            if account
            in [
                Address(0x100),
                Address(0x200),
                Address(0x300),
            ]
        }
    elif test_case == ZeroAmountTestCases.FOUR_ONE_WITH_MAX:
        withdrawals = all_withdrawals
        post = all_post
    elif test_case == ZeroAmountTestCases.FOUR_ONE_WITH_MAX_REVERSED:
        for i, w in enumerate(reversed(all_withdrawals)):
            withdrawals.append(
                Withdrawal(
                    index=i,
                    validator_index=w.validator_index,
                    address=w.address,
                    amount=w.amount,
                )
            )
        post = all_post
    else:
        raise Exception("Unknown test case.")

    blockchain_test(
        pre=pre,
        # TODO: Fix in BlockchainTest? post: Mapping[str, Account | object]
        # to allow for Account.NONEXISTENT
        post=post,  # type: ignore
        blocks=[Block(withdrawals=withdrawals)],
        tag=test_case.value,
    )


def test_large_amount(blockchain_test: BlockchainTestFiller):
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
        addr = Address(0x100 * (i + 1))
        withdrawals.append(
            Withdrawal(
                index=i,
                validator_index=i,
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
    blockchain_test(pre=pre, post=post, blocks=blocks)


@pytest.mark.parametrize("amount", [0, 1])
@pytest.mark.with_all_precompiles
def test_withdrawing_to_precompiles(
    blockchain_test: BlockchainTestFiller, precompile: int, amount: int, t8n: TransitionTool
):
    """
    Test withdrawing to all precompiles for a given fork.
    """
    if precompile == 3 and str(t8n.default_binary) == "ethereum-spec-evm":
        pytest.xfail("ethereum-spec-evm doesn't support hash type ripemd160")
    pre: Dict = {
        TestAddress: Account(balance=1000000000000000000000, nonce=0),
    }
    post: Dict = {}

    blocks = [
        # First block performs the withdrawal
        Block(
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=Address(precompile),
                    amount=amount,
                )
            ]
        ),
        # Second block sends a transaction to the precompile
        Block(
            txs=[
                Transaction(
                    nonce=0,
                    gas_limit=100000,
                    to=Address(precompile),
                ),
            ],
        ),
    ]
    blockchain_test(pre=pre, post=post, blocks=blocks)
