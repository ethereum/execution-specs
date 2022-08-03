"""
Ethereum Virtual Machine (EVM) System Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM system related instructions.
"""
from ethereum.base_types import U256, Bytes0, Uint

from ...eth_types import Address
from ...state import (
    account_has_code_or_nonce,
    get_account,
    increment_nonce,
    set_account_balance,
)
from ...utils.address import compute_contract_address, to_address
from .. import Evm, Message
from ..exceptions import ExceptionalHalt
from ..gas import (
    GAS_CALL,
    GAS_CREATE,
    GAS_ZERO,
    calculate_call_gas_cost,
    calculate_message_call_gas_stipend,
    charge_gas,
)
from ..memory import extend_memory, memory_read_bytes, memory_write
from ..stack import pop, push


def create(evm: Evm) -> None:
    """
    Creates a new account with associated code.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # This import causes a circular import error
    # if it's not moved inside this method
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_create_message

    # STACK
    endowment = pop(evm.stack)
    memory_start_position = pop(evm.stack)
    memory_size = pop(evm.stack)

    # GAS
    extend_memory(evm, memory_start_position, memory_size)
    charge_gas(evm, GAS_CREATE)

    create_message_gas = evm.gas_left
    evm.gas_left = U256(0)

    # OPERATION
    sender_address = evm.message.current_target
    sender = get_account(evm.env.state, sender_address)

    contract_address = compute_contract_address(
        evm.message.current_target,
        get_account(evm.env.state, evm.message.current_target).nonce,
    )

    if (
        sender.balance < endowment
        or sender.nonce == Uint(2**64 - 1)
        or evm.message.depth + 1 > STACK_DEPTH_LIMIT
    ):
        push(evm.stack, U256(0))
        evm.gas_left += create_message_gas
    elif account_has_code_or_nonce(evm.env.state, contract_address):
        raise ExceptionalHalt
    else:
        call_data = memory_read_bytes(
            evm.memory, memory_start_position, memory_size
        )

        increment_nonce(evm.env.state, evm.message.current_target)

        child_message = Message(
            caller=evm.message.current_target,
            target=Bytes0(),
            gas=create_message_gas,
            value=endowment,
            data=b"",
            code=call_data,
            current_target=contract_address,
            depth=evm.message.depth + 1,
            code_address=None,
            should_transfer_value=True,
        )
        child_evm = process_create_message(child_message, evm.env)
        evm.children.append(child_evm)
        if child_evm.has_erred:
            push(evm.stack, U256(0))
        else:
            evm.logs += child_evm.logs
            push(
                evm.stack, U256.from_be_bytes(child_evm.message.current_target)
            )
        evm.gas_left = child_evm.gas_left
        child_evm.gas_left = U256(0)

    # PROGRAM COUNTER
    evm.pc += 1


def return_(evm: Evm) -> None:
    """
    Halts execution returning output data.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    memory_start_position = pop(evm.stack)
    memory_size = pop(evm.stack)

    # GAS
    extend_memory(evm, memory_start_position, memory_size)
    charge_gas(evm, GAS_ZERO)

    # OPERATION
    evm.output = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    evm.running = False

    # PROGRAM COUNTER
    pass


def do_call(
    evm: Evm,
    gas: Uint,
    value: U256,
    caller: Address,
    to: Address,
    code_address: Address,
    should_transfer_value: bool,
    memory_input_start_position: U256,
    memory_input_size: U256,
    memory_output_start_position: U256,
    memory_output_size: U256,
) -> None:
    """
    Do a message-call. Used by all the `CALL*` opcode family.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    if evm.message.depth + 1 > STACK_DEPTH_LIMIT:
        evm.gas_left += gas
        push(evm.stack, U256(0))
    else:
        call_data = memory_read_bytes(
            evm.memory, memory_input_start_position, memory_input_size
        )
        code = get_account(evm.env.state, code_address).code
        child_message = Message(
            caller=caller,
            target=to,
            gas=U256(gas),
            value=value,
            data=call_data,
            code=code,
            current_target=to,
            depth=evm.message.depth + 1,
            code_address=code_address,
            should_transfer_value=should_transfer_value,
        )
        child_evm = process_message(child_message, evm.env)
        evm.children.append(child_evm)

        if child_evm.has_erred:
            push(evm.stack, U256(0))
        else:
            evm.logs += child_evm.logs
            push(evm.stack, U256(1))

        actual_output_size = min(
            memory_output_size, U256(len(child_evm.output))
        )
        memory_write(
            evm.memory,
            memory_output_start_position,
            child_evm.output[:actual_output_size],
        )
        evm.gas_left += child_evm.gas_left
        child_evm.gas_left = U256(0)


def call(evm: Evm) -> None:
    """
    Message-call into an account.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    gas = Uint(pop(evm.stack))
    to = to_address(pop(evm.stack))
    value = pop(evm.stack)
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS
    extend_memory(evm, memory_input_start_position, memory_input_size)
    extend_memory(evm, memory_output_start_position, memory_output_size)
    call_gas_fee = calculate_call_gas_cost(evm.env.state, gas, to, value)
    charge_gas(evm, call_gas_fee)

    # OPERATION
    sender_balance = get_account(
        evm.env.state, evm.message.current_target
    ).balance
    message_call_gas = gas + calculate_message_call_gas_stipend(value)
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.gas_left += message_call_gas
    else:
        do_call(
            evm,
            message_call_gas,
            value,
            evm.message.current_target,
            to,
            to,
            True,
            memory_input_start_position,
            memory_input_size,
            memory_output_start_position,
            memory_output_size,
        )

    # PROGRAM COUNTER
    evm.pc += 1


def callcode(evm: Evm) -> None:
    """
    Message-call into this account with alternative account’s code.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    gas = Uint(pop(evm.stack))
    code_address = to_address(pop(evm.stack))
    value = pop(evm.stack)
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS
    to = evm.message.current_target

    extend_memory(evm, memory_input_start_position, memory_input_size)
    extend_memory(evm, memory_output_start_position, memory_output_size)
    call_gas_fee = calculate_call_gas_cost(evm.env.state, gas, to, value)
    charge_gas(evm, call_gas_fee)

    # OPERATION
    sender_balance = get_account(
        evm.env.state, evm.message.current_target
    ).balance
    message_call_gas = gas + calculate_message_call_gas_stipend(value)
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.gas_left += message_call_gas
    else:
        do_call(
            evm,
            message_call_gas,
            value,
            evm.message.current_target,
            to,
            code_address,
            True,
            memory_input_start_position,
            memory_input_size,
            memory_output_start_position,
            memory_output_size,
        )

    # PROGRAM COUNTER
    evm.pc += 1


def selfdestruct(evm: Evm) -> None:
    """
    Halt execution and register account for later deletion.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    beneficiary = to_address(pop(evm.stack))

    # GAS
    pass

    # OPERATION
    originator = evm.message.current_target
    beneficiary_balance = get_account(evm.env.state, beneficiary).balance
    originator_balance = get_account(evm.env.state, originator).balance

    # First Transfer to beneficiary
    set_account_balance(
        evm.env.state, beneficiary, beneficiary_balance + originator_balance
    )
    # Next, Zero the balance of the address being deleted (must come after
    # sending to beneficiary in case the contract named itself as the
    # beneficiary).
    set_account_balance(evm.env.state, originator, U256(0))

    # register account for deletion
    evm.accounts_to_delete.add(originator)

    # HALT the execution
    evm.running = False

    # PROGRAM COUNTER
    pass


def delegatecall(evm: Evm) -> None:
    """
    Message-call into an account.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    gas = Uint(pop(evm.stack))
    code_address = to_address(pop(evm.stack))
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS
    extend_memory(evm, memory_input_start_position, memory_input_size)
    extend_memory(evm, memory_output_start_position, memory_output_size)
    charge_gas(evm, GAS_CALL + gas)

    # OPERATION
    do_call(
        evm,
        gas,
        evm.message.value,
        evm.message.caller,
        evm.message.current_target,
        code_address,
        False,
        memory_input_start_position,
        memory_input_size,
        memory_output_start_position,
        memory_output_size,
    )

    # PROGRAM COUNTER
    evm.pc += 1
