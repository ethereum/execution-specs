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
from ethereum.base_types import U256, Uint

from ...state import get_account, increment_nonce
from ...utils.address import compute_contract_address
from .. import Evm, Message
from ..gas import (
    GAS_CREATE,
    GAS_ZERO,
    calculate_gas_extend_memory,
    subtract_gas,
)
from ..memory import extend_memory, memory_read_bytes
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

    endowment = pop(evm.stack)
    memory_start_position = Uint(pop(evm.stack))
    memory_size = pop(evm.stack)

    gas_cost = GAS_CREATE + calculate_gas_extend_memory(
        evm.memory, memory_start_position, memory_size
    )
    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)
    extend_memory(evm.memory, memory_start_position, memory_size)
    sender_address = evm.env.origin
    sender = get_account(evm.env.state, sender_address)
    if sender.balance < endowment:
        push(evm.stack, U256(0))
        return None

    if evm.message.depth + 1 > STACK_DEPTH_LIMIT:
        push(evm.stack, U256(0))
        return None

    call_data = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    increment_nonce(evm.env.state, evm.message.current_target)
    contract_address = compute_contract_address(
        evm.message.current_target,
        get_account(evm.env.state, evm.message.current_target).nonce - U256(1),
    )

    gas_left = evm.gas_left
    evm.gas_left = subtract_gas(evm.gas_left, gas_left)

    child_message = Message(
        caller=evm.message.current_target,
        target=b"",
        gas=gas_left,
        value=endowment,
        data=b"",
        code=call_data,
        current_target=contract_address,
        depth=evm.message.depth + 1,
    )
    child_evm = process_create_message(child_message, evm.env)
    push(evm.stack, U256.from_be_bytes(child_evm.message.current_target))
    evm.gas_left = child_evm.gas_left


def return_(evm: Evm) -> None:
    """
    Halts execution returning output data.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    memory_start_position = Uint(pop(evm.stack))
    memory_size = pop(evm.stack)
    gas_cost = GAS_ZERO + calculate_gas_extend_memory(
        evm.memory, memory_start_position, memory_size
    )
    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)
    extend_memory(evm.memory, memory_start_position, memory_size)
    evm.output = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )
    # HALT the execution
    evm.running = False
