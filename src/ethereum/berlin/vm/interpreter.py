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
from typing import Iterable, Set, Tuple

from ethereum import evm_trace
from ethereum.base_types import U256, Bytes0, Uint
from ethereum.utils.ensure import ensure

from ..eth_types import Address, Log
from ..state import (
    account_exists_and_is_empty,
    account_has_code_or_nonce,
    begin_transaction,
    commit_transaction,
    destroy_storage,
    increment_nonce,
    move_ether,
    rollback_transaction,
    set_code,
    touch_account,
)
from ..vm import Message
from ..vm.gas import GAS_CODE_DEPOSIT, REFUND_SELF_DESTRUCT, charge_gas
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from . import Environment, Evm
from .exceptions import (
    ExceptionalHalt,
    InvalidOpcode,
    OutOfGasError,
    Revert,
    StackDepthLimitError,
)
from .instructions import Ops, op_implementation
from .runtime import get_valid_jump_destinations

STACK_DEPTH_LIMIT = U256(1024)
MAX_CODE_SIZE = 0x6000


@dataclass
class MessageCallOutput:
    """
    Output of a particular message call

    Contains the following:

          1. `gas_left`: remaining gas after execution.
          2. `refund_counter`: gas to refund after execution.
          3. `logs`: list of `Log` generated during execution.
          4. `accounts_to_delete`: Contracts which have self-destructed.
          5. `touched_accounts`: Accounts that have been touched.
          6. `has_erred`: True if execution has caused an error.
    """

    gas_left: U256
    refund_counter: U256
    logs: Tuple[Log, ...]
    accounts_to_delete: Set[Address]
    touched_accounts: Iterable[Address]
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
            return MessageCallOutput(
                U256(0), U256(0), tuple(), set(), set(), True
            )
        else:
            evm = process_create_message(message, env)
    else:
        evm = process_message(message, env)
        if account_exists_and_is_empty(env.state, Address(message.target)):
            evm.touched_accounts.add(Address(message.target))

    if evm.has_erred:
        logs: Tuple[Log, ...] = ()
        accounts_to_delete = set()
        touched_accounts = set()
        refund_counter = U256(0)
    else:
        logs = evm.logs
        accounts_to_delete = evm.accounts_to_delete
        touched_accounts = evm.touched_accounts
        refund_counter = U256(evm.refund_counter) + REFUND_SELF_DESTRUCT * len(
            evm.accounts_to_delete
        )

    return MessageCallOutput(
        gas_left=evm.gas_left,
        refund_counter=refund_counter,
        logs=logs,
        accounts_to_delete=accounts_to_delete,
        touched_accounts=touched_accounts,
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
    evm: :py:class:`~ethereum.berlin.vm.Evm`
        Items containing execution specific objects.
    """
    # take snapshot of state before processing the message
    begin_transaction(env.state)

    # It's expected that the creation operation works on empty storage. Hence
    # we delete the storage and restore the account's state if there is an
    # error in the initialization code execution.
    destroy_storage(env.state, message.current_target)

    increment_nonce(env.state, message.current_target)
    evm = process_message(message, env)
    if not evm.has_erred:
        contract_code = evm.output
        contract_code_gas = len(contract_code) * GAS_CODE_DEPOSIT
        try:
            charge_gas(evm, contract_code_gas)
            ensure(len(contract_code) <= MAX_CODE_SIZE, OutOfGasError)
        except ExceptionalHalt:
            rollback_transaction(env.state)
            evm.gas_left = U256(0)
            evm.output = b""
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
    evm: :py:class:`~ethereum.berlin.vm.Evm`
        Items containing execution specific objects
    """
    if message.depth > STACK_DEPTH_LIMIT:
        raise StackDepthLimitError("Stack depth limit reached")

    # take snapshot of state before processing the message
    begin_transaction(env.state)

    touch_account(env.state, message.current_target)

    if message.should_transfer_value and message.value != 0:
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
        refund_counter=0,
        running=True,
        message=message,
        output=b"",
        accounts_to_delete=set(),
        touched_accounts=set(),
        has_erred=False,
        return_data=b"",
        error=None,
        accessed_addresses=message.accessed_addresses,
        accessed_storage_keys=message.accessed_storage_keys,
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
        evm.output = b""
        evm.has_erred = True
    except Revert as e:
        evm.error = e
        evm.has_erred = True
    return evm
