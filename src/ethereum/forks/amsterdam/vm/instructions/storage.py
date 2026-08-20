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

from ...fork_types import ExecutionGas, StateGas
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
    GasCosts,
    StateGasCosts,
    charge_gas,
    charge_state_gas,
    check_gas,
    credit_frame_state_gas_refund,
    credit_state_gas_refund,
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
    if (evm.current_target, key) in evm.accessed_storage_keys:
        charge_gas(evm, GasCosts.WARM_ACCESS)
    else:
        evm.accessed_storage_keys.add((evm.current_target, key))
        charge_gas(evm, GasCosts.COLD_STORAGE_ACCESS)

    # OPERATION
    tx_state = evm.tx_env.state
    value = get_storage(tx_state, evm.current_target, key)

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
    if evm.is_static:
        raise WriteInStaticContext

    # STACK
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)

    # GAS (STATE-INDEPENDENT)
    # Price what is computable without touching state, and check it is
    # affordable before any state access is performed.
    gas_cost = GasCosts.ZERO

    # Access cost: cold or warm, always charged.
    is_cold_access = (
        evm.current_target,
        key,
    ) not in evm.accessed_storage_keys
    if is_cold_access:
        gas_cost += GasCosts.COLD_STORAGE_ACCESS
    else:
        gas_cost += GasCosts.WARM_ACCESS

    # Gas must cover the access cost before the state access below
    # records the slot read in the Block Access List. Post-repricing the
    # access cost can exceed the stipend, so the EIP-2200 stipend sentry
    # (`gas_left > CALL_STIPEND`) is no longer sufficient on its own.
    check_gas(
        evm, max(gas_cost, ExecutionGas(GasCosts.CALL_STIPEND + Uint(1)))
    )

    # STATE ACCESS (STATE-DEPENDENT GAS)
    # Perform the access and complete the state-dependent pricing from
    # the slot's original and current values, adjusting the
    # transaction's refunds.
    if is_cold_access:
        evm.accessed_storage_keys.add((evm.current_target, key))

    tx_state = evm.tx_env.state
    original_value = get_storage_original(tx_state, evm.current_target, key)
    current_value = get_storage(tx_state, evm.current_target, key)

    state_gas = StateGas(Uint(0))

    # Write cost: charged on the first change to the slot this transaction.
    if original_value == current_value and current_value != new_value:
        gas_cost += GasCosts.STORAGE_WRITE

    # Refund Counter Calculation
    if current_value != new_value:
        if original_value != 0 and current_value != 0 and new_value == 0:
            # Storage is cleared for the first time in the transaction
            evm.gas_meter.refund_counter += GasCosts.REFUND_STORAGE_CLEAR

        if original_value != 0 and current_value == 0:
            # Gas refund issued earlier to be reversed
            evm.gas_meter.refund_counter -= GasCosts.REFUND_STORAGE_CLEAR

        if original_value == new_value:
            # Slot restored to its original value: refund the STORAGE_WRITE
            # charged on the first-time change earlier this transaction.
            evm.gas_meter.refund_counter += int(GasCosts.STORAGE_WRITE)

    # STATE GAS
    # A first-time set of a zero slot pays for the state it creates; a
    # slot set then cleared refills the earlier charge — to the meter's
    # reservoir, or to the frame that owns the outstanding charge.
    frame_context = evm.tx_env.frame_context
    if original_value == current_value and current_value != new_value:
        if original_value == 0:
            state_gas = StateGasCosts.STORAGE_SET

    if current_value != new_value and original_value == new_value:
        if original_value == 0:
            if frame_context is None:
                credit_state_gas_refund(
                    evm.gas_meter, StateGasCosts.STORAGE_SET
                )
            else:
                owner = frame_context.outstanding_charge_owners.pop(
                    (evm.current_target, key)
                )
                credit_frame_state_gas_refund(
                    frame_context, owner, StateGasCosts.STORAGE_SET
                )

    # Charge execution gas before state gas so that an execution-gas
    # OOG does not consume state gas that would inflate the parent's
    # reservoir on frame failure.
    charge_gas(evm, gas_cost)
    charge_state_gas(evm, state_gas)
    # Record the executing frame as the outstanding charge's owner: a
    # later refill of this slot is attributed back to it.
    if frame_context is not None and state_gas != Uint(0):
        frame_context.outstanding_charge_owners[(evm.current_target, key)] = (
            frame_context.current_frame_index
        )
    set_storage(tx_state, evm.current_target, key, new_value)

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
    charge_gas(evm, GasCosts.OPCODE_TLOAD)

    # OPERATION
    value = get_transient_storage(evm.tx_env.state, evm.current_target, key)
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
    if evm.is_static:
        raise WriteInStaticContext

    # STACK
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_TSTORE)
    set_transient_storage(
        evm.tx_env.state,
        evm.current_target,
        key,
        new_value,
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)
