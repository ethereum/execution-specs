"""
abstract: Tests [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780)
    Tests for [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780).

"""  # noqa: E501

from itertools import cycle
from typing import Dict, List

import pytest

from ethereum_test_forks import Cancun, Fork
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Hash,
    Initcode,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools.code.generators import Conditional
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "2f8299df31bb8173618901a03a8366a3183479b0"

SELFDESTRUCT_DISABLE_FORK = Cancun

"""
Address of a pre-existing contract that self-destructs.
"""

# Sentinel value to indicate that the self-destructing contract address should be used, only for
# use in `pytest.mark.parametrize`, not for use within the test method itself.
SELF_ADDRESS = Address(0x01)
# Sentinel value to indicate that the contract should not self-destruct.
NO_SELFDESTRUCT = Address(0x00)

PRE_DEPLOY_CONTRACT_1 = "pre_deploy_contract_1"
PRE_DEPLOY_CONTRACT_2 = "pre_deploy_contract_2"
PRE_DEPLOY_CONTRACT_3 = "pre_deploy_contract_3"


@pytest.fixture
def eip_enabled(fork: Fork) -> bool:
    """Whether the EIP is enabled or not."""
    return fork >= SELFDESTRUCT_DISABLE_FORK


@pytest.fixture
def env() -> Environment:
    """Environment for all tests."""
    return Environment(
        fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
    )


@pytest.fixture
def sendall_recipient_addresses(request: pytest.FixtureRequest, pre: Alloc) -> List[Address]:
    """
    List of addresses that receive the SENDALL operation in any test.

    If the test case requires a pre-existing contract, it will be deployed here.

    By default the list is a single pre-deployed contract that unconditionally sets storage.
    """
    address_list = getattr(request, "param", [PRE_DEPLOY_CONTRACT_1])
    deployed_contracts: Dict[str, Address] = {}
    return_list = []
    for sendall_recipient in address_list:
        if type(sendall_recipient) is str:
            if sendall_recipient not in deployed_contracts:
                deployed_contracts[sendall_recipient] = pre.deploy_contract(
                    code=Op.SSTORE(0, 0),
                    storage={0: 1},
                )
            return_list.append(deployed_contracts[sendall_recipient])
        else:
            return_list.append(sendall_recipient)
    return return_list


def selfdestruct_code_preset(
    *,
    sendall_recipient_addresses: List[Address],
) -> Bytecode:
    """Return a bytecode that self-destructs."""
    # First we register entry into the contract
    bytecode = Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))

    if len(sendall_recipient_addresses) != 1:
        # Load the recipient address from calldata, each test case needs to pass the addresses as
        # calldata
        bytecode += Conditional(
            # We avoid having the caller to give us our own address by checking
            # against a constant that is a magic number
            condition=Op.EQ(Op.CALLDATALOAD(0), SELF_ADDRESS),
            if_true=Op.MSTORE(0, Op.ADDRESS()),
            if_false=Op.MSTORE(0, Op.CALLDATALOAD(0)),
        )
        bytecode += Conditional(
            condition=Op.EQ(Op.MLOAD(0), NO_SELFDESTRUCT),
            if_true=Op.STOP,
            if_false=Op.SELFDESTRUCT(Op.MLOAD(0)),
        )
    else:
        # Hard-code the single only possible recipient address
        sendall_recipient = sendall_recipient_addresses[0]
        assert sendall_recipient != NO_SELFDESTRUCT, "test error"
        if sendall_recipient == SELF_ADDRESS:
            bytecode += Op.SELFDESTRUCT(Op.ADDRESS)
        else:
            bytecode += Op.SELFDESTRUCT(sendall_recipient_addresses[0])
        bytecode += Op.SSTORE(0, 0)
    return bytecode + Op.STOP


@pytest.fixture
def selfdestruct_code(
    sendall_recipient_addresses: List[Address],
) -> Bytecode:
    """
    Create default self-destructing bytecode,
    which can be modified by each test if necessary.
    """
    return selfdestruct_code_preset(sendall_recipient_addresses=sendall_recipient_addresses)


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """EOA that will be used to send transactions."""
    return pre.fund_eoa()


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "call_times,sendall_recipient_addresses",
    [
        pytest.param(
            1,
            [PRE_DEPLOY_CONTRACT_1],
            id="single_call",
        ),
        pytest.param(
            1,
            [SELF_ADDRESS],
            id="single_call_self",
        ),
        pytest.param(
            2,
            [PRE_DEPLOY_CONTRACT_1],
            id="multiple_calls_single_sendall_recipient",
        ),
        pytest.param(
            2,
            [SELF_ADDRESS],
            id="multiple_calls_single_self_recipient",
        ),
        pytest.param(
            3,
            [PRE_DEPLOY_CONTRACT_1, PRE_DEPLOY_CONTRACT_2, PRE_DEPLOY_CONTRACT_3],
            id="multiple_calls_multiple_sendall_recipients",
        ),
        pytest.param(
            3,
            [SELF_ADDRESS, PRE_DEPLOY_CONTRACT_2, PRE_DEPLOY_CONTRACT_3],
            id="multiple_calls_multiple_sendall_recipients_including_self",
        ),
        pytest.param(
            3,
            [PRE_DEPLOY_CONTRACT_1, PRE_DEPLOY_CONTRACT_2, SELF_ADDRESS],
            id="multiple_calls_multiple_sendall_recipients_including_self_last",
        ),
        pytest.param(
            6,
            [SELF_ADDRESS, PRE_DEPLOY_CONTRACT_2, PRE_DEPLOY_CONTRACT_3],
            id="multiple_calls_multiple_repeating_sendall_recipients_including_self",
        ),
        pytest.param(
            6,
            [PRE_DEPLOY_CONTRACT_1, PRE_DEPLOY_CONTRACT_2, SELF_ADDRESS],
            id="multiple_calls_multiple_repeating_sendall_recipients_including_self_last",
        ),
    ],
    indirect=["sendall_recipient_addresses"],
)
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_create_selfdestruct_same_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
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
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_contract_initcode)
    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_bytecode = create_opcode(size=len(selfdestruct_contract_initcode))
    selfdestruct_contract_address = compute_create_address(
        address=compute_create_address(address=sender, nonce=0),
        nonce=1,
        initcode=selfdestruct_contract_initcode,
        opcode=create_opcode,
    )
    for i in range(len(sendall_recipient_addresses)):
        if sendall_recipient_addresses[i] == SELF_ADDRESS:
            sendall_recipient_addresses[i] = selfdestruct_contract_address
    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(selfdestruct_contract_address, selfdestruct_contract_initial_balance)

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(sendall_recipient_addresses, [0] * len(sendall_recipient_addresses), strict=False)
    )
    selfdestruct_contract_current_balance = selfdestruct_contract_initial_balance

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            initcode_copy_from_address,
            0,
            0,
            len(selfdestruct_contract_initcode),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_bytecode,
        )
    )

    # Store the EXTCODE* properties of the created address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    entry_code_balance = 0
    for i, sendall_recipient in zip(range(call_times), cycle(sendall_recipient_addresses)):
        entry_code += Op.MSTORE(0, sendall_recipient)
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                selfdestruct_contract_address,  # Address
                i,  # Value
                0,
                32,
                0,
                0,
            ),
        )
        entry_code_balance += i
        selfdestruct_contract_current_balance += i

        # Balance is always sent to other contracts
        if sendall_recipient != selfdestruct_contract_address:
            sendall_final_balances[sendall_recipient] += selfdestruct_contract_current_balance

        # Self-destructing contract must always have zero balance after the call because the
        # self-destruct always happens in the same transaction in this test
        selfdestruct_contract_current_balance = 0

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(selfdestruct_contract_address),
        )

    # Check the EXTCODE* properties of the self-destructing contract again
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_contract_initcode), 32), 1)

    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=500_000,
    )

    entry_code_address = tx.created_contract

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
    }

    # Check the balances of the sendall recipients
    for address, balance in sendall_final_balances.items():
        post[address] = Account(balance=balance, storage={0: 1})

    post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("call_times", [0, 1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_self_destructing_initcode(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
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
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_code)
    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()
    sendall_amount = 0

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_bytecode = create_opcode(size=len(selfdestruct_code))

    selfdestruct_contract_address = compute_create_address(
        address=compute_create_address(address=sender, nonce=0),
        nonce=1,
        initcode=selfdestruct_code,
        opcode=create_opcode,
    )

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            initcode_copy_from_address,
            0,
            0,
            len(selfdestruct_code),
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
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(Bytecode().keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    entry_code_balance = 0
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                selfdestruct_contract_address,  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )
        entry_code_balance += i

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(selfdestruct_contract_address),
        )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_code), 32), 1)

    if selfdestruct_contract_initial_balance > 0:
        # Address where the contract is created already had some balance,
        # which must be included in the send-all operation
        sendall_amount += selfdestruct_contract_initial_balance
        pre.fund_address(selfdestruct_contract_address, selfdestruct_contract_initial_balance)

    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=500_000,
    )

    entry_code_address = tx.created_contract

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("tx_value", [0, 100_000])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_self_destructing_initcode_create_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    tx_value: int,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    selfdestruct_contract_initial_balance: int,
):
    """
    Use a Create Transaction to execute a self-destructing initcode.

    Behavior should be the same before and after EIP-6780.

    Test using:
        - Different initial balances for the self-destructing contract
        - Different transaction value amounts
    """
    tx = Transaction(
        sender=sender,
        value=tx_value,
        data=selfdestruct_code,
        to=None,
        gas_limit=500_000,
    )
    selfdestruct_contract_address = tx.created_contract
    pre.fund_address(selfdestruct_contract_address, selfdestruct_contract_initial_balance)

    # Our entry point is an initcode that in turn creates a self-destructing contract
    sendall_amount = selfdestruct_contract_initial_balance + tx_value

    post: Dict[Address, Account] = {
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE2])  # Can only recreate using CREATE2
@pytest.mark.parametrize(
    "sendall_recipient_addresses",
    [
        pytest.param(
            [PRE_DEPLOY_CONTRACT_1],
            id="selfdestruct_other_address",
        ),
        pytest.param(
            [SELF_ADDRESS],
            id="selfdestruct_to_self",
        ),
    ],
    indirect=["sendall_recipient_addresses"],
)
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.parametrize("recreate_times", [1])
@pytest.mark.parametrize("call_times", [1])
@pytest.mark.valid_from("Shanghai")
def test_recreate_self_destructed_contract_different_txs(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[Address],
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
        - Contract creating opcodes that are not CREATE
    """
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_contract_initcode)
    entry_code_storage = Storage()
    sendall_amount = selfdestruct_contract_initial_balance

    # Bytecode used to create the contract
    assert create_opcode != Op.CREATE, "cannot recreate contract using CREATE opcode"
    create_bytecode = create_opcode(size=len(selfdestruct_contract_initcode))

    # Entry code that will be executed, creates the contract and then calls it
    entry_code = (
        # Initcode is already deployed at initcode_copy_from_address, so just copy it
        Op.EXTCODECOPY(
            initcode_copy_from_address,
            0,
            0,
            len(selfdestruct_contract_initcode),
        )
        + Op.MSTORE(0, create_bytecode)
        + Op.SSTORE(
            Op.CALLDATALOAD(0),
            Op.MLOAD(0),
        )
    )

    for i in range(call_times):
        entry_code += Op.CALL(
            Op.GASLIMIT,
            Op.MLOAD(0),
            i,
            0,
            0,
            0,
            0,
        )
        sendall_amount += i

    entry_code += Op.STOP

    entry_code_address = pre.deploy_contract(code=entry_code)
    selfdestruct_contract_address = compute_create_address(
        address=entry_code_address, initcode=selfdestruct_contract_initcode, opcode=create_opcode
    )
    pre.fund_address(selfdestruct_contract_address, selfdestruct_contract_initial_balance)
    for i in range(len(sendall_recipient_addresses)):
        if sendall_recipient_addresses[i] == SELF_ADDRESS:
            sendall_recipient_addresses[i] = selfdestruct_contract_address

    txs: List[Transaction] = []
    for i in range(recreate_times + 1):
        txs.append(
            Transaction(
                data=Hash(i),
                sender=sender,
                to=entry_code_address,
                gas_limit=500_000,
            )
        )
        entry_code_storage[i] = selfdestruct_contract_address

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
    }
    if sendall_recipient_addresses[0] != selfdestruct_contract_address:
        post[sendall_recipient_addresses[0]] = Account(balance=sendall_amount, storage={0: 1})

    blockchain_test(genesis_environment=env, pre=pre, post=post, blocks=[Block(txs=txs)])


@pytest.mark.parametrize(
    "call_times,sendall_recipient_addresses",
    [
        pytest.param(
            1,
            [PRE_DEPLOY_CONTRACT_1],
            id="single_call",
        ),
        pytest.param(
            1,
            [SELF_ADDRESS],
            id="single_call_self",
        ),
        pytest.param(
            2,
            [PRE_DEPLOY_CONTRACT_1],
            id="multiple_calls_single_sendall_recipient",
        ),
        pytest.param(
            2,
            [SELF_ADDRESS],
            id="multiple_calls_single_self_recipient",
        ),
        pytest.param(
            3,
            [PRE_DEPLOY_CONTRACT_1, PRE_DEPLOY_CONTRACT_2, PRE_DEPLOY_CONTRACT_3],
            id="multiple_calls_multiple_sendall_recipients",
        ),
        pytest.param(
            3,
            [SELF_ADDRESS, PRE_DEPLOY_CONTRACT_2, PRE_DEPLOY_CONTRACT_3],
            id="multiple_calls_multiple_sendall_recipients_including_self",
        ),
        pytest.param(
            3,
            [PRE_DEPLOY_CONTRACT_1, PRE_DEPLOY_CONTRACT_2, SELF_ADDRESS],
            id="multiple_calls_multiple_sendall_recipients_including_self_last",
        ),
        pytest.param(
            6,
            [SELF_ADDRESS, PRE_DEPLOY_CONTRACT_2, PRE_DEPLOY_CONTRACT_3],
            id="multiple_calls_multiple_repeating_sendall_recipients_including_self",
        ),
        pytest.param(
            6,
            [PRE_DEPLOY_CONTRACT_1, PRE_DEPLOY_CONTRACT_2, SELF_ADDRESS],
            id="multiple_calls_multiple_repeating_sendall_recipients_including_self_last",
        ),
    ],
    indirect=["sendall_recipient_addresses"],
)
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_selfdestruct_pre_existing(
    state_test: StateTestFiller,
    eip_enabled: bool,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[Address],
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
    selfdestruct_contract_address = pre.deploy_contract(selfdestruct_code)
    entry_code_storage = Storage()

    for i in range(len(sendall_recipient_addresses)):
        if sendall_recipient_addresses[i] == SELF_ADDRESS:
            sendall_recipient_addresses[i] = selfdestruct_contract_address
    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(selfdestruct_contract_address, selfdestruct_contract_initial_balance)

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(sendall_recipient_addresses, [0] * len(sendall_recipient_addresses), strict=False)
    )
    selfdestruct_contract_current_balance = selfdestruct_contract_initial_balance

    # Entry code in this case will simply call the pre-existing self-destructing contract,
    # as many times as required
    entry_code = Bytecode()

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    entry_code_balance = 0
    for i, sendall_recipient in zip(range(call_times), cycle(sendall_recipient_addresses)):
        entry_code += Op.MSTORE(0, sendall_recipient)
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                selfdestruct_contract_address,  # Address
                i,  # Value
                0,
                32,
                0,
                0,
            ),
        )
        entry_code_balance += i
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
            Op.BALANCE(selfdestruct_contract_address),
        )

    # Check the EXTCODE* properties of the self-destructing contract
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(32, 1)

    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=500_000,
    )

    entry_code_address = tx.created_contract

    post: Dict[Address, Account] = {
        entry_code_address: Account(
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
            storage={0: call_times},
        )
    else:
        post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("call_times", [1, 10])
@pytest.mark.valid_from("Shanghai")
def test_selfdestruct_created_same_block_different_tx(
    blockchain_test: BlockchainTestFiller,
    eip_enabled: bool,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[Address],
    call_times: int,
):
    """
    Test that if an account created in the same block that contains a selfdestruct is
    called, its balance is sent to the send-all address, but the account is not deleted.
    """
    selfdestruct_code = selfdestruct_code_preset(
        sendall_recipient_addresses=sendall_recipient_addresses,
    )
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    selfdestruct_contract_address = compute_create_address(address=sender, nonce=0)
    entry_code_address = compute_create_address(address=sender, nonce=1)
    entry_code_storage = Storage()
    sendall_amount = selfdestruct_contract_initial_balance
    entry_code = Bytecode()

    # Entry code in this case will simply call the pre-existing self-destructing contract,
    # as many times as required

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    entry_code_balance = 0
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                selfdestruct_contract_address,  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )
        entry_code_balance += i
        sendall_amount += i

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(selfdestruct_contract_address),
        )

    # Check the EXTCODE* properties of the self-destructing contract
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(32, 1)

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    if eip_enabled:
        post[selfdestruct_contract_address] = Account(balance=0, storage={0: call_times})
    else:
        post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    txs = [
        Transaction(
            value=selfdestruct_contract_initial_balance,
            data=selfdestruct_contract_initcode,
            sender=sender,
            to=None,
            gas_limit=500_000,
        ),
        Transaction(
            value=entry_code_balance,
            data=entry_code,
            sender=sender,
            to=None,
            gas_limit=500_000,
        ),
    ]

    blockchain_test(genesis_environment=env, pre=pre, post=post, blocks=[Block(txs=txs)])


@pytest.mark.parametrize("call_times", [1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@pytest.mark.parametrize("create_opcode", [Op.CREATE])
@pytest.mark.valid_from("Shanghai")
def test_calling_from_new_contract_to_pre_existing_contract(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    sendall_recipient_addresses: List[Address],
    create_opcode: Op,
    call_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
):
    """
    Test that if an account created in the current transaction delegate-call a previously created
    account that executes self-destruct, the calling account is deleted.
    """
    pre_existing_selfdestruct_address = pre.deploy_contract(
        selfdestruct_code_preset(
            sendall_recipient_addresses=sendall_recipient_addresses,
        ),
    )
    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()
    sendall_amount = 0

    entry_code_address = compute_create_address(address=sender, nonce=0)
    selfdestruct_contract_address = compute_create_address(address=entry_code_address, nonce=1)

    pre.fund_address(selfdestruct_contract_address, selfdestruct_contract_initial_balance)

    # self-destructing call
    selfdestruct_code = call_opcode(address=pre_existing_selfdestruct_address)
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_contract_initcode)

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_bytecode = create_opcode(size=len(selfdestruct_contract_initcode))

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            initcode_copy_from_address,
            0,
            0,
            len(selfdestruct_contract_initcode),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_bytecode,
        )
    )

    # Store the EXTCODE* properties of the created address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    entry_code_balance = 0
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                selfdestruct_contract_address,  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )
        entry_code_balance += i
        sendall_amount += i

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(selfdestruct_contract_address),
        )

    # Check the EXTCODE* properties of the self-destructing contract again
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_contract_initcode), 32), 1)

    if selfdestruct_contract_initial_balance > 0:
        # Address where the contract is created already had some balance,
        # which must be included in the send-all operation
        sendall_amount += selfdestruct_contract_initial_balance

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=500_000,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@pytest.mark.parametrize("call_times", [1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("pre_existing_contract_initial_balance", [0, 1])
@pytest.mark.valid_from("Shanghai")
def test_calling_from_pre_existing_contract_to_new_contract(
    state_test: StateTestFiller,
    eip_enabled: bool,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    call_opcode: Op,
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
    pre_existing_contract_initial_balance: int,
):
    """
    Test that if an account created in the current transaction contains a self-destruct and is
    delegate-called by an account created before the current transaction, the calling account
    is not deleted.
    """
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(
        selfdestruct_contract_initcode,
    )

    selfdestruct_contract_address = compute_create_address(
        address=compute_create_address(address=sender, nonce=0),
        nonce=1,
        salt=0,
        initcode=selfdestruct_contract_initcode,
        opcode=create_opcode,
    )

    # Add the contract that delegate calls to the newly created contract
    caller_code = Op.SSTORE(1, Op.ADD(Op.SLOAD(1), 1)) + call_opcode(
        address=selfdestruct_contract_address
    )
    caller_address = pre.deploy_contract(
        caller_code,
        balance=pre_existing_contract_initial_balance,
    )

    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()
    sendall_amount = pre_existing_contract_initial_balance

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            initcode_copy_from_address,
            0,
            0,
            len(selfdestruct_contract_initcode),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_opcode(
                value=selfdestruct_contract_initial_balance,
                size=len(selfdestruct_contract_initcode),
            ),
        )
    )

    # Store the EXTCODE* properties of the pre-existing address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(caller_code)),
        Op.EXTCODESIZE(caller_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(caller_code.keccak256()),
        Op.EXTCODEHASH(caller_address),
    )

    # Now instead of calling the newly created contract directly, we delegate call to it
    # from a pre-existing contract, and the contract must not self-destruct
    entry_code_balance = selfdestruct_contract_initial_balance
    for i in range(call_times):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                caller_address,  # Address
                i,  # Value
                0,
                0,
                0,
                0,
            ),
        )
        entry_code_balance += i
        sendall_amount += i

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(caller_address),
        )

    # Check the EXTCODE* properties of the pre-existing address again
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(caller_code)),
        Op.EXTCODESIZE(caller_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(caller_code.keccak256()),
        Op.EXTCODEHASH(caller_address),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_contract_initcode), 32), 1)

    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=500_000,
    )

    entry_code_address = tx.created_contract

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        sendall_recipient_addresses[0]: Account(balance=sendall_amount, storage={0: 1}),
    }

    if eip_enabled:
        post[caller_address] = Account(
            storage={
                0: call_times,
                1: call_times,
            },
            balance=0,
        )
    else:
        post[caller_address] = Account.NONEXISTENT  # type: ignore

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.parametrize(
    "call_times,sendall_recipient_addresses",
    [
        pytest.param(1, [PRE_DEPLOY_CONTRACT_1], id="single_call"),
        pytest.param(5, [PRE_DEPLOY_CONTRACT_1], id="multiple_calls_single beneficiary"),
    ],
    indirect=["sendall_recipient_addresses"],
)
@pytest.mark.valid_from("Shanghai")
def test_create_selfdestruct_same_tx_increased_nonce(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
):
    """
    Verify that a contract can self-destruct if it was created in the same transaction, even when
    its nonce has been increased due to contract creation.
    """
    initcode = Op.RETURN(0, 1)
    selfdestruct_pre_bytecode = Op.MSTORE(0, Op.PUSH32(bytes(initcode))) + Op.POP(
        Op.CREATE(offset=32 - len(initcode), size=len(initcode))
    )
    selfdestruct_code = selfdestruct_pre_bytecode + selfdestruct_code
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_contract_initcode)

    selfdestruct_contract_address = compute_create_address(
        address=compute_create_address(address=sender, nonce=0),
        nonce=1,
        initcode=selfdestruct_contract_initcode,
        opcode=create_opcode,
    )
    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(selfdestruct_contract_address, selfdestruct_contract_initial_balance)
    # Our entry point is an initcode that in turn creates a self-destructing contract
    entry_code_storage = Storage()

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(sendall_recipient_addresses, [0] * len(sendall_recipient_addresses), strict=False)
    )
    selfdestruct_contract_current_balance = selfdestruct_contract_initial_balance

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_bytecode = create_opcode(size=len(selfdestruct_contract_initcode))

    # Entry code that will be executed, creates the contract and then calls it in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just copy it
        Op.EXTCODECOPY(
            initcode_copy_from_address,
            0,
            0,
            len(selfdestruct_contract_initcode),
        )
        # And we store the created address for verification purposes
        + Op.SSTORE(
            entry_code_storage.store_next(selfdestruct_contract_address),
            create_bytecode,
        )
    )

    # Store the EXTCODE* properties of the created address
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Call the self-destructing contract multiple times as required, increasing the wei sent each
    # time
    entry_code_balance = 0
    for i, sendall_recipient in zip(range(call_times), cycle(sendall_recipient_addresses)):
        entry_code += Op.MSTORE(0, sendall_recipient)
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,  # Gas
                selfdestruct_contract_address,  # Address
                i,  # Value
                0,
                32,
                0,
                0,
            ),
        )
        entry_code_balance += i
        selfdestruct_contract_current_balance += i

        # Balance is always sent to other contracts
        if sendall_recipient != selfdestruct_contract_address:
            sendall_final_balances[sendall_recipient] += selfdestruct_contract_current_balance

        # Self-destructing contract must always have zero balance after the call because the
        # self-destruct always happens in the same transaction in this test
        selfdestruct_contract_current_balance = 0

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(selfdestruct_contract_address),
        )

    # Check the EXTCODE* properties of the self-destructing contract again
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(len(selfdestruct_code)),
        Op.EXTCODESIZE(selfdestruct_contract_address),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(selfdestruct_code.keccak256()),
        Op.EXTCODEHASH(selfdestruct_contract_address),
    )

    # Lastly return zero so the entry point contract is created and we can retain the stored
    # values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_contract_initcode), 32), 1)

    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=1_000_000,
    )

    entry_code_address = tx.created_contract

    post: Dict[Address, Account] = {
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

    # Check the new contracts created from the self-destructing contract were correctly created.
    for address in [
        compute_create_address(address=selfdestruct_contract_address, nonce=i + 1)
        for i in range(call_times)
    ]:
        post[address] = Account(
            code=b"\x00",
        )

    post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    state_test(env=env, pre=pre, post=post, tx=tx)
