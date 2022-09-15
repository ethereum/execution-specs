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
from typing import Iterable, Set, Tuple, Union

from ethereum import evm_trace
from ethereum.base_types import U256, Bytes0, Uint
from ethereum.utils.ensure import ensure

from ..eth_types import Address, Log
from ..state import (
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
from ..utils.address import to_address
from ..vm import Message
from ..vm.gas import GAS_CODE_DEPOSIT, REFUND_SELF_DESTRUCT, subtract_gas
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
RIPEMD160_ADDRESS = to_address(Uint(3))


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
    logs: Union[Tuple[()], Tuple[Log, ...]]
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
        touched_accounts=collect_touched_accounts(evm),
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
    evm: :py:class:`~ethereum.constantinople.vm.Evm`
        Items containing execution specific objects.
    """
    # take snapshot of state before processing the message
    begin_transaction(env.state)

    increment_nonce(env.state, message.current_target)
    evm = process_message(message, env)
    if not evm.has_erred:
        contract_code = evm.output
        contract_code_gas = len(contract_code) * GAS_CODE_DEPOSIT
        try:
            evm.gas_left = subtract_gas(evm.gas_left, contract_code_gas)
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


def process_create2_message(message: Message, env: Environment) -> Evm:
    """
    Executes a call to create a smart contract via CREATE2 opcode.

    Parameters
    ----------
    message :
        Transaction specific items.
    env :
        External items required for EVM execution.

    Returns
    -------
    evm: :py:class:`~ethereum.constantinople.vm.Evm`
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
            evm.gas_left = subtract_gas(evm.gas_left, contract_code_gas)
            ensure(len(contract_code) <= MAX_CODE_SIZE, OutOfGasError)
        except OutOfGasError:
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
    evm: :py:class:`~ethereum.constantinople.vm.Evm`
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
        refund_counter=U256(0),
        running=True,
        message=message,
        output=b"",
        accounts_to_delete=dict(),
        has_erred=False,
        children=[],
        return_data=b"",
        error=None,
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


def collect_touched_accounts(
    evm: Evm, ancestor_had_error: bool = False
) -> Iterable[Address]:
    """
    Collect all of the accounts that *may* need to be deleted based on
    `EIP-161 <https://eips.ethereum.org/EIPS/eip-161>`_.
    Checking whether they *do* need to be deleted happens in the caller.
    See also: https://github.com/ethereum/EIPs/issues/716

    Parameters
    ----------
    evm :
        The current EVM frame.
    ancestor_had_error :
        True if the ancestors of the evm object erred else False

    Returns
    -------
    touched_accounts: `typing.Iterable`
        returns all the accounts that were touched and may need to be deleted.
    """
    # collect the coinbase account if it was touched via zero-fee transfer
    if (evm.message.caller == evm.env.origin) and evm.env.gas_price == 0:
        yield evm.env.coinbase

    # collect those explicitly marked for deletion
    # ("beneficiary" is of SELFDESTRUCT)
    for beneficiary in sorted(set(evm.accounts_to_delete.values())):
        if evm.has_erred or ancestor_had_error:
            # Special case to account for geth+parity bug
            # https://github.com/ethereum/EIPs/issues/716
            if beneficiary == RIPEMD160_ADDRESS:
                yield beneficiary
            continue
        else:
            yield beneficiary

    # collect account directly addressed
    if not isinstance(evm.message.target, Bytes0):
        if evm.has_erred or ancestor_had_error:
            # collect RIPEMD160 precompile even if ancestor evm had error.
            # otherwise, skip collection from children of erred-out evm objects
            if evm.message.target == RIPEMD160_ADDRESS:
                yield evm.message.target
        else:
            yield evm.message.target

    # recurse into nested computations
    # (even erred ones, since looking for RIPEMD160)
    for child in evm.children:
        yield from collect_touched_accounts(
            child, ancestor_had_error=(evm.has_erred or ancestor_had_error)
        )


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
                evm.accounts_to_delete.keys(),
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
