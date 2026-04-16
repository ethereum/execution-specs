"""
SELFDESTRUCT only in same transaction tests.

Tests for [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780).
"""

from itertools import cycle
from typing import Dict, List

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Conditional,
    Fork,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Cancun

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "1b6a0e94cc47e859b9866e570391cf37dc55059a"

SELFDESTRUCT_DISABLE_FORK = Cancun

"""
Address of a pre-existing contract that self-destructs.
"""

# Sentinel value to indicate that the self-destructing contract address should
# be used, only for use in `pytest.mark.parametrize`, not for use within the
# test method itself.
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
def sendall_recipient_addresses(
    request: pytest.FixtureRequest, pre: Alloc
) -> List[Address]:
    """
    List of addresses that receive the SENDALL operation in any test.

    If the test case requires a pre-existing contract, it will be deployed
    here.

    By default the list is a single pre-deployed contract that unconditionally
    sets storage.
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
        # Load the recipient address from calldata, each test case needs to
        # pass the addresses as calldata
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
    Create default self-destructing bytecode, which can be modified by each
    test if necessary.
    """
    return selfdestruct_code_preset(
        sendall_recipient_addresses=sendall_recipient_addresses
    )


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
            [
                PRE_DEPLOY_CONTRACT_1,
                PRE_DEPLOY_CONTRACT_2,
                PRE_DEPLOY_CONTRACT_3,
            ],
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
@pytest.mark.parametrize(
    "selfdestruct_contract_initial_balance",
    [0, 100_000],
)
@pytest.mark.valid_from("Shanghai")
def test_create_selfdestruct_same_tx(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Use CREATE or CREATE2 to create a self-destructing contract, and call it in
    the same transaction.

    Behavior should be the same before and after EIP-6780.

    Test using:
        - Different send-all recipient addresses: single, multiple,
           including self
        - Different initial balances for the self-destructing contract
        - Different opcodes: CREATE, CREATE2
    """
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(
        selfdestruct_contract_initcode
    )
    # Our entry point is an initcode that in turn creates a self-destructing
    # contract
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
        pre.fund_address(
            selfdestruct_contract_address,
            selfdestruct_contract_initial_balance,
        )

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(
            sendall_recipient_addresses,
            [0] * len(sendall_recipient_addresses),
            strict=False,
        )
    )
    selfdestruct_contract_current_balance = (
        selfdestruct_contract_initial_balance
    )

    # Entry code that will be executed, creates the contract and then calls it
    # in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just
        # copy it
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

    # Call the self-destructing contract multiple times as required, increasing
    # the wei sent each time
    entry_code_balance = 0
    for i, sendall_recipient in zip(
        range(call_times), cycle(sendall_recipient_addresses)
    ):
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
            sendall_final_balances[sendall_recipient] += (
                selfdestruct_contract_current_balance
            )

        # Self-destructing contract must always have zero balance after the
        # call because the self-destruct always happens in the same transaction
        # in this test
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

    # Lastly return zero so the entry point contract is created and we can
    # retain the stored values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_contract_initcode), 32), 1)

    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
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

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("call_times", [0, 1])
@pytest.mark.parametrize(
    "selfdestruct_contract_initial_balance",
    [0, 100_000],
)
@pytest.mark.valid_from("Shanghai")
def test_self_destructing_initcode(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    create_opcode: Op,
    call_times: int,  # Number of times to call the self-destructing contract
    # in the same tx
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Test that a contract can self-destruct in its initcode.

    Behavior is the same before and after EIP-6780.

    Test using:
        - Different initial balances for the self-destructing contract
        - Different opcodes: CREATE, CREATE2
        - Different number of calls to the self-destructing contract in
           the same tx
    """
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_code)
    # Our entry point is an initcode that in turn creates a self-destructing
    # contract
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

    # Entry code that will be executed, creates the contract and then calls it
    # in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just
        # copy it
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

    # Call the self-destructing contract multiple times as required, increasing
    # the wei sent each time
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

    # Lastly return zero so the entry point contract is created and we can
    # retain the stored values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_code), 32), 1)

    if selfdestruct_contract_initial_balance > 0:
        # Address where the contract is created already had some balance,
        # which must be included in the send-all operation
        sendall_amount += selfdestruct_contract_initial_balance
        pre.fund_address(
            selfdestruct_contract_address,
            selfdestruct_contract_initial_balance,
        )

    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
    )

    entry_code_address = tx.created_contract

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        sendall_recipient_addresses[0]: Account(
            balance=sendall_amount, storage={0: 1}
        ),
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("tx_value", [0, 100_000])
@pytest.mark.parametrize(
    "selfdestruct_contract_initial_balance",
    [0, 100_000],
)
@pytest.mark.valid_from("Shanghai")
def test_self_destructing_initcode_create_tx(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    sender: EOA,
    tx_value: int,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Use a Create Transaction to execute a self-destructing initcode.

    Behavior should be the same before and after EIP-6780.

    Test using:
      - Different initial balances for the self-destructing contract
      - Different transaction value amounts
    """
    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        sender=sender,
        value=tx_value,
        data=selfdestruct_code,
        to=None,
        gas_limit=gas_limit,
    )
    selfdestruct_contract_address = tx.created_contract
    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(
            selfdestruct_contract_address,
            selfdestruct_contract_initial_balance,
        )

    # Our entry point is an initcode that in turn creates a self-destructing
    # contract
    sendall_amount = selfdestruct_contract_initial_balance + tx_value

    post: Dict[Address, Account] = {
        selfdestruct_contract_address: Account.NONEXISTENT,  # type: ignore
        sendall_recipient_addresses[0]: Account(
            balance=sendall_amount, storage={0: 1}
        ),
    }

    state_test(pre=pre, post=post, tx=tx)


# Can only recreate using CREATE2
@pytest.mark.parametrize("create_opcode", [Op.CREATE2])
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
@pytest.mark.parametrize(
    "selfdestruct_contract_initial_balance",
    [0, 100_000],
)
@pytest.mark.parametrize("recreate_times", [1])
@pytest.mark.parametrize("call_times", [1])
@pytest.mark.valid_from("Shanghai")
def test_recreate_self_destructed_contract_different_txs(
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[Address],
    create_opcode: Op,
    # Number of times to recreate the contract in different transactions
    recreate_times: int,
    # Number of times to call the self-destructing contract in the same tx
    call_times: int,
) -> None:
    """
    Test that a contract can be recreated after it has self-destructed, over
    the lapse of multiple transactions.

    Behavior should be the same before and after EIP-6780.

    Test using:
      - Different initial balances for the self-destructing contract
      - Contract creating opcodes that are not CREATE
    """
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(
        selfdestruct_contract_initcode
    )
    entry_code_storage = Storage()
    sendall_amount = selfdestruct_contract_initial_balance

    # Bytecode used to create the contract
    assert create_opcode != Op.CREATE, (
        "cannot recreate contract using CREATE opcode"
    )
    create_bytecode = create_opcode(size=len(selfdestruct_contract_initcode))

    # Entry code that will be executed, creates the contract and then calls it
    entry_code = (
        # Initcode is already deployed at initcode_copy_from_address, so just
        # copy it
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
        address=entry_code_address,
        initcode=selfdestruct_contract_initcode,
        opcode=create_opcode,
    )
    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(
            selfdestruct_contract_address,
            selfdestruct_contract_initial_balance,
        )
    for i in range(len(sendall_recipient_addresses)):
        if sendall_recipient_addresses[i] == SELF_ADDRESS:
            sendall_recipient_addresses[i] = selfdestruct_contract_address

    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    txs: List[Transaction] = []
    for i in range(recreate_times + 1):
        txs.append(
            Transaction(
                data=Hash(i),
                sender=sender,
                to=entry_code_address,
                gas_limit=gas_limit,
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
        post[sendall_recipient_addresses[0]] = Account(
            balance=sendall_amount, storage={0: 1}
        )

    blockchain_test(pre=pre, post=post, blocks=[Block(txs=txs)])


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
            [
                PRE_DEPLOY_CONTRACT_1,
                PRE_DEPLOY_CONTRACT_2,
                PRE_DEPLOY_CONTRACT_3,
            ],
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
    fork: Fork,
    eip_enabled: bool,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[Address],
    call_times: int,
) -> None:
    """
    Test calling a previously created account that contains a selfdestruct, and
    verify its balance is sent to the destination address.

    After EIP-6780, the balance should be sent to the send-all recipient
    address, similar to the behavior before the EIP, but the account is not
    deleted.

    Test using:
    - Different send-all recipient addresses: single, multiple,
       including self
    - Different initial balances for the self-destructing contract
    """
    selfdestruct_contract_address = pre.deploy_contract(
        selfdestruct_code, balance=selfdestruct_contract_initial_balance
    )
    entry_code_storage = Storage()

    for i in range(len(sendall_recipient_addresses)):
        if sendall_recipient_addresses[i] == SELF_ADDRESS:
            sendall_recipient_addresses[i] = selfdestruct_contract_address

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(
            sendall_recipient_addresses,
            [0] * len(sendall_recipient_addresses),
            strict=False,
        )
    )
    selfdestruct_contract_current_balance = (
        selfdestruct_contract_initial_balance
    )

    # Entry code in this case will simply call the pre-existing self-
    # destructing contract, as many times as required
    entry_code = Bytecode()

    # Call the self-destructing contract multiple times as required, increasing
    # the wei sent each time
    entry_code_balance = 0
    for i, sendall_recipient in zip(
        range(call_times), cycle(sendall_recipient_addresses)
    ):
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
            sendall_final_balances[sendall_recipient] += (
                selfdestruct_contract_current_balance
            )

        # Balance is only kept by the self-destructing contract if we are
        # sending to self and the EIP is activated, otherwise the balance is
        # destroyed
        if (
            sendall_recipient != selfdestruct_contract_address
            or not eip_enabled
        ):
            selfdestruct_contract_current_balance = 0

        entry_code += Op.SSTORE(
            entry_code_storage.store_next(
                selfdestruct_contract_current_balance
            ),
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

    # Lastly return zero so the entry point contract is created and we can
    # retain the stored values for verification.
    entry_code += Op.RETURN(32, 1)

    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
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

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("call_times", [1, 10])
@pytest.mark.valid_from("Shanghai")
def test_selfdestruct_created_same_block_different_tx(
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    eip_enabled: bool,
    pre: Alloc,
    sender: EOA,
    selfdestruct_contract_initial_balance: int,
    sendall_recipient_addresses: List[Address],
    call_times: int,
) -> None:
    """
    Test that if an account created in the same block that contains a
    selfdestruct is called, its balance is sent to the send-all address, but
    the account is not deleted.
    """
    selfdestruct_code = selfdestruct_code_preset(
        sendall_recipient_addresses=sendall_recipient_addresses,
    )
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    selfdestruct_contract_address = compute_create_address(
        address=sender, nonce=0
    )
    entry_code_address = compute_create_address(address=sender, nonce=1)
    entry_code_storage = Storage()
    sendall_amount = selfdestruct_contract_initial_balance
    entry_code = Bytecode()

    # Entry code in this case will simply call the pre-existing self-
    # destructing contract, as many times as required

    # Call the self-destructing contract multiple times as required, increasing
    # the wei sent each time
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

    # Lastly return zero so the entry point contract is created and we can
    # retain the stored values for verification.
    entry_code += Op.RETURN(32, 1)

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        sendall_recipient_addresses[0]: Account(
            balance=sendall_amount, storage={0: 1}
        ),
    }

    if eip_enabled:
        post[selfdestruct_contract_address] = Account(
            balance=0, storage={0: call_times}
        )
    else:
        post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    txs = [
        Transaction(
            value=selfdestruct_contract_initial_balance,
            data=selfdestruct_contract_initcode,
            sender=sender,
            to=None,
            gas_limit=gas_limit,
        ),
        Transaction(
            value=entry_code_balance,
            data=entry_code,
            sender=sender,
            to=None,
            gas_limit=gas_limit,
        ),
    ]

    blockchain_test(pre=pre, post=post, blocks=[Block(txs=txs)])


@pytest.mark.parametrize("call_times", [1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@pytest.mark.parametrize("create_opcode", [Op.CREATE])
@pytest.mark.valid_from("Shanghai")
def test_calling_from_new_contract_to_pre_existing_contract(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    sender: EOA,
    sendall_recipient_addresses: List[Address],
    create_opcode: Op,
    call_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Test that if an account created in the current transaction delegate-call a
    previously created account that executes self-destruct, the calling account
    is deleted.
    """
    pre_existing_selfdestruct_address = pre.deploy_contract(
        selfdestruct_code_preset(
            sendall_recipient_addresses=sendall_recipient_addresses,
        ),
    )
    # Our entry point is an initcode that in turn creates a self-destructing
    # contract
    entry_code_storage = Storage()
    sendall_amount = 0

    entry_code_address = compute_create_address(address=sender, nonce=0)
    selfdestruct_contract_address = compute_create_address(
        address=entry_code_address, nonce=1
    )

    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(
            selfdestruct_contract_address,
            selfdestruct_contract_initial_balance,
        )

    # self-destructing call
    selfdestruct_code = call_opcode(address=pre_existing_selfdestruct_address)
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(
        selfdestruct_contract_initcode
    )

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_bytecode = create_opcode(size=len(selfdestruct_contract_initcode))

    # Entry code that will be executed, creates the contract and then calls it
    # in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just
        # copy it
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

    # Call the self-destructing contract multiple times as required, increasing
    # the wei sent each time
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

    # Lastly return zero so the entry point contract is created and we can
    # retain the stored values for verification.
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
        sendall_recipient_addresses[0]: Account(
            balance=sendall_amount, storage={0: 1}
        ),
    }

    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@pytest.mark.parametrize("call_times", [1])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 1])
@pytest.mark.parametrize("pre_existing_contract_initial_balance", [0, 1])
@pytest.mark.valid_from("Shanghai")
def test_calling_from_pre_existing_contract_to_new_contract(
    state_test: StateTestFiller,
    fork: Fork,
    eip_enabled: bool,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    call_opcode: Op,
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
    pre_existing_contract_initial_balance: int,
) -> None:
    """
    Test that if an account created in the current transaction contains a
    self-destruct and is delegate-called by an account created before the
    current transaction, the calling account is not deleted.
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

    # Our entry point is an initcode that in turn creates a self-destructing
    # contract
    entry_code_storage = Storage()
    sendall_amount = pre_existing_contract_initial_balance

    # Entry code that will be executed, creates the contract and then calls it
    # in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just
        # copy it
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

    # Now instead of calling the newly created contract directly, we delegate
    # call to it from a pre-existing contract, and the contract must not self-
    # destruct
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

    # Lastly return zero so the entry point contract is created and we can
    # retain the stored values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_contract_initcode), 32), 1)

    gas_limit = 500_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
    )

    entry_code_address = tx.created_contract

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            storage=entry_code_storage,
        ),
        sendall_recipient_addresses[0]: Account(
            balance=sendall_amount, storage={0: 1}
        ),
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

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.parametrize(
    "call_times,sendall_recipient_addresses",
    [
        pytest.param(1, [PRE_DEPLOY_CONTRACT_1], id="single_call"),
        pytest.param(
            5, [PRE_DEPLOY_CONTRACT_1], id="multiple_calls_single beneficiary"
        ),
    ],
    indirect=["sendall_recipient_addresses"],
)
@pytest.mark.valid_from("Shanghai")
def test_create_selfdestruct_same_tx_increased_nonce(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    sender: EOA,
    selfdestruct_code: Bytecode,
    sendall_recipient_addresses: List[Address],
    create_opcode: Op,
    call_times: int,
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Verify that a contract can self-destruct if it was created in the same
    transaction, even when its nonce has been increased due to contract
    creation.
    """
    initcode = Op.RETURN(0, 1)
    selfdestruct_pre_bytecode = Op.MSTORE(
        0, Op.PUSH32(bytes(initcode))
    ) + Op.POP(Op.CREATE(offset=32 - len(initcode), size=len(initcode)))
    selfdestruct_code = selfdestruct_pre_bytecode + selfdestruct_code
    selfdestruct_contract_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(
        selfdestruct_contract_initcode
    )

    selfdestruct_contract_address = compute_create_address(
        address=compute_create_address(address=sender, nonce=0),
        nonce=1,
        initcode=selfdestruct_contract_initcode,
        opcode=create_opcode,
    )
    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(
            selfdestruct_contract_address,
            selfdestruct_contract_initial_balance,
        )
    # Our entry point is an initcode that in turn creates a self-destructing
    # contract
    entry_code_storage = Storage()

    # Create a dict to record the expected final balances
    sendall_final_balances = dict(
        zip(
            sendall_recipient_addresses,
            [0] * len(sendall_recipient_addresses),
            strict=False,
        )
    )
    selfdestruct_contract_current_balance = (
        selfdestruct_contract_initial_balance
    )

    # Bytecode used to create the contract, can be CREATE or CREATE2
    create_bytecode = create_opcode(size=len(selfdestruct_contract_initcode))

    # Entry code that will be executed, creates the contract and then calls it
    # in the same tx
    entry_code = (
        # Initcode is already deployed at `initcode_copy_from_address`, so just
        # copy it
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

    # Call the self-destructing contract multiple times as required, increasing
    # the wei sent each time
    entry_code_balance = 0
    for i, sendall_recipient in zip(
        range(call_times), cycle(sendall_recipient_addresses)
    ):
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
            sendall_final_balances[sendall_recipient] += (
                selfdestruct_contract_current_balance
            )

        # Self-destructing contract must always have zero balance after the
        # call because the self-destruct always happens in the same transaction
        # in this test
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

    # Lastly return zero so the entry point contract is created and we can
    # retain the stored values for verification.
    entry_code += Op.RETURN(max(len(selfdestruct_contract_initcode), 32), 1)

    gas_limit = 1_000_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        value=entry_code_balance,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
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

    # Check the new contracts created from the self-destructing contract were
    # correctly created.
    for address in [
        compute_create_address(
            address=selfdestruct_contract_address, nonce=i + 1
        )
        for i in range(call_times)
    ]:
        post[address] = Account(
            code=b"\x00",
        )

    post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("num_contracts", [2, 3])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_create_and_destroy_multiple_contracts_same_tx(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    sender: EOA,
    num_contracts: int,
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Test creating multiple distinct contracts and self-destructing all of them
    in the same transaction.

    Each contract is created via CREATE2 with different salts and then called
    to trigger self-destruction. All contracts should be deleted because they
    are destroyed in the same transaction they were created.
    """
    entry_code_storage = Storage()

    # Pre-deploy a recipient contract that will receive the self-destruct funds
    sendall_recipient = pre.deploy_contract(
        code=Op.SSTORE(0, 0),
        storage={0: 1},
    )

    # Each self-destructing contract code: increment storage, then selfdestruct
    selfdestruct_code = (
        Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.SELFDESTRUCT(sendall_recipient)
        + Op.STOP
    )
    selfdestruct_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_initcode)

    # Entry point address (will be created by the transaction)
    entry_code_address = compute_create_address(address=sender, nonce=0)

    # Compute addresses for each contract to be created
    contract_addresses: List[Address] = []
    for i in range(num_contracts):
        addr = compute_create_address(
            address=entry_code_address,
            salt=i,
            initcode=selfdestruct_initcode,
            opcode=Op.CREATE2,
        )
        contract_addresses.append(addr)
        if selfdestruct_contract_initial_balance > 0:
            pre.fund_address(addr, selfdestruct_contract_initial_balance)

    # Build entry code that creates all contracts then calls each to
    # self-destruct
    entry_code = Op.EXTCODECOPY(
        initcode_copy_from_address,
        0,
        0,
        len(selfdestruct_initcode),
    )

    # Create each contract with a different salt
    for i in range(num_contracts):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(contract_addresses[i]),
            Op.CREATE2(
                value=0,
                offset=0,
                size=len(selfdestruct_initcode),
                salt=i,
            ),
        )

    # Call each contract to trigger self-destruction
    total_sendall = selfdestruct_contract_initial_balance * num_contracts
    for i in range(num_contracts):
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(1),
            Op.CALL(
                Op.GASLIMIT,
                contract_addresses[i],
                0,
                0,
                0,
                0,
                0,
            ),
        )
        # After each self-destruct, balance should be zero
        entry_code += Op.SSTORE(
            entry_code_storage.store_next(0),
            Op.BALANCE(contract_addresses[i]),
        )

    entry_code += Op.RETURN(32, 1)

    gas_limit = 1_000_000
    if fork.is_eip_enabled(8037):
        gas_limit = 5_000_000
    tx = Transaction(
        value=0,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
    )

    post: Dict[Address, Account] = {
        entry_code_address: Account(storage=entry_code_storage),
        sendall_recipient: Account(balance=total_sendall, storage={0: 1}),
    }

    # All created contracts should be non-existent
    for addr in contract_addresses:
        post[addr] = Account.NONEXISTENT  # type: ignore

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_create_multiple_contracts_destroy_one_then_destroy_other_next_tx(
    blockchain_test: BlockchainTestFiller,
    eip_enabled: bool,
    pre: Alloc,
    sender: EOA,
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Test creating multiple contracts in one transaction, destroying only one
    of them, then attempting to destroy the other in a subsequent transaction.

    Contract A: Self-destructs in the same transaction as creation (deleted)
    Contract B: Does NOT self-destruct in creation tx, attempted destruction
                in subsequent tx (persists after EIP-6780)
    """
    # Pre-deploy a recipient contract
    sendall_recipient = pre.deploy_contract(
        code=Op.SSTORE(0, 0),
        storage={0: 1},
    )

    # Self-destructing contract code: selfdestruct based on calldata
    # If calldata[0] == 1, self-destruct; otherwise just increment storage
    selfdestruct_code = Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)) + Conditional(
        condition=Op.EQ(Op.CALLDATALOAD(0), 1),
        if_true=Op.SELFDESTRUCT(sendall_recipient),
        if_false=Op.STOP,
    )
    selfdestruct_initcode = Initcode(deploy_code=selfdestruct_code)
    initcode_copy_from_address = pre.deploy_contract(selfdestruct_initcode)

    # Deploy entry contract
    entry_code_storage = Storage()

    # Entry code: create both contracts, call A with selfdestruct flag,
    # call B without
    entry_code = Op.EXTCODECOPY(
        initcode_copy_from_address,
        0,
        0,
        len(selfdestruct_initcode),
    )

    # Create contract A with salt=0
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(0),  # Replaced with actual address
        Op.CREATE2(value=0, offset=0, size=len(selfdestruct_initcode), salt=0),
    )

    # Create contract B with salt=1
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(0),  # Replaced with actual address
        Op.CREATE2(value=0, offset=0, size=len(selfdestruct_initcode), salt=1),
    )

    # Call contract A (slot 0) with flag=1 to self-destruct
    entry_code += Op.MSTORE(0, 1)
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(1),
        Op.CALL(Op.GASLIMIT, Op.SLOAD(0), 0, 0, 32, 0, 0),
    )

    # Call contract B (slot 1) with flag=0 to NOT self-destruct
    entry_code += Op.MSTORE(0, 0)
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(1),
        Op.CALL(Op.GASLIMIT, Op.SLOAD(1), 0, 0, 32, 0, 0),
    )

    entry_code += Op.STOP

    entry_code_address = pre.deploy_contract(entry_code)

    # Calculate contract addresses
    contract_a_address = compute_create_address(
        address=entry_code_address,
        salt=0,
        initcode=selfdestruct_initcode,
        opcode=Op.CREATE2,
    )
    contract_b_address = compute_create_address(
        address=entry_code_address,
        salt=1,
        initcode=selfdestruct_initcode,
        opcode=Op.CREATE2,
    )

    # Update expected storage
    entry_code_storage[0] = contract_a_address
    entry_code_storage[1] = contract_b_address

    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(
            contract_a_address, selfdestruct_contract_initial_balance
        )
        pre.fund_address(
            contract_b_address, selfdestruct_contract_initial_balance
        )

    # Second transaction: try to self-destruct contract B
    tx2_caller = pre.deploy_contract(
        Op.MSTORE(0, 1)
        + Op.CALL(Op.GASLIMIT, contract_b_address, 0, 0, 32, 0, 0)
        + Op.STOP
    )

    txs = [
        Transaction(
            sender=sender,
            to=entry_code_address,
            gas_limit=1_000_000,
        ),
        Transaction(
            sender=sender,
            to=tx2_caller,
            gas_limit=500_000,
        ),
    ]

    post: Dict[Address, Account] = {
        entry_code_address: Account(storage=entry_code_storage),
        # Contract A is always destroyed (created and destroyed same tx)
        contract_a_address: Account.NONEXISTENT,  # type: ignore
    }

    if eip_enabled:
        # After EIP-6780: Contract B persists (not destroyed in same tx)
        # Storage shows 2 calls (one in tx1, one in tx2)
        post[contract_b_address] = Account(
            storage={0: 2},
            balance=0,  # Balance sent but contract persists
        )
        post[sendall_recipient] = Account(
            balance=selfdestruct_contract_initial_balance * 2,
            storage={0: 1},
        )
    else:
        # Before EIP-6780: Contract B is destroyed in tx2
        post[contract_b_address] = Account.NONEXISTENT  # type: ignore
        post[sendall_recipient] = Account(
            balance=selfdestruct_contract_initial_balance * 2,
            storage={0: 1},
        )

    blockchain_test(pre=pre, post=post, blocks=[Block(txs=txs)])


@pytest.mark.parametrize("destroy_parent", [True, False])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_parent_creates_child_selfdestruct_one(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    destroy_parent: bool,
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Test a parent contract that creates a child contract, then only one
    of them self-destructs (either parent or child, based on parameter).

    Both contracts are created in the same transaction:
    - If destroy_parent=True: Parent self-destructs, child survives
    - If destroy_parent=False: Child self-destructs, parent survives

    Since both are created in the same tx, whichever self-destructs should be
    deleted.
    """
    entry_code_storage = Storage()

    sendall_recipient = pre.deploy_contract(
        code=Op.SSTORE(0, 0),
        storage={0: 1},
    )

    # Child contract: just has code, self-destructs when called
    child_code = Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)) + Op.SELFDESTRUCT(
        sendall_recipient
    )
    child_initcode = Initcode(deploy_code=child_code)

    # Parent contract: creates child, then either self-destructs or calls child
    # to self-destruct based on calldata[0]: 1 = destroy parent, 0 = destroy
    # child
    # For simplicity, use pre-deployed child initcode
    child_initcode_address = pre.deploy_contract(child_initcode)

    parent_code = (
        Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.EXTCODECOPY(child_initcode_address, 0, 0, len(child_initcode))
        + Op.SSTORE(1, Op.CREATE(value=0, offset=0, size=len(child_initcode)))
        + Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            if_true=Op.SELFDESTRUCT(sendall_recipient),
            if_false=Op.CALL(Op.GASLIMIT, Op.SLOAD(1), 0, 0, 0, 0, 0),
        )
        + Op.STOP
    )
    parent_initcode = Initcode(deploy_code=parent_code)
    parent_initcode_address = pre.deploy_contract(parent_initcode)

    entry_code_address = compute_create_address(address=sender, nonce=0)
    parent_address = compute_create_address(
        address=entry_code_address,
        nonce=1,
        initcode=parent_initcode,
        opcode=Op.CREATE,
    )
    child_address = compute_create_address(address=parent_address, nonce=1)

    if selfdestruct_contract_initial_balance > 0:
        pre.fund_address(parent_address, selfdestruct_contract_initial_balance)
        pre.fund_address(child_address, selfdestruct_contract_initial_balance)

    # Entry code: create parent and call it with appropriate flag
    entry_code = Op.EXTCODECOPY(
        parent_initcode_address,
        0,
        0,
        len(parent_initcode),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(parent_address),
        Op.CREATE(value=0, offset=0, size=len(parent_initcode)),
    )

    flag = 1 if destroy_parent else 0
    entry_code += Op.MSTORE(0, flag)
    entry_code += Op.SSTORE(
        entry_code_storage.store_next(1),
        Op.CALL(Op.GASLIMIT, parent_address, 0, 0, 32, 0, 0),
    )

    entry_code += Op.RETURN(32, 1)

    tx = Transaction(
        value=0,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=1_000_000,
    )

    post: Dict[Address, Account] = {
        entry_code_address: Account(storage=entry_code_storage),
    }

    if destroy_parent:
        post[parent_address] = Account.NONEXISTENT  # type: ignore
        post[child_address] = Account(
            storage={0: 0},
            balance=selfdestruct_contract_initial_balance,
        )
        post[sendall_recipient] = Account(
            balance=selfdestruct_contract_initial_balance,
            storage={0: 1},
        )
    else:
        post[child_address] = Account.NONEXISTENT  # type: ignore
        post[parent_address] = Account(
            storage={0: 1, 1: child_address},
            balance=selfdestruct_contract_initial_balance,
        )
        post[sendall_recipient] = Account(
            balance=selfdestruct_contract_initial_balance,
            storage={0: 1},
        )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("recursion_depth", [2, 3])
@pytest.mark.parametrize("selfdestruct_on_unwind", [True, False])
@pytest.mark.parametrize("selfdestruct_contract_initial_balance", [0, 100_000])
@pytest.mark.valid_from("Shanghai")
def test_recursive_contract_creation_and_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    recursion_depth: int,
    selfdestruct_on_unwind: bool,
    selfdestruct_contract_initial_balance: int,
) -> None:
    """
    Test recursive contract creation with self-destruct.

    Each contract creates another, forming a chain. Then self-destruct is
    triggered either:
    - selfdestruct_on_unwind=True: Each contract self-destructs as the call
      stack unwinds
    - selfdestruct_on_unwind=False: Only the deepest contract self-destructs

    All contracts are created in the same transaction, so any that
    self-destruct should be deleted.
    """
    entry_code_storage = Storage()

    sendall_recipient = pre.deploy_contract(
        code=Op.SSTORE(0, 0),
        storage={0: 1},
    )

    # We'll create a chain of contracts where each creates the next one
    # using CREATE. Each contract's code will:
    # 1. Check depth (from calldata)
    # 2. If depth > 0: copy child initcode, create child, call child with
    #    depth-1
    # 3. If selfdestruct_on_unwind: selfdestruct after child call returns
    # 4. If depth == 0: selfdestruct immediately

    # To make this work, we pre-deploy initcodes for each level
    # Level 0 (deepest): just selfdestructs
    level_initcodes: List[Bytecode] = []
    level_codes: List[Bytecode] = []

    # Build from deepest to shallowest
    # Level 0 (deepest): always self-destructs
    level_0_code = Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)) + Op.SELFDESTRUCT(
        sendall_recipient
    )
    level_codes.append(level_0_code)
    level_initcodes.append(Initcode(deploy_code=level_0_code))

    # Higher levels: create child, call it, optionally self-destruct
    for level in range(1, recursion_depth):
        child_initcode = level_initcodes[level - 1]
        child_initcode_deployed = pre.deploy_contract(child_initcode)

        child_len = len(child_initcode)
        if selfdestruct_on_unwind:
            level_code = (
                Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
                + Op.EXTCODECOPY(child_initcode_deployed, 0, 0, child_len)
                + Op.SSTORE(1, Op.CREATE(value=0, offset=0, size=child_len))
                + Op.CALL(Op.GASLIMIT, Op.SLOAD(1), 0, 0, 0, 0, 0)
                + Op.SELFDESTRUCT(sendall_recipient)
            )
        else:
            level_code = (
                Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
                + Op.EXTCODECOPY(child_initcode_deployed, 0, 0, child_len)
                + Op.SSTORE(1, Op.CREATE(value=0, offset=0, size=child_len))
                + Op.CALL(Op.GASLIMIT, Op.SLOAD(1), 0, 0, 0, 0, 0)
                + Op.STOP
            )
        level_codes.append(level_code)
        level_initcodes.append(Initcode(deploy_code=level_code))

    # Top level initcode (the one we'll create from entry code)
    top_initcode = level_initcodes[-1]
    top_initcode_address = pre.deploy_contract(top_initcode)

    entry_code_address = compute_create_address(address=sender, nonce=0)

    # Calculate all contract addresses
    contract_addresses: List[Address] = []
    for level in range(recursion_depth - 1, -1, -1):
        if level == recursion_depth - 1:
            addr = compute_create_address(
                address=entry_code_address,
                nonce=1,
                initcode=level_initcodes[level],
                opcode=Op.CREATE,
            )
        else:
            addr = compute_create_address(
                address=contract_addresses[-1],
                nonce=1,
                initcode=level_initcodes[level],
                opcode=Op.CREATE,
            )
        contract_addresses.append(addr)
        if selfdestruct_contract_initial_balance > 0:
            pre.fund_address(addr, selfdestruct_contract_initial_balance)

    # Entry code
    entry_code = Op.EXTCODECOPY(
        top_initcode_address,
        0,
        0,
        len(top_initcode),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(contract_addresses[0]),
        Op.CREATE(value=0, offset=0, size=len(top_initcode)),
    )

    entry_code += Op.SSTORE(
        entry_code_storage.store_next(1),
        Op.CALL(Op.GASLIMIT, contract_addresses[0], 0, 0, 0, 0, 0),
    )

    entry_code += Op.RETURN(32, 1)

    tx = Transaction(
        value=0,
        data=entry_code,
        sender=sender,
        to=None,
        gas_limit=2_000_000,
    )

    post: Dict[Address, Account] = {
        entry_code_address: Account(storage=entry_code_storage),
    }

    if selfdestruct_on_unwind:
        # All contracts self-destruct
        total_sendall = selfdestruct_contract_initial_balance * recursion_depth
        for addr in contract_addresses:
            post[addr] = Account.NONEXISTENT  # type: ignore
    else:
        # Only the deepest contract (last in list) self-destructs
        total_sendall = selfdestruct_contract_initial_balance
        for i, addr in enumerate(contract_addresses):
            if i == len(contract_addresses) - 1:
                # Deepest - destroyed
                post[addr] = Account.NONEXISTENT  # type: ignore
            else:
                # Survives with storage: slot 0 = call count, slot 1 = child
                # Retains its initial balance since it didn't self-destruct
                child_addr = contract_addresses[i + 1]
                post[addr] = Account(
                    storage={0: 1, 1: child_addr},
                    balance=selfdestruct_contract_initial_balance,
                )

    post[sendall_recipient] = Account(
        balance=total_sendall,
        storage={0: 1},
    )

    state_test(pre=pre, post=post, tx=tx)
