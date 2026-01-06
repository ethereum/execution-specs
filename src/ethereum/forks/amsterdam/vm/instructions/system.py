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
from ethereum_types.numeric import U64, U256, Uint

from ethereum.utils.numeric import ceil32

from ...fork_types import Address
from ...state import (
    account_has_code_or_nonce,
    account_has_storage,
    get_account,
    increment_nonce,
    is_account_alive,
    move_ether,
    set_account_balance,
)
from ...state_tracker import (
    capture_pre_balance,
    create_child_frame,
    track_address,
    track_balance_change,
    track_nonce_change,
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
    GAS_CREATE,
    GAS_KECCAK256_WORD,
    GAS_NEW_ACCOUNT,
    GAS_SELF_DESTRUCT,
    GAS_SELF_DESTRUCT_NEW_ACCOUNT,
    GAS_WARM_ACCESS,
    GAS_ZERO,
    calculate_gas_extend_memory,
    calculate_message_call_gas,
    charge_gas,
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

    # Check static context first
    if evm.message.is_static:
        raise WriteInStaticContext

    # Check max init code size early before memory read
    if memory_size > U256(MAX_INIT_CODE_SIZE):
        raise OutOfGasError

    state = evm.message.block_env.state

    call_data = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    create_message_gas = max_message_call_gas(Uint(evm.gas_left))
    evm.gas_left -= create_message_gas
    evm.return_data = b""

    sender_address = evm.message.current_target
    sender = get_account(state, sender_address)

    if (
        sender.balance < endowment
        or sender.nonce == Uint(2**64 - 1)
        or evm.message.depth + Uint(1) > STACK_DEPTH_LIMIT
    ):
        evm.gas_left += create_message_gas
        push(evm.stack, U256(0))
        return

    evm.accessed_addresses.add(contract_address)

    track_address(evm.state_changes, contract_address)
    if account_has_code_or_nonce(
        state, contract_address
    ) or account_has_storage(state, contract_address):
        increment_nonce(state, evm.message.current_target)
        nonce_after = get_account(state, evm.message.current_target).nonce
        track_nonce_change(
            evm.state_changes,
            evm.message.current_target,
            U64(nonce_after),
        )
        push(evm.stack, U256(0))
        return

    # Track nonce increment for CREATE
    increment_nonce(state, evm.message.current_target)
    nonce_after = get_account(state, evm.message.current_target).nonce
    track_nonce_change(
        evm.state_changes,
        evm.message.current_target,
        U64(nonce_after),
    )

    # Create call frame as child of parent EVM's frame
    child_state_changes = create_child_frame(evm.state_changes)

    child_message = Message(
        block_env=evm.message.block_env,
        tx_env=evm.message.tx_env,
        caller=evm.message.current_target,
        target=Bytes0(),
        gas=create_message_gas,
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
        state_changes=child_state_changes,
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

    charge_gas(evm, GAS_CREATE + extend_memory.cost + init_code_gas)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    contract_address = compute_contract_address(
        evm.message.current_target,
        get_account(
            evm.message.block_env.state, evm.message.current_target
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

    It's similar to CREATE opcode except that the address of new account
    depends on the init_code instead of the nonce of sender.

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
        GAS_CREATE
        + GAS_KECCAK256_WORD * call_data_words
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
        push(evm.stack, U256(0))
        return

    call_data = memory_read_bytes(
        evm.memory, memory_input_start_position, memory_input_size
    )

    # Create call frame as child of parent EVM's frame
    child_state_changes = create_child_frame(evm.state_changes)

    child_message = Message(
        block_env=evm.message.block_env,
        tx_env=evm.message.tx_env,
        caller=caller,
        target=to,
        gas=gas,
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
        state_changes=child_state_changes,
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
    state = evm.message.block_env.state
    if is_cold_access:
        evm.accessed_addresses.add(to)

    create_gas_cost = GAS_NEW_ACCOUNT
    if value == 0 or is_account_alive(state, to):
        create_gas_cost = Uint(0)

    extra_gas = access_gas_cost + transfer_gas_cost + create_gas_cost
    (
        is_delegated,
        code_address,
        delegation_access_cost,
    ) = calculate_delegation_cost(evm, to)

    if is_delegated:
        # check enough gas for delegation access
        extra_gas += delegation_access_cost
        check_gas(evm, extra_gas + extend_memory.cost)
        track_address(evm.state_changes, code_address)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    code = get_account(state, code_address).code

    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    evm.memory += b"\x00" * extend_memory.expand_by
    sender_balance = get_account(state, evm.message.current_target).balance
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.return_data = b""
        evm.gas_left += message_call_gas.sub_call
    else:
        generic_call(
            evm,
            message_call_gas.sub_call,
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
    state = evm.message.block_env.state
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
        track_address(evm.state_changes, code_address)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    code = get_account(state, code_address).code

    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    sender_balance = get_account(
        evm.message.block_env.state, evm.message.current_target
    ).balance

    # EIP-7928: For CALLCODE with value transfer, capture pre-balance
    # in transaction frame. CALLCODE transfers value from/to current_target
    # (same address), affecting current storage context, not child frame
    if value != 0 and sender_balance >= value:
        capture_pre_balance(
            evm.message.tx_env.state_changes,
            evm.message.current_target,
            sender_balance,
        )

    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.return_data = b""
        evm.gas_left += message_call_gas.sub_call
    else:
        generic_call(
            evm,
            message_call_gas.sub_call,
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
    state = evm.message.block_env.state
    if is_cold_access:
        evm.accessed_addresses.add(beneficiary)

    track_address(evm.state_changes, beneficiary)

    if (
        not is_account_alive(state, beneficiary)
        and get_account(state, evm.message.current_target).balance != 0
    ):
        gas_cost += GAS_SELF_DESTRUCT_NEW_ACCOUNT

    charge_gas(evm, gas_cost)

    state = evm.message.block_env.state
    originator = evm.message.current_target
    originator_balance = get_account(state, originator).balance
    beneficiary_balance = get_account(state, beneficiary).balance

    # Get tracking context
    tx_frame = evm.message.tx_env.state_changes

    # Capture pre-balances for net-zero filtering
    track_address(evm.state_changes, originator)
    capture_pre_balance(tx_frame, originator, originator_balance)
    capture_pre_balance(tx_frame, beneficiary, beneficiary_balance)

    # Transfer balance
    move_ether(state, originator, beneficiary, originator_balance)

    # Track balance changes
    originator_new_balance = get_account(state, originator).balance
    beneficiary_new_balance = get_account(state, beneficiary).balance
    track_balance_change(
        evm.state_changes,
        originator,
        originator_new_balance,
    )
    track_balance_change(
        evm.state_changes,
        beneficiary,
        beneficiary_new_balance,
    )

    # register account for deletion only if it was created
    # in the same transaction
    if originator in state.created_accounts:
        # If beneficiary is the same as originator, then
        # the ether is burnt.
        set_account_balance(state, originator, U256(0))
        track_balance_change(evm.state_changes, originator, U256(0))
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
    state = evm.message.block_env.state
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
        track_address(evm.state_changes, code_address)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    code = get_account(state, code_address).code

    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    generic_call(
        evm,
        message_call_gas.sub_call,
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
    state = evm.message.block_env.state
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
        track_address(evm.state_changes, code_address)
        if code_address not in evm.accessed_addresses:
            evm.accessed_addresses.add(code_address)

    code = get_account(state, code_address).code

    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    generic_call(
        evm,
        message_call_gas.sub_call,
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
