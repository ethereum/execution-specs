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
from dataclasses import dataclass
from itertools import chain
from typing import Set, Tuple, Union

from ethereum import evm_trace
from ethereum.base_types import U256, Bytes0, Uint

from ..eth_types import Address, Log
from ..state import (
    account_has_code_or_nonce,
    begin_transaction,
    commit_transaction,
    get_account,
    move_ether,
    rollback_transaction,
    set_code,
    touch_account,
)
from ..vm import Message
from ..vm.gas import GAS_CODE_DEPOSIT, REFUND_SELF_DESTRUCT, subtract_gas
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from . import Environment, Evm
from .exceptions import (
    ExceptionalHalt,
    InsufficientFunds,
    InvalidOpcode,
    StackDepthLimitError,
)
from .instructions import Ops, op_implementation
from .runtime import get_valid_jump_destinations

STACK_DEPTH_LIMIT = U256(1024)


@dataclass
class MessageCallOutput:
    """
    Output of a particular message call

    Contains the following:

          1. `gas_left`: remaining gas after execution.
          2. `refund_counter`: gas to refund after execution.
          3. `logs`: list of `Log` generated during execution.
          4. `accounts_to_delete`: Contracts which have self-destructed.
          5. `has_erred`: True if execution has caused an error.
    """

    gas_left: U256
    refund_counter: U256
    logs: Union[Tuple[()], Tuple[Log, ...]]
    accounts_to_delete: Set[Address]
    has_erred: bool


def process_message_call(
    message: Message, env: Environment
) -> MessageCallOutput:
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
    output : `MessageCallOutput`
        Output of the message call
    """
    if message.target == Bytes0(b""):
        is_collision = account_has_code_or_nonce(
            env.state, message.current_target
        )
        if is_collision:
            return MessageCallOutput(U256(0), U256(0), tuple(), set(), True)
        else:
            evm = process_create_message(message, env)
    else:
        evm = process_message(message, env)

    accounts_to_delete = collect_accounts_to_delete(evm)
    refund_counter = (
        calculate_gas_refund(evm)
        + len(accounts_to_delete) * REFUND_SELF_DESTRUCT
    )

    return MessageCallOutput(
        gas_left=evm.gas_left,
        refund_counter=refund_counter,
        logs=evm.logs if not evm.has_erred else (),
        accounts_to_delete=accounts_to_delete,
        has_erred=evm.has_erred,
    )


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
    evm: :py:class:`~ethereum.homestead.vm.Evm`
        Items containing execution specific objects.
    """
    # take snapshot of state before processing the message
    begin_transaction(env.state)

    evm = process_message(message, env)
    if not evm.has_erred:
        contract_code = evm.output
        contract_code_gas = len(contract_code) * GAS_CODE_DEPOSIT
        try:
            evm.gas_left = subtract_gas(evm.gas_left, contract_code_gas)
        except ExceptionalHalt:
            rollback_transaction(env.state)
            evm.gas_left = U256(0)
            evm.has_erred = True
        else:
            set_code(env.state, message.current_target, contract_code)
            commit_transaction(env.state)
    else:
        rollback_transaction(env.state)
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
    evm: :py:class:`~ethereum.homestead.vm.Evm`
        Items containing execution specific objects
    """
    if message.depth > STACK_DEPTH_LIMIT:
        raise StackDepthLimitError("Stack depth limit reached")

    # take snapshot of state before processing the message
    begin_transaction(env.state)

    touch_account(env.state, message.current_target)

    sender_balance = get_account(env.state, message.caller).balance

    if message.should_transfer_value and message.value != 0:
        if sender_balance < message.value:
            rollback_transaction(env.state)
            raise InsufficientFunds(
                f"Insufficient funds: {sender_balance} < {message.value}"
            )
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
        running=True,
        message=message,
        output=b"",
        accounts_to_delete=set(),
        has_erred=False,
        children=[],
    )
    try:

        if evm.message.code_address in PRE_COMPILED_CONTRACTS:
            evm_trace(evm, evm.message.code_address)
            PRE_COMPILED_CONTRACTS[evm.message.code_address](evm)
            return evm

        while evm.running and evm.pc < len(evm.code):
            try:
                op = Ops(evm.code[evm.pc])
            except ValueError:
                raise InvalidOpcode(evm.code[evm.pc])

            evm_trace(evm, op)
            op_implementation[op](evm)

    except ExceptionalHalt:
        evm.gas_left = U256(0)
        evm.has_erred = True
    return evm


def collect_accounts_to_delete(evm: Evm) -> Set[Address]:
    """
    Collects all the accounts that were marked for deletion by the
    `SELFDESTRUCT` opcode.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Returns
    -------
    accounts_to_delete: `set`
        returns all the accounts need marked for deletion by the
        `SELFDESTRUCT` opcode.
    """
    if evm.has_erred:
        return set()
    else:
        return set(
            chain(
                evm.accounts_to_delete,
                *(collect_accounts_to_delete(child) for child in evm.children),
            )
        )


def calculate_gas_refund(evm: Evm) -> U256:
    """
    Adds up the gas that was refunded in each execution frame during the
    message call.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Returns
    -------
    gas_refund: `ethereum.base_types.U256`
        returns the total gas that needs to be refunded after executing the
        message call.
    """
    if evm.has_erred:
        return U256(0)
    else:
        return evm.refund_counter + sum(
            calculate_gas_refund(child_evm) for child_evm in evm.children
        )
