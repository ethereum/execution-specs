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
from typing import Optional, Set, Tuple, final

from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U256, Uint, ulen

from ethereum.exceptions import EthereumException
from ethereum.state import EMPTY_ACCOUNT, Address
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
    account_deployable,
    copy_tx_state,
    destroy_storage,
    get_account,
    get_code,
    get_pre_state_account,
    increment_nonce,
    is_account_alive,
    mark_account_created,
    move_ether,
    restore_tx_state,
    set_code,
)
from ..vm import Message
from ..vm.eoa_delegation import get_delegated_code_address, set_delegation
from ..vm.gas import (
    GasCosts,
    GasMeter,
    StateGasCosts,
    charge_gas,
    charge_state_gas,
    commit_state_gas,
    forfeit_remaining_gas,
    restore_state_gas,
    restore_state_gas_to_entry,
    tx_state_gas_used,
)
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from . import (
    Evm,
    emit_transfer_log,
)
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
MAX_CODE_SIZE = 0x10000
MAX_INIT_CODE_SIZE = 2 * MAX_CODE_SIZE


@final
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
          7. `state_gas_left`: remaining state gas after execution.
          8. `state_gas_used`: State gas used during execution.
    """

    gas_left: Uint
    refund_counter: U256
    logs: Tuple[Log, ...]
    accounts_to_delete: Set[Address]
    error: Optional[EthereumException]
    return_data: Bytes
    state_gas_left: Uint
    state_gas_used: int


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
    if message.target == Bytes0(b""):
        if account_deployable(tx_state, message.current_target):
            evm = process_create_message(message)
        else:
            return MessageCallOutput(
                gas_left=Uint(0),
                refund_counter=U256(0),
                logs=tuple(),
                accounts_to_delete=set(),
                error=AddressCollision(),
                return_data=Bytes(b""),
                state_gas_left=message.state_gas_reservoir,
                state_gas_used=0,
            )
    else:
        # Authorizations and delegation resolution are handled at the
        # top frame inside ``process_message`` (depth 0), so their
        # state-dependent gas charges go through the EVM gas pools and
        # an out-of-gas there halts the frame cleanly.
        evm = process_message(message)

    if evm.error:
        logs: Tuple[Log, ...] = ()
        accounts_to_delete = set()
    else:
        logs = evm.logs
        accounts_to_delete = evm.accounts_to_delete

    tx_end = TransactionEnd(
        int(message.gas) - int(evm.gas_meter.gas_left), evm.output, evm.error
    )
    evm_trace(evm, tx_end)

    # A failed frame settles its meter with a zero refund counter, so
    # the refunds can be read unconditionally.
    return MessageCallOutput(
        gas_left=evm.gas_meter.gas_left,
        refund_counter=U256(evm.gas_meter.refund_counter),
        logs=logs,
        accounts_to_delete=accounts_to_delete,
        error=evm.error,
        return_data=evm.output,
        state_gas_left=evm.gas_meter.state_gas_left,
        state_gas_used=tx_state_gas_used(
            evm.gas_meter, message.state_gas_reservoir
        ),
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
            if len(contract_code) > MAX_CODE_SIZE:
                raise OutOfGasError
            # Hash cost for computing keccak256 of deployed bytecode
            code_hash_gas = (
                GasCosts.OPCODE_KECCAK256_PER_WORD
                * ceil32(ulen(contract_code))
                // Uint(32)
            )
            charge_gas(evm, code_hash_gas)
            code_deposit_state_gas = (
                ulen(contract_code) * StateGasCosts.COST_PER_STATE_BYTE
            )
            charge_state_gas(evm, code_deposit_state_gas)
        except ExceptionalHalt as error:
            restore_tx_state(tx_state, snapshot)
            # A create frame never applies authorizations, so its
            # baseline is still the frame's entry reservoir.
            restore_state_gas(evm.gas_meter)
            forfeit_remaining_gas(evm.gas_meter)
            evm.output = b""
            evm.error = error
        else:
            set_code(tx_state, message.current_target, contract_code)
    else:
        restore_tx_state(tx_state, snapshot)
    return evm


def prepare_dispatch(evm: Evm) -> None:
    """
    Charge the state-dependent dispatch costs and resolve the code the
    top frame will run.

    Runs at the top frame (depth 0), after any EIP-7702 authorizations
    have been applied by ``set_delegation`` and before the call is
    dispatched:

    - charges the ``NEW_ACCOUNT`` state gas for a contract creation
      whose target leaf does not yet exist, or for a value transfer to
      a recipient that is not yet alive; and
    - resolves a delegation on the recipient, charging the warm or
      cold account access and pointing the frame at the delegated
      code.

    The creation target is checked against the transaction pre-state:
    ``process_create_message`` has already bumped the target's nonce
    by the time this runs, so a live check would always see the
    account. The recipient check is live, so an authority
    materialized earlier in the transaction is not charged
    ``NEW_ACCOUNT`` again.

    This function must not mutate the transaction state. Every charge
    here pays for state that only materializes inside the dispatched
    frame and rolls back with it, so these charges stay refillable --
    unlike the ``set_delegation`` charges, whose state outlives a
    dispatch failure and whose gas the caller folds into the frame
    baseline. The no-mutation rule is also what keeps the caller's
    execution snapshot equal to the state at that fold.

    Insufficient gas raises an ``ExceptionalHalt``; the caller rolls
    back the whole preparation -- including the applied authorizations
    -- and halts the frame without dispatching.
    """
    message = evm.message
    tx_state = message.tx_env.state

    if message.target == Bytes0(b""):
        if (
            get_pre_state_account(tx_state, message.current_target)
            == EMPTY_ACCOUNT
        ):
            charge_state_gas(evm, StateGasCosts.NEW_ACCOUNT)
    else:
        recipient = message.current_target
        if message.value > U256(0) and not is_account_alive(
            tx_state, recipient
        ):
            charge_state_gas(evm, StateGasCosts.NEW_ACCOUNT)
        recipient_code = get_code(
            tx_state, get_account(tx_state, recipient).code_hash
        )
        delegated_address = get_delegated_code_address(recipient_code)
        if delegated_address is not None:
            if delegated_address in evm.accessed_addresses:
                charge_gas(evm, GasCosts.WARM_ACCESS)
            else:
                charge_gas(evm, GasCosts.COLD_ACCOUNT_ACCESS)
                evm.accessed_addresses.add(delegated_address)

            message.disable_precompiles = True
            message.code_address = delegated_address
            message.code = get_code(
                tx_state,
                get_account(tx_state, delegated_address).code_hash,
            )
        else:
            message.code = recipient_code


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

    evm = Evm(
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        code=Bytes(b""),
        gas_meter=GasMeter(
            gas_left=message.gas,
            state_gas_left=message.state_gas_reservoir,
            state_gas_baseline=message.state_gas_reservoir,
        ),
        valid_jump_destinations=set(),
        logs=(),
        running=True,
        message=message,
        output=b"",
        accounts_to_delete=set(),
        return_data=b"",
        error=None,
        accessed_addresses=message.accessed_addresses,
        accessed_storage_keys=message.accessed_storage_keys,
    )

    if message.depth == Uint(0):
        prep_snapshot = copy_tx_state(tx_state)
        try:
            if message.tx_env.authorizations != ():
                set_delegation(evm)
                # The applied delegations outlive a failure of the
                # dispatched code, so their state gas is committed as
                # non-refillable; a later failure restores only to the
                # post-commit baseline.
                commit_state_gas(evm.gas_meter)
            prepare_dispatch(evm)
        except ExceptionalHalt as error:
            evm_trace(evm, OpException(error))
            restore_tx_state(tx_state, prep_snapshot)
            # The rollback reverts any applied delegations, so the
            # commit above is undone with it: roll state gas back to
            # frame entry, refilling every state charge.
            restore_state_gas_to_entry(
                evm.gas_meter, message.state_gas_reservoir
            )
            forfeit_remaining_gas(evm.gas_meter)
            evm.error = error
            return evm

    assert message.code is not None
    evm.code = message.code
    evm.valid_jump_destinations = get_valid_jump_destinations(message.code)

    snapshot = copy_tx_state(tx_state)

    # Execute message code and handle errors
    try:
        if message.should_transfer_value and message.value != 0:
            move_ether(
                tx_state,
                message.caller,
                message.current_target,
                message.value,
            )
            if message.caller != message.current_target:
                emit_transfer_log(
                    evm,
                    message.caller,
                    message.current_target,
                    message.value,
                )
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
        # Frame settlement: refill state gas to the baseline, then
        # forfeit -- a halted frame returns no regular gas to its
        # parent. After these handlers the meter states exactly what
        # the frame gives back, so parents absorb unconditionally.
        restore_state_gas(evm.gas_meter)
        forfeit_remaining_gas(evm.gas_meter)
        evm.output = b""
        evm.error = error
    except Revert as error:
        evm_trace(evm, OpException(error))
        # Frame settlement: refill state gas to the baseline -- a
        # reverted frame returns its unspent `gas_left` to its parent.
        restore_state_gas(evm.gas_meter)
        evm.error = error

    if evm.error:
        restore_tx_state(tx_state, snapshot)
    return evm
