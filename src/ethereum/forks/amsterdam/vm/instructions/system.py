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

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ethereum.state import Address
from ethereum.utils.numeric import ceil32

from ...fork_types import ExecutionGas, StateGas
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
    emit_transfer_log,
    incorporate_child,
)
from ..exceptions import OutOfGasError, Revert, WriteInStaticContext
from ..gas import (
    GasCosts,
    GasMeter,
    StateGasCosts,
    calculate_gas_extend_memory,
    calculate_message_call_gas,
    charge_gas,
    charge_state_gas,
    check_gas,
    credit_state_gas_refund,
    drain_state_gas_reservoir,
    init_code_cost,
    restore_child_gas,
    withhold_create_gas,
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
    Run the child-frame lifecycle for the `CREATE*` family of opcodes.

    The opcode has already priced the operation itself; this function
    runs the lifecycle: preflight checks that abort without spawning,
    the destination access with its account-creation charge and
    collision check, the child's gas grant, the child frame itself,
    and the resolution of its outcome back into the creating frame.
    """
    # These imports cause a circular import error
    # if they're not moved inside this method
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_create
    from ...vm.runtime import get_valid_jump_destinations

    tx_state = evm.tx_env.state

    init_code = memory_read_bytes(
        evm.memory, memory_start_position, memory_size
    )

    evm.return_data = b""

    # PREFLIGHT
    # Abort without spawning the child: nothing has been charged or
    # withheld for it yet.
    sender_address = evm.current_target
    sender = get_account(tx_state, sender_address)

    if (
        sender.balance < endowment
        or sender.nonce == Uint(2**64 - 1)
        or evm.depth + Uint(1) > STACK_DEPTH_LIMIT
    ):
        push(evm.stack, U256(0))
        return

    # DESTINATION ACCESS
    # The account-creation charge is decided by existence alone,
    # independently of the collision outcome below.
    evm.accessed_addresses.add(contract_address)

    new_account_charged = not is_account_alive(tx_state, contract_address)
    if new_account_charged:
        charge_state_gas(evm, StateGasCosts.NEW_ACCOUNT)

    # CHILD GRANT
    # Withhold all but one 64th of the execution gas.
    create_message_gas = withhold_create_gas(evm.gas_meter)

    # On a collision the child's execution-gas grant is consumed and no
    # account is created; a storage-only collision target is
    # non-existent: charged above, refilled here.
    if not account_deployable(tx_state, contract_address):
        increment_nonce(tx_state, sender_address)
        if new_account_charged:
            credit_state_gas_refund(evm.gas_meter, StateGasCosts.NEW_ACCOUNT)
        push(evm.stack, U256(0))
        return

    # The whole state gas reservoir rides along (no 63/64 rule for
    # state gas) and is restored when the child returns.
    create_message_state_gas_reservoir = drain_state_gas_reservoir(
        evm.gas_meter
    )

    increment_nonce(tx_state, sender_address)

    # DISPATCH

    child_evm = Evm(
        # Context
        block_env=evm.block_env,
        tx_env=evm.tx_env,
        parent_evm=evm,
        depth=evm.depth + Uint(1),
        # Call Parameters
        caller=evm.current_target,
        current_target=contract_address,
        value=endowment,
        call_data=b"",
        should_transfer_value=True,
        is_static=False,
        disable_precompiles=False,
        # Code
        code_address=None,
        code=init_code,
        valid_jump_destinations=get_valid_jump_destinations(init_code),
        # Machine State
        gas_meter=GasMeter(
            gas_left=create_message_gas,
            state_gas_left=create_message_state_gas_reservoir,
            state_gas_baseline=create_message_state_gas_reservoir,
        ),
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        return_data=b"",
        # Accrued Effects
        logs=(),
        accessed_addresses=evm.accessed_addresses.copy(),
        accessed_storage_keys=evm.accessed_storage_keys.copy(),
        # Outcome
        running=True,
        output=b"",
        error=None,
    )
    child_evm = process_create(child_evm)

    # OUTCOME
    # The child settled its own gas; absorb it and resolve the
    # account-creation charge by the state's fate: it refills when a
    # charged creation failed.
    incorporate_child(evm, child_evm)
    if child_evm.error:
        if new_account_charged:
            credit_state_gas_refund(evm.gas_meter, StateGasCosts.NEW_ACCOUNT)
        evm.return_data = child_evm.output
        push(evm.stack, U256(0))
    else:
        evm.return_data = b""
        push(evm.stack, U256.from_be_bytes(child_evm.current_target))


def create(evm: Evm) -> None:
    """
    Creates a new account with associated code.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # This import causes a circular import error
    # if it's not moved inside this method
    from ...vm.interpreter import MAX_INIT_CODE_SIZE

    if evm.is_static:
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
        GasCosts.CREATE_ACCESS + extend_memory.cost + init_code_gas,
    )

    if memory_size > U256(MAX_INIT_CODE_SIZE):
        raise OutOfGasError

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    contract_address = compute_contract_address(
        evm.current_target,
        get_account(evm.tx_env.state, evm.current_target).nonce,
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
    # This import causes a circular import error
    # if it's not moved inside this method
    from ...vm.interpreter import MAX_INIT_CODE_SIZE

    if evm.is_static:
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
        ExecutionGas(
            GasCosts.CREATE_ACCESS
            + GasCosts.OPCODE_KECCAK256_PER_WORD * call_data_words
            + extend_memory.cost
            + init_code_gas
        ),
    )

    if memory_size > U256(MAX_INIT_CODE_SIZE):
        raise OutOfGasError

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    contract_address = compute_create2_contract_address(
        evm.current_target,
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

    gas: ExecutionGas
    state_gas_reservoir: StateGas
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
    insufficient_balance: bool = False
    """
    True when the calling account cannot cover `value`; the call then
    aborts in preflight without spawning the child frame.
    """


def generic_call(evm: Evm, params: GenericCall) -> None:
    """
    Run the child-frame lifecycle for the `CALL*` family of opcodes.

    The opcode has already priced the call and withheld the child's
    grant; this function only runs the lifecycle: preflight checks
    that abort without spawning, the child frame itself, and the
    resolution of its outcome back into the calling frame.
    """
    from ...vm.interpreter import STACK_DEPTH_LIMIT, process_call
    from ...vm.runtime import get_valid_jump_destinations

    evm.return_data = b""

    # PREFLIGHT
    # Abort without spawning the child: both grants return untouched
    # and any account-creation charge refills.
    if evm.depth + Uint(1) > STACK_DEPTH_LIMIT or params.insufficient_balance:
        restore_child_gas(
            evm.gas_meter, params.gas, params.state_gas_reservoir
        )
        if params.new_account_charged:
            credit_state_gas_refund(evm.gas_meter, StateGasCosts.NEW_ACCOUNT)
        push(evm.stack, U256(0))
        return

    # DISPATCH
    call_data = memory_read_bytes(
        evm.memory,
        params.memory_input_start_position,
        params.memory_input_size,
    )

    child_evm = Evm(
        # Context
        block_env=evm.block_env,
        tx_env=evm.tx_env,
        parent_evm=evm,
        depth=evm.depth + Uint(1),
        # Call Parameters
        caller=params.caller,
        current_target=params.to,
        value=params.value,
        call_data=call_data,
        should_transfer_value=params.should_transfer_value,
        is_static=params.is_staticcall or evm.is_static,
        disable_precompiles=params.disable_precompiles,
        # Code
        code_address=params.code_address,
        code=params.code,
        valid_jump_destinations=get_valid_jump_destinations(params.code),
        # Machine State
        gas_meter=GasMeter(
            gas_left=params.gas,
            state_gas_left=params.state_gas_reservoir,
            state_gas_baseline=params.state_gas_reservoir,
        ),
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        return_data=b"",
        # Accrued Effects
        logs=(),
        accessed_addresses=evm.accessed_addresses.copy(),
        accessed_storage_keys=evm.accessed_storage_keys.copy(),
        # Outcome
        running=True,
        output=b"",
        error=None,
    )

    child_evm = process_call(child_evm)

    # OUTCOME
    # The child settled its own gas; absorb it and resolve the
    # account-creation charge by the state's fate.
    incorporate_child(evm, child_evm)
    evm.return_data = child_evm.output
    if child_evm.error:
        if params.new_account_charged:
            credit_state_gas_refund(evm.gas_meter, StateGasCosts.NEW_ACCOUNT)
        push(evm.stack, U256(0))
    else:
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
    gas = ExecutionGas(Uint(pop(evm.stack)))
    to = to_address_masked(pop(evm.stack))
    value = pop(evm.stack)
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    if evm.is_static and value != U256(0):
        raise WriteInStaticContext

    # GAS (STATE-INDEPENDENT)
    # Price what is computable without touching state, and check it is
    # affordable before any state access is performed.
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

    transfer_gas_cost = GasCosts.ZERO if value == 0 else GasCosts.CALL_VALUE

    check_gas(
        evm,
        access_gas_cost + transfer_gas_cost + extend_memory.cost,
    )

    # STATE ACCESS (STATE-DEPENDENT GAS)
    # Perform the accesses and complete the state-dependent pricing --
    # a delegation adds its access cost -- then charge the execution
    # gas.
    tx_state = evm.tx_env.state
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

    # STATE GAS
    # A value transfer that will create the recipient is charged by
    # the frame whose opcode causes it; refilled in `generic_call`
    # whenever the creation fails or never happens.
    has_value = value != 0
    new_account_charged = has_value and not is_account_alive(tx_state, to)
    if new_account_charged:
        charge_state_gas(evm, StateGasCosts.NEW_ACCOUNT)

    # CHILD GRANT
    # Computed after every charge above, so any state-gas spill has
    # already thinned `gas_left`. The whole reservoir rides along (no
    # 63/64 rule for state gas).
    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        evm.gas_meter.gas_left,
        memory_cost=GasCosts.ZERO,
        extra_gas=GasCosts.ZERO,
    )
    charge_gas(evm, message_call_gas.cost)
    call_state_gas_reservoir = drain_state_gas_reservoir(evm.gas_meter)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    sender_balance = get_account(tx_state, evm.current_target).balance

    generic_call(
        evm,
        GenericCall(
            gas=message_call_gas.sub_call,
            state_gas_reservoir=call_state_gas_reservoir,
            value=value,
            caller=evm.current_target,
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
            insufficient_balance=sender_balance < value,
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
    gas = ExecutionGas(Uint(pop(evm.stack)))
    code_address = to_address_masked(pop(evm.stack))
    value = pop(evm.stack)
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS (STATE-INDEPENDENT)
    # Price what is computable without touching state, and check it is
    # affordable before any state access is performed.
    to = evm.current_target

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

    transfer_gas_cost = GasCosts.ZERO if value == 0 else GasCosts.CALL_VALUE

    check_gas(
        evm,
        access_gas_cost + extend_memory.cost + transfer_gas_cost,
    )

    # STATE ACCESS (STATE-DEPENDENT GAS)
    # Perform the accesses and complete the state-dependent pricing --
    # a delegation adds its access cost; the execution gas is charged
    # with the child grant.
    tx_state = evm.tx_env.state
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

    # CHILD GRANT
    # Charge the call's cost and withhold the child's execution gas
    # share in one step. The whole reservoir rides along (no 63/64
    # rule for state gas).
    message_call_gas = calculate_message_call_gas(
        value,
        gas,
        evm.gas_meter.gas_left,
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)
    call_state_gas_reservoir = drain_state_gas_reservoir(evm.gas_meter)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    sender_balance = get_account(tx_state, evm.current_target).balance

    generic_call(
        evm,
        GenericCall(
            gas=message_call_gas.sub_call,
            state_gas_reservoir=call_state_gas_reservoir,
            value=value,
            caller=evm.current_target,
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
            insufficient_balance=sender_balance < value,
        ),
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sendall(evm: Evm) -> None:
    """
    Halt execution and send the entire balance of the current account to
    the beneficiary.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    if evm.is_static:
        raise WriteInStaticContext

    # STACK
    beneficiary = to_address_masked(pop(evm.stack))

    # GAS (STATE-INDEPENDENT)
    # Price what is computable without touching state, and check it is
    # affordable before any state access is performed.
    gas_cost = GasCosts.OPCODE_SENDALL_BASE

    is_cold_access = beneficiary not in evm.accessed_addresses
    if is_cold_access:
        gas_cost += GasCosts.COLD_ACCOUNT_ACCESS

    check_gas(evm, gas_cost)

    # STATE ACCESS (STATE-DEPENDENT GAS)
    # Perform the access; the pricing completes with the state gas
    # below.
    tx_state = evm.tx_env.state
    if is_cold_access:
        evm.accessed_addresses.add(beneficiary)

    # STATE GAS
    # A sweep that will create the beneficiary pays the account write
    # and the creation, charged by the frame whose opcode causes it;
    # it refills only through the frame's own rollback.
    state_gas = StateGas(Uint(0))
    account_write_gas = GasCosts.ZERO
    if (
        not is_account_alive(tx_state, beneficiary)
        and get_account(tx_state, evm.current_target).balance != 0
    ):
        state_gas = StateGasCosts.NEW_ACCOUNT
        account_write_gas = GasCosts.ACCOUNT_WRITE

    # Charge execution gas before state gas so that an execution-gas
    # OOG does not consume state gas that would inflate the parent's
    # reservoir on frame failure.
    charge_gas(evm, gas_cost + account_write_gas)
    charge_state_gas(evm, state_gas)

    # OPERATION
    originator = evm.current_target
    originator_balance = get_account(tx_state, originator).balance

    # Transfer balance
    move_ether(tx_state, originator, beneficiary, originator_balance)

    # Emit transfer log
    if beneficiary != originator:
        emit_transfer_log(evm, originator, beneficiary, originator_balance)

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
    gas = ExecutionGas(Uint(pop(evm.stack)))
    code_address = to_address_masked(pop(evm.stack))
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS (STATE-INDEPENDENT)
    # Price what is computable without touching state, and check it is
    # affordable before any state access is performed.
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

    check_gas(evm, access_gas_cost + extend_memory.cost)

    # STATE ACCESS (STATE-DEPENDENT GAS)
    # Perform the accesses and complete the state-dependent pricing --
    # a delegation adds its access cost; the execution gas is charged
    # with the child grant.
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

    tx_state = evm.tx_env.state
    code_hash = get_account(tx_state, code_address).code_hash
    code = get_code(tx_state, code_hash)

    # CHILD GRANT
    # Charge the call's cost and withhold the child's execution gas
    # share in one step. The whole reservoir rides along (no 63/64
    # rule for state gas).
    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        evm.gas_meter.gas_left,
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)
    call_state_gas_reservoir = drain_state_gas_reservoir(evm.gas_meter)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    generic_call(
        evm,
        GenericCall(
            gas=message_call_gas.sub_call,
            state_gas_reservoir=call_state_gas_reservoir,
            value=evm.value,
            caller=evm.caller,
            to=evm.current_target,
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
    gas = ExecutionGas(Uint(pop(evm.stack)))
    to = to_address_masked(pop(evm.stack))
    memory_input_start_position = pop(evm.stack)
    memory_input_size = pop(evm.stack)
    memory_output_start_position = pop(evm.stack)
    memory_output_size = pop(evm.stack)

    # GAS (STATE-INDEPENDENT)
    # Price what is computable without touching state, and check it is
    # affordable before any state access is performed.
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

    check_gas(evm, access_gas_cost + extend_memory.cost)

    # STATE ACCESS (STATE-DEPENDENT GAS)
    # Perform the accesses and complete the state-dependent pricing --
    # a delegation adds its access cost; the execution gas is charged
    # with the child grant.
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

    tx_state = evm.tx_env.state
    code_hash = get_account(tx_state, code_address).code_hash
    code = get_code(tx_state, code_hash)

    # CHILD GRANT
    # Charge the call's cost and withhold the child's execution gas
    # share in one step. The whole reservoir rides along (no 63/64
    # rule for state gas).
    message_call_gas = calculate_message_call_gas(
        U256(0),
        gas,
        evm.gas_meter.gas_left,
        extend_memory.cost,
        extra_gas,
    )
    charge_gas(evm, message_call_gas.cost + extend_memory.cost)
    call_state_gas_reservoir = drain_state_gas_reservoir(evm.gas_meter)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by

    generic_call(
        evm,
        GenericCall(
            gas=message_call_gas.sub_call,
            state_gas_reservoir=call_state_gas_reservoir,
            value=U256(0),
            caller=evm.current_target,
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
