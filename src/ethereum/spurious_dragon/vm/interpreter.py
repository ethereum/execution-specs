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
from typing import Iterable, Set, Tuple, Union

from ethereum.base_types import U256, Bytes0, Uint
from ethereum.utils.ensure import EnsureError, ensure

from ..eth_types import Address, Log
from ..state import (
    account_has_code_or_nonce,
    begin_transaction,
    commit_transaction,
    get_account,
    increment_nonce,
    move_ether,
    rollback_transaction,
    set_code,
    touch_account,
)
from ..utils.address import to_address
from ..vm import Message
from ..vm.error import (
    InsufficientFunds,
    InvalidJumpDestError,
    InvalidOpcode,
    OutOfGasError,
    StackDepthLimitError,
    StackOverflowError,
    StackUnderflowError,
)
from ..vm.gas import GAS_CODE_DEPOSIT, REFUND_SELF_DESTRUCT, subtract_gas
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from . import Environment, Evm
from .instructions import Ops, op_implementation
from .runtime import get_valid_jump_destinations

STACK_DEPTH_LIMIT = U256(1024)
MAX_CODE_SIZE = 0x6000
RIPEMD160_ADDRESS = to_address(Uint(3))


def process_message_call(
    message: Message, env: Environment
) -> Tuple[
    U256,
    U256,
    Union[Tuple[()], Tuple[Log, ...]],
    Set[Address],
    Iterable[Address],
    bool,
]:
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
    output : `Tuple`
        A tuple of the following:

          1. `gas_left`: remaining gas after execution.
          2. `refund_counter`: gas to refund after execution.
          3. `logs`: list of `Log` generated during execution.
          4. `accounts_to_delete`: Contracts which have self-destructed.
          5. `touched_accounts`: Accounts that have been touched.
          6. `has_erred`: True if execution has caused an error.
    """
    if message.target == Bytes0(b""):
        is_collision = account_has_code_or_nonce(
            env.state, message.current_target
        )
        if is_collision:
            return U256(0), U256(0), tuple(), set(), set(), True
        else:
            evm = process_create_message(message, env)
    else:
        evm = process_message(message, env)

    accounts_to_delete = collect_accounts_to_delete(evm, set())
    evm.refund_counter += len(accounts_to_delete) * REFUND_SELF_DESTRUCT

    return (
        evm.gas_left,
        evm.refund_counter,
        evm.logs,
        accounts_to_delete,
        collect_touched_accounts(evm),
        evm.has_erred,
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
    evm: :py:class:`~ethereum.spurious_dragon.vm.Evm`
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
        except OutOfGasError:
            rollback_transaction(env.state)
            evm.gas_left = U256(0)
            evm.logs = ()
            evm.accounts_to_delete = dict()
            evm.refund_counter = U256(0)
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
    evm: :py:class:`~ethereum.spurious_dragon.vm.Evm`
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
        accounts_to_delete=dict(),
        has_erred=False,
        children=[],
    )
    try:

        if evm.message.code_address in PRE_COMPILED_CONTRACTS:
            PRE_COMPILED_CONTRACTS[evm.message.code_address](evm)
            return evm

        while evm.running and evm.pc < len(evm.code):
            try:
                op = Ops(evm.code[evm.pc])
            except ValueError:
                raise InvalidOpcode(evm.code[evm.pc])

            op_implementation[op](evm)

    except (
        OutOfGasError,
        InvalidOpcode,
        InvalidJumpDestError,
        InsufficientFunds,
        StackOverflowError,
        StackUnderflowError,
        StackDepthLimitError,
    ):
        evm.gas_left = U256(0)
        evm.logs = ()
        evm.accounts_to_delete = dict()
        evm.refund_counter = U256(0)
        evm.has_erred = True
    except (
        EnsureError,
        ValueError,
    ):
        evm.has_erred = True
    finally:
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


def collect_accounts_to_delete(
    evm: Evm, accounts_to_delete: Set[Address]
) -> Set[Address]:
    """
    Collects all the accounts that need to deleted from the `evm` object and
    its children

    Parameters
    ----------
    evm :
        The current EVM frame.
    accounts_to_delete :
        list of accounts that need to be deleted.
        Note: An empty set should be passed to this parameter. This set
        is used to store the results obtained by recursively iterating over the
        child evm objects

    Returns
    -------
    touched_accounts: `set`
        returns all the accounts that were touched and may need to be deleted.
    """
    if not evm.has_erred:
        for address in evm.accounts_to_delete.keys():
            accounts_to_delete.add(address)
        for child in evm.children:
            collect_accounts_to_delete(child, accounts_to_delete)
    return accounts_to_delete
