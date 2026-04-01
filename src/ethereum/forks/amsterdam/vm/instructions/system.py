"""
Ethereum Virtual Machine (EVM) System Instructions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM system related instructions.
"""

from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U256, Uint

from ethereum.state import Address
from ethereum.utils.numeric import ceil32

from ...state_tracker import (
    account_has_code_or_nonce,
    account_has_storage,
    get_account,
    get_code,
    increment_nonce,
    is_account_alive,
    move_ether,
    set_account_balance,
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
    Evm,
    Message,
    incorporate_child_on_error,
    incorporate_child_on_success,
)
from ..exceptions import OutOfGasError, Revert, WriteInStaticContext
from ..gas import (
    GAS_CALL_VALUE,
    GAS_COLD_ACCOUNT_ACCESS,
    GAS_KECCAK256_PER_WORD,
    GAS_SELF_DESTRUCT,
    GAS_WARM_ACCESS,
    GAS_ZERO,
    REGULAR_GAS_CREATE,
    STATE_BYTES_PER_NEW_ACCOUNT,
    calculate_gas_extend_memory,
    calculate_message_call_gas,
    charge_gas,
    charge_state_gas,
    check_gas,
    init_code_cost,
    max_message_call_gas,
    state_gas_per_byte,
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

    # Check static context first
    if evm.message.is_static:
        raise WriteInStaticContext

    # Check max init code size early before memory read
    if memory_size > U256(MAX_INIT_CODE_SIZE):
        raise OutOfGasError

    # Charge state gas for account creation after initcode validation
    cost_per_state_byte = state_gas_per_byte(
        evm.message.block_env.block_gas_limit
    )
    charge_state_gas(evm, STATE_BYTES_PER_NEW_ACCOUNT * cost_per_state_byte)

    tx_state = evm.message.tx_env.state

    call_data = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    create_message_gas = max_message_call_gas(Uint(evm.gas_left))
    evm.gas_left -= create_message_gas

    # Pass full reservoir to child (no 63/64 rule for state gas)
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
        push(evm.stack, U256(0))
        return

    evm.accessed_addresses.add(contract_address)

    if account_has_code_or_nonce(
        tx_state, contract_address
    ) or account_has_storage(tx_state, contract_address):
        increment_nonce(tx_state, evm.message.current_target)
        evm.regular_gas_used += create_message_gas
        evm.state_gas_left += create_message_state_gas_reservoir
        push(evm.stack, U256(0))
        return

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
        is_create=True,
    )
    child_evm = process_create_message(child_message)

    if child_evm.error:
        incorporate_child_on_error(evm, child_evm)
        evm.return_data = child_evm.output
        push(evm.stack, U256(0))
    else:
        incorporate_child_on_success(evm, child_evm)
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
    # STACK
    endowment = pop(evm.stack)
    memory_start_position = pop(evm.stack)
    memory_size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_position, memory_size)]
    )
    init_code_gas = init_code_cost(Uint(memory_size))
    charge_gas(evm, REGULAR_GAS_CREATE + extend_memory.cost + init_code_gas)

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
        REGULAR_GAS_CREATE
        + GAS_KECCAK256_PER_WORD * call_data_words
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

    charge_gas(evm, GAS_ZERO + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    evm.output = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    evm.running = False

    # PROGRAM COUNTER
    pass


def generic_call(
    evm: Evm,
    gas: Uint,
    state_gas_reservoir: Uint,
    value: U256,
    caller: Address,
    to: Address,
    code_address: Address,
    should_transfer_value: bool,
    is_staticcall: bool,
    memory_input_start_position: U256,
    memory_input_size: U256,
    memory_output_start_position: U256,
    memory_output_size: U256,
    code: Bytes,
    disable_precompiles: bool,
) -> None:
    """
    Perform the core logic of the `CALL*` family of opcodes.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    evm.return_data = b""

    if evm.message.depth + Uint(1) > STACK_DEPTH_LIMIT:
        evm.gas_left += gas
        evm.state_gas_left += state_gas_reservoir
        push(evm.stack, U256(0))
        return

    call_data = memory_read_bytes(
        evm.memory, memory_input_start_position, memory_input_size
    )

    child_message = Message(
        block_env=evm.message.block_env,
        tx_env=evm.message.tx_env,
        caller=caller,
        target=to,
        gas=gas,
        state_gas_reservoir=state_gas_reservoir,
        value=value,
        data=call_data,
        code=code,
        current_target=to,
        depth=evm.message.depth + Uint(1),
        code_address=code_address,
        should_transfer_value=should_transfer_value,
        is_static=True if is_staticcall else evm.message.is_static,
        accessed_addresses=evm.accessed_addresses.copy(),
        accessed_storage_keys=evm.accessed_storage_keys.copy(),
        disable_precompiles=disable_precompiles,
        parent_evm=evm,
        is_create=False,
    )

    child_evm = process_message(child_message)

    if child_evm.error:
        incorporate_child_on_error(evm, child_evm)
        evm.return_data = child_evm.output
        push(evm.stack, U256(0))
    else:
        incorporate_child_on_success(evm, child_evm)
        evm.return_data = child_evm.output
        push(evm.stack, U256(1))

    actual_output_size = min(memory_output_size, U256(len(child_evm.output)))
    memory_write(
        evm.memory,
        memory_output_start_position,
        child_evm.output[:actual_output_size],
    )


def escrow_subcall_regular_gas(evm: Evm, sub_call_gas: Uint) -> None:
    """
    Remove forwarded CALL* gas from the caller's regular gas usage.

    CALL* forwards `sub_call_gas` to the child frame as temporary escrow.
    Only gas actually burned by the child should be reintroduced via
    `incorporate_child_*` child gas accounting.
    """
    evm.regular_gas_used -= sub_call_gas


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
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GAS_WARM_ACCESS

    transfer_gas_cost = Uint(0) if value == 0 else GAS_CALL_VALUE

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

    # TODO: Consider consolidating charge_gas + charge_state_gas into
    # a single gas charge to avoid duplicate EVM trace entries.
    # Applies here and in create, create2, selfdestruct. See #2526.
    charge_gas(evm, extra_gas + extend_memory.cost)
    if value != 0 and not is_account_alive(tx_state, to):
        cost_per_state_byte = state_gas_per_byte(
            evm.message.block_env.block_gas_limit
        )
        charge_state_gas(
            evm, STATE_BYTES_PER_NEW_ACCOUNT * cost_per_state_byte
        )

    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        memory_cost=Uint(0),
        extra_gas=Uint(0),
    )
    charge_gas(evm, message_call_gas.cost)
    escrow_subcall_regular_gas(evm, message_call_gas.sub_call)

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
            message_call_gas.sub_call,
            call_state_gas_reservoir,
            value,
            evm.message.current_target,
            to,
            code_address,
            True,
            False,
            memory_input_start_position,
            memory_input_size,
            memory_output_start_position,
            memory_output_size,
            code,
            is_delegated,
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
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GAS_WARM_ACCESS

    transfer_gas_cost = Uint(0) if value == 0 else GAS_CALL_VALUE

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
    escrow_subcall_regular_gas(evm, message_call_gas.sub_call)

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
            message_call_gas.sub_call,
            call_state_gas_reservoir,
            value,
            evm.message.current_target,
            to,
            code_address,
            True,
            False,
            memory_input_start_position,
            memory_input_size,
            memory_output_start_position,
            memory_output_size,
            code,
            is_delegated,
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
    gas_cost = GAS_SELF_DESTRUCT

    is_cold_access = beneficiary not in evm.accessed_addresses
    if is_cold_access:
        gas_cost += GAS_COLD_ACCOUNT_ACCESS

    # check access gas cost before state access
    check_gas(evm, gas_cost)

    # STATE ACCESS
    tx_state = evm.message.tx_env.state
    if is_cold_access:
        evm.accessed_addresses.add(beneficiary)

    needs_state_gas = (
        not is_account_alive(tx_state, beneficiary)
        and get_account(tx_state, evm.message.current_target).balance != 0
    )

    # Charge regular gas before state gas so that a regular-gas OOG
    # does not consume state gas that would inflate the parent's
    # reservoir on frame failure.
    charge_gas(evm, gas_cost)
    if needs_state_gas:
        cost_per_state_byte = state_gas_per_byte(
            evm.message.block_env.block_gas_limit
        )
        charge_state_gas(
            evm, STATE_BYTES_PER_NEW_ACCOUNT * cost_per_state_byte
        )

    originator = evm.message.current_target
    originator_balance = get_account(tx_state, originator).balance

    # Transfer balance
    move_ether(tx_state, originator, beneficiary, originator_balance)

    # register account for deletion only if it was created
    # in the same transaction
    if originator in tx_state.created_accounts:
        # If beneficiary is the same as originator, then
        # the ether is burnt.
        set_account_balance(tx_state, originator, U256(0))
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
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GAS_WARM_ACCESS

    # check static gas before state access
    check_gas(evm, access_gas_cost + extend_memory.cost)

    # STATE ACCESS
    tx_state = evm.message.tx_env.state
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
    escrow_subcall_regular_gas(evm, message_call_gas.sub_call)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    # Pass full reservoir to child (no 63/64 rule for state gas)
    call_state_gas_reservoir = evm.state_gas_left
    evm.state_gas_left = Uint(0)

    generic_call(
        evm,
        message_call_gas.sub_call,
        call_state_gas_reservoir,
        evm.message.value,
        evm.message.caller,
        evm.message.current_target,
        code_address,
        False,
        False,
        memory_input_start_position,
        memory_input_size,
        memory_output_start_position,
        memory_output_size,
        code,
        is_delegated,
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
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GAS_WARM_ACCESS

    # check static gas before state access
    check_gas(evm, access_gas_cost + extend_memory.cost)

    # STATE ACCESS
    tx_state = evm.message.tx_env.state
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
    escrow_subcall_regular_gas(evm, message_call_gas.sub_call)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    # Pass full reservoir to child (no 63/64 rule for state gas)
    call_state_gas_reservoir = evm.state_gas_left
    evm.state_gas_left = Uint(0)

    generic_call(
        evm,
        message_call_gas.sub_call,
        call_state_gas_reservoir,
        U256(0),
        evm.message.current_target,
        to,
        code_address,
        True,
        True,
        memory_input_start_position,
        memory_input_size,
        memory_output_start_position,
        memory_output_size,
        code,
        is_delegated,
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
