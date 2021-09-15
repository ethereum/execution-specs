"""
Ethereum Virtual Machine (EVM) Interpreter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

A straightforward interpreter that executes EVM code.
"""
from ethereum.base_types import U256, Bytes0, Uint
from ethereum.frontier.state import (
    begin_transaction,
    commit_transaction,
    move_ether,
    rollback_transaction,
    set_code,
    touch_account,
)
from ethereum.frontier.vm import Message
from ethereum.frontier.vm.error import (
    Halt,
    InvalidJumpDestError,
    InvalidOpcode,
    OutOfGasError,
    StackDepthLimitError,
    StackOverflowError,
    StackUnderflowError,
)
from ethereum.frontier.vm.gas import (
    GAS_CODE_DEPOSIT,
    REFUND_SELF_DESTRUCT,
    subtract_gas,
)
from ethereum.frontier.vm.precompiled_contracts.mapping import (
    PRE_COMPILED_CONTRACTS,
)

from . import Environment, Evm
from .instructions import Ops, op_implementation
from .runtime import get_valid_jump_destinations

PC_CHANGING_OPS = {Ops.JUMP, Ops.JUMPI}


STACK_DEPTH_LIMIT = U256(1024)


def process_message_call(message: Message, env: Environment) -> Evm:
    """
    If `message.current` is empty then it creates a smart contract
    else it executes a call from the `message.caller` to the `message.target`.

    Parameters
    ----------
    message :
        Transaction specific items.

    env :
        External items required for EVM execution.

    Returns
    -------
    output : `Tuple[U256, List[eth1spec.eth_types.Log]]`
        The tuple `(gas_left, logs)`, where `gas_left` is the remaining gas
        after execution, and logs is the list of `eth1spec.eth_types.Log`
        generated during execution.
    """
    if message.target == Bytes0(b""):
        evm = process_create_message(message, env)
    else:
        evm = process_message(message, env)

    evm.refund_counter += len(evm.accounts_to_delete) * REFUND_SELF_DESTRUCT

    return evm


def process_create_message(message: Message, env: Environment) -> Evm:
    """
    Executes a call to create a smart contract.

    Parameters
    ----------
    message :
        Transaction specific items.
    env :
        External items required for EVM execution.

    Returns
    -------
    evm: `ethereum.frontier.vm.Evm`
        Items containing execution specific objects.
    """
    evm = process_message(message, env)
    contract_code = evm.output
    if contract_code:
        contract_code_gas = len(contract_code) * GAS_CODE_DEPOSIT
        evm.gas_left = subtract_gas(evm.gas_left, contract_code_gas)
        set_code(env.state, message.current_target, contract_code)
    return evm


def process_message(message: Message, env: Environment) -> Evm:
    """
    Executes a call to create a smart contract.

    Parameters
    ----------
    message :
        Transaction specific items.
    env :
        External items required for EVM execution.

    Returns
    -------
    evm: `ethereum.frontier.vm.Evm`
        Items containing execution specific objects
    """
    if message.depth > STACK_DEPTH_LIMIT:
        raise StackDepthLimitError("Stack depth limit reached")

    # take snapshot of state before processing the message
    begin_transaction(env.state)

    touch_account(env.state, message.current_target)
    if message.value != 0:
        move_ether(
            env.state, message.caller, message.current_target, message.value
        )

    evm = execute_code(message, env)
    if evm.has_erred:
        # revert state to the last saved checkpoint
        # since the message call resulted in an error
        rollback_transaction(env.state)
    else:
        commit_transaction(env.state)
    return evm


def execute_code(message: Message, env: Environment) -> Evm:
    """
    Executes bytecode present in the `message`.

    Parameters
    ----------
    message :
        Transaction specific items.
    env :
        External items required for EVM execution.

    Returns
    -------
    evm: `ethereum.vm.EVM`
        Items containing execution specific objects
    """
    code = message.code
    valid_jump_destinations = get_valid_jump_destinations(code)
    evm = Evm(
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        code=code,
        gas_left=message.gas,
        env=env,
        valid_jump_destinations=valid_jump_destinations,
        logs=(),
        refund_counter=U256(0),
        message=message,
        output=b"",
        accounts_to_delete=set(),
        has_erred=False,
    )
    try:

        if evm.message.code_address in PRE_COMPILED_CONTRACTS:
            PRE_COMPILED_CONTRACTS[evm.message.code_address](evm)
            return evm

        while evm.pc < len(evm.code):
            try:
                op = Ops(evm.code[evm.pc])
            except ValueError:
                raise InvalidOpcode(evm.code[evm.pc])

            op_implementation[op](evm)

            if op not in PC_CHANGING_OPS:
                evm.pc += 1

    except (
        OutOfGasError,
        InvalidOpcode,
        InvalidJumpDestError,
        StackOverflowError,
        StackUnderflowError,
        StackDepthLimitError,
    ):
        evm.gas_left = U256(0)
        evm.has_erred = True
    except (
        AssertionError,
        ValueError,
    ):
        evm.has_erred = True
    except Halt:
        pass
    finally:
        return evm
