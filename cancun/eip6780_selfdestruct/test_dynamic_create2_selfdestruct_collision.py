"""
Suicide scenario requested test
https://github.com/ethereum/execution-spec-tests/issues/381
"""

from itertools import count
from typing import Dict, Union

import pytest

from ethereum_test_forks import Cancun, Fork
from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    Conditional,
    Environment,
    Initcode,
    StateTestFiller,
    TestAddress,
    Transaction,
    compute_create2_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "2f8299df31bb8173618901a03a8366a3183479b0"


@pytest.fixture
def env():  # noqa: D103
    return Environment(
        fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x020000,
        gas_limit=71794957647893862,
        number=1,
        timestamp=1000,
    )


@pytest.mark.valid_from("Paris")
@pytest.mark.parametrize(
    "create2_dest_already_in_state",
    (True, False),
)
@pytest.mark.parametrize(
    "call_create2_contract_in_between,call_create2_contract_at_the_end",
    [
        (True, True),
        (True, False),
        (False, True),
    ],
)
def test_dynamic_create2_selfdestruct_collision(
    env: Environment,
    fork: Fork,
    create2_dest_already_in_state: bool,
    call_create2_contract_in_between: bool,
    call_create2_contract_at_the_end: bool,
    state_test: StateTestFiller,
):
    """Dynamic Create2->Suicide->Create2 collision scenario:

    Perform a CREATE2, make sure that the initcode sets at least a couple of storage keys,
    then on a different call, in the same tx, perform a self-destruct.
    Then:
        a) on the same tx, attempt to recreate the contract   <=== Covered in this test
            1) and create2 contract already in the state
            2) and create2 contract is not in the state
        b) on a different tx, attempt to recreate the contract
    Perform a CREATE2, make sure that the initcode sets at least a couple of storage keys,
    then in a different tx, perform a self-destruct.
    Then:
        a) on the same tx, attempt to recreate the contract
        b) on a different tx, attempt to recreate the contract
    Verify that the test case described
    in https://wiki.hyperledger.org/pages/viewpage.action?pageId=117440824 is covered
    """
    assert call_create2_contract_in_between or call_create2_contract_at_the_end, "invalid test"

    # Storage locations
    create2_constructor_worked = 1
    first_create2_result = 2
    second_create2_result = 3
    code_worked = 4

    # Pre-Existing Addresses
    address_zero = Address(0x00)
    address_to = Address(0x0600)
    address_code = Address(0x0601)
    address_create2_storage = Address(0x0512)
    sendall_destination = Address(0x03E8)

    # CREATE2 Initcode
    create2_salt = 1
    deploy_code = Op.SELFDESTRUCT(sendall_destination)
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_prefix=Op.SSTORE(create2_constructor_worked, 1)
        + Op.CALL(Op.GAS(), address_create2_storage, 0, 0, 0, 0, 0),
    )

    # Created addresses
    create2_address = compute_create2_address(address_code, create2_salt, initcode)
    call_address_in_between = create2_address if call_create2_contract_in_between else address_zero
    call_address_in_the_end = create2_address if call_create2_contract_at_the_end else address_zero

    # Values
    pre_existing_create2_balance = 1
    first_create2_value = 10
    first_call_value = 100
    second_create2_value = 1000
    second_call_value = 10000

    pre = {
        address_to: Account(
            balance=100000000,
            nonce=0,
            code=Op.JUMPDEST()
            # Make a subcall that do CREATE2 and returns its the result
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.CALL(100000, address_code, first_create2_value, 0, Op.CALLDATASIZE(), 0, 32)
            + Op.SSTORE(
                first_create2_result,
                Op.MLOAD(0),
            )
            # In case the create2 didn't work, flush account balance
            + Op.CALL(100000, address_code, 0, 0, 0, 0, 0)
            # Call to the created account to trigger selfdestruct
            + Op.CALL(100000, call_address_in_between, first_call_value, 0, 0, 0, 0)
            # Make a subcall that do CREATE2 collision and returns its address as the result
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.CALL(100000, address_code, second_create2_value, 0, Op.CALLDATASIZE(), 0, 32)
            + Op.SSTORE(
                second_create2_result,
                Op.MLOAD(0),
            )
            # Call to the created account to trigger selfdestruct
            + Op.CALL(100000, call_address_in_the_end, second_call_value, 0, 0, 0, 0)
            + Op.SSTORE(code_worked, 1),
            storage={first_create2_result: 0xFF, second_create2_result: 0xFF},
        ),
        address_code: Account(
            balance=0,
            nonce=0,
            code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.MSTORE(
                0,
                Op.CREATE2(Op.SELFBALANCE(), 0, Op.CALLDATASIZE(), create2_salt),
            )
            + Op.RETURN(0, 32),
            storage={},
        ),
        address_create2_storage: Account(
            balance=7000000000000000000,
            nonce=0,
            code=Op.SSTORE(1, 1),
            storage={},
        ),
        TestAddress: Account(
            balance=7000000000000000000,
            nonce=0,
            code="0x",
            storage={},
        ),
    }

    if create2_dest_already_in_state:
        # Create2 address already in the state, e.g. deployed in a previous block
        pre[create2_address] = Account(
            balance=pre_existing_create2_balance,
            nonce=1,
            code=deploy_code,
            storage={},
        )

    post: Dict[Address, Union[Account, object]] = {}

    # Create2 address only exists if it was pre-existing and after cancun
    post[create2_address] = (
        Account(balance=0, nonce=1, code=deploy_code, storage={create2_constructor_worked: 0x00})
        if create2_dest_already_in_state and fork >= Cancun
        else Account.NONEXISTENT
    )

    # Create2 initcode is only executed if the contract did not already exist
    post[address_create2_storage] = Account(
        storage={create2_constructor_worked: int(not create2_dest_already_in_state)}
    )

    # Entry code that makes the calls to the create2 contract creator
    post[address_to] = Account(
        storage={
            code_worked: 0x01,
            # First create2 only works if the contract was not preexisting
            first_create2_result: 0x00 if create2_dest_already_in_state else create2_address,
            # Second create2 must never work
            second_create2_result: 0x00,
        }
    )

    # Calculate the destination account expected balance for the selfdestruct/sendall calls
    sendall_destination_balance = (
        pre_existing_create2_balance if create2_dest_already_in_state else first_create2_value
    )

    if call_create2_contract_in_between:
        sendall_destination_balance += first_call_value

    if call_create2_contract_at_the_end:
        sendall_destination_balance += second_call_value

    post[sendall_destination] = Account(balance=sendall_destination_balance)

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to=address_to,
        gas_price=10,
        protected=False,
        data=initcode.bytecode if initcode.bytecode is not None else bytes(),
        gas_limit=5000000,
        value=0,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Paris")
@pytest.mark.parametrize(
    "create2_dest_already_in_state",
    (True, False),
)
@pytest.mark.parametrize(
    "call_create2_contract_at_the_end",
    [
        (True, False),
    ],
)
def test_dynamic_create2_selfdestruct_collision_two_different_transactions(
    env: Environment,
    fork: Fork,
    create2_dest_already_in_state: bool,
    call_create2_contract_at_the_end: bool,
    blockchain_test: BlockchainTestFiller,
):
    """Dynamic Create2->Suicide->Create2 collision scenario:

    Perform a CREATE2, make sure that the initcode sets at least a couple of storage keys,
    then on a different call, in the same tx, perform a self-destruct.
    Then:
        a) on the same tx, attempt to recreate the contract
            1) and create2 contract already in the state
            2) and create2 contract is not in the state
        b) on a different tx, attempt to recreate the contract <=== Covered in this test
    Perform a CREATE2, make sure that the initcode sets at least a couple of storage keys,
    then in a different tx, perform a self-destruct.
    Then:
        a) on the same tx, attempt to recreate the contract
        b) on a different tx, attempt to recreate the contract
    Verify that the test case described
    in https://wiki.hyperledger.org/pages/viewpage.action?pageId=117440824 is covered
    """
    # assert call_create2_contract_at_the_end, "invalid test"

    # Storage locations
    create2_constructor_worked = 1
    first_create2_result = 2
    second_create2_result = 3
    code_worked = 4

    # Pre-Existing Addresses
    address_zero = Address(0x00)
    address_to = Address(0x0600)
    address_to_second = Address(0x0700)
    address_code = Address(0x0601)
    address_create2_storage = Address(0x0512)
    sendall_destination = Address(0x03E8)

    # CREATE2 Initcode
    create2_salt = 1
    deploy_code = Op.SELFDESTRUCT(sendall_destination)
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_prefix=Op.SSTORE(create2_constructor_worked, 1)
        + Op.CALL(Op.GAS(), address_create2_storage, 0, 0, 0, 0, 0),
    )

    # Created addresses
    create2_address = compute_create2_address(address_code, create2_salt, initcode)
    call_address_in_the_end = create2_address if call_create2_contract_at_the_end else address_zero

    # Values
    pre_existing_create2_balance = 1
    first_create2_value = 10
    first_call_value = 100
    second_create2_value = 1000
    second_call_value = 10000

    pre = {
        address_to: Account(
            balance=100000000,
            nonce=0,
            code=Op.JUMPDEST()
            # Make a subcall that do CREATE2 and returns its the result
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.CALL(100000, address_code, first_create2_value, 0, Op.CALLDATASIZE(), 0, 32)
            + Op.SSTORE(
                first_create2_result,
                Op.MLOAD(0),
            )
            # In case the create2 didn't work, flush account balance
            + Op.CALL(100000, address_code, 0, 0, 0, 0, 0)
            # Call to the created account to trigger selfdestruct
            + Op.CALL(100000, create2_address, first_call_value, 0, 0, 0, 0)
            + Op.SSTORE(code_worked, 1),
            storage={first_create2_result: 0xFF},
        ),
        address_to_second: Account(
            balance=100000000,
            nonce=0,
            code=Op.JUMPDEST()
            # Make a subcall that do CREATE2 collision and returns its address as the result
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.CALL(100000, address_code, second_create2_value, 0, Op.CALLDATASIZE(), 0, 32)
            + Op.SSTORE(
                second_create2_result,
                Op.MLOAD(0),
            )
            # Call to the created account to trigger selfdestruct
            + Op.CALL(200000, call_address_in_the_end, second_call_value, 0, 0, 0, 0)
            + Op.SSTORE(code_worked, 1),
            storage={second_create2_result: 0xFF},
        ),
        address_code: Account(
            balance=0,
            nonce=0,
            code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.MSTORE(
                0,
                Op.CREATE2(Op.SELFBALANCE(), 0, Op.CALLDATASIZE(), create2_salt),
            )
            + Op.RETURN(0, 32),
            storage={},
        ),
        address_create2_storage: Account(
            balance=7000000000000000000,
            nonce=0,
            code=Op.SSTORE(1, 1),
            storage={},
        ),
        TestAddress: Account(
            balance=7000000000000000000,
            nonce=0,
            code="0x",
            storage={},
        ),
    }

    if create2_dest_already_in_state:
        # Create2 address already in the state, e.g. deployed in a previous block
        pre[create2_address] = Account(
            balance=pre_existing_create2_balance,
            nonce=1,
            code=deploy_code,
            storage={},
        )

    post: Dict[Address, Union[Account, object]] = {}

    # Create2 address only exists if it was pre-existing and after cancun
    post[create2_address] = (
        Account(balance=0, nonce=1, code=deploy_code, storage={create2_constructor_worked: 0x00})
        if create2_dest_already_in_state and fork >= Cancun
        else Account.NONEXISTENT
    )

    # after Cancun Create2 initcode is only executed if the contract did not already exist
    # and before it will always be executed as the first tx deletes the account
    post[address_create2_storage] = Account(
        storage={
            create2_constructor_worked: int(fork < Cancun or not create2_dest_already_in_state)
        }
    )

    # Entry code that makes the calls to the create2 contract creator
    post[address_to] = Account(
        storage={
            code_worked: 0x01,
            # First create2 only works if the contract was not preexisting
            first_create2_result: 0x00 if create2_dest_already_in_state else create2_address,
        }
    )
    post[address_to_second] = Account(
        storage={
            code_worked: 0x01,
            # Second create2 will not collide before Cancun as the first tx calls selfdestruct
            # After cancun it will collide only if create2_dest_already_in_state otherwise the
            # first tx creates and deletes it
            second_create2_result: (
                (0x00 if create2_dest_already_in_state else create2_address)
                if fork >= Cancun
                else create2_address
            ),
        }
    )

    # Calculate the destination account expected balance for the selfdestruct/sendall calls
    sendall_destination_balance = 0

    if create2_dest_already_in_state:
        sendall_destination_balance += pre_existing_create2_balance
        if fork >= Cancun:
            # first create2 fails, but first calls ok. the account is not removed on cancun
            # therefore with the second create2 it is not successful
            sendall_destination_balance += first_call_value
        else:
            # first create2 fails, first calls totally removes the account
            # in the second transaction second create2 is successful
            sendall_destination_balance += first_call_value + second_create2_value
    else:
        # if no account in the state, first create2 successful, first call successful and removes
        # because it is removed in the next transaction second create2 successful
        sendall_destination_balance = first_create2_value + first_call_value + second_create2_value

    if call_create2_contract_at_the_end:
        sendall_destination_balance += second_call_value

    post[sendall_destination] = Account(balance=sendall_destination_balance)

    nonce = count()

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        ty=0x0,
                        chain_id=0x0,
                        nonce=next(nonce),
                        to=address_to,
                        gas_price=10,
                        protected=False,
                        data=initcode.bytecode if initcode.bytecode is not None else bytes(),
                        gas_limit=5000000,
                        value=0,
                    ),
                    Transaction(
                        ty=0x0,
                        chain_id=0x0,
                        nonce=next(nonce),
                        to=address_to_second,
                        gas_price=10,
                        protected=False,
                        data=initcode.bytecode if initcode.bytecode is not None else bytes(),
                        gas_limit=5000000,
                        value=0,
                    ),
                ]
            )
        ],
    )


@pytest.mark.valid_from("Paris")
@pytest.mark.parametrize(
    "selfdestruct_on_first_tx,recreate_on_first_tx",
    [
        (False, False),
        (True, False),
        (True, True),
    ],
)
def test_dynamic_create2_selfdestruct_collision_multi_tx(
    fork: Fork,
    selfdestruct_on_first_tx: bool,
    recreate_on_first_tx: bool,
    blockchain_test: BlockchainTestFiller,
):
    """Dynamic Create2->Suicide->Create2 collision scenario over multiple transactions:

    Perform a CREATE2, make sure that the initcode sets at least a couple of storage keys,
    then on a different call, in the same or different tx but same block, perform a self-destruct.
    Then:
        a) on the same tx, attempt to recreate the contract
        b) on a different tx, attempt to recreate the contract
    Perform a CREATE2, make sure that the initcode sets at least a couple of storage keys,
    then in a different tx, perform a self-destruct.
    Then:
        a) on the same tx, attempt to recreate the contract       <=== Covered in this test
        b) on a different tx, attempt to recreate the contract    <=== Covered in this test
    Verify that the test case described
    in https://wiki.hyperledger.org/pages/viewpage.action?pageId=117440824 is covered
    """
    if recreate_on_first_tx:
        assert selfdestruct_on_first_tx, "invalid test"

    # Storage locations
    create2_constructor_worked = 1
    first_create2_result = 2
    second_create2_result = 3
    part_1_worked = 4
    part_2_worked = 5

    # Pre-Existing Addresses
    address_to = Address(0x0600)
    address_code = Address(0x0601)
    address_create2_storage = Address(0x0512)
    sendall_destination = Address(0x03E8)

    # CREATE2 Initcode
    create2_salt = 1
    deploy_code = Op.SELFDESTRUCT(sendall_destination)
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_prefix=Op.SSTORE(create2_constructor_worked, 1)
        + Op.CALL(Op.GAS(), address_create2_storage, 0, 0, 0, 0, 0),
    )

    # Created addresses
    create2_address = compute_create2_address(address_code, create2_salt, initcode)

    # Values
    first_create2_value = 3
    first_call_value = 5
    second_create2_value = 7
    second_call_value = 11

    # Code is divided in two transactions part of the same block
    first_tx_code = bytes()
    second_tx_code = bytes()

    first_tx_code += (
        Op.JUMPDEST()
        # Make a subcall that do CREATE2 and returns its the result
        + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        + Op.CALL(100000, address_code, first_create2_value, 0, Op.CALLDATASIZE(), 0, 32)
        + Op.SSTORE(
            first_create2_result,
            Op.MLOAD(0),
        )
    )

    if selfdestruct_on_first_tx:
        first_tx_code += (
            # Call to the created account to trigger selfdestruct
            Op.CALL(100000, create2_address, first_call_value, 0, 0, 0, 0)
        )
    else:
        second_tx_code += (
            # Call to the created account to trigger selfdestruct
            Op.CALL(100000, create2_address, first_call_value, 0, 0, 0, 0)
        )

    if recreate_on_first_tx:
        first_tx_code += (
            # Make a subcall that do CREATE2 collision and returns its address as the result
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.CALL(100000, address_code, second_create2_value, 0, Op.CALLDATASIZE(), 0, 32)
            + Op.SSTORE(
                second_create2_result,
                Op.MLOAD(0),
            )
        )

    else:
        second_tx_code += (
            # Make a subcall that do CREATE2 collision and returns its address as the result
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.CALL(100000, address_code, second_create2_value, 0, Op.CALLDATASIZE(), 0, 32)
            + Op.SSTORE(
                second_create2_result,
                Op.MLOAD(0),
            )
        )

    # Second tx code always calls the create2 contract at the end
    second_tx_code += Op.CALL(100000, create2_address, second_call_value, 0, 0, 0, 0)

    first_tx_code += Op.SSTORE(part_1_worked, 1)
    second_tx_code += Op.SSTORE(part_2_worked, 1)

    pre = {
        address_to: Account(
            balance=100000000,
            nonce=0,
            code=Conditional(
                # Depending on the tx, execute the first or second tx code
                condition=Op.EQ(Op.SLOAD(part_1_worked), 0),
                if_true=first_tx_code,
                if_false=second_tx_code,
            ),
            storage={first_create2_result: 0xFF, second_create2_result: 0xFF},
        ),
        address_code: Account(
            balance=0,
            nonce=0,
            code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
            + Op.MSTORE(
                0,
                Op.CREATE2(Op.SELFBALANCE(), 0, Op.CALLDATASIZE(), create2_salt),
            )
            + Op.RETURN(0, 32),
            storage={},
        ),
        address_create2_storage: Account(
            balance=7000000000000000000,
            nonce=0,
            code=Op.SSTORE(1, 1),
            storage={},
        ),
        TestAddress: Account(
            balance=7000000000000000000,
            nonce=0,
            code="0x",
            storage={},
        ),
    }

    post: Dict[Address, Union[Account, object]] = {}

    # Create2 address only exists if it was pre-existing and after cancun
    account_will_exist_with_code = not selfdestruct_on_first_tx and fork >= Cancun
    # If the contract is self-destructed and we also attempt to recreate it on the first tx,
    # the second call on the second tx will only place balance in the account
    account_will_exist_with_balance = selfdestruct_on_first_tx and recreate_on_first_tx

    post[create2_address] = (
        Account(balance=0, nonce=1, code=deploy_code, storage={create2_constructor_worked: 0x01})
        if account_will_exist_with_code
        else (
            Account(balance=second_call_value, nonce=0)
            if account_will_exist_with_balance
            else Account.NONEXISTENT
        )
    )

    # Create2 initcode saves storage unconditionally
    post[address_create2_storage] = Account(storage={create2_constructor_worked: 0x01})

    # Entry code that makes the calls to the create2 contract creator
    post[address_to] = Account(
        storage={
            part_1_worked: 0x01,
            part_2_worked: 0x01,
            # First create2 always works
            first_create2_result: create2_address,
            # Second create2 only works if we successfully self-destructed on the first tx
            second_create2_result: (
                create2_address if selfdestruct_on_first_tx and not recreate_on_first_tx else 0x00
            ),
        }
    )

    # Calculate the destination account expected balance for the selfdestruct/sendall calls
    sendall_destination_balance = first_create2_value + first_call_value

    if not account_will_exist_with_balance:
        sendall_destination_balance += second_call_value

    if selfdestruct_on_first_tx and not recreate_on_first_tx:
        sendall_destination_balance += second_create2_value

    post[sendall_destination] = Account(balance=sendall_destination_balance)

    nonce = count()

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        ty=0x0,
                        chain_id=0x0,
                        nonce=next(nonce),
                        to=address_to,
                        gas_price=10,
                        protected=False,
                        data=initcode.bytecode if initcode.bytecode is not None else bytes(),
                        gas_limit=5000000,
                        value=0,
                    ),
                    Transaction(
                        ty=0x0,
                        chain_id=0x0,
                        nonce=next(nonce),
                        to=address_to,
                        gas_price=10,
                        protected=False,
                        data=initcode.bytecode if initcode.bytecode is not None else bytes(),
                        gas_limit=5000000,
                        value=0,
                    ),
                ]
            )
        ],
    )
