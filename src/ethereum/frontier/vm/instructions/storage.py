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

from ethereum.base_types import U256

from .. import Evm
from ..gas import (
    GAS_STORAGE_CLEAR_REFUND,
    GAS_STORAGE_SET,
    GAS_STORAGE_UPDATE,
    subtract_gas,
)
from ..stack import pop


def sstore(evm: Evm) -> None:
    """
    Stores a value at a certain key in the current context's storage.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `20000`.
    """
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)
    current_value = evm.env.state[evm.current].storage.get(key, U256(0))

    # TODO: SSTORE gas usage hasn't been tested yet. Testing this needs
    # other opcodes to be implemented.
    # Calculating the gas needed for the storage
    if new_value != 0 and current_value == 0:
        gas_cost = GAS_STORAGE_SET
    else:
        gas_cost = GAS_STORAGE_UPDATE

    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    # TODO: Refund counter hasn't been tested yet. Testing this needs other
    # Opcodes to be implemented
    if new_value == 0 and current_value != 0:
        evm.refund_counter += GAS_STORAGE_CLEAR_REFUND

    if new_value == 0:
        # Deletes a k-v pair from dict if key is present, else does nothing
        evm.env.state[evm.current].storage.pop(key, None)
    else:
        evm.env.state[evm.current].storage[key] = new_value
