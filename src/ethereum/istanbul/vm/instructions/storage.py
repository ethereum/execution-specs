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
from ethereum.utils.ensure import ensure

from ...state import get_storage, set_storage
from ...trie import trie_get
from .. import Evm
from ..error import OutOfGasError, WriteInStaticContext
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
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
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
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `20000`.
    """
    if evm.gas_left <= GAS_CALL_STIPEND:
        raise OutOfGasError

    ensure(not evm.message.is_static, WriteInStaticContext)
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)
    current_value = get_storage(evm.env.state, evm.message.current_target, key)

    _, original_trie = evm.env.state._snapshots[0]
    original_account_trie = original_trie.get(evm.message.current_target)

    if original_account_trie is None:
        original_value = U256(0)
    else:
        original_value = trie_get(original_account_trie, key)

    assert isinstance(original_value, U256)

    if current_value == new_value:
        gas_cost = GAS_SLOAD
    else:
        if original_value == current_value:
            if original_value == 0:
                gas_cost = GAS_STORAGE_SET
            else:
                gas_cost = GAS_STORAGE_UPDATE
                if new_value == 0:
                    evm.refund_counter += int(GAS_STORAGE_CLEAR_REFUND)
        else:
            gas_cost = GAS_SLOAD
            if original_value != 0:
                if current_value == 0:
                    evm.refund_counter -= int(GAS_STORAGE_CLEAR_REFUND)
                if new_value == 0:
                    evm.refund_counter += int(GAS_STORAGE_CLEAR_REFUND)
            if original_value == new_value:
                if original_value == 0:
                    evm.refund_counter += int(GAS_STORAGE_SET - GAS_SLOAD)
                else:
                    evm.refund_counter += int(GAS_STORAGE_UPDATE - GAS_SLOAD)

    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    set_storage(evm.env.state, evm.message.current_target, key, new_value)

    evm.pc += 1
