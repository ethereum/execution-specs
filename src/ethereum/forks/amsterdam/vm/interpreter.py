"""
Ethereum Virtual Machine (EVM) Interpreter.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

A straightforward interpreter that executes EVM code.
"""

from dataclasses import dataclass
from typing import Optional, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U256, Uint, ulen

from ethereum.exceptions import EthereumException
from ethereum.state import Address
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
from ethereum.utils.numeric import ceil32

from ..blocks import Log
from ..state_tracker import (
    account_has_code_or_nonce,
    account_has_storage,
    copy_tx_state,
    destroy_storage,
    get_account,
    get_code,
    increment_nonce,
    mark_account_created,
    move_ether,
    restore_tx_state,
    set_code,
)
from ..vm import Message
from ..vm.eoa_delegation import get_delegated_code_address, set_delegation
from ..vm.gas import (
    GAS_KECCAK256_PER_WORD,
    charge_gas,
    charge_state_gas,
    state_gas_per_byte,
)
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from . import Evm, emit_transfer_log
from .exceptions import (
    AddressCollision,
    ExceptionalHalt,
    InvalidContractPrefix,
    InvalidOpcode,
    OutOfGasError,
    Revert,
    StackDepthLimitError,
)
from .instructions import Ops, op_implementation
from .runtime import get_valid_jump_destinations

STACK_DEPTH_LIMIT = Uint(1024)
MAX_CODE_SIZE = 0x8000
MAX_INIT_CODE_SIZE = 2 * MAX_CODE_SIZE


@dataclass
class MessageCallOutput:
    """
    Output of a particular message call.

    Contains the following:

          1. `gas_left`: remaining gas after execution.
          2. `refund_counter`: gas to refund after execution.
          3. `logs`: list of `Log` generated during execution.
          4. `accounts_to_delete`: Contracts which have self-destructed.
          5. `error`: The error from the execution if any.
          6. `return_data`: The output of the execution.
          7. `regular_gas_used`: Regular gas used during execution.
          8. `state_gas_used`: State gas used during execution.
    """

    gas_left: Uint
    state_gas_left: Uint
    refund_counter: U256
    logs: Tuple[Log, ...]
    accounts_to_delete: Set[Address]
    error: Optional[EthereumException]
    return_data: Bytes
    regular_gas_used: Uint
    state_gas_used: Uint


def process_message_call(message: Message) -> MessageCallOutput:
    """
    If `message.target` is empty then it creates a smart contract
    else it executes a call from the `message.caller` to the `message.target`.

    Parameters
    ----------
    message :
        Transaction specific items.

    Returns
    -------
    output : `MessageCallOutput`
        Output of the message call

    """
    tx_state = message.tx_env.state
    refund_counter = U256(0)
    if message.target == Bytes0(b""):
        is_collision = account_has_code_or_nonce(
            tx_state, message.current_target
        ) or account_has_storage(tx_state, message.current_target)
        if is_collision:
            return MessageCallOutput(
                gas_left=Uint(0),
                state_gas_left=Uint(0),
                refund_counter=U256(0),
                logs=tuple(),
                accounts_to_delete=set(),
                error=AddressCollision(),
                return_data=Bytes(b""),
                regular_gas_used=Uint(0),
                state_gas_used=Uint(0),
            )
        else:
            evm = process_create_message(message)
    else:
        if message.tx_env.authorizations != ():
            set_delegation(message)

        delegated_address = get_delegated_code_address(message.code)
        if delegated_address is not None:
            message.disable_precompiles = True
            message.accessed_addresses.add(delegated_address)
            message.code = get_code(
                tx_state,
                get_account(tx_state, delegated_address).code_hash,
            )
            message.code_address = delegated_address

        evm = process_message(message)

    if evm.error:
        logs: Tuple[Log, ...] = ()
        accounts_to_delete = set()
    else:
        logs = evm.logs
        accounts_to_delete = evm.accounts_to_delete
        refund_counter += U256(evm.refund_counter)

    tx_end = TransactionEnd(
        int(message.gas) - int(evm.gas_left), evm.output, evm.error
    )
    evm_trace(evm, tx_end)

    return MessageCallOutput(
        gas_left=evm.gas_left,
        state_gas_left=evm.state_gas_left,
        refund_counter=refund_counter,
        logs=logs,
        accounts_to_delete=accounts_to_delete,
        error=evm.error,
        return_data=evm.output,
        regular_gas_used=evm.regular_gas_used,
        state_gas_used=evm.state_gas_used,
    )


def process_create_message(message: Message) -> Evm:
    """
    Executes a call to create a smart contract.

    Parameters
    ----------
    message :
        Transaction specific items.

    Returns
    -------
    evm: :py:class:`~ethereum.forks.amsterdam.vm.Evm`
        Items containing execution specific objects.

    """
    tx_state = message.tx_env.state
    # take snapshot of state before processing the message
    snapshot = copy_tx_state(tx_state)

    # If the address where the account is being created has storage, it is
    # destroyed. This can only happen in the following highly unlikely
    # circumstances:
    # * The address created by a `CREATE` call collides with a subsequent
    #   `CREATE` or `CREATE2` call.
    # * The first `CREATE` happened before Spurious Dragon and left empty
    #   code.
    destroy_storage(tx_state, message.current_target)

    # In the previously mentioned edge case the preexisting storage is ignored
    # for gas refund purposes. In order to do this we must track created
    # accounts. This tracking is also needed to respect the constraints
    # added to SELFDESTRUCT by EIP-6780.
    mark_account_created(tx_state, message.current_target)

    increment_nonce(tx_state, message.current_target)

    evm = process_message(message)
    if not evm.error:
        contract_code = evm.output
        try:
            if len(contract_code) > 0:
                if contract_code[0] == 0xEF:
                    raise InvalidContractPrefix
            cost_per_state_byte = state_gas_per_byte(
                message.block_env.block_gas_limit
            )
            code_deposit_state_gas = (
                Uint(len(contract_code)) * cost_per_state_byte
            )
            charge_state_gas(evm, code_deposit_state_gas)
            # Hash cost for computing keccak256 of deployed bytecode
            code_hash_gas = (
                GAS_KECCAK256_PER_WORD
                * ceil32(Uint(len(contract_code)))
                // Uint(32)
            )
            charge_gas(evm, code_hash_gas)
            if len(contract_code) > MAX_CODE_SIZE:
                raise OutOfGasError
        except ExceptionalHalt as error:
            restore_tx_state(tx_state, snapshot)
            evm.regular_gas_used += evm.gas_left
            evm.gas_left = Uint(0)
            # State gas is preserved on exceptional halt so it can be
            # returned to the parent frame via incorporate_child_on_error.
            evm.output = b""
            evm.error = error
        else:
            set_code(tx_state, message.current_target, contract_code)
    else:
        restore_tx_state(tx_state, snapshot)
    return evm


def process_message(message: Message) -> Evm:
    """
    Move ether and execute the relevant code.

    Parameters
    ----------
    message :
        Transaction specific items.

    Returns
    -------
    evm: :py:class:`~ethereum.forks.amsterdam.vm.Evm`
        Items containing execution specific objects

    """
    tx_state = message.tx_env.state
    if message.depth > STACK_DEPTH_LIMIT:
        raise StackDepthLimitError("Stack depth limit reached")

    code = message.code
    valid_jump_destinations = get_valid_jump_destinations(code)

    evm = Evm(
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        code=code,
        gas_left=message.gas,
        state_gas_left=message.state_gas_reservoir,
        valid_jump_destinations=valid_jump_destinations,
        logs=(),
        refund_counter=0,
        running=True,
        message=message,
        output=b"",
        accounts_to_delete=set(),
        return_data=b"",
        error=None,
        accessed_addresses=message.accessed_addresses,
        accessed_storage_keys=message.accessed_storage_keys,
    )

    # take snapshot of state before processing the message
    snapshot = copy_tx_state(tx_state)

    if message.should_transfer_value and message.value != 0:
        move_ether(
            tx_state,
            message.caller,
            message.current_target,
            message.value,
        )
        # EIP-7708: Only emit transfer log to a different account
        if message.caller != message.current_target:
            emit_transfer_log(
                evm, message.caller, message.current_target, message.value
            )

    # Execute message code and handle errors
    try:
        if evm.message.code_address in PRE_COMPILED_CONTRACTS:
            if not message.disable_precompiles:
                evm_trace(evm, PrecompileStart(evm.message.code_address))
                PRE_COMPILED_CONTRACTS[evm.message.code_address](evm)
                evm_trace(evm, PrecompileEnd())
        else:
            while evm.running and evm.pc < ulen(evm.code):
                try:
                    op = Ops(evm.code[evm.pc])
                except ValueError as e:
                    raise InvalidOpcode(evm.code[evm.pc]) from e

                evm_trace(evm, OpStart(op))
                op_implementation[op](evm)
                evm_trace(evm, OpEnd())

            evm_trace(evm, EvmStop(Ops.STOP))

    except ExceptionalHalt as error:
        evm_trace(evm, OpException(error))
        evm.regular_gas_used += evm.gas_left
        evm.gas_left = Uint(0)
        # State gas is preserved on exceptional halt so it can be
        # returned to the parent frame via incorporate_child_on_error.
        evm.output = b""
        evm.error = error
    except Revert as error:
        evm_trace(evm, OpException(error))
        evm.error = error

    if evm.error:
        restore_tx_state(tx_state, snapshot)
    return evm
