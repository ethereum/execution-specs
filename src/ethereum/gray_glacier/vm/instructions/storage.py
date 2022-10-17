"""
Ethereum Virtual Machine (EVM) Storage Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM storage related instructions.
"""
from ethereum.base_types import Uint
from ethereum.utils.ensure import ensure

from ...state import get_storage, get_storage_original, set_storage
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
    if (evm.message.current_target, key) in evm.accessed_storage_keys:
        charge_gas(evm, GAS_WARM_ACCESS)
    else:
        evm.accessed_storage_keys.add((evm.message.current_target, key))
        charge_gas(evm, GAS_COLD_SLOAD)

    # OPERATION
    value = get_storage(evm.env.state, evm.message.current_target, key)

    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += 1


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

    # GAS
    ensure(evm.gas_left > GAS_CALL_STIPEND, OutOfGasError)

    original_value = get_storage_original(
        evm.env.state, evm.message.current_target, key
    )
    current_value = get_storage(evm.env.state, evm.message.current_target, key)

    gas_cost = Uint(0)

    if (evm.message.current_target, key) not in evm.accessed_storage_keys:
        evm.accessed_storage_keys.add((evm.message.current_target, key))
        gas_cost += GAS_COLD_SLOAD

    if original_value == current_value and current_value != new_value:
        if original_value == 0:
            gas_cost += GAS_STORAGE_SET
        else:
            gas_cost += GAS_STORAGE_UPDATE - GAS_COLD_SLOAD
    else:
        gas_cost += GAS_WARM_ACCESS

    charge_gas(evm, gas_cost)

    # Refund Counter Calculation
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
    ensure(not evm.message.is_static, WriteInStaticContext)
    set_storage(evm.env.state, evm.message.current_target, key, new_value)

    # PROGRAM COUNTER
    evm.pc += 1
