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
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Hash,
    Transaction,
    TransactionException,
    Withdrawal,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from evm_transition_tool import TransitionTool

from .spec import ref_spec_4895

REFERENCE_SPEC_GIT_PATH = ref_spec_4895.git_path
REFERENCE_SPEC_VERSION = ref_spec_4895.version

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
    def sender(self, pre: Alloc) -> EOA:
        """
        Funded EOA used for sending transactions.
        """
        return pre.fund_eoa(1)

    @pytest.fixture
    def recipient(self, pre: Alloc) -> EOA:
        """
        Funded EOA used for sending transactions.
        """
        return pre.fund_eoa(0)

    @pytest.fixture
    def tx(self, sender: EOA, recipient: EOA):  # noqa: D102
        # Transaction sent from the `sender`, which has 1 wei balance at start
        return Transaction(
            gas_price=ONE_GWEI,
            gas_limit=21000,
            to=recipient,
            sender=sender,
        )

    @pytest.fixture
    def withdrawal(self, tx: Transaction, sender: EOA):  # noqa: D102
        return Withdrawal(
            index=0,
            validator_index=0,
            address=sender,
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
    def post(self, sender: EOA, test_case: str) -> Dict:  # noqa: D102
        if test_case == "tx_in_withdrawals_block":
            return {}
        if test_case == "tx_after_withdrawals_block":
            return {sender: Account(balance=ONE_GWEI + 1)}
        raise Exception("Invalid test case.")

    def test_use_value_in_tx(
        self,
        pre: Alloc,
        blockchain_test: BlockchainTestFiller,
        post: dict,
        blocks: List[Block],
    ):
        """
        Test sending withdrawal value in a transaction.
        """
        blockchain_test(pre=pre, post=post, blocks=blocks)


def test_use_value_in_contract(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    Test sending value from contract that has not received a withdrawal
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(1)

    contract_address = pre.deploy_contract(
        Op.SSTORE(
            Op.NUMBER,
            Op.CALL(address=recipient, value=1000000000),
        )
    )
    (tx_0, tx_1) = (
        Transaction(
            sender=sender,
            value=0,
            gas_limit=100_000,
            to=contract_address,
        )
        for _ in range(2)
    )

    withdrawal = Withdrawal(
        index=0,
        validator_index=0,
        address=contract_address,
        amount=1,
    )

    blocks = [
        Block(
            txs=[tx_0],
            withdrawals=[withdrawal],
        ),
        Block(
            txs=[tx_1],  # Same tx again, just increase nonce
        ),
    ]
    post = {
        contract_address: Account(
            storage={
                0x1: 0x0,  # Call fails on the first attempt
                0x2: 0x1,  # Succeeds on the second attempt
            }
        ),
        recipient: Account(
            balance=ONE_GWEI + 1,
        ),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)


def test_balance_within_block(blockchain_test: BlockchainTestFiller, pre: Alloc):
    """
    Test Withdrawal balance increase within the same block,
    inside contract call.
    """
    SAVE_BALANCE_ON_BLOCK_NUMBER = Op.SSTORE(
        Op.NUMBER,
        Op.BALANCE(Op.CALLDATALOAD(0)),
    )
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(ONE_GWEI)
    contract_address = pre.deploy_contract(SAVE_BALANCE_ON_BLOCK_NUMBER)

    blocks = [
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    gas_limit=100000,
                    to=contract_address,
                    data=Hash(recipient),
                )
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=recipient,
                    amount=1,
                )
            ],
        ),
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    gas_limit=100000,
                    to=contract_address,
                    data=Hash(recipient),
                )
            ]
        ),
    ]

    post = {
        contract_address: Account(
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

    @pytest.fixture
    def addresses(self, fork: Fork) -> List[Address]:  # noqa: D102
        addresses = [Address(p) for p in fork.precompiles(block_number=0, timestamp=0)]
        return addresses + [Address(2**160 - 1)]

    @pytest.fixture
    def blocks(self, addresses: Address, test_case: str):  # noqa: D102
        if test_case == "single_block":
            # Many repeating withdrawals of the same accounts in the same
            # block.
            return [
                Block(
                    withdrawals=[
                        Withdrawal(
                            index=i,
                            validator_index=i,
                            address=addresses[i % len(addresses)],
                            amount=1,
                        )
                        for i in range(len(addresses) * 16)
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
                            address=addresses[i],
                            amount=1,
                        )
                        for j in range(16)
                    ],
                )
                for i in range(len(addresses))
            ]
        raise Exception("Invalid test case.")

    def test_multiple_withdrawals_same_address(
        self,
        blockchain_test: BlockchainTestFiller,
        test_case: str,
        pre: Alloc,
        addresses: List[Address],
        blocks: List[Block],
    ):
        """
        Test Withdrawals can be done to the same address multiple times in
        the same block.
        """
        # Expected post is the same for both test cases.
        post = {}
        for addr in addresses:
            post[addr] = Account(
                balance=16 * ONE_GWEI,
                storage={},
            )

        blockchain_test(pre=pre, post=post, blocks=blocks, tag=test_case)


def test_many_withdrawals(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    Test Withdrawals with a count of N withdrawals in a single block where
    N is a high number not expected to be seen in mainnet.
    """
    N = 400
    withdrawals = []
    post = {}
    for i in range(N):
        addr = pre.deploy_contract(Op.SSTORE(Op.NUMBER, 1))
        amount = i * 1
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


def test_self_destructing_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """
    Test withdrawals can be done to self-destructed accounts.
    Account `0x100` self-destructs and sends all its balance to `0x200`.
    Then, a withdrawal is received at `0x100` with 99 wei.
    """
    self_destruct_code = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(1)
    self_destruct_contract_address = pre.deploy_contract(
        self_destruct_code,
        balance=100 * ONE_GWEI,
    )

    tx_1 = Transaction(
        # Transaction sent from the `sender`, that calls a
        # self-destructing contract.
        sender=sender,
        gas_limit=100000,
        to=self_destruct_contract_address,
        data=Hash(recipient),
    )

    withdrawal = Withdrawal(
        index=0,
        validator_index=0,
        address=self_destruct_contract_address,
        amount=(99),
    )

    block = Block(
        txs=[tx_1],
        withdrawals=[withdrawal],
    )

    post = {
        self_destruct_contract_address: Account(
            code=self_destruct_code if fork >= Cancun else b"",
            balance=(99 * ONE_GWEI),
        ),
        recipient: Account(
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
    pre: Alloc,
    include_value_in_tx: bool,
    request,
):
    """
    Test Withdrawing to a newly created contract.
    """
    sender = pre.fund_eoa()
    initcode = Op.RETURN(0, 1)
    tx = Transaction(
        # Transaction sent from the `sender`, that creates a
        # new contract.
        sender=sender,
        gas_limit=1000000,
        to=None,
        value=ONE_GWEI if include_value_in_tx else 0,
        data=initcode,
    )
    created_contract = tx.created_contract

    withdrawal = Withdrawal(
        index=0,
        validator_index=0,
        address=created_contract,
        amount=1,
    )

    created_contract_balance = ONE_GWEI
    if include_value_in_tx:
        created_contract_balance = 2 * ONE_GWEI

    post = {
        created_contract: Account(
            code=Op.STOP,
            balance=created_contract_balance,
        ),
    }

    block = Block(
        txs=[tx],
        withdrawals=[withdrawal],
    )

    blockchain_test(pre=pre, post=post, blocks=[block])


def test_no_evm_execution(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    Test Withdrawals don't trigger EVM execution.
    """
    sender = pre.fund_eoa()
    contracts = [pre.deploy_contract(Op.SSTORE(Op.NUMBER, 1)) for _ in range(4)]
    blocks = [
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    gas_limit=100000,
                    to=contracts[2],
                ),
                Transaction(
                    sender=sender,
                    gas_limit=100000,
                    to=contracts[3],
                ),
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=contracts[0],
                    amount=1,
                ),
                Withdrawal(
                    index=1,
                    validator_index=1,
                    address=contracts[1],
                    amount=1,
                ),
            ],
        ),
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    gas_limit=100000,
                    to=contracts[0],
                ),
                Transaction(
                    sender=sender,
                    gas_limit=100000,
                    to=contracts[1],
                ),
            ],
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=contracts[2],
                    amount=1,
                ),
                Withdrawal(
                    index=1,
                    validator_index=1,
                    address=contracts[3],
                    amount=1,
                ),
            ],
        ),
    ]

    post = {
        contracts[0]: Account(storage={2: 1}),
        contracts[1]: Account(storage={2: 1}),
        contracts[2]: Account(storage={1: 1}),
        contracts[3]: Account(storage={1: 1}),
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
    pre: Alloc,
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
    empty_accounts = [pre.fund_eoa(0) for _ in range(3)]
    zero_balance_contract = pre.deploy_contract(Op.STOP)

    all_withdrawals = [
        # No value, untouched account
        Withdrawal(
            index=0,
            validator_index=0,
            address=empty_accounts[0],
            amount=0,
        ),
        # No value, touched account
        Withdrawal(
            index=0,
            validator_index=0,
            address=zero_balance_contract,
            amount=0,
        ),
        # Withdrawal with value
        Withdrawal(
            index=1,
            validator_index=0,
            address=empty_accounts[1],
            amount=1,
        ),
        # Withdrawal with maximum amount
        Withdrawal(
            index=2,
            validator_index=0,
            address=empty_accounts[2],
            amount=2**64 - 1,
        ),
    ]
    all_post = {
        empty_accounts[0]: Account.NONEXISTENT,
        zero_balance_contract: Account(code=Op.STOP, balance=0),
        empty_accounts[1]: Account(balance=ONE_GWEI),
        empty_accounts[2]: Account(balance=(2**64 - 1) * ONE_GWEI),
    }

    withdrawals: List[Withdrawal] = []
    post: Mapping[Address, Account | object] = {}
    if test_case == ZeroAmountTestCases.TWO_ZERO:
        withdrawals = all_withdrawals[0:2]
        post = {
            account: all_post[account]
            for account in post
            if account in [empty_accounts[0], zero_balance_contract]
        }
    elif test_case == ZeroAmountTestCases.THREE_ONE_WITH_VALUE:
        withdrawals = all_withdrawals[0:3]
        post = {
            account: all_post[account]
            for account in post
            if account
            in [
                empty_accounts[0],
                zero_balance_contract,
                empty_accounts[1],
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

    blockchain_test(
        pre=pre,
        # TODO: Fix in BlockchainTest? post: Mapping[str, Account | object]
        # to allow for Account.NONEXISTENT
        post=post,  # type: ignore
        blocks=[Block(withdrawals=withdrawals)],
        tag=test_case.value,
    )


def test_large_amount(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    Test Withdrawals that have a large gwei amount, so that (gwei * 1e9)
    could overflow uint64 but not uint256.
    """
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
        addr = pre.fund_eoa(0)
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
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    precompile: int,
    amount: int,
    t8n: TransitionTool,
):
    """
    Test withdrawing to all precompiles for a given fork.
    """
    sender = pre.fund_eoa()
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
                    sender=sender,
                    gas_limit=100000,
                    to=Address(precompile),
                ),
            ],
        ),
    ]
    blockchain_test(pre=pre, post=post, blocks=blocks)
