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

from ...state_tracker import (
    get_storage,
    get_storage_original,
    get_transient_storage,
    set_storage,
    set_transient_storage,
)
from .. import Evm
from ..exceptions import WriteInStaticContext
from ..gas import (
    GAS_CALL_STIPEND,
    GAS_COLD_STORAGE_ACCESS,
    GAS_STORAGE_UPDATE,
    GAS_WARM_ACCESS,
    REFUND_STORAGE_CLEAR,
    STATE_BYTES_PER_STORAGE_SET,
    charge_gas,
    charge_state_gas,
    check_gas,
    state_gas_per_byte,
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
        charge_gas(evm, GasCosts.WARM_ACCESS)
    else:
        evm.accessed_storage_keys.add((evm.message.current_target, key))
        charge_gas(evm, GasCosts.COLD_STORAGE_ACCESS)

    # OPERATION
    tx_state = evm.message.tx_env.state
    value = get_storage(tx_state, evm.message.current_target, key)

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
    if evm.message.is_static:
        raise WriteInStaticContext

    # STACK
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)

    # check we have at least the stipend gas
    check_gas(evm, GasCosts.CALL_STIPEND + Uint(1))

    tx_state = evm.message.tx_env.state
    original_value = get_storage_original(
        tx_state, evm.message.current_target, key
    )
    current_value = get_storage(tx_state, evm.message.current_target, key)

    cost_per_state_byte = state_gas_per_byte(
        evm.message.block_env.block_gas_limit
    )
    state_gas_storage_set = STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte
    gas_cost = Uint(0)

    if (evm.message.current_target, key) not in evm.accessed_storage_keys:
        evm.accessed_storage_keys.add((evm.message.current_target, key))
        gas_cost += GasCosts.COLD_STORAGE_ACCESS

    if original_value == current_value and current_value != new_value:
        if original_value == 0:
            charge_state_gas(evm, state_gas_storage_set)
        # charge regular cost for the operation, even when we
        # already charge state gas for state creation
        gas_cost += GAS_STORAGE_UPDATE - GAS_COLD_STORAGE_ACCESS
    else:
        gas_cost += GasCosts.WARM_ACCESS

    # Refund Counter Calculation
    if current_value != new_value:
        if original_value != 0 and current_value != 0 and new_value == 0:
            # Storage is cleared for the first time in the transaction
            evm.refund_counter += GasCosts.REFUND_STORAGE_CLEAR

        if original_value != 0 and current_value == 0:
            # Gas refund issued earlier to be reversed
            evm.refund_counter -= GasCosts.REFUND_STORAGE_CLEAR

        if original_value == new_value:
            # Storage slot being restored to its original value
            if original_value == 0:
                # Slot was originally empty and was SET earlier.
                # Refund state gas and the write cost (the write
                # is cancelled — clients batch trie writes to slot
                # boundaries, so no IO actually happens).
                evm.refund_counter += int(
                    state_gas_storage_set
                    + GAS_STORAGE_UPDATE
                    - GAS_COLD_STORAGE_ACCESS
                    - GAS_WARM_ACCESS
                )
            else:
                # Slot was originally non-empty and was UPDATED earlier
                evm.refund_counter += int(
                    GAS_STORAGE_UPDATE
                    - GAS_COLD_STORAGE_ACCESS
                    - GAS_WARM_ACCESS
                )

    charge_gas(evm, gas_cost)
    set_storage(tx_state, evm.message.current_target, key, new_value)

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
    charge_gas(evm, GasCosts.WARM_ACCESS)

    # OPERATION
    value = get_transient_storage(
        evm.message.tx_env.state, evm.message.current_target, key
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
    if evm.message.is_static:
        raise WriteInStaticContext

    # STACK
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.WARM_ACCESS)
    set_transient_storage(
        evm.message.tx_env.state,
        evm.message.current_target,
        key,
        new_value,
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)
