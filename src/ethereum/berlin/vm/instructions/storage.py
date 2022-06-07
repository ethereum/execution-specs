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
from ethereum.utils.ensure import ensure

from ...state import get_storage, get_storage_original, set_storage
from .. import Evm
from ..exceptions import OutOfGasError, WriteInStaticContext
from ..gas import (
    GAS_CALL_STIPEND,
    GAS_SLOAD,
    GAS_STORAGE_CLEAR_REFUND,
    GAS_STORAGE_SET,
    GAS_STORAGE_UPDATE,
    subtract_gas,
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

    Raises
    ------
    :py:class:`~ethereum.berlin.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.berlin.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `50`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_SLOAD)

    key = pop(evm.stack).to_be_bytes32()
    value = get_storage(evm.env.state, evm.message.current_target, key)

    push(evm.stack, value)

    evm.pc += 1


def sstore(evm: Evm) -> None:
    """
    Stores a value at a certain key in the current context's storage.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.berlin.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.berlin.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `20000`.
    """
    ensure(evm.gas_left > GAS_CALL_STIPEND, OutOfGasError)
    ensure(not evm.message.is_static, WriteInStaticContext)

    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)
    current_value = get_storage(evm.env.state, evm.message.current_target, key)

    original_value = get_storage_original(
        evm.env.state, evm.message.current_target, key
    )

    # Gas Cost Calculation
    gas_cost = GAS_SLOAD

    if original_value == current_value and current_value != new_value:
        if original_value == 0:
            gas_cost = GAS_STORAGE_SET
        else:
            gas_cost = GAS_STORAGE_UPDATE

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
                evm.refund_counter += int(GAS_STORAGE_SET - GAS_SLOAD)
            else:
                # Slot was originally non-empty and was UPDATED earlier
                evm.refund_counter += int(GAS_STORAGE_UPDATE - GAS_SLOAD)

    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    set_storage(evm.env.state, evm.message.current_target, key, new_value)

    evm.pc += 1
