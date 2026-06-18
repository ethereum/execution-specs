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

from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U256, Uint

from ethereum.state import Address
from ethereum.utils.numeric import ceil32

from ...fork_types import StateGas
from ...state_tracker import (
    account_deployable,
    get_account,
    get_code,
    increment_nonce,
    is_account_alive,
    move_ether,
)
from ...utils.address import (
    compute_contract_address,
    compute_create2_contract_address,
    to_address_masked,
)
from ...vm.eoa_delegation import (
    calculate_delegation_cost,
)
from .. import (
    CALL_SUCCESS,
    Evm,
    Message,
    credit_state_gas_refund,
    emit_transfer_log,
    incorporate_child_on_error,
    incorporate_child_on_success,
)
from ..exceptions import OutOfGasError, Revert, WriteInStaticContext
from ..gas import (
    GasCosts,
    StateGasCosts,
    calculate_gas_extend_memory,
    calculate_message_call_gas,
    charge_gas,
    charge_state_gas,
    check_gas,
    init_code_cost,
    max_message_call_gas,
)
from ..memory import memory_read_bytes, memory_write
from ..stack import pop, push


def generic_create(
    evm: Evm,
    endowment: U256,
    contract_address: Address,
    memory_start_position: U256,
    memory_size: U256,
) -> None:
    """
    Core logic used by the `CREATE*` family of opcodes.
    """
    # This import causes a circular import error
    # if it's not moved inside this method
    from ...vm.interpreter import (
        MAX_INIT_CODE_SIZE,
        STACK_DEPTH_LIMIT,
        process_create_message,
    )

    # Check max init code size early before memory read
    if memory_size > U256(MAX_INIT_CODE_SIZE):
        raise OutOfGasError

    # Charge state gas for account creation (pay-before-execute).
    # Refunded to the reservoir on any failure path below.
    charge_state_gas(evm, StateGasCosts.NEW_ACCOUNT)

    tx_state = evm.message.tx_env.state

    call_data = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    create_message_gas = max_message_call_gas(Uint(evm.gas_left))
    evm.gas_left -= create_message_gas

    # Move full reservoir to child (no 63/64 rule for state gas). Parent's
    # `state_gas_left` is zeroed and restored when the child returns.
    create_message_state_gas_reservoir = evm.state_gas_left
    evm.state_gas_left = Uint(0)

    evm.return_data = b""

    sender_address = evm.message.current_target
    sender = get_account(tx_state, sender_address)

    if (
        sender.balance < endowment
        or sender.nonce == Uint(2**64 - 1)
        or evm.message.depth + Uint(1) > STACK_DEPTH_LIMIT
    ):
        evm.gas_left += create_message_gas
        evm.state_gas_left += create_message_state_gas_reservoir
        credit_state_gas_refund(evm, StateGasCosts.NEW_ACCOUNT)
        push(evm.stack, U256(0))
        return

    evm.accessed_addresses.add(contract_address)

    if not account_deployable(tx_state, contract_address):
        increment_nonce(tx_state, evm.message.current_target)
        evm.regular_gas_used += create_message_gas
        evm.state_gas_left += create_message_state_gas_reservoir
        # Address collision — no account created, refund state gas.
        credit_state_gas_refund(evm, StateGasCosts.NEW_ACCOUNT)
        push(evm.stack, U256(0))
        return

    target_alive = is_account_alive(tx_state, contract_address)

    increment_nonce(tx_state, evm.message.current_target)

    child_message = Message(
        block_env=evm.message.block_env,
        tx_env=evm.message.tx_env,
        caller=evm.message.current_target,
        target=Bytes0(),
        gas=create_message_gas,
        state_gas_reservoir=create_message_state_gas_reservoir,
        value=endowment,
        data=b"",
        code=call_data,
        current_target=contract_address,
        depth=evm.message.depth + Uint(1),
        code_address=None,
        should_transfer_value=True,
        is_static=False,
        accessed_addresses=evm.accessed_addresses.copy(),
        accessed_storage_keys=evm.accessed_storage_keys.copy(),
        disable_precompiles=False,
        parent_evm=evm,
    )
    child_evm = process_create_message(child_message)

    if child_evm.error:
        incorporate_child_on_error(evm, child_evm)
        # No account created, refund parent's CREATE state gas.
        credit_state_gas_refund(evm, StateGasCosts.NEW_ACCOUNT)
        evm.return_data = child_evm.output
        push(evm.stack, U256(0))
    else:
        incorporate_child_on_success(evm, child_evm)
        if target_alive:
            credit_state_gas_refund(evm, StateGasCosts.NEW_ACCOUNT)
        evm.return_data = b""
        push(evm.stack, U256.from_be_bytes(child_evm.message.current_target))


def create(evm: Evm) -> None:
    """
    Creates a new account with associated code.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    if evm.message.is_static:
        raise WriteInStaticContext

    # STACK
    endowment = pop(evm.stack)
    memory_start_position = pop(evm.stack)
    memory_size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_position, memory_size)]
    )
    init_code_gas = init_code_cost(Uint(memory_size))
    charge_gas(
        evm,
        GasCosts.REGULAR_GAS_CREATE + extend_memory.cost + init_code_gas,
    )

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    contract_address = compute_contract_address(
        evm.message.current_target,
        get_account(
            evm.message.tx_env.state, evm.message.current_target
        ).nonce,
    )

    generic_create(
        evm,
        endowment,
        contract_address,
        memory_start_position,
        memory_size,
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def create2(evm: Evm) -> None:
    """
    Creates a new account with associated code.

    It's similar to the CREATE opcode except that the address of the new
    account depends on the init_code instead of the nonce of sender.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    if evm.message.is_static:
        raise WriteInStaticContext

    # STACK
    endowment = pop(evm.stack)
    memory_start_position = pop(evm.stack)
    memory_size = pop(evm.stack)
    salt = pop(evm.stack).to_be_bytes32()

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_position, memory_size)]
    )
    call_data_words = ceil32(Uint(memory_size)) // Uint(32)
    init_code_gas = init_code_cost(Uint(memory_size))
    charge_gas(
        evm,
        GasCosts.REGULAR_GAS_CREATE
        + GasCosts.OPCODE_KECCAK256_PER_WORD * call_data_words
        + extend_memory.cost
        + init_code_gas,
    )

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    contract_address = compute_create2_contract_address(
        evm.message.current_target,
        salt,
        memory_read_bytes(evm.memory, memory_start_position, memory_size),
    )

    generic_create(
        evm,
        endowment,
        contract_address,
        memory_start_position,
        memory_size,
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
    state_gas_reservoir: Uint
    value: U256
    caller: Address
    to: Address
    code_address: Address
    should_transfer_value: bool
    is_staticcall: bool
    memory_input_start_position: U256
    memory_input_size: U256
    memory_output_start_position: U256
    memory_output_size: U256
    code: Bytes
    disable_precompiles: bool
    new_account_charged: bool = False


def generic_call(evm: Evm, params: GenericCall) -> None:
    """
    Perform the core logic of the `CALL*` family of opcodes.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    evm.return_data = b""

    if evm.message.depth + Uint(1) > STACK_DEPTH_LIMIT:
        evm.gas_left += params.gas
        evm.state_gas_left += params.state_gas_reservoir
        if params.new_account_charged:
            credit_state_gas_refund(evm, StateGasCosts.NEW_ACCOUNT)
        push(evm.stack, U256(0))
        return

    call_data = memory_read_bytes(
        evm.memory,
        params.memory_input_start_position,
        params.memory_input_size,
    )

    child_message = Message(
        block_env=evm.message.block_env,
        tx_env=evm.message.tx_env,
        caller=params.caller,
        target=params.to,
        gas=params.gas,
        state_gas_reservoir=params.state_gas_reservoir,
        value=params.value,
        data=call_data,
        code=params.code,
        current_target=params.to,
        depth=evm.message.depth + Uint(1),
        code_address=params.code_address,
        should_transfer_value=params.should_transfer_value,
        is_static=params.is_staticcall or evm.message.is_static,
        accessed_addresses=evm.accessed_addresses.copy(),
        accessed_storage_keys=evm.accessed_storage_keys.copy(),
        disable_precompiles=params.disable_precompiles,
        parent_evm=evm,
    )

    child_evm = process_message(child_message)

    if child_evm.error:
        incorporate_child_on_error(evm, child_evm)
        if params.new_account_charged:
            credit_state_gas_refund(evm, StateGasCosts.NEW_ACCOUNT)
        evm.return_data = child_evm.output
        push(evm.stack, U256(0))
    else:
        incorporate_child_on_success(evm, child_evm)
        evm.return_data = child_evm.output
        push(evm.stack, CALL_SUCCESS)

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

    if evm.message.is_static and value != U256(0):
        raise WriteInStaticContext

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory,
        [
            (memory_input_start_position, memory_input_size),
            (memory_output_start_position, memory_output_size),
        ],
    )

    is_cold_access = to not in evm.accessed_addresses
    if is_cold_access:
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GasCosts.WARM_ACCESS

    transfer_gas_cost = Uint(0) if value == 0 else GasCosts.CALL_VALUE

    # check static gas before state access
    check_gas(
        evm,
        access_gas_cost + transfer_gas_cost + extend_memory.cost,
    )

    # STATE ACCESS
    tx_state = evm.message.tx_env.state
    if is_cold_access:
        evm.accessed_addresses.add(to)

    extra_gas = access_gas_cost + transfer_gas_cost
    (
        is_delegated,
        code_address,
        delegation_access_cost,
    ) = calculate_delegation_cost(evm, to)

    if is_delegated:
        # check enough gas for delegation access
        extra_gas += delegation_access_cost
        check_gas(evm, extra_gas + extend_memory.cost)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    code_hash = get_account(tx_state, code_address).code_hash
    code = get_code(tx_state, code_hash)

    charge_gas(evm, extra_gas + extend_memory.cost)
    has_value = value != 0
    new_account_charged = has_value and not is_account_alive(tx_state, to)
    if new_account_charged:
        charge_state_gas(evm, StateGasCosts.NEW_ACCOUNT)

    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        memory_cost=Uint(0),
        extra_gas=Uint(0),
    )
    charge_gas(evm, message_call_gas.cost)
    evm.regular_gas_used -= message_call_gas.sub_call

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    # Pass full reservoir to child (no 63/64 rule for state gas)
    call_state_gas_reservoir = evm.state_gas_left
    evm.state_gas_left = Uint(0)

    sender_balance = get_account(tx_state, evm.message.current_target).balance
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.return_data = b""
        evm.gas_left += message_call_gas.sub_call
        evm.state_gas_left += call_state_gas_reservoir
        if new_account_charged:
            credit_state_gas_refund(evm, StateGasCosts.NEW_ACCOUNT)
    else:
        generic_call(
            evm,
            GenericCall(
                gas=message_call_gas.sub_call,
                state_gas_reservoir=call_state_gas_reservoir,
                value=value,
                caller=evm.message.current_target,
                to=to,
                code_address=code_address,
                should_transfer_value=True,
                is_staticcall=False,
                memory_input_start_position=memory_input_start_position,
                memory_input_size=memory_input_size,
                memory_output_start_position=memory_output_start_position,
                memory_output_size=memory_output_size,
                code=code,
                disable_precompiles=is_delegated,
                new_account_charged=new_account_charged,
            ),
        )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def callcode(evm: Evm) -> None:
    """
    Message-call into this account with alternative account's code.

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

    is_cold_access = code_address not in evm.accessed_addresses
    if is_cold_access:
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GasCosts.WARM_ACCESS

    transfer_gas_cost = Uint(0) if value == 0 else GasCosts.CALL_VALUE

    # check static gas before state access
    check_gas(
        evm,
        access_gas_cost + extend_memory.cost + transfer_gas_cost,
    )

    # STATE ACCESS
    tx_state = evm.message.tx_env.state
    if is_cold_access:
        evm.accessed_addresses.add(code_address)

    extra_gas = access_gas_cost + transfer_gas_cost
    (
        is_delegated,
        code_address,
        delegation_access_cost,
    ) = calculate_delegation_cost(evm, code_address)

    if is_delegated:
        # check enough gas for delegation access
        extra_gas += delegation_access_cost
        check_gas(evm, extra_gas + extend_memory.cost)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    code_hash = get_account(tx_state, code_address).code_hash
    code = get_code(tx_state, code_hash)

    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)
    evm.regular_gas_used -= message_call_gas.sub_call

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    # Pass full reservoir to child (no 63/64 rule for state gas)
    call_state_gas_reservoir = evm.state_gas_left
    evm.state_gas_left = Uint(0)

    sender_balance = get_account(tx_state, evm.message.current_target).balance

    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.return_data = b""
        evm.gas_left += message_call_gas.sub_call
        evm.state_gas_left += call_state_gas_reservoir
    else:
        generic_call(
            evm,
            GenericCall(
                gas=message_call_gas.sub_call,
                state_gas_reservoir=call_state_gas_reservoir,
                value=value,
                caller=evm.message.current_target,
                to=to,
                code_address=code_address,
                should_transfer_value=True,
                is_staticcall=False,
                memory_input_start_position=memory_input_start_position,
                memory_input_size=memory_input_size,
                memory_output_start_position=memory_output_start_position,
                memory_output_size=memory_output_size,
                code=code,
                disable_precompiles=is_delegated,
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
    if evm.message.is_static:
        raise WriteInStaticContext

    # STACK
    beneficiary = to_address_masked(pop(evm.stack))

    # GAS
    gas_cost = GasCosts.OPCODE_SELFDESTRUCT_BASE

    is_cold_access = beneficiary not in evm.accessed_addresses
    if is_cold_access:
        gas_cost += GasCosts.COLD_ACCOUNT_ACCESS

    # check access gas cost before state access
    check_gas(evm, gas_cost)

    # STATE ACCESS
    tx_state = evm.message.tx_env.state
    if is_cold_access:
        evm.accessed_addresses.add(beneficiary)

    state_gas = StateGas(Uint(0))
    if (
        not is_account_alive(tx_state, beneficiary)
        and get_account(tx_state, evm.message.current_target).balance != 0
    ):
        state_gas = StateGasCosts.NEW_ACCOUNT

    # Charge regular gas before state gas so that a regular-gas OOG
    # does not consume state gas that would inflate the parent's
    # reservoir on frame failure.
    charge_gas(evm, gas_cost)
    charge_state_gas(evm, state_gas)

    originator = evm.message.current_target
    originator_balance = get_account(tx_state, originator).balance

    # Transfer balance
    move_ether(tx_state, originator, beneficiary, originator_balance)

    # Emit transfer or burn log
    if beneficiary != originator:
        emit_transfer_log(evm, originator, beneficiary, originator_balance)

    # Register account for deletion iff created in same transaction
    if originator in tx_state.created_accounts:
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

    is_cold_access = code_address not in evm.accessed_addresses
    if is_cold_access:
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GasCosts.WARM_ACCESS

    # check static gas before state access
    check_gas(evm, access_gas_cost + extend_memory.cost)

    # STATE ACCESS
    if is_cold_access:
        evm.accessed_addresses.add(code_address)

    extra_gas = access_gas_cost
    (
        is_delegated,
        code_address,
        delegation_access_cost,
    ) = calculate_delegation_cost(evm, code_address)

    if is_delegated:
        # check enough gas for delegation access
        extra_gas += delegation_access_cost
        check_gas(evm, extra_gas + extend_memory.cost)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    tx_state = evm.message.tx_env.state
    code_hash = get_account(tx_state, code_address).code_hash
    code = get_code(tx_state, code_hash)

    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)
    evm.regular_gas_used -= message_call_gas.sub_call

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    # Pass full reservoir to child (no 63/64 rule for state gas)
    call_state_gas_reservoir = evm.state_gas_left
    evm.state_gas_left = Uint(0)

    generic_call(
        evm,
        GenericCall(
            gas=message_call_gas.sub_call,
            state_gas_reservoir=call_state_gas_reservoir,
            value=evm.message.value,
            caller=evm.message.caller,
            to=evm.message.current_target,
            code_address=code_address,
            should_transfer_value=False,
            is_staticcall=False,
            memory_input_start_position=memory_input_start_position,
            memory_input_size=memory_input_size,
            memory_output_start_position=memory_output_start_position,
            memory_output_size=memory_output_size,
            code=code,
            disable_precompiles=is_delegated,
        ),
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def staticcall(evm: Evm) -> None:
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

    is_cold_access = to not in evm.accessed_addresses
    if is_cold_access:
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GasCosts.WARM_ACCESS

    # check static gas before state access
    check_gas(evm, access_gas_cost + extend_memory.cost)

    # STATE ACCESS
    if is_cold_access:
        evm.accessed_addresses.add(to)

    extra_gas = access_gas_cost
    (
        is_delegated,
        code_address,
        delegation_access_cost,
    ) = calculate_delegation_cost(evm, to)

    if is_delegated:
        # check enough gas for delegation access
        extra_gas += delegation_access_cost
        check_gas(evm, extra_gas + extend_memory.cost)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    tx_state = evm.message.tx_env.state
    code_hash = get_account(tx_state, code_address).code_hash
    code = get_code(tx_state, code_hash)

    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)
    evm.regular_gas_used -= message_call_gas.sub_call

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    # Pass full reservoir to child (no 63/64 rule for state gas)
    call_state_gas_reservoir = evm.state_gas_left
    evm.state_gas_left = Uint(0)

    generic_call(
        evm,
        GenericCall(
            gas=message_call_gas.sub_call,
            state_gas_reservoir=call_state_gas_reservoir,
            value=U256(0),
            caller=evm.message.current_target,
            to=to,
            code_address=code_address,
            should_transfer_value=True,
            is_staticcall=True,
            memory_input_start_position=memory_input_start_position,
            memory_input_size=memory_input_size,
            memory_output_start_position=memory_output_start_position,
            memory_output_size=memory_output_size,
            code=code,
            disable_precompiles=is_delegated,
        ),
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def revert(evm: Evm) -> None:
    """
    Stop execution and revert state changes, without consuming all provided gas
    and also has the ability to return a reason.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    memory_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )

    charge_gas(evm, extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    output = memory_read_bytes(evm.memory, memory_start_index, size)
    evm.output = Bytes(output)
    raise Revert

    # PROGRAM COUNTER
    # no-op
