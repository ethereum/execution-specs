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
from typing import List

from ethereum.base_types import U256

from ...state import get_storage, set_storage
from .. import Evm
from ..gas import (
    GAS_SLOAD,
    GAS_STORAGE_CLEAR_REFUND,
    GAS_STORAGE_SET,
    GAS_STORAGE_UPDATE,
    subtract_gas,
)
from ..operation import Operation, static_gas


def do_sload(evm: Evm, stack: List[U256], key: U256) -> U256:
    """
    Loads to the stack, the value corresponding to a certain key from the
    storage of the current account.
    """
    return get_storage(
        evm.env.state, evm.message.current_target, key.to_be_bytes32()
    )


sload = Operation(static_gas(GAS_SLOAD), do_sload, 1, 1)


def gas_sstore(
    evm: Evm, stack: List[U256], new_value: U256, key: U256
) -> None:
    """
    Stores a value at a certain key in the current context's storage.
    """
    current_value = get_storage(
        evm.env.state, evm.message.current_target, key.to_be_bytes32()
    )

    if new_value != 0 and current_value == 0:
        subtract_gas(evm, GAS_STORAGE_SET)
    else:
        subtract_gas(evm, GAS_STORAGE_UPDATE)

    if new_value == 0 and current_value != 0:
        evm.refund_counter += GAS_STORAGE_CLEAR_REFUND


def do_sstore(evm: Evm, stack: List[U256], new_value: U256, key: U256) -> None:
    """
    Stores a value at a certain key in the current context's storage.
    """
    set_storage(
        evm.env.state,
        evm.message.current_target,
        key.to_be_bytes32(),
        new_value,
    )


sstore = Operation(gas_sstore, do_sstore, 2, 0)
