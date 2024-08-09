"""
Ethereum Virtual Machine (EVM) System Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM system related instructions.
"""
from ethereum.base_types import U256, Bytes0, Uint
from ethereum.crypto.hash import keccak256
from ethereum.utils.numeric import ceil32

from ...fork_types import Address
from ...state import (
    account_exists_and_is_empty,
    account_has_code_or_nonce,
    account_has_storage,
    get_account,
    increment_nonce,
    is_account_alive,
    move_ether,
    set_account_balance,
)
from ...utils.address import (
    compute_contract_address,
    compute_create2_contract_address,
    to_address,
    to_address_without_mask,
)
from ...vm.eoa_delegation import access_delegation
from .. import (
    MAX_CODE_SIZE,
    Eof,
    Evm,
    Message,
    OpcodeStackItemCount,
    get_eof_version,
    incorporate_child_on_error,
    incorporate_child_on_success,
)
from ..exceptions import (
    ExceptionalHalt,
    OutOfGasError,
    Revert,
    WriteInStaticContext,
)
from ..gas import (
    EOF_CALL_MIN_CALLEE_GAS,
    EOF_CALL_MIN_RETAINED_GAS,
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
    init_code_cost,
    max_message_call_gas,
)
from ..memory import memory_read_bytes, memory_write
from ..stack import pop, push

STACK_CREATE = OpcodeStackItemCount(inputs=3, outputs=1)
STACK_CREATE2 = OpcodeStackItemCount(inputs=4, outputs=1)
STACK_RETURN = OpcodeStackItemCount(inputs=2, outputs=0)
STACK_CALL = OpcodeStackItemCount(inputs=7, outputs=1)
STACK_CALLCODE = OpcodeStackItemCount(inputs=7, outputs=1)
STACK_SELFDESTRUCT = OpcodeStackItemCount(inputs=1, outputs=0)
STACK_DELEGATECALL = OpcodeStackItemCount(inputs=6, outputs=1)
STACK_STATICCALL = OpcodeStackItemCount(inputs=6, outputs=1)
STACK_REVERT = OpcodeStackItemCount(inputs=2, outputs=0)
STACK_INVALID = OpcodeStackItemCount(inputs=0, outputs=0)
STACK_EXT_CALL = OpcodeStackItemCount(inputs=4, outputs=1)
STACK_EXT_DELEGATECALL = OpcodeStackItemCount(inputs=3, outputs=1)
STACK_EXT_STATICCALL = OpcodeStackItemCount(inputs=3, outputs=1)
STACK_EOF_CREATE = OpcodeStackItemCount(inputs=4, outputs=1)
STACK_RETURN_CONTRACT = OpcodeStackItemCount(inputs=2, outputs=0)


# TODO: Integrate EOF CALL* and CREATE in generic


def generic_create(
    evm: Evm,
    endowment: U256,
    contract_address: Address,
    memory_start_position: U256,
    memory_size: U256,
    init_code_gas: Uint,
) -> None:
    """
    Core logic used by the `CREATE*` family of opcodes.
    """
    # This import causes a circular import error
    # if it's not moved inside this method
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_create_message

    call_data = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )
    if len(call_data) > 2 * MAX_CODE_SIZE:
        raise OutOfGasError

    evm.accessed_addresses.add(contract_address)

    create_message_gas = max_message_call_gas(Uint(evm.gas_left))
    evm.gas_left -= create_message_gas
    if evm.message.is_static:
        raise WriteInStaticContext
    evm.return_data = b""

    sender_address = evm.message.current_target
    sender = get_account(evm.env.state, sender_address)

    if (
        sender.balance < endowment
        or sender.nonce == Uint(2**64 - 1)
        or evm.message.depth + 1 > STACK_DEPTH_LIMIT
        or get_eof_version(call_data) == Eof.EOF1
    ):
        evm.gas_left += create_message_gas
        push(evm.stack, U256(0))
        return

    if account_has_code_or_nonce(
        evm.env.state, contract_address
    ) or account_has_storage(evm.env.state, contract_address):
        increment_nonce(evm.env.state, evm.message.current_target)
        push(evm.stack, U256(0))
        return

    increment_nonce(evm.env.state, evm.message.current_target)

    child_message = Message(
        caller=evm.message.current_target,
        target=Bytes0(),
        gas=create_message_gas,
        value=endowment,
        data=b"",
        code=call_data,
        current_target=contract_address,
        depth=evm.message.depth + 1,
        code_address=None,
        should_transfer_value=True,
        is_static=False,
        accessed_addresses=evm.accessed_addresses.copy(),
        accessed_storage_keys=evm.accessed_storage_keys.copy(),
        parent_evm=evm,
        authorizations=(),
        is_init_container=None,
    )
    child_evm = process_create_message(child_message, evm.env)

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
        get_account(evm.env.state, evm.message.current_target).nonce,
    )

    generic_create(
        evm,
        endowment,
        contract_address,
        memory_start_position,
        memory_size,
        init_code_gas,
    )

    # PROGRAM COUNTER
    evm.pc += 1


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
    call_data_words = ceil32(Uint(memory_size)) // 32
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
        init_code_gas,
    )

    # PROGRAM COUNTER
    evm.pc += 1


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
    code: bytes,
    is_delegated_code: bool,
) -> None:
    """
    Perform the core logic of the `CALL*` family of opcodes.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    evm.return_data = b""

    if evm.message.depth + 1 > STACK_DEPTH_LIMIT:
        evm.gas_left += gas
        push(evm.stack, U256(0))
        return

    call_data = memory_read_bytes(
        evm.memory, memory_input_start_position, memory_input_size
    )

    if is_delegated_code and len(code) == 0:
        evm.gas_left += gas
        push(evm.stack, U256(1))
        return
    if get_eof_version(code) == Eof.LEGACY:
        is_init_container = None
    else:
        is_init_container = False
    child_message = Message(
        caller=caller,
        target=to,
        gas=gas,
        value=value,
        data=call_data,
        container=code,
        current_target=to,
        depth=evm.message.depth + 1,
        code_address=code_address,
        should_transfer_value=should_transfer_value,
        is_static=True if is_staticcall else evm.message.is_static,
        accessed_addresses=evm.accessed_addresses.copy(),
        accessed_storage_keys=evm.accessed_storage_keys.copy(),
        parent_evm=evm,
        authorizations=(),
        is_init_container=is_init_container,
    )
    child_evm = process_message(child_message, evm.env)

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
    to = to_address(pop(evm.stack))
    value = pop(evm.stack)
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

    if to in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(to)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    code_address = to
    (
        is_delegated_code,
        code_address,
        code,
        delegated_access_gas_cost,
    ) = access_delegation(evm, code_address)
    access_gas_cost += delegated_access_gas_cost

    create_gas_cost = (
        Uint(0)
        if is_account_alive(evm.env.state, to) or value == 0
        else GAS_NEW_ACCOUNT
    )
    transfer_gas_cost = Uint(0) if value == 0 else GAS_CALL_VALUE
    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        access_gas_cost + create_gas_cost + transfer_gas_cost,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)
    if evm.message.is_static and value != U256(0):
        raise WriteInStaticContext
    evm.memory += b"\x00" * extend_memory.expand_by
    sender_balance = get_account(
        evm.env.state, evm.message.current_target
    ).balance
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.return_data = b""
        evm.gas_left += message_call_gas.stipend
    else:
        generic_call(
            evm,
            message_call_gas.stipend,
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
            is_delegated_code,
        )

    # PROGRAM COUNTER
    evm.pc += 1


def callcode(evm: Evm) -> None:
    """
    Message-call into this account with alternative account’s code.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    gas = Uint(pop(evm.stack))
    code_address = to_address(pop(evm.stack))
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

    if code_address in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(code_address)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    (
        is_delegated_code,
        code_address,
        code,
        delegated_access_gas_cost,
    ) = access_delegation(evm, code_address)
    access_gas_cost += delegated_access_gas_cost

    transfer_gas_cost = Uint(0) if value == 0 else GAS_CALL_VALUE
    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        access_gas_cost + transfer_gas_cost,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    sender_balance = get_account(
        evm.env.state, evm.message.current_target
    ).balance
    if sender_balance < value:
        push(evm.stack, U256(0))
        evm.return_data = b""
        evm.gas_left += message_call_gas.stipend
    else:
        generic_call(
            evm,
            message_call_gas.stipend,
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
            is_delegated_code,
        )

    # PROGRAM COUNTER
    evm.pc += 1


def selfdestruct(evm: Evm) -> None:
    """
    Halt execution and register account for later deletion.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    beneficiary = to_address(pop(evm.stack))

    # GAS
    gas_cost = GAS_SELF_DESTRUCT
    if beneficiary not in evm.accessed_addresses:
        evm.accessed_addresses.add(beneficiary)
        gas_cost += GAS_COLD_ACCOUNT_ACCESS

    if (
        not is_account_alive(evm.env.state, beneficiary)
        and get_account(evm.env.state, evm.message.current_target).balance != 0
    ):
        gas_cost += GAS_SELF_DESTRUCT_NEW_ACCOUNT

    charge_gas(evm, gas_cost)
    if evm.message.is_static:
        raise WriteInStaticContext

    originator = evm.message.current_target
    originator_balance = get_account(evm.env.state, originator).balance

    move_ether(
        evm.env.state,
        originator,
        beneficiary,
        originator_balance,
    )

    # register account for deletion only if it was created
    # in the same transaction
    if originator in evm.env.state.created_accounts:
        # If beneficiary is the same as originator, then
        # the ether is burnt.
        set_account_balance(evm.env.state, originator, U256(0))
        evm.accounts_to_delete.add(originator)

    # mark beneficiary as touched
    if account_exists_and_is_empty(evm.env.state, beneficiary):
        evm.touched_accounts.add(beneficiary)

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
    code_address = to_address(pop(evm.stack))
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

    if code_address in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(code_address)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    (
        is_delegated_code,
        code_address,
        code,
        delegated_access_gas_cost,
    ) = access_delegation(evm, code_address)
    access_gas_cost += delegated_access_gas_cost

    message_call_gas = calculate_message_call_gas(
        U256(0), gas, Uint(evm.gas_left), extend_memory.cost, access_gas_cost
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    generic_call(
        evm,
        message_call_gas.stipend,
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
        is_delegated_code,
    )

    # PROGRAM COUNTER
    evm.pc += 1


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
    to = to_address(pop(evm.stack))
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

    if to in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(to)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    code_address = to
    (
        is_delegated_code,
        code_address,
        code,
        delegated_access_gas_cost,
    ) = access_delegation(evm, code_address)
    access_gas_cost += delegated_access_gas_cost

    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        Uint(evm.gas_left),
        extend_memory.cost,
        access_gas_cost,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    generic_call(
        evm,
        message_call_gas.stipend,
        U256(0),
        evm.message.current_target,
        to,
        to,
        True,
        True,
        memory_input_start_position,
        memory_input_size,
        memory_output_start_position,
        memory_output_size,
        code,
        is_delegated_code,
    )

    # PROGRAM COUNTER
    evm.pc += 1


def revert(evm: Evm) -> None:
    """
    Stop execution and revert state changes, without consuming all provided gas
    and also has the ability to return a reason
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
    evm.output = bytes(output)
    raise Revert

    # PROGRAM COUNTER
    pass


def invalid(evm: Evm) -> None:
    """
    Designated invalid instruction.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    pass

    # GAS
    pass

    # OPERATION
    raise ExceptionalHalt("Invalid opcode.")

    # PROGRAM COUNTER
    pass


def ext_call(evm: Evm) -> None:
    """
    Message-call into an account for EOF.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    # STACK
    try:
        target_address = to_address_without_mask(pop(evm.stack))
    except ValueError:
        raise ExceptionalHalt
    input_offset = pop(evm.stack)
    input_size = pop(evm.stack)
    value = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(input_offset, input_size)]
    )

    if target_address in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(target_address)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    create_gas_cost = (
        Uint(0)
        if is_account_alive(evm.env.state, target_address) or value == 0
        else GAS_NEW_ACCOUNT
    )
    transfer_gas_cost = Uint(0) if value == 0 else GAS_CALL_VALUE
    charge_gas(
        evm,
        extend_memory.cost
        + access_gas_cost
        + create_gas_cost
        + transfer_gas_cost,
    )

    # OPERATION
    message_call_gas = evm.gas_left - max(
        evm.gas_left // 64, EOF_CALL_MIN_RETAINED_GAS
    )

    if evm.message.is_static and value != U256(0):
        raise WriteInStaticContext

    evm.memory += b"\x00" * extend_memory.expand_by

    sender_balance = get_account(
        evm.env.state, evm.message.current_target
    ).balance

    evm.return_data = b""

    call_data = memory_read_bytes(evm.memory, input_offset, input_size)

    container = get_account(evm.env.state, target_address).code

    if (
        message_call_gas < EOF_CALL_MIN_CALLEE_GAS
        or sender_balance < value
        or evm.message.depth + 1 > STACK_DEPTH_LIMIT
    ):
        push(evm.stack, U256(1))
    else:
        evm.gas_left -= message_call_gas

        child_message = Message(
            caller=evm.message.current_target,
            target=target_address,
            gas=Uint(message_call_gas),
            value=value,
            data=call_data,
            code=container,
            current_target=target_address,
            depth=evm.message.depth + 1,
            code_address=target_address,
            should_transfer_value=True,
            is_static=False,
            accessed_addresses=evm.accessed_addresses.copy(),
            accessed_storage_keys=evm.accessed_storage_keys.copy(),
            parent_evm=evm,
            is_init_container=False,
        )
        child_evm = process_message(child_message, evm.env)

        evm.return_data = child_evm.output

        if child_evm.error:
            incorporate_child_on_error(evm, child_evm)
            if isinstance(child_evm.error, Revert):
                push(evm.stack, U256(1))
            else:
                push(evm.stack, U256(2))
        else:
            incorporate_child_on_success(evm, child_evm)
            push(evm.stack, U256(0))

    # PROGRAM COUNTER
    evm.pc += 1


def ext_delegatecall(evm: Evm) -> None:
    """
    Message-call into an account with the callee's context
    for EOF.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    # STACK
    try:
        target_address = to_address_without_mask(pop(evm.stack))
    except ValueError:
        raise ExceptionalHalt
    input_offset = pop(evm.stack)
    input_size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(input_offset, input_size)]
    )

    if target_address in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(target_address)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    charge_gas(evm, extend_memory.cost + access_gas_cost)

    # OPERATION
    message_call_gas = evm.gas_left - max(
        evm.gas_left // 64, EOF_CALL_MIN_RETAINED_GAS
    )

    evm.memory += b"\x00" * extend_memory.expand_by

    evm.return_data = b""

    call_data = memory_read_bytes(evm.memory, input_offset, input_size)

    container = get_account(evm.env.state, target_address).code

    if (
        message_call_gas < EOF_CALL_MIN_CALLEE_GAS
        or evm.message.depth + 1 > STACK_DEPTH_LIMIT
        or get_eof_version(container) == Eof.LEGACY
    ):
        push(evm.stack, U256(1))
    else:
        evm.gas_left -= message_call_gas

        child_message = Message(
            caller=evm.message.caller,
            target=evm.message.current_target,
            gas=Uint(message_call_gas),
            value=U256(0),
            data=call_data,
            code=container,
            current_target=evm.message.current_target,
            depth=evm.message.depth + 1,
            code_address=target_address,
            should_transfer_value=False,
            is_static=False,
            accessed_addresses=evm.accessed_addresses.copy(),
            accessed_storage_keys=evm.accessed_storage_keys.copy(),
            parent_evm=evm,
            is_init_container=False,
        )
        child_evm = process_message(child_message, evm.env)

        evm.return_data = child_evm.output

        if child_evm.error:
            incorporate_child_on_error(evm, child_evm)
            if isinstance(child_evm.error, Revert):
                push(evm.stack, U256(1))
            else:
                push(evm.stack, U256(2))
        else:
            incorporate_child_on_success(evm, child_evm)
            push(evm.stack, U256(0))

    # PROGRAM COUNTER
    evm.pc += 1


def ext_staticcall(evm: Evm) -> None:
    """
    Static message-call into an account for EOF.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_message

    # STACK
    try:
        target_address = to_address_without_mask(pop(evm.stack))
    except ValueError:
        raise ExceptionalHalt
    input_offset = pop(evm.stack)
    input_size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(input_offset, input_size)]
    )

    if target_address in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(target_address)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    charge_gas(evm, extend_memory.cost + access_gas_cost)

    # OPERATION
    message_call_gas = evm.gas_left - max(
        evm.gas_left // 64, EOF_CALL_MIN_RETAINED_GAS
    )

    evm.memory += b"\x00" * extend_memory.expand_by

    evm.return_data = b""

    call_data = memory_read_bytes(evm.memory, input_offset, input_size)

    container = get_account(evm.env.state, target_address).code

    if (
        message_call_gas < EOF_CALL_MIN_CALLEE_GAS
        or evm.message.depth + 1 > STACK_DEPTH_LIMIT
    ):
        push(evm.stack, U256(1))
    else:
        evm.gas_left -= message_call_gas

        child_message = Message(
            caller=evm.message.current_target,
            target=target_address,
            gas=Uint(message_call_gas),
            value=U256(0),
            data=call_data,
            code=container,
            current_target=target_address,
            depth=evm.message.depth + 1,
            code_address=target_address,
            should_transfer_value=False,
            is_static=True,
            accessed_addresses=evm.accessed_addresses.copy(),
            accessed_storage_keys=evm.accessed_storage_keys.copy(),
            parent_evm=evm,
            is_init_container=False,
        )
        child_evm = process_message(child_message, evm.env)

        evm.return_data = child_evm.output

        if child_evm.error:
            incorporate_child_on_error(evm, child_evm)
            if isinstance(child_evm.error, Revert):
                push(evm.stack, U256(1))
            else:
                push(evm.stack, U256(2))
        else:
            incorporate_child_on_success(evm, child_evm)
            push(evm.stack, U256(0))

    # PROGRAM COUNTER
    evm.pc += 1


def eof_create(evm: Evm) -> None:
    """
    Creates a new account with associated code for EOF.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_create_message

    # STACK
    value = pop(evm.stack)
    salt = pop(evm.stack).to_be_bytes32()
    input_offset = pop(evm.stack)
    input_size = pop(evm.stack)

    # GAS
    init_container_index = Uint.from_be_bytes(
        evm.code[evm.pc + 1 : evm.pc + 2]
    )
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(input_offset, input_size)]
    )
    init_container = evm.eof_metadata.container_section_contents[
        init_container_index
    ]
    init_container_size = evm.eof_metadata.container_sizes[
        init_container_index
    ]
    init_code_gas = GAS_KECCAK256_WORD * ceil32(init_container_size) // 32

    charge_gas(evm, GAS_CREATE + extend_memory.cost + init_code_gas)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    sender_address = evm.message.current_target
    sender = get_account(evm.env.state, sender_address)

    contract_address = keccak256(
        b"\xff" + sender_address + salt + keccak256(init_container)
    )[12:]

    evm.accessed_addresses.add(contract_address)
    create_message_gas = max_message_call_gas(Uint(evm.gas_left))
    evm.gas_left -= create_message_gas

    if (
        sender.balance < value
        or sender.nonce == Uint(2**64 - 1)
        or evm.message.depth + 1 > STACK_DEPTH_LIMIT
    ):
        evm.gas_left += create_message_gas
        push(evm.stack, U256(0))
    elif account_has_code_or_nonce(evm.env.state, contract_address):
        increment_nonce(evm.env.state, evm.message.current_target)
        push(evm.stack, U256(0))
    else:
        call_data = memory_read_bytes(evm.memory, input_offset, input_size)

        increment_nonce(evm.env.state, evm.message.current_target)

        child_message = Message(
            caller=evm.message.current_target,
            target=Bytes0(),
            gas=create_message_gas,
            value=value,
            data=call_data,
            code=init_container,
            current_target=contract_address,
            depth=evm.message.depth + 1,
            code_address=None,
            should_transfer_value=True,
            is_static=False,
            accessed_addresses=evm.accessed_addresses.copy(),
            accessed_storage_keys=evm.accessed_storage_keys.copy(),
            parent_evm=evm,
            is_init_container=True,
        )
        child_evm = process_create_message(child_message, evm.env)

        if child_evm.error:
            incorporate_child_on_error(evm, child_evm)
            evm.return_data = child_evm.output
            push(evm.stack, U256(0))
        else:
            incorporate_child_on_success(evm, child_evm)
            evm.return_data = b""
            push(
                evm.stack, U256.from_be_bytes(child_evm.message.current_target)
            )

    # PROGRAM COUNTER
    evm.pc += 2


def return_contract(evm: Evm) -> None:
    """
    Returns contract to be deployed.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    from ..eof import build_container_from_metadata, parse_container_metadata

    # STACK
    aux_data_offset = pop(evm.stack)
    aux_data_size = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(aux_data_offset, aux_data_size)]
    )
    charge_gas(evm, GAS_ZERO + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    deploy_container_index = Uint.from_be_bytes(
        evm.code[evm.pc + 1 : evm.pc + 2]
    )
    deploy_container = evm.eof_metadata.container_section_contents[
        deploy_container_index
    ]
    deploy_container_metadata = parse_container_metadata(
        deploy_container,
        validate=True,
        is_deploy_container=True,
        is_init_container=False,
    )
    aux_data = memory_read_bytes(evm.memory, aux_data_offset, aux_data_size)
    deploy_container_metadata.data_section_contents += aux_data

    if (
        len(deploy_container_metadata.data_section_contents) > 0xFFFF
        or len(deploy_container_metadata.data_section_contents)
        < deploy_container_metadata.data_size
    ):
        raise ExceptionalHalt
    deploy_container_metadata.data_size = Uint(
        len(deploy_container_metadata.data_section_contents)
    )

    evm.deploy_container = build_container_from_metadata(
        deploy_container_metadata
    )

    # PROGRAM COUNTER
    evm.running = False
