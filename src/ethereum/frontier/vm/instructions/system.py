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
from typing import List

from ethereum.base_types import U256, Bytes0, Uint
from ethereum.utils.safe_arithmetic import u256_safe_add

from ...eth_types import Address
from ...state import (
    account_has_code_or_nonce,
    get_account,
    increment_nonce,
    set_account_balance,
)
from ...utils.address import compute_contract_address, to_address
from ...vm.error import OutOfGasError
from .. import Evm, Message
from ..gas import (
    GAS_CREATE,
    GAS_ZERO,
    calculate_call_gas_cost,
    calculate_message_call_gas_stipend,
    subtract_gas,
)
from ..memory import memory_read_bytes, memory_write, touch_memory
from ..operation import Operation, static_gas


def gas_create(
    evm: Evm,
    stack: List[U256],
    memory_size: U256,
    memory_start_position: U256,
    endowment: U256,
) -> None:
    """
    Creates a new account with associated code.
    """
    subtract_gas(evm, GAS_CREATE)
    touch_memory(evm, memory_start_position, memory_size)


def do_create(
    evm: Evm,
    stack: List[U256],
    memory_size: U256,
    memory_start_position: U256,
    endowment: U256,
) -> U256:
    """
    Creates a new account with associated code.
    """
    # This import causes a circular import error
    # if it's not moved inside this method
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_create_message

    call_data = memory_read_bytes(evm, memory_start_position, memory_size)

    sender_address = evm.message.current_target
    sender = get_account(evm.env.state, sender_address)

    if sender.balance < endowment:
        return U256(0)

    if sender.nonce == Uint(2**64 - 1):
        return U256(0)

    if evm.message.depth + 1 > STACK_DEPTH_LIMIT:
        return U256(0)

    increment_nonce(evm.env.state, evm.message.current_target)

    create_message_gas = evm.gas_left
    subtract_gas(evm, create_message_gas)

    contract_address = compute_contract_address(
        evm.message.current_target,
        get_account(evm.env.state, evm.message.current_target).nonce - U256(1),
    )
    is_collision = account_has_code_or_nonce(evm.env.state, contract_address)
    if is_collision:
        return U256(0)

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
    )
    child_evm = process_create_message(child_message, evm.env)
    evm.children.append(child_evm)
    evm.gas_left = child_evm.gas_left
    child_evm.gas_left = U256(0)
    if child_evm.has_erred:
        return U256(0)
    else:
        evm.logs += child_evm.logs
        return U256.from_be_bytes(child_evm.message.current_target)


create = Operation(gas_create, do_create, 3, 1)


def gas_return(
    evm: Evm,
    stack: List[U256],
    memory_size: U256,
    memory_start_position: U256,
) -> None:
    """
    Halts execution returning output data.
    """
    subtract_gas(evm, GAS_ZERO)
    touch_memory(evm, memory_start_position, memory_size)


def do_return(
    evm: Evm,
    stack: List[U256],
    memory_size: U256,
    memory_start_position: U256,
) -> None:
    """
    Halts execution returning output data.
    """
    evm.output = memory_read_bytes(evm, memory_start_position, memory_size)
    # HALT the execution
    evm.running = False


return_ = Operation(gas_return, do_return, 2, 0)


def do_general_call(
    evm: Evm,
    gas: U256,
    to: Address,
    code_address: Address,
    value: U256,
    memory_input_start_position: U256,
    memory_input_size: U256,
    memory_output_start_position: U256,
    memory_output_size: U256,
) -> U256:
    """
    Message-call into an account.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    call_data = memory_read_bytes(
        evm, memory_input_start_position, memory_input_size
    )

    message_call_gas_fee = u256_safe_add(
        gas,
        calculate_message_call_gas_stipend(value),
        exception_type=OutOfGasError,
    )

    sender_balance = get_account(
        evm.env.state, evm.message.current_target
    ).balance

    if sender_balance < value:
        evm.gas_left += message_call_gas_fee
        return U256(0)
    if evm.message.depth + 1 > STACK_DEPTH_LIMIT:
        evm.gas_left += message_call_gas_fee
        return U256(0)

    code = get_account(evm.env.state, code_address).code
    child_message = Message(
        caller=evm.message.current_target,
        target=to,
        gas=message_call_gas_fee,
        value=value,
        data=call_data,
        code=code,
        current_target=to,
        depth=evm.message.depth + 1,
        code_address=code_address,
    )
    child_evm = process_message(child_message, evm.env)
    evm.children.append(child_evm)

    actual_output_size = min(memory_output_size, U256(len(child_evm.output)))
    memory_write(
        evm,
        memory_output_start_position,
        child_evm.output[:actual_output_size],
    )

    evm.gas_left += child_evm.gas_left
    child_evm.gas_left = U256(0)

    if child_evm.has_erred:
        return U256(0)
    else:
        evm.logs += child_evm.logs
        return U256(1)


def gas_call(
    evm: Evm,
    stack: List[U256],
    memory_output_size: U256,
    memory_output_start_position: U256,
    memory_input_size: U256,
    memory_input_start_position: U256,
    value: U256,
    to: U256,
    gas: U256,
) -> None:
    """
    Message-call into an account.
    """
    touch_memory(evm, memory_input_start_position, memory_input_size)
    touch_memory(evm, memory_output_start_position, memory_output_size)
    subtract_gas(
        evm, calculate_call_gas_cost(evm.env.state, gas, to_address(to), value)
    )


def do_call(
    evm: Evm,
    stack: List[U256],
    memory_output_size: U256,
    memory_output_start_position: U256,
    memory_input_size: U256,
    memory_input_start_position: U256,
    value: U256,
    to: U256,
    gas: U256,
) -> U256:
    """
    Message-call into an account.
    """
    return do_general_call(
        evm,
        gas,
        to_address(to),
        to_address(to),
        value,
        memory_input_start_position,
        memory_input_size,
        memory_output_start_position,
        memory_output_size,
    )


call = Operation(gas_call, do_call, 7, 1)


def gas_callcode(
    evm: Evm,
    stack: List[U256],
    memory_output_size: U256,
    memory_output_start_position: U256,
    memory_input_size: U256,
    memory_input_start_position: U256,
    value: U256,
    code_address: U256,
    gas: U256,
) -> None:
    """
    Message-call into this account with alternative account’s code.
    """
    touch_memory(evm, memory_input_start_position, memory_input_size)
    touch_memory(evm, memory_output_start_position, memory_output_size)
    subtract_gas(
        evm,
        calculate_call_gas_cost(
            evm.env.state, gas, evm.message.current_target, value
        ),
    )


def do_callcode(
    evm: Evm,
    stack: List[U256],
    memory_output_size: U256,
    memory_output_start_position: U256,
    memory_input_size: U256,
    memory_input_start_position: U256,
    value: U256,
    code_address: U256,
    gas: U256,
) -> U256:
    """
    Message-call into this account with alternative account’s code.
    """
    return do_general_call(
        evm,
        gas,
        evm.message.current_target,
        to_address(code_address),
        value,
        memory_input_start_position,
        memory_input_size,
        memory_output_start_position,
        memory_output_size,
    )


callcode = Operation(gas_callcode, do_callcode, 7, 1)


def do_selfdestruct(
    evm: Evm, stack: List[U256], beneficiary_u256: U256
) -> None:
    """
    Halt execution and register account for later deletion.
    """
    beneficiary = to_address(beneficiary_u256)

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


selfdestruct = Operation(static_gas(GAS_ZERO), do_selfdestruct, 1, 0)
