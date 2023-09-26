"""
abstract: Tests [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780)

    Tests for [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780).

"""  # noqa: E501

from itertools import count, cycle
from typing import Dict, List, SupportsBytes

import pytest
from ethereum.crypto.hash import keccak256

from ethereum_test_forks import Cancun, Fork, is_fork
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    Environment,
    Initcode,
    StateTestFiller,
    Storage,
    TestAddress,
    Transaction,
    YulCompiler,
    compute_create2_address,
    compute_create_address,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "2f8299df31bb8173618901a03a8366a3183479b0"

SELFDESTRUCT_ENABLE_FORK = Cancun

PRE_EXISTING_SELFDESTRUCT_ADDRESS = "0x1111111111111111111111111111111111111111"
"""
Address of a pre-existing contract that self-destructs.
"""

# Sentinel value to indicate that the self-destructing contract address should be used, only for
# use in `pytest.mark.parametrize`, not for use within the test method itself.
SELF_ADDRESS = "0x1"
# Sentinel value to indicate that the contract should not self-destruct.
NO_SELFDESTRUCT = "0x0"


@pytest.fixture
def eip_enabled(fork: Fork) -> bool:
    """Whether the EIP is enabled or not."""
    return is_fork(fork, SELFDESTRUCT_ENABLE_FORK)


@pytest.fixture
def env() -> Environment:
    """Default environment for all tests."""
    return Environment(
        coinbase="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
    )


@pytest.fixture
def sendall_recipient_addresses() -> List[str]:
    """List of possible addresses that can receive a SENDALL operation."""
    return [to_address(0x1234)]


def selfdestruct_code_preset(
    *,
    sendall_recipient_addresses: List[str],
    yul: YulCompiler,
) -> SupportsBytes:
    """Return a bytecode that self-destructs."""
    if len(sendall_recipient_addresses) != 1:
        # Load the recipient address from calldata, each test case needs to pass the addresses as
        # calldata
        return yul(
            f"""
            {{
                sstore(0, add(sload(0), 1))
                let selfdestruct_recipient := calldataload(0)
                if eq(selfdestruct_recipient, {SELF_ADDRESS}) {{
                    // One sends to self
                    selfdestruct_recipient := address()
                }}
                if not(eq(selfdestruct_recipient, {NO_SELFDESTRUCT})) {{
                    // zero is the sentinel value for not self-destructing
                    selfdestruct(selfdestruct_recipient)
                    sstore(0, 0)
                }}
            }}
            """  # noqa: E272, E201, E202, E221
        )
    else:
        # Hard-code the single only possible recipient address
        sendall_recipient = sendall_recipient_addresses[0]
        assert sendall_recipient != NO_SELFDESTRUCT, "test error"
        if sendall_recipient == SELF_ADDRESS:
            # Use the self address of the contract we are creating
            sendall_recipient = "address()"
        return yul(
            f"""
            {{
                sstore(0, add(sload(0), 1))
                selfdestruct({sendall_recipient_addresses[0]})
                sstore(0, 0)
            }}
            """  # noqa: E272, E201, E202, E221
        )


@pytest.fixture
def selfdestruct_code(
    sendall_recipient_addresses: List[str],
    yul: YulCompiler,
) -> SupportsBytes:
    """
    Creates the default self-destructing bytecode,
    which can be modified by each test if necessary.
    """
    return selfdestruct_code_preset(
        sendall_recipient_addresses=sendall_recipient_addresses,
        yul=yul,
    )


@pytest.fixture
def self_destructing_initcode() -> bool:
    """
    Whether the contract shall self-destruct during initialization.
    By default it does not.
    """
    return False


@pytest.fixture
def selfdestruct_contract_initcode(
    selfdestruct_code: SupportsBytes,
    self_destructing_initcode: bool,
) -> SupportsBytes:
    """Prepares an initcode that creates a self-destructing account."""
    if self_destructing_initcode:
        return selfdestruct_code
    return Initcode(deploy_code=selfdestruct_code)


@pytest.fixture
def initcode_copy_from_address() -> str:
    """Address of a pre-existing contract we use to simply copy initcode from."""
    return to_address(0xABCD)


@pytest.fixture
def entry_code_address() -> str:
    """Address where the entry code will run."""
    return compute_create_address(TestAddress, 0)


@pytest.fixture
def selfdestruct_contract_address(
    create_opcode: Op,
    entry_code_address: str,
    selfdestruct_contract_initcode: SupportsBytes,
) -> str:
    """Returns the address of the self-destructing contract."""
    if create_opcode == Op.CREATE:
        return compute_create_address(entry_code_address, 1)

    if create_opcode == Op.CREATE2:
        return compute_create2_address(entry_code_address, 0, selfdestruct_contract_initcode)

    raise Exception("Invalid opcode")


@pytest.fixture
def pre(
    initcode_copy_from_address: str,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_address: str,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[str],
    yul: YulCompiler,
) -> Dict[str, Account]:
    """Pre-state of all tests"""
    pre = {
        TestAddress: Account(balance=100_000_000_000_000_000_000),
        initcode_copy_from_address: Account(code=selfdestruct_contract_initcode),
    }

    if (
        selfdestruct_contract_initial_balance > 0
        and selfdestruct_contract_address != PRE_EXISTING_SELFDESTRUCT_ADDRESS
    ):
        pre[selfdestruct_contract_address] = Account(balance=selfdestruct_contract_initial_balance)

    # Also put a pre-existing copy of the self-destruct contract in a known place
    pre[PRE_EXISTING_SELFDESTRUCT_ADDRESS] = Account(
        code=selfdestruct_code_preset(
            sendall_recipient_addresses=sendall_recipient_addresses,
            yul=yul,
        ),
        balance=selfdestruct_contract_initial_balance,
    )

    # Send-all recipient accounts contain code that unconditionally resets an storage key upon
    # entry, so we can check that it was not executed
    for i in range(len(sendall_recipient_addresses)):
        if sendall_recipient_addresses[i] == SELF_ADDRESS:
            sendall_recipient_addresses[i] = selfdestruct_contract_address
        address = sendall_recipient_addresses[i]
        if (
            address != PRE_EXISTING_SELFDESTRUCT_ADDRESS
            and address != selfdestruct_contract_address
        ):
            pre[address] = Account(
                code=Op.SSTORE(0, 0),
                storage={0: 1},
            )

    return pre


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "call_times,sendall_recipient_addresses",
    [
        pytest.param(
            1,
            [to_address(0x1000)],
            id="single_call",
        ),
        pytest.param(
            1,
            [SELF_ADDRESS],
            id="single_call_self",
        ),
        pytest.param(
            10,
            [to_address(0x1000)],
            id="multiple_calls_single_sendall_recipient",
        ),
        pytest.param(
            10,
            [to_address(0x1000), to_address(0x2000), to_address(0x3000)],
            id="multiple_calls_multiple_sendall_recipients",
        ),
        pytest.param(
            10,
            [SELF_ADDRESS, to_address(0x2000), to_address(0x3000)],
            id="multiple_calls_multiple_sendall_recipients_including_self",
        ),
        pytest.param(
            10,
            [to_address(0x1000), to_address(0x2000), SELF_ADDRESS],
            id="multiple_calls_multiple_sendall_recipients_including_self_different_order",
        ),
        pytest.param(
            3,
            [to_address(0x1000), to_address(0x2000), SELF_ADDRESS],
            id="multiple_calls_multiple_sendall_recipients_including_self_last",
        ),
    ],
)
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_create_selfdestruct_same_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict[str, Account],
    entry_code_address: str,
    selfdestruct_code: SupportsBytes,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_address: str,
    sendall_recipient_addresses: List[str],
    initcode_copy_from_address: str,
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
):
    """
    Use CREATE or CREATE2 to create a self-destructing contract, and call it in the same
    transaction.

    Behavior should be the same before and after EIP-6780.

    Test using:
        - Different send-all recipient addresses: single, multiple, including self
        - Different initial balances for the self-destructing contract
        - Different opcodes: CREATE, CREATE2
    """
    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(sendall_recipient_addresses, [0] * len(sendall_recipient_addresses))
    )
    selfdestruct_contract_current_balance = selfdestruct_contract_initial_balance

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_args = [
        0,  # Value
        0,  # Offset
        len(bytes(selfdestruct_contract_initcode)),  # Length
    ]
    if create_opcode == Op.CREATE2:
        # CREATE2 requires a salt argument
        create_args.append(0)
    create_bytecode = create_opcode(*create_args)

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            Op.PUSH20(initcode_copy_from_address),
            0,
            0,
            len(bytes(selfdestruct_contract_initcode)),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_bytecode,
        )
    )

    # Store the EXTCODE* properties of the created address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(bytes(selfdestruct_code))),
        Op.EXTCODESIZE(Op.PUSH20(selfdestruct_contract_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes(selfdestruct_code))),
        Op.EXTCODEHASH(Op.PUSH20(selfdestruct_contract_address)),
    )

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    for i, sendall_recipient in zip(range(call_times), cycle(sendall_recipient_addresses)):
        entry_code += Op.MSTORE(0, Op.PUSH20(sendall_recipient))
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                Op.PUSH20(selfdestruct_contract_address),  # Address
                i,  # Value
                0,
                32,
                0,
                0,
            ),
        )
        selfdestruct_contract_current_balance += i

        # Balance is always sent to other contracts
        if sendall_recipient != selfdestruct_contract_address:
            sendall_final_balances[sendall_recipient] += selfdestruct_contract_current_balance

        # Self-destructing contract must always have zero balance after the call because the
        # self-destruct always happens in the same transaction in this test
        selfdestruct_contract_current_balance = 0

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(Op.PUSH20(selfdestruct_contract_address)),
        )

    # Check the EXTCODE* properties of the self-destructing contract again
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(bytes(selfdestruct_code))),
        Op.EXTCODESIZE(Op.PUSH20(selfdestruct_contract_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes(selfdestruct_code))),
        Op.EXTCODEHASH(Op.PUSH20(selfdestruct_contract_address)),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(bytes(selfdestruct_contract_initcode)), 32), 1)

    post: Dict[str, Account] = {
        entry_code_address: Account(
            code="0x00",
            storage=entry_code_storage,
        ),
        initcode_copy_from_address: Account(
            code=selfdestruct_contract_initcode,
        ),
    }

    # Check the balances of the sendall recipients
    for address, balance in sendall_final_balances.items():
        post[address] = Account(balance=balance, storage={0: 1})

    post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=100_000,
        data=entry_code,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, txs=[tx])


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("call_times", [0, 1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.parametrize("self_destructing_initcode", [True], ids=[""])
@pytest.mark.valid_from("Shanghai")
def test_self_destructing_initcode(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict[str, Account],
    entry_code_address: str,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_address: str,
    sendall_recipient_addresses: List[str],
    initcode_copy_from_address: str,
    create_opcode: Op,
    call_times: int,  # Number of times to call the self-destructing contract in the same tx
    selfdestruct_contract_initial_balance: int,
):
    """
    Test that a contract can self-destruct in its initcode.

    Behavior is the same before and after EIP-6780.

    Test using:
        - Different initial balances for the self-destructing contract
        - Different opcodes: CREATE, CREATE2
        - Different number of calls to the self-destructing contract in the same tx
    """
    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()
    sendall_amount = 0

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_args = [
        0,  # Value
        0,  # Offset
        len(bytes(selfdestruct_contract_initcode)),  # Length
    ]
    if create_opcode == Op.CREATE2:
        # CREATE2 requires a salt argument
        create_args.append(0)
    create_bytecode = create_opcode(*create_args)

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            Op.PUSH20(initcode_copy_from_address),
            0,
            0,
            len(bytes(selfdestruct_contract_initcode)),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_bytecode,
        )
    )

    # Store the EXTCODE* properties of the created address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(0),
        Op.EXTCODESIZE(Op.PUSH20(selfdestruct_contract_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes())),
        Op.EXTCODEHASH(Op.PUSH20(selfdestruct_contract_address)),
    )

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                Op.PUSH20(selfdestruct_contract_address),  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(Op.PUSH20(selfdestruct_contract_address)),
        )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(bytes(selfdestruct_contract_initcode)), 32), 1)

    if selfdestruct_contract_initial_balance > 0:
        # Address where the contract is created already had some balance,
        # which must be included in the send-all operation
        sendall_amount += selfdestruct_contract_initial_balance

    post: Dict[str, Account] = {
        entry_code_address: Account(
            code="0x00",
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        initcode_copy_from_address: Account(
            code=selfdestruct_contract_initcode,
        ),
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=100_000,
        data=entry_code,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, txs=[tx])


@pytest.mark.parametrize("tx_value", [0, 100_000])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.parametrize("selfdestruct_contract_address", [compute_create_address(TestAddress, 0)])
@pytest.mark.parametrize("self_destructing_initcode", [True], ids=[""])
@pytest.mark.valid_from("Shanghai")
def test_self_destructing_initcode_create_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict[str, Account],
    tx_value: int,
    entry_code_address: str,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_address: str,
    sendall_recipient_addresses: List[str],
    initcode_copy_from_address: str,
    selfdestruct_contract_initial_balance: int,
):
    """
    Use a Create Transaction to execute a self-destructing initcode.

    Behavior should be the same before and after EIP-6780.

    Test using:
        - Different initial balances for the self-destructing contract
        - Different transaction value amounts
    """
    assert entry_code_address == selfdestruct_contract_address

    # Our entry point is an initcode that in turn creates a self-destructing contract
    sendall_amount = selfdestruct_contract_initial_balance + tx_value

    post: Dict[str, Account] = {
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        initcode_copy_from_address: Account(
            code=selfdestruct_contract_initcode,
        ),
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=tx_value,
        data=selfdestruct_contract_initcode,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, txs=[tx])


@pytest.mark.parametrize("create_opcode", [Op.CREATE2])  # Can only recreate using CREATE2
@pytest.mark.parametrize(
    "sendall_recipient_addresses",
    [
        pytest.param(
            [to_address(0x1000)],
            id="selfdestruct_other_address",
        ),
        pytest.param(
            [SELF_ADDRESS],
            id="selfdestruct_to_self",
        ),
    ],
)
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.parametrize("recreate_times", [1])
@pytest.mark.parametrize("call_times", [1])
@pytest.mark.valid_from("Shanghai")
def test_recreate_self_destructed_contract_different_txs(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Dict[str, Account],
    entry_code_address: str,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_address: str,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[str],
    initcode_copy_from_address: str,
    create_opcode: Op,
    recreate_times: int,  # Number of times to recreate the contract in different transactions
    call_times: int,  # Number of times to call the self-destructing contract in the same tx
):
    """
    Test that a contract can be recreated after it has self-destructed, over the lapse
    of multiple transactions.

    Behavior should be the same before and after EIP-6780.

    Test using:
        - Different initial balances for the self-destructing contract
        - CREATE2 only
    """
    entry_code_storage = Storage()
    sendall_amount = selfdestruct_contract_initial_balance

    # Bytecode used to create the contract
    assert create_opcode == Op.CREATE2, "cannot recreate contract using CREATE opcode"
    create_bytecode = Op.CREATE2(0, 0, len(bytes(selfdestruct_contract_initcode)), 0)

    # Entry code that will be executed, creates the contract and then calls it
    entry_code = (
        # Initcode is already deployed at initcode_copy_from_address, so just copy it
        Op.EXTCODECOPY(
            Op.PUSH20(initcode_copy_from_address),
            0,
            0,
            len(bytes(selfdestruct_contract_initcode)),
        )
        + Op.SSTORE(
            Op.CALLDATALOAD(0),
            create_bytecode,
        )
    )

    for i in range(call_times):
        entry_code += Op.CALL(
            Op.GASLIMIT,
            Op.PUSH20(selfdestruct_contract_address),
            i,
            0,
            0,
            0,
            0,
        )
        sendall_amount += i

    entry_code += Op.STOP

    txs: List[Transaction] = []
    nonce = count()
    for i in range(recreate_times + 1):
        txs.append(
            Transaction(
                ty=0x0,
                data=to_hash_bytes(i),
                chain_id=0x0,
                nonce=next(nonce),
                to=entry_code_address,
                gas_limit=100_000_000,
                gas_price=10,
                protected=False,
            )
        )
        entry_code_storage[i] = selfdestruct_contract_address

    pre[entry_code_address] = Account(code=entry_code)
    post: Dict[str, Account] = {
        entry_code_address: Account(
            code=entry_code,
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        initcode_copy_from_address: Account(
            code=selfdestruct_contract_initcode,
        ),
    }
    if sendall_recipient_addresses[0] != selfdestruct_contract_address:
        post[sendall_recipient_addresses[0]] = Account(balance=sendall_amount, storage={0: 1})

    blockchain_test(genesis_environment=env, pre=pre, post=post, blocks=[Block(txs=txs)])


@pytest.mark.parametrize(
    "call_times,sendall_recipient_addresses",
    [
        pytest.param(
            1,
            [to_address(0x1000)],
            id="single_call",
        ),
        pytest.param(
            1,
            [PRE_EXISTING_SELFDESTRUCT_ADDRESS],
            id="single_call_self_sendall_recipient",
        ),
        pytest.param(
            10,
            [to_address(0x1000)],
            id="multiple_calls_single_sendall_recipient",
        ),
        pytest.param(
            10,
            [to_address(0x1000), to_address(0x2000), to_address(0x3000)],
            id="multiple_calls_multiple_sendall_recipients",
        ),
        pytest.param(
            10,
            [PRE_EXISTING_SELFDESTRUCT_ADDRESS, to_address(0x2000), to_address(0x3000)],
            id="multiple_calls_multiple_sendall_recipients_including_self",
        ),
        pytest.param(
            10,
            [to_address(0x1000), to_address(0x2000), PRE_EXISTING_SELFDESTRUCT_ADDRESS],
            id="multiple_calls_multiple_sendall_recipients_including_self_different_order",
        ),
        pytest.param(
            3,
            [to_address(0x1000), to_address(0x2000), PRE_EXISTING_SELFDESTRUCT_ADDRESS],
            id="multiple_calls_multiple_sendall_recipients_including_self_last",
        ),
    ],
)
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.parametrize(
    "selfdestruct_contract_address", [PRE_EXISTING_SELFDESTRUCT_ADDRESS], ids=["pre_existing"]
)
@pytest.mark.valid_from("Shanghai")
def test_selfdestruct_pre_existing(
    state_test: StateTestFiller,
    eip_enabled: bool,
    env: Environment,
    pre: Dict[str, Account],
    entry_code_address: str,
    selfdestruct_contract_address: str,
    selfdestruct_code: SupportsBytes,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[str],
    call_times: int,
):
    """
    Test calling a previously created account that contains a selfdestruct, and verify its balance
    is sent to the destination address.

    After EIP-6780, the balance should be sent to the send-all recipient address, similar to
    the behavior before the EIP, but the account is not deleted.

    Test using:
        - Different send-all recipient addresses: single, multiple, including self
        - Different initial balances for the self-destructing contract
    """
    entry_code_storage = Storage()

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(sendall_recipient_addresses, [0] * len(sendall_recipient_addresses))
    )
    selfdestruct_contract_current_balance = selfdestruct_contract_initial_balance

    # Entry code in this case will simply call the pre-existing self-destructing contract,
    # as many times as required
    entry_code = b""

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    for i, sendall_recipient in zip(range(call_times), cycle(sendall_recipient_addresses)):
        entry_code += Op.MSTORE(0, Op.PUSH20(sendall_recipient))
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                Op.PUSH20(selfdestruct_contract_address),  # Address
                i,  # Value
                0,
                32,
                0,
                0,
            ),
        )
        selfdestruct_contract_current_balance += i

        # Balance is always sent to other contracts
        if sendall_recipient != selfdestruct_contract_address:
            sendall_final_balances[sendall_recipient] += selfdestruct_contract_current_balance

        # Balance is only kept by the self-destructing contract if we are sending to self and the
        # EIP is activated, otherwise the balance is destroyed
        if sendall_recipient != selfdestruct_contract_address or not eip_enabled:
            selfdestruct_contract_current_balance = 0

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_current_balance),
            Op.BALANCE(Op.PUSH20(selfdestruct_contract_address)),
        )

    # Check the EXTCODE* properties of the self-destructing contract
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(bytes(selfdestruct_code))),
        Op.EXTCODESIZE(Op.PUSH20(selfdestruct_contract_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes(selfdestruct_code))),
        Op.EXTCODEHASH(Op.PUSH20(selfdestruct_contract_address)),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(32, 1)

    post: Dict[str, Account] = {
        entry_code_address: Account(
            code="0x00",
            storage=entry_code_storage,
        ),
    }

    # Check the balances of the sendall recipients
    for address, balance in sendall_final_balances.items():
        if address != selfdestruct_contract_address:
            post[address] = Account(balance=balance, storage={0: 1})

    if eip_enabled:
        balance = selfdestruct_contract_current_balance
        post[selfdestruct_contract_address] = Account(
            balance=balance,
            code=selfdestruct_code,
            storage={0: call_times},
        )
    else:
        post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=100_000,
        data=entry_code,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, txs=[tx])


@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("call_times", [1, 10])
@pytest.mark.parametrize(
    "selfdestruct_contract_address,entry_code_address",
    [(compute_create_address(TestAddress, 0), compute_create_address(TestAddress, 1))],
)
@pytest.mark.valid_from("Shanghai")
def test_selfdestruct_created_same_block_different_tx(
    blockchain_test: BlockchainTestFiller,
    eip_enabled: bool,
    env: Environment,
    pre: Dict[str, Account],
    entry_code_address: str,
    selfdestruct_contract_address: str,
    selfdestruct_code: SupportsBytes,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[str],
    call_times: int,
):
    """
    Test that if an account created in the same block that contains a selfdestruct is
    called, its balance is sent to the send-all address, but the account is not deleted.
    """
    entry_code_storage = Storage()
    sendall_amount = selfdestruct_contract_initial_balance
    entry_code = b""

    # Entry code in this case will simply call the pre-existing self-destructing contract,
    # as many times as required

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                Op.PUSH20(selfdestruct_contract_address),  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )

        sendall_amount += i

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(Op.PUSH20(selfdestruct_contract_address)),
        )

    # Check the EXTCODE* properties of the self-destructing contract
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(bytes(selfdestruct_code))),
        Op.EXTCODESIZE(Op.PUSH20(selfdestruct_contract_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes(selfdestruct_code))),
        Op.EXTCODEHASH(Op.PUSH20(selfdestruct_contract_address)),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(32, 1)

    post: Dict[str, Account] = {
        entry_code_address: Account(
            code="0x00",
            storage=entry_code_storage,
        ),
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    if eip_enabled:
        post[selfdestruct_contract_address] = Account(
            balance=0, code=selfdestruct_code, storage={0: call_times}
        )
    else:
        post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    nonce = count()
    txs = [
        Transaction(
            ty=0x0,
            value=0,
            data=selfdestruct_contract_initcode,
            chain_id=0x0,
            nonce=next(nonce),
            to=None,
            gas_limit=100_000_000,
            gas_price=10,
            protected=False,
        ),
        Transaction(
            ty=0x0,
            value=100_000,
            data=entry_code,
            chain_id=0x0,
            nonce=next(nonce),
            to=None,
            gas_limit=100_000_000,
            gas_price=10,
            protected=False,
        ),
    ]

    blockchain_test(genesis_environment=env, pre=pre, post=post, blocks=[Block(txs=txs)])


@pytest.mark.parametrize(
    "selfdestruct_code",
    [
        pytest.param(
            Op.DELEGATECALL(
                Op.GAS,
                Op.PUSH20(PRE_EXISTING_SELFDESTRUCT_ADDRESS),
                0,
                0,
                0,
                0,
            ),
            id="delegatecall",
        ),
        pytest.param(
            Op.CALLCODE(
                Op.GAS,
                Op.PUSH20(PRE_EXISTING_SELFDESTRUCT_ADDRESS),
                0,
                0,
                0,
                0,
                0,
            ),
            id="callcode",
        ),
    ],
)  # The self-destruct code is delegatecall
@pytest.mark.parametrize("call_times", [1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("create_opcode", [Op.CREATE])
@pytest.mark.valid_from("Shanghai")
def test_delegatecall_from_new_contract_to_pre_existing_contract(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict[str, Account],
    entry_code_address: str,
    selfdestruct_code: SupportsBytes,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_address: str,
    sendall_recipient_addresses: List[str],
    initcode_copy_from_address: str,
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
):
    """
    Test that if an account created in the current transaction delegate-call a previously created
    account that executes self-destruct, the calling account is deleted.
    """
    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()
    sendall_amount = 0

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_args = [
        0,  # Value
        0,  # Offset
        len(bytes(selfdestruct_contract_initcode)),  # Length
    ]
    if create_opcode == Op.CREATE2:
        # CREATE2 requires a salt argument
        create_args.append(0)
    create_bytecode = create_opcode(*create_args)

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            Op.PUSH20(initcode_copy_from_address),
            0,
            0,
            len(bytes(selfdestruct_contract_initcode)),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_bytecode,
        )
    )

    # Store the EXTCODE* properties of the created address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(bytes(selfdestruct_code))),
        Op.EXTCODESIZE(Op.PUSH20(selfdestruct_contract_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes(selfdestruct_code))),
        Op.EXTCODEHASH(Op.PUSH20(selfdestruct_contract_address)),
    )

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                Op.PUSH20(selfdestruct_contract_address),  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )

        sendall_amount += i

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(Op.PUSH20(selfdestruct_contract_address)),
        )

    # Check the EXTCODE* properties of the self-destructing contract again
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(bytes(selfdestruct_code))),
        Op.EXTCODESIZE(Op.PUSH20(selfdestruct_contract_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes(selfdestruct_code))),
        Op.EXTCODEHASH(Op.PUSH20(selfdestruct_contract_address)),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(bytes(selfdestruct_contract_initcode)), 32), 1)

    if selfdestruct_contract_initial_balance > 0:
        # Address where the contract is created already had some balance,
        # which must be included in the send-all operation
        sendall_amount += selfdestruct_contract_initial_balance

    post: Dict[str, Account] = {
        entry_code_address: Account(
            code="0x00",
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        initcode_copy_from_address: Account(
            code=selfdestruct_contract_initcode,
        ),
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=100_000,
        data=entry_code,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, txs=[tx])


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@pytest.mark.parametrize("call_times", [1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.valid_from("Shanghai")
def test_delegatecall_from_pre_existing_contract_to_new_contract(
    state_test: StateTestFiller,
    eip_enabled: bool,
    env: Environment,
    pre: Dict[str, Account],
    entry_code_address: str,
    selfdestruct_code: SupportsBytes,
    selfdestruct_contract_initcode: SupportsBytes,
    selfdestruct_contract_address: str,
    sendall_recipient_addresses: List[str],
    initcode_copy_from_address: str,
    call_opcode: Op,
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
):
    """
    Test that if an account created in the current transaction contains a self-destruct and is
    delegate-called by an account created before the current transaction, the calling account
    is not deleted.
    """
    # Add the contract that delegate calls to the newly created contract
    delegate_caller_address = "0x2222222222222222222222222222222222222222"
    call_args: List[int | bytes] = [
        Op.GAS(),
        Op.PUSH20(selfdestruct_contract_address),
        0,
        0,
        0,
        0,
    ]
    if call_opcode == Op.CALLCODE:
        # CALLCODE requires `value`
        call_args.append(0)
    delegate_caller_code = call_opcode(*call_args)
    pre[delegate_caller_address] = Account(code=delegate_caller_code)

    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()
    sendall_amount = 0

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_args = [
        0,  # Value
        0,  # Offset
        len(bytes(selfdestruct_contract_initcode)),  # Length
    ]
    if create_opcode == Op.CREATE2:
        # CREATE2 requires a salt argument
        create_args.append(0)
    create_bytecode = create_opcode(*create_args)

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            Op.PUSH20(initcode_copy_from_address),
            0,
            0,
            len(bytes(selfdestruct_contract_initcode)),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_bytecode,
        )
    )

    # Store the EXTCODE* properties of the pre-existing address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(delegate_caller_code)),
        Op.EXTCODESIZE(Op.PUSH20(delegate_caller_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(delegate_caller_code)),
        Op.EXTCODEHASH(Op.PUSH20(delegate_caller_address)),
    )

    # Now instead of calling the newly created contract directly, we delegate call to it
    # from a pre-existing contract, and the contract must not self-destruct
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                Op.PUSH20(delegate_caller_address),  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )

        sendall_amount += i

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(Op.PUSH20(delegate_caller_address)),
        )

    # Check the EXTCODE* properties of the pre-existing address again
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(bytes(delegate_caller_code))),
        Op.EXTCODESIZE(Op.PUSH20(delegate_caller_address)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(keccak256(bytes(delegate_caller_code))),
        Op.EXTCODEHASH(Op.PUSH20(delegate_caller_address)),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(bytes(selfdestruct_contract_initcode)), 32), 1)

    post: Dict[str, Account] = {
        entry_code_address: Account(
            code="0x00",
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account(
            code=selfdestruct_code, balance=selfdestruct_contract_initial_balance
        ),
        initcode_copy_from_address: Account(
            code=selfdestruct_contract_initcode,
        ),
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    if eip_enabled:
        post[delegate_caller_address] = Account(code=delegate_caller_code, balance=0)
    else:
        post[delegate_caller_address] = Account.NONEXISTENT  # type: ignore

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=100_000,
        data=entry_code,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, txs=[tx])
