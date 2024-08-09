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
from typing import Iterable, Optional, Set, Tuple, Union

from ethereum.base_types import U256, Bytes, Bytes0, Uint
from ethereum.trace import (
    EvmStop,
    OpEnd,
    OpException,
    OpStart,
    PrecompileEnd,
    PrecompileStart,
    TransactionEnd,
    evm_trace,
)

from ..blocks import Log
from ..fork_types import Address
from ..state import (
    account_exists_and_is_empty,
    account_has_code_or_nonce,
    account_has_storage,
    begin_transaction,
    commit_transaction,
    destroy_storage,
    increment_nonce,
    mark_account_created,
    move_ether,
    rollback_transaction,
    set_code,
    touch_account,
)
from ..vm import Message
from ..vm.eoa_delegation import set_delegation
from ..vm.gas import GAS_CODE_DEPOSIT, charge_gas
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from . import MAX_CODE_SIZE, Environment, Eof, Evm, Message, get_eof_version
from .eof import map_int_to_op, parse_container_metadata
from .exceptions import (
    AddressCollision,
    ExceptionalHalt,
    InvalidContractPrefix,
    InvalidEof,
    InvalidOpcode,
    OutOfGasError,
    Revert,
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
          5. `touched_accounts`: Accounts that have been touched.
          6. `error`: The error from the execution if any.
          7. `return_data`: The output of the execution.
    """

    gas_left: Uint
    refund_counter: U256
    logs: Union[Tuple[()], Tuple[Log, ...]]
    accounts_to_delete: Set[Address]
    touched_accounts: Iterable[Address]
    error: Optional[Exception]
    return_data: Bytes


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
    refund_counter = U256(0)
    if message.target == Bytes0(b""):
        is_collision = account_has_code_or_nonce(
            env.state, message.current_target
        ) or account_has_storage(env.state, message.current_target)
        if is_collision:
            return MessageCallOutput(
                Uint(0),
                U256(0),
                tuple(),
                set(),
                set(),
                AddressCollision(),
                Bytes(b""),
            )
        else:
            evm = process_create_message(message, env)
    else:
        if message.authorizations != set():
            refund_counter += set_delegation(message, env)
        evm = process_message(message, env)
        if account_exists_and_is_empty(env.state, Address(message.target)):
            evm.touched_accounts.add(Address(message.target))

    if evm.error:
        logs: Tuple[Log, ...] = ()
        accounts_to_delete = set()
        touched_accounts = set()
    else:
        logs = evm.logs
        accounts_to_delete = evm.accounts_to_delete
        touched_accounts = evm.touched_accounts
        refund_counter += U256(evm.refund_counter)

    tx_end = TransactionEnd(message.gas - evm.gas_left, evm.output, evm.error)
    evm_trace(evm, tx_end)

    return MessageCallOutput(
        gas_left=evm.gas_left,
        refund_counter=refund_counter,
        logs=logs,
        accounts_to_delete=accounts_to_delete,
        touched_accounts=touched_accounts,
        error=evm.error,
        return_data=evm.output,
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
    evm: :py:class:`~ethereum.prague.vm.Evm`
        Items containing execution specific objects.
    """
    # take snapshot of state before processing the message
    begin_transaction(env.state, env.transient_storage)

    # If the address where the account is being created has storage, it is
    # destroyed. This can only happen in the following highly unlikely
    # circumstances:
    # * The address created by a `CREATE` call collides with a subsequent
    #   `CREATE` or `CREATE2` call.
    # * The first `CREATE` happened before Spurious Dragon and left empty
    #   code.
    destroy_storage(env.state, message.current_target)

    # In the previously mentioned edge case the preexisting storage is ignored
    # for gas refund purposes. In order to do this we must track created
    # accounts.
    mark_account_created(env.state, message.current_target)

    increment_nonce(env.state, message.current_target)
    evm = process_message(message, env)
    if not evm.error:
        if evm.deploy_container is not None:
            contract_code = evm.deploy_container
        else:
            contract_code = evm.output
        contract_code_gas = len(contract_code) * GAS_CODE_DEPOSIT
        try:
            if len(contract_code) > 0:
                if (
                    get_eof_version(contract_code) == Eof.LEGACY
                    and contract_code[0] == 0xEF
                ):
                    raise InvalidContractPrefix
                if (
                    evm.eof_version == Eof.LEGACY
                    and get_eof_version(contract_code) == Eof.EOF1
                ):
                    raise ExceptionalHalt(
                        "Cannot deploy EOF1 from legacy init code"
                    )
            charge_gas(evm, contract_code_gas)
            if len(contract_code) > MAX_CODE_SIZE:
                raise OutOfGasError
        except ExceptionalHalt as error:
            rollback_transaction(env.state, env.transient_storage)
            evm.gas_left = Uint(0)
            evm.output = b""
            evm.error = error
        else:
            set_code(env.state, message.current_target, contract_code)
            commit_transaction(env.state, env.transient_storage)
    else:
        rollback_transaction(env.state, env.transient_storage)
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
    evm: :py:class:`~ethereum.prague.vm.Evm`
        Items containing execution specific objects
    """
    if message.depth > STACK_DEPTH_LIMIT:
        raise StackDepthLimitError("Stack depth limit reached")

    # take snapshot of state before processing the message
    begin_transaction(env.state, env.transient_storage)

    touch_account(env.state, message.current_target)

    if message.should_transfer_value and message.value != 0:
        move_ether(
            env.state, message.caller, message.current_target, message.value
        )

    evm = execute_code(message, env)
    if evm.error:
        # revert state to the last saved checkpoint
        # since the message call resulted in an error
        rollback_transaction(env.state, env.transient_storage)
    else:
        commit_transaction(env.state, env.transient_storage)
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
    # TODO: Get eof_metadata from message
    code_or_container = message.code

    eof_version = get_eof_version(code_or_container)

    if eof_version == Eof.EOF1:
        assert message.is_init_container is not None
        container = code_or_container
        eof_metadata = parse_container_metadata(
            code_or_container,
            validate=False,
            is_deploy_container=False,
            is_init_container=message.is_init_container,
        )
        code = eof_metadata.code_section_contents[0]
        valid_jump_destinations = set()
    elif eof_version == Eof.LEGACY:
        container = None
        eof_metadata = None
        code = code_or_container
        valid_jump_destinations = get_valid_jump_destinations(
            code_or_container
        )
    else:
        raise InvalidEof

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
        return_data=b"",
        error=None,
        accessed_addresses=message.accessed_addresses,
        accessed_storage_keys=message.accessed_storage_keys,
        eof_version=eof_version,
        eof_container=container,
        eof_metadata=eof_metadata,
        current_section_index=Uint(0),
        return_stack=[],
        deploy_container=None,
    )
    try:
        if evm.message.code_address in PRE_COMPILED_CONTRACTS:
            evm_trace(evm, PrecompileStart(evm.message.code_address))
            PRE_COMPILED_CONTRACTS[evm.message.code_address](evm)
            evm_trace(evm, PrecompileEnd())
            return evm

        while evm.running and evm.pc < len(evm.code):
            try:
                op = map_int_to_op(evm.code[evm.pc], evm.eof_version)
            except ValueError:
                raise InvalidOpcode(evm.code[evm.pc])

            evm_trace(evm, OpStart(op))
            op_implementation[op](evm)
            evm_trace(evm, OpEnd())

        evm_trace(evm, EvmStop(Ops.STOP))

    except ExceptionalHalt as error:
        evm_trace(evm, OpException(error))
        evm.gas_left = Uint(0)
        evm.output = b""
        evm.error = error
    except Revert as error:
        evm_trace(evm, OpException(error))
        evm.error = error
    return evm
