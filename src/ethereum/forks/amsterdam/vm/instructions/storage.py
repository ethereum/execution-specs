"""
Ethereum Virtual Machine (EVM) Storage Instructions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM storage related instructions.
"""

from ethereum_types.numeric import Uint

from ...block_access_lists.tracker import (
    track_storage_read,
    track_storage_write,
)
from ...state import (
    get_storage,
    get_storage_original,
    get_transient_storage,
    set_storage,
    set_transient_storage,
)
from .. import Evm
from ..exceptions import OutOfGasError, WriteInStaticContext
from ..gas import (
    GAS_CALL_STIPEND,
    GAS_COLD_SLOAD,
    GAS_STORAGE_CLEAR_REFUND,
    GAS_STORAGE_SET,
    GAS_STORAGE_UPDATE,
    GAS_WARM_ACCESS,
    charge_gas,
    check_gas,
)
from ..stack import pop, push


def sload(evm: Evm) -> None:
    """
    Loads to the stack, the value corresponding to a certain key from the
    storage of the current account.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    key = pop(evm.stack).to_be_bytes32()

    # GAS
    gas_cost = (
        GAS_WARM_ACCESS
        if (evm.message.current_target, key) in evm.accessed_storage_keys
        else GAS_COLD_SLOAD
    )
    check_gas(evm, gas_cost)
    if (evm.message.current_target, key) not in evm.accessed_storage_keys:
        evm.accessed_storage_keys.add((evm.message.current_target, key))
    track_storage_read(
        evm.message.block_env,
        evm.message.current_target,
        key,
    )
    charge_gas(evm, gas_cost)

    # OPERATION
    state = evm.message.block_env.state
    value = get_storage(state, evm.message.current_target, key)

    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sstore(evm: Evm) -> None:
    """
    Stores a value at a certain key in the current context's storage.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)
    if evm.gas_left <= GAS_CALL_STIPEND:
        raise OutOfGasError

    state = evm.message.block_env.state
    original_value = get_storage_original(
        state, evm.message.current_target, key
    )
    current_value = get_storage(state, evm.message.current_target, key)
    track_storage_read(
        evm.message.block_env,
        evm.message.current_target,
        key,
    )

    # GAS
    gas_cost = Uint(0)
    is_cold_access = (
        evm.message.current_target,
        key,
    ) not in evm.accessed_storage_keys

    if is_cold_access:
        gas_cost += GAS_COLD_SLOAD

    if original_value == current_value and current_value != new_value:
        if original_value == 0:
            gas_cost += GAS_STORAGE_SET
        else:
            gas_cost += GAS_STORAGE_UPDATE - GAS_COLD_SLOAD
    else:
        gas_cost += GAS_WARM_ACCESS

    check_gas(evm, gas_cost)

    if is_cold_access:
        evm.accessed_storage_keys.add((evm.message.current_target, key))

    charge_gas(evm, gas_cost)
    if evm.message.is_static:
        raise WriteInStaticContext

    # REFUND COUNTER
    if current_value != new_value:
        if original_value != 0 and current_value != 0 and new_value == 0:
            # Storage is cleared for the first time in the transaction
            evm.refund_counter += int(GAS_STORAGE_CLEAR_REFUND)

        if original_value != 0 and current_value == 0:
            # Gas refund issued earlier to be reversed
            evm.refund_counter -= int(GAS_STORAGE_CLEAR_REFUND)

        if original_value == new_value:
            # Storage slot being restored to its original value
            if original_value == 0:
                # Slot was originally empty and was SET earlier
                evm.refund_counter += int(GAS_STORAGE_SET - GAS_WARM_ACCESS)
            else:
                # Slot was originally non-empty and was UPDATED earlier
                evm.refund_counter += int(
                    GAS_STORAGE_UPDATE - GAS_COLD_SLOAD - GAS_WARM_ACCESS
                )

    # OPERATION
    set_storage(state, evm.message.current_target, key, new_value)
    track_storage_write(
        evm.message.block_env,
        evm.message.current_target,
        key,
        new_value,
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def tload(evm: Evm) -> None:
    """
    Loads to the stack, the value corresponding to a certain key from the
    transient storage of the current account.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    key = pop(evm.stack).to_be_bytes32()

    # GAS
    charge_gas(evm, GAS_WARM_ACCESS)

    # OPERATION
    value = get_transient_storage(
        evm.message.tx_env.transient_storage, evm.message.current_target, key
    )
    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def tstore(evm: Evm) -> None:
    """
    Stores a value at a certain key in the current context's transient storage.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_WARM_ACCESS)
    if evm.message.is_static:
        raise WriteInStaticContext
    set_transient_storage(
        evm.message.tx_env.transient_storage,
        evm.message.current_target,
        key,
        new_value,
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)
