"""
abstract: Tests [EIP-7516: BLOBBASEFEE opcode](https://eips.ethereum.org/EIPS/eip-7516)
    Test BLOBGASFEE opcode [EIP-7516: BLOBBASEFEE opcode](https://eips.ethereum.org/EIPS/eip-7516).

"""  # noqa: E501

from itertools import count

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7516.md"
REFERENCE_SPEC_VERSION = "dcd2f4ede58a6ed908acd3cc2c198e9f605cbf3b"

BLOBBASEFEE_GAS = 2


@pytest.fixture
def call_gas() -> int:
    """Amount of gas to use when calling the callee code."""
    return 0xFFFF


@pytest.fixture
def callee_code() -> Bytecode:
    """Bytecode under test, by default, only call the BLOBBASEFEE opcode."""
    return Op.BLOBBASEFEE + Op.STOP


@pytest.fixture
def callee_address(pre: Alloc, callee_code: Bytecode) -> Address:
    """Address of the account containing the bytecode under test."""
    return pre.deploy_contract(callee_code)


@pytest.fixture
def caller_code(
    call_gas: int,
    callee_address: Address,
) -> Bytecode:
    """Bytecode used to call the bytecode containing the BLOBBASEFEE opcode."""
    return Op.SSTORE(Op.NUMBER, Op.CALL(gas=call_gas, address=callee_address))


@pytest.fixture
def caller_pre_storage() -> Storage:
    """Storage of the account containing the bytecode that calls the test contract."""
    return Storage()


@pytest.fixture
def caller_address(pre: Alloc, caller_code: Bytecode, caller_pre_storage) -> Address:
    """Address of the account containing the bytecode that calls the test contract."""
    return pre.deploy_contract(caller_code)


@pytest.fixture
def tx(pre: Alloc, caller_address: Address) -> Transaction:
    """
    Prepare test transaction, by setting the destination account, the
    transaction value, the transaction gas limit, and the transaction data.
    """
    return Transaction(
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        to=caller_address,
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
    caller_address: Address,
    callee_address: Address,
    tx: Transaction,
    call_fails: bool,
):
    """Tests that the BLOBBASEFEE opcode produces a stack overflow by using it repeatedly."""
    post = {
        caller_address: Account(
            storage={1: 0 if call_fails else 1},
        ),
        callee_address: Account(
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
    caller_address: Address,
    callee_address: Address,
    tx: Transaction,
    call_fails: bool,
):
    """Tests that the BLOBBASEFEE opcode fails with insufficient gas."""
    post = {
        caller_address: Account(
            storage={1: 0 if call_fails else 1},
        ),
        callee_address: Account(
            balance=0,
        ),
    }
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize("caller_pre_storage", [{1: 1}], ids=[""])
@pytest.mark.valid_at_transition_to("Cancun")
def test_blobbasefee_before_fork(
    state_test: StateTestFiller,
    pre: Alloc,
    caller_address: Address,
    callee_address: Address,
    tx: Transaction,
):
    """Tests that the BLOBBASEFEE opcode results on exception when called before the fork."""
    # Fork happens at timestamp 15_000
    timestamp = 7_500
    post = {
        caller_address: Account(
            storage={1: 0},
        ),
        callee_address: Account(
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


timestamps = [7_500, 14_999, 15_000]


@pytest.mark.parametrize(
    "caller_pre_storage",
    [{block_number: 0xFF for block_number, _ in enumerate(timestamps, start=1)}],
    ids=[""],
)
@pytest.mark.valid_at_transition_to("Cancun")
def test_blobbasefee_during_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    caller_address: Address,
    callee_address: Address,
    tx: Transaction,
):
    """
    Tests that the BLOBBASEFEE opcode results on exception when called before the fork and
    succeeds when called after the fork.
    """
    code_caller_post_storage = Storage()

    nonce = count(0)

    blocks = []

    for block_number, timestamp in enumerate(timestamps, start=1):
        blocks.append(
            Block(
                txs=[tx.with_nonce(next(nonce))],
                timestamp=timestamp,
            ),
        )
        # pre-set storage just to make sure we detect the change
        code_caller_post_storage[block_number] = 0 if timestamp < 15_000 else 1

    post = {
        caller_address: Account(
            storage=code_caller_post_storage,
        ),
        callee_address: Account(
            balance=0,
        ),
    }
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        blocks=blocks,
        post=post,
    )
