"""
abstract: Tests [EIP-7516: BLOBBASEFEE opcode](https://eips.ethereum.org/EIPS/eip-7516)
    Test BLOBGASFEE opcode [EIP-7516: BLOBBASEFEE opcode](https://eips.ethereum.org/EIPS/eip-7516)

"""  # noqa: E501

from itertools import count

import pytest

from ethereum_test_tools import Account, Address, Alloc, Block, BlockchainTestFiller, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Storage, TestAddress, Transaction

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7516.md"
REFERENCE_SPEC_VERSION = "2ade0452efe8124378f35284676ddfd16dd56ecd"

# Code address used to call the test bytecode on every test case.
code_caller_address = Address(0x100)
code_callee_address = Address(0x200)

BLOBBASEFEE_GAS = 2


@pytest.fixture
def call_gas() -> int:
    """
    Amount of gas to use when calling the callee code.
    """
    return 0xFFFF


@pytest.fixture
def caller_code(
    call_gas: int,
) -> bytes:
    """
    Bytecode used to call the bytecode containing the BLOBBASEFEE opcode.
    """
    return Op.SSTORE(Op.NUMBER, Op.CALL(call_gas, code_callee_address, 0, 0, 0, 0, 0))


@pytest.fixture
def callee_code() -> bytes:
    """
    Bytecode under test, by default, only call the BLOBBASEFEE opcode.
    """
    return bytes(Op.BLOBBASEFEE + Op.STOP)


@pytest.fixture
def pre(
    caller_code: bytes,
    callee_code: bytes,
) -> Alloc:
    """
    Prepares the pre state of all test cases, by setting the balance of the
    source account of all test transactions, and the required code.
    """
    return Alloc(
        {
            TestAddress: Account(balance=10**40),
            code_caller_address: Account(
                balance=0,
                code=caller_code,
            ),
            code_callee_address: Account(
                balance=0,
                code=callee_code,
            ),
        }
    )


@pytest.fixture
def tx() -> Transaction:
    """
    Prepares the test transaction, by setting the destination account, the
    transaction value, the transaction gas limit, and the transaction data.
    """
    return Transaction(
        gas_price=1_000_000_000,
        gas_limit=1_000_000,
        to=code_caller_address,
        value=0,
        data=b"",
    )


@pytest.mark.parametrize(
    "callee_code,call_fails",
    [
        pytest.param(Op.BLOBBASEFEE * 1024, False, id="no_stack_overflow"),
        pytest.param(Op.BLOBBASEFEE * 1025, True, id="stack_overflow"),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_blobbasefee_stack_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    call_fails: bool,
):
    """
    Tests that the BLOBBASEFEE opcode produces a stack overflow by using it repeatedly.
    """
    post = {
        code_caller_address: Account(
            storage={1: 0 if call_fails else 1},
        ),
        code_callee_address: Account(
            balance=0,
        ),
    }
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "call_gas,call_fails",
    [
        pytest.param(BLOBBASEFEE_GAS, False, id="enough_gas"),
        pytest.param(BLOBBASEFEE_GAS - 1, True, id="out_of_gas"),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_blobbasefee_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    call_fails: bool,
):
    """
    Tests that the BLOBBASEFEE opcode fails with insufficient gas.
    """
    post = {
        code_caller_address: Account(
            storage={1: 0 if call_fails else 1},
        ),
        code_callee_address: Account(
            balance=0,
        ),
    }
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.valid_at_transition_to("Cancun")
def test_blobbasefee_before_fork(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
):
    """
    Tests that the BLOBBASEFEE opcode results on exception when called before the fork.
    """
    # Fork happens at timestamp 15_000
    timestamp = 7_500
    code_caller_account = pre[code_caller_address]
    assert code_caller_account is not None
    pre[code_caller_address] = code_caller_account.copy(
        storage={1: 1},
    )
    post = {
        code_caller_address: Account(
            storage={1: 0},
        ),
        code_callee_address: Account(
            balance=0,
        ),
    }
    state_test(
        env=Environment(
            timestamp=timestamp,
        ),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.valid_at_transition_to("Cancun")
def test_blobbasefee_during_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    tx: Transaction,
):
    """
    Tests that the BLOBBASEFEE opcode results on exception when called before the fork and
    succeeds when called after the fork.
    """
    code_caller_pre_storage = Storage()
    code_caller_post_storage = Storage()

    nonce = count(0)

    timestamps = [7_500, 14_999, 15_000]

    blocks = []

    for block_number, timestamp in enumerate(timestamps, start=1):
        blocks.append(
            Block(
                txs=[tx.with_nonce(next(nonce))],
                timestamp=timestamp,
            ),
        )
        # pre-set storage just to make sure we detect the change
        code_caller_pre_storage[block_number] = 0xFF
        code_caller_post_storage[block_number] = 0 if timestamp < 15_000 else 1

    code_caller_account = pre[code_caller_address]
    assert code_caller_account is not None
    pre[code_caller_address] = code_caller_account.copy(
        storage=code_caller_pre_storage,
    )
    post = {
        code_caller_address: Account(
            storage=code_caller_post_storage,
        ),
        code_callee_address: Account(
            balance=0,
        ),
    }
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        blocks=blocks,
        post=post,
    )
