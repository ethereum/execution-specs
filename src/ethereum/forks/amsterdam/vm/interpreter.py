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
    TransactionState,
    account_has_code_or_nonce,
    account_has_storage,
    compute_state_byte_diff,
    copy_tx_state,
    destroy_account,
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
    GasCosts,
    StateCosts,
    charge_gas,
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
          2. `state_gas_reservoir`: remaining state gas reservoir after
                    execution.
          3. `refund_counter`: gas to refund after execution.
          4. `logs`: list of `Log` generated during execution.
          5. `accounts_to_delete`: Contracts which have self-destructed.
          6. `error`: The error from the execution if any.
          7. `return_data`: The output of the execution.
          8. `regular_gas_used`: Regular gas used during execution.
          9. `state_gas_used`: State gas used during execution.
    """

    gas_left: Uint
    state_gas_reservoir: Uint
    refund_counter: U256
    logs: Tuple[Log, ...]
    accounts_to_delete: Set[Address]
    error: Optional[EthereumException]
    return_data: Bytes
    regular_gas_used: Uint
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
    refund_counter = U256(0)
    if message.target == Bytes0(b""):
        is_collision = account_has_code_or_nonce(
            tx_state, message.current_target
        ) or account_has_storage(tx_state, message.current_target)
        if is_collision:
            return MessageCallOutput(
                gas_left=Uint(0),
                state_gas_reservoir=Uint(0),
                refund_counter=U256(0),
                logs=tuple(),
                accounts_to_delete=set(),
                error=AddressCollision(),
                return_data=Bytes(b""),
                regular_gas_used=Uint(0),
                state_gas_used=0,
            )
        else:
            evm = process_message(message, True)
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

        evm = process_message(message, False)

    if evm.error:
        logs: Tuple[Log, ...] = ()
        accounts_to_delete = set()
    else:
        logs = evm.logs
        accounts_to_delete = evm.accounts_to_delete
        refund_counter += U256(evm.refund_counter)

        # Deferred SELFDESTRUCT processing per EIP-8037 + EIP-6780.
        # SELFDESTRUCT queues the originator into `accounts_to_delete` at
        # opcode time; the actual `destroy_account` runs at the top-level
        # frame to deduplicate (an account SELFDESTRUCTed multiple times
        # is destroyed once) and to integrate with revert (child
        # SELFDESTRUCTs in a reverted ancestor are dropped via
        # `incorporate_child_on_error`).
        #
        # Per EIP-6780 only same-tx-created accounts are actually
        # removed. The frame-end diff above charged for the create
        # (account record, deployed code, new storage slots); refund
        # those here directly to the reservoir (no 20% cap), then
        # destroy the account for state-trie purposes.
        for address in evm.accounts_to_delete:
            if address in tx_state.created_accounts:
                account = get_account(tx_state, address)
                code = get_code(tx_state, account.code_hash)
                refund_bytes = int(StateCosts.NEW_ACCOUNT) + len(code)
                for slot_value in tx_state.storage_writes.get(
                    address, {}
                ).values():
                    if slot_value != U256(0):
                        refund_bytes += int(StateCosts.STORAGE_SET)
                refill_amount = refund_bytes * int(StateCosts.PER_BYTE)
                # Per EIP-8037: refill `state_gas_reservoir` with
                # the previously-charged state gas (account creation,
                # code deposit, new storage slots), and decrease
                # `execution_state_gas_used` by the same amount. The
                # decrement may go negative because the account-
                # creation portion was charged via
                # `intrinsic_state_gas` (not via this counter); the
                # negative offsets the intrinsic at block-level
                # `tx_state_gas` accounting.
                evm.state_gas_reservoir += Uint(refill_amount)
                evm.state_gas_used -= refill_amount
                destroy_account(tx_state, address)

    tx_end = TransactionEnd(
        int(message.gas) - int(evm.gas_left), evm.output, evm.error
    )
    evm_trace(evm, tx_end)

    return MessageCallOutput(
        gas_left=evm.gas_left,
        state_gas_reservoir=evm.state_gas_reservoir,
        refund_counter=refund_counter,
        logs=logs,
        accounts_to_delete=accounts_to_delete,
        error=evm.error,
        return_data=evm.output,
        regular_gas_used=evm.regular_gas_used,
        state_gas_used=evm.state_gas_used,
    )


def apply_frame_state_gas(
    evm: Evm, snapshot: TransactionState, message: Message
) -> None:
    """
    Settle state-gas at a frame boundary.

    Compute the signed byte delta between ``snapshot`` and the
    current transaction state, multiply by ``CPSB`` to derive the
    growth cost, and reconcile against this frame's reservoir.

    `already_paid` is what successful descendants have already
    drained from this frame's reservoir; subtracting it gives the
    residual this frame still owes (or is owed back). When a
    descendant over-credited the reservoir on a cross-frame
    ephemeral, `already_paid` is negative, which flips this frame's
    residual to positive and naturally cancels out the over-credit.

    On out-of-gas, roll back to ``snapshot`` and mark ``evm.error``.
    """
    if evm.error:
        return
    tx_state = message.tx_env.state
    byte_delta = compute_state_byte_diff(snapshot, tx_state)
    growth_cost = byte_delta * int(StateCosts.PER_BYTE)
    already_paid = int(message.state_gas_reservoir) - int(
        evm.state_gas_reservoir
    )
    this_call_cost = growth_cost - already_paid

    if this_call_cost > 0:
        # Drain reservoir first; spill into `gas_left` if the
        # reservoir is empty. Spillover is the backward-compat
        # path: legacy txs that didn't separately budget for
        # state gas can still succeed by burning regular gas.
        cost = Uint(this_call_cost)
        if evm.state_gas_reservoir >= cost:
            evm.state_gas_reservoir -= cost
        elif evm.state_gas_reservoir + evm.gas_left >= cost:
            remainder = cost - evm.state_gas_reservoir
            evm.state_gas_reservoir = Uint(0)
            evm.gas_left -= remainder
        else:
            # Combined budget can't cover the growth → OOG. Roll
            # back state changes; same semantics as a regular-gas
            # OOG mid-frame.
            restore_tx_state(tx_state, snapshot)
            evm.error = OutOfGasError()
            evm.output = b""
        if not evm.error:
            evm.state_gas_used += int(cost)
    elif this_call_cost < 0:
        # Negative residual means this subtree net-shrunk state.
        # Credit the reservoir directly; the credit is bounded by
        # `already_paid` going negative when ancestors compose
        # this frame's reservoir (their `this_call_cost` flips
        # positive and recharges).
        evm.state_gas_reservoir += Uint(-this_call_cost)


def process_message(message: Message, create: bool = False) -> Evm:
    """
    Move ether and execute the relevant code.

    Parameters
    ----------
    message :
        Transaction specific items.
    create  :
        Whether the message is contract-creating.
    include_account_creation_in_diff  :
        Whether to include account creation in the diff to calculate state gas.

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
        state_gas_reservoir=message.state_gas_reservoir,
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
    revert_snapshot = copy_tx_state(tx_state)

    if create:
        # If the address where the account is being created has storage, it is
        # destroyed. This can only happen in the following highly unlikely
        # circumstances:
        # * The address created by a `CREATE` call collides with a subsequent
        #   `CREATE` or `CREATE2` call.
        # * The first `CREATE` happened before Spurious Dragon and left empty
        #   code.
        destroy_storage(tx_state, message.current_target)

        # In the previously mentioned edge case the preexisting storage is
        # ignored for gas refund purposes. In order to do this we must track
        # created accounts. This tracking is also needed to respect the
        # constraints added to SELFDESTRUCT by EIP-6780.
        mark_account_created(tx_state, message.current_target)

        increment_nonce(tx_state, message.current_target)

    if message.should_transfer_value and message.value != 0:
        # CALL-with-value to a non-existent address creates the
        # target account when `move_ether` deposits the balance. The
        # account creation surfaces in `tx_state.account_writes` and
        # is picked up by `compute_state_byte_diff` at this frame's
        # frame-end (or rolled back by `restore_tx_state` on error).
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

    diff_snapshot = copy_tx_state(tx_state)

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

        if create:
            contract_code = evm.output
            if len(contract_code) > 0:
                if contract_code[0] == 0xEF:
                    raise InvalidContractPrefix
            if len(contract_code) > MAX_CODE_SIZE:
                raise OutOfGasError
            # The legacy per-byte code-deposit cost (200 gas/byte) is
            # gone; deposited bytes now pay through the state-byte
            # counter (`+len(contract_code)` below) at frame-end via
            # `× PER_BYTE`. The only regular-gas cost retained for
            # code deposit is the keccak256 hashing of the deployed
            # bytecode, since that's a real per-word CPU cost the
            # client incurs to derive `code_hash`.
            code_hash_gas = (
                GasCosts.OPCODE_KECCACK256_PER_WORD
                * ceil32(ulen(contract_code))
                // Uint(32)
            )
            charge_gas(evm, code_hash_gas)
            set_code(tx_state, message.current_target, contract_code)

        # Frame-end state-gas settlement.
        apply_frame_state_gas(evm, diff_snapshot, message)

    except ExceptionalHalt as error:
        evm_trace(evm, OpException(error))
        # On exceptional halt the frame consumes all remaining
        # `gas_left`. Spill that into `regular_gas_used` so the
        # parent's `incorporate_child_on_error` sees the full
        # regular-gas burn (otherwise the forfeited remainder would
        # be lost from the per-tx total). State gas isn't touched
        # here — `incorporate_child_on_error` returns the child's
        # state-gas budget (used + unused) to the parent reservoir,
        # since the rolled-back state never grew.
        evm.regular_gas_used += evm.gas_left
        evm.gas_left = Uint(0)
        # State gas is preserved on exceptional halt so it can be
        # returned to the parent frame via incorporate_child_on_error.
        evm.output = b""
        evm.error = error
    except Revert as error:
        # REVERT preserves remaining `gas_left` (refunded to the
        # parent via `incorporate_child_on_error`); only the error
        # is recorded here.
        evm_trace(evm, OpException(error))
        evm.error = error

    if evm.error:
        restore_tx_state(tx_state, revert_snapshot)
    return evm
