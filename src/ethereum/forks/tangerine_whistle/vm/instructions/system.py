"""
Ethereum Virtual Machine (EVM) System Instructions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM system related instructions.
"""

from dataclasses import dataclass
from typing import final

from ethereum_types.bytes import Bytes0
from ethereum_types.numeric import U256, Uint

from ethereum.state import Address

from ...state_tracker import (
    account_deployable,
    account_exists,
    get_account,
    get_code,
    increment_nonce,
    set_account_balance,
)
from ...utils.address import compute_contract_address, to_address_masked
from .. import (
    Evm,
    Message,
    incorporate_child_on_error,
    incorporate_child_on_success,
)
from ..gas import (
    GasCosts,
    calculate_gas_extend_memory,
    calculate_message_call_gas,
    charge_gas,
    max_message_call_gas,
)
from ..memory import memory_read_bytes, memory_write
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
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_position, memory_size)]
    )

    charge_gas(evm, GasCosts.OPCODE_CREATE_BASE + extend_memory.cost)

    create_message_gas = max_message_call_gas(Uint(evm.gas_left))
    evm.gas_left -= create_message_gas

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    sender_address = evm.message.current_target
    sender = get_account(evm.message.tx_env.state, sender_address)

    contract_address = compute_contract_address(
        evm.message.current_target,
        get_account(
            evm.message.tx_env.state, evm.message.current_target
        ).nonce,
    )

    if (
        sender.balance < endowment
        or sender.nonce == Uint(2**64 - 1)
        or evm.message.depth + Uint(1) > STACK_DEPTH_LIMIT
    ):
        push(evm.stack, U256(0))
        evm.gas_left += create_message_gas
    elif not account_deployable(evm.message.tx_env.state, contract_address):
        increment_nonce(evm.message.tx_env.state, evm.message.current_target)
        push(evm.stack, U256(0))
    else:
        call_data = memory_read_bytes(
            evm.memory, memory_start_position, memory_size
        )

        increment_nonce(evm.message.tx_env.state, evm.message.current_target)

        child_message = Message(
            block_env=evm.message.block_env,
            tx_env=evm.message.tx_env,
            caller=evm.message.current_target,
            target=Bytes0(),
            gas=create_message_gas,
            value=endowment,
            data=b"",
            code=call_data,
            current_target=contract_address,
            depth=evm.message.depth + Uint(1),
            code_address=None,
            should_transfer_value=True,
            parent_evm=evm,
        )
        child_evm = process_create_message(child_message)

        if child_evm.error:
            incorporate_child_on_error(evm, child_evm)
            push(evm.stack, U256(0))
        else:
            incorporate_child_on_success(evm, child_evm)
            push(
                evm.stack, U256.from_be_bytes(child_evm.message.current_target)
            )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


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
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_position, memory_size)]
    )

    charge_gas(evm, GasCosts.ZERO + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    evm.output = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    evm.running = False

    # PROGRAM COUNTER
    pass


@final
@dataclass
class GenericCall:
    """
    Parameters for the core logic of the `CALL*` family of opcodes.
    """

    gas: Uint
    value: U256
    caller: Address
    to: Address
    code_address: Address
    should_transfer_value: bool
    memory_input_start_position: U256
    memory_input_size: U256
    memory_output_start_position: U256
    memory_output_size: U256


def generic_call(evm: Evm, params: GenericCall) -> None:
    """
    Perform the core logic of the `CALL*` family of opcodes.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    if evm.message.depth + Uint(1) > STACK_DEPTH_LIMIT:
        evm.gas_left += params.gas
        push(evm.stack, U256(0))
        return

    call_data = memory_read_bytes(
        evm.memory,
        params.memory_input_start_position,
        params.memory_input_size,
    )
    account = get_account(evm.message.tx_env.state, params.code_address)
    code = get_code(evm.message.tx_env.state, account.code_hash)
    child_message = Message(
        block_env=evm.message.block_env,
        tx_env=evm.message.tx_env,
        caller=params.caller,
        target=params.to,
        gas=params.gas,
        value=params.value,
        data=call_data,
        code=code,
        current_target=params.to,
        depth=evm.message.depth + Uint(1),
        code_address=params.code_address,
        should_transfer_value=params.should_transfer_value,
        parent_evm=evm,
    )
    child_evm = process_message(child_message)

    if child_evm.error:
        incorporate_child_on_error(evm, child_evm)
        push(evm.stack, U256(0))
    else:
        incorporate_child_on_success(evm, child_evm)
        push(evm.stack, U256(1))

    actual_output_size = min(
        params.memory_output_size, U256(len(child_evm.output))
    )
    memory_write(
        evm.memory,
        params.memory_output_start_position,
        child_evm.output[:actual_output_size],
    )


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
    to = to_address_masked(pop(evm.stack))
    value = pop(evm.stack)
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory,
        [
            (memory_input_start_position, memory_input_size),
            (memory_output_start_position, memory_output_size),
        ],
    )

    code_address = to

    _account_exists = account_exists(evm.message.tx_env.state, to)
    create_gas_cost = Uint(0) if _account_exists else GasCosts.NEW_ACCOUNT
    transfer_gas_cost = Uint(0) if value == 0 else GasCosts.CALL_VALUE
    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        memory_cost=extend_memory.cost,
        extra_gas=GasCosts.OPCODE_CALL_BASE
        + create_gas_cost
        + transfer_gas_cost,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    sender_balance = get_account(
        evm.message.tx_env.state, evm.message.current_target
    ).balance
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.gas_left += message_call_gas.sub_call
    else:
        generic_call(
            evm,
            GenericCall(
                gas=message_call_gas.sub_call,
                value=value,
                caller=evm.message.current_target,
                to=to,
                code_address=code_address,
                should_transfer_value=True,
                memory_input_start_position=memory_input_start_position,
                memory_input_size=memory_input_size,
                memory_output_start_position=memory_output_start_position,
                memory_output_size=memory_output_size,
            ),
        )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


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
    code_address = to_address_masked(pop(evm.stack))
    value = pop(evm.stack)
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS
    to = evm.message.current_target

    extend_memory = calculate_gas_extend_memory(
        evm.memory,
        [
            (memory_input_start_position, memory_input_size),
            (memory_output_start_position, memory_output_size),
        ],
    )
    transfer_gas_cost = Uint(0) if value == 0 else GasCosts.CALL_VALUE
    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        GasCosts.OPCODE_CALL_BASE + transfer_gas_cost,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    sender_balance = get_account(
        evm.message.tx_env.state, evm.message.current_target
    ).balance
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.gas_left += message_call_gas.sub_call
    else:
        generic_call(
            evm,
            GenericCall(
                gas=message_call_gas.sub_call,
                value=value,
                caller=evm.message.current_target,
                to=to,
                code_address=code_address,
                should_transfer_value=True,
                memory_input_start_position=memory_input_start_position,
                memory_input_size=memory_input_size,
                memory_output_start_position=memory_output_start_position,
                memory_output_size=memory_output_size,
            ),
        )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def selfdestruct(evm: Evm) -> None:
    """
    Halt execution and register account for later deletion.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    beneficiary = to_address_masked(pop(evm.stack))

    # GAS
    gas_cost = GasCosts.OPCODE_SELFDESTRUCT_BASE
    if not account_exists(evm.message.tx_env.state, beneficiary):
        gas_cost += GasCosts.OPCODE_SELFDESTRUCT_NEW_ACCOUNT

    originator = evm.message.current_target

    refunded_accounts = evm.accounts_to_delete
    parent_evm = evm.message.parent_evm
    while parent_evm is not None:
        refunded_accounts.update(parent_evm.accounts_to_delete)
        parent_evm = parent_evm.message.parent_evm

    if originator not in refunded_accounts:
        evm.refund_counter += GasCosts.REFUND_SELF_DESTRUCT

    charge_gas(evm, gas_cost)

    # OPERATION
    beneficiary_balance = get_account(
        evm.message.tx_env.state, beneficiary
    ).balance
    originator_balance = get_account(
        evm.message.tx_env.state, originator
    ).balance

    # First Transfer to beneficiary
    set_account_balance(
        evm.message.tx_env.state,
        beneficiary,
        beneficiary_balance + originator_balance,
    )
    # Next, Zero the balance of the address being deleted (must come after
    # sending to beneficiary in case the contract named itself as the
    # beneficiary).
    set_account_balance(evm.message.tx_env.state, originator, U256(0))

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
    code_address = to_address_masked(pop(evm.stack))
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory,
        [
            (memory_input_start_position, memory_input_size),
            (memory_output_start_position, memory_output_size),
        ],
    )
    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        GasCosts.OPCODE_CALL_BASE,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    generic_call(
        evm,
        GenericCall(
            gas=message_call_gas.sub_call,
            value=evm.message.value,
            caller=evm.message.caller,
            to=evm.message.current_target,
            code_address=code_address,
            should_transfer_value=False,
            memory_input_start_position=memory_input_start_position,
            memory_input_size=memory_input_size,
            memory_output_start_position=memory_output_start_position,
            memory_output_size=memory_output_size,
        ),
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)
