"""
Ethereum Virtual Machine (EVM) Environmental Instructions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM environment related instructions.
"""

from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256, Uint, ulen

from ethereum.state import EMPTY_ACCOUNT
from ethereum.utils.numeric import ceil32

from ...state_tracker import get_account, get_code
from ...transactions import (
    APPROVE_SCOPE_MASK,
    ATOMIC_BATCH_FLAG,
    SIGNATURE_SCHEME_ARBITRARY,
    resolve_frame_target,
    tx_signature_scheme_is_protocol_validated,
)
from ...utils.address import to_address_masked
from ...vm.memory import buffer_read, memory_write
from .. import Evm, FrameTransactionContext
from ..exceptions import InvalidParameter, OutOfBoundsRead
from ..gas import (
    GasCosts,
    calculate_blob_gas_price,
    calculate_gas_extend_memory,
    charge_gas,
)
from ..stack import pop, push


def address(evm: Evm) -> None:
    """
    Pushes the address of the current executing account to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_ADDRESS)

    # OPERATION
    push(evm.stack, U256.from_be_bytes(evm.message.current_target))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def balance(evm: Evm) -> None:
    """
    Pushes the balance of the given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    address = to_address_masked(pop(evm.stack))

    # GAS
    if address in evm.accessed_addresses:
        charge_gas(evm, GasCosts.WARM_ACCESS)
    else:
        evm.accessed_addresses.add(address)
        charge_gas(evm, GasCosts.COLD_ACCOUNT_ACCESS)

    # OPERATION
    # Non-existent accounts default to EMPTY_ACCOUNT, which has balance 0.
    tx_state = evm.message.tx_env.state
    balance = get_account(tx_state, address).balance

    push(evm.stack, balance)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def origin(evm: Evm) -> None:
    """
    Pushes the address of the original transaction sender to the stack.
    The origin address can only be an EOA.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_ORIGIN)

    # OPERATION
    push(evm.stack, U256.from_be_bytes(evm.message.tx_env.origin))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def caller(evm: Evm) -> None:
    """
    Pushes the address of the caller onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CALLER)

    # OPERATION
    push(evm.stack, U256.from_be_bytes(evm.message.caller))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def callvalue(evm: Evm) -> None:
    """
    Push the value (in wei) sent with the call onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CALLVALUE)

    # OPERATION
    push(evm.stack, evm.message.value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def calldataload(evm: Evm) -> None:
    """
    Push a word (32 bytes) of the input data belonging to the current
    environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_index = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CALLDATALOAD)

    # OPERATION
    value = buffer_read(evm.message.data, start_index, U256(32))

    push(evm.stack, U256.from_be_bytes(value))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def calldatasize(evm: Evm) -> None:
    """
    Push the size of input data in current environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CALLDATASIZE)

    # OPERATION
    push(evm.stack, U256(len(evm.message.data)))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def calldatacopy(evm: Evm) -> None:
    """
    Copy a portion of the input data in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    memory_start_index = pop(evm.stack)
    data_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // Uint(32)
    copy_gas_cost = GasCosts.OPCODE_COPY_PER_WORD * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(
        evm,
        GasCosts.OPCODE_CALLDATACOPY_BASE + copy_gas_cost + extend_memory.cost,
    )

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    value = buffer_read(evm.message.data, data_start_index, size)
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def codesize(evm: Evm) -> None:
    """
    Push the size of code running in current environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CODESIZE)

    # OPERATION
    push(evm.stack, U256(len(evm.code)))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def codecopy(evm: Evm) -> None:
    """
    Copy a portion of the code in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    memory_start_index = pop(evm.stack)
    code_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // Uint(32)
    copy_gas_cost = GasCosts.OPCODE_COPY_PER_WORD * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(
        evm,
        GasCosts.OPCODE_CODECOPY_BASE + copy_gas_cost + extend_memory.cost,
    )

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    value = buffer_read(evm.code, code_start_index, size)
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def gasprice(evm: Evm) -> None:
    """
    Push the gas price used in current environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_GASPRICE)

    # OPERATION
    push(evm.stack, U256(evm.message.tx_env.gas_price))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def extcodesize(evm: Evm) -> None:
    """
    Push the code size of a given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    address = to_address_masked(pop(evm.stack))

    # GAS
    if address in evm.accessed_addresses:
        access_gas_cost = GasCosts.WARM_ACCESS
    else:
        evm.accessed_addresses.add(address)
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    access_gas_cost += GasCosts.WARM_ACCESS  # Code reading cost (EIP-8038)
    charge_gas(evm, access_gas_cost)

    # OPERATION
    tx_state = evm.message.tx_env.state
    code_hash = get_account(tx_state, address).code_hash
    code = get_code(tx_state, code_hash)

    codesize = U256(len(code))
    push(evm.stack, codesize)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def extcodecopy(evm: Evm) -> None:
    """
    Copy a portion of an account's code to memory.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    address = to_address_masked(pop(evm.stack))
    memory_start_index = pop(evm.stack)
    code_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // Uint(32)
    copy_gas_cost = GasCosts.OPCODE_COPY_PER_WORD * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )

    if address in evm.accessed_addresses:
        access_gas_cost = GasCosts.WARM_ACCESS
    else:
        evm.accessed_addresses.add(address)
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    access_gas_cost += GasCosts.WARM_ACCESS  # Code reading cost (EIP-8038)

    total_gas_cost = access_gas_cost + copy_gas_cost + extend_memory.cost

    charge_gas(evm, total_gas_cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    tx_state = evm.message.tx_env.state
    code_hash = get_account(tx_state, address).code_hash
    code = get_code(tx_state, code_hash)

    value = buffer_read(code, code_start_index, size)
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def returndatasize(evm: Evm) -> None:
    """
    Pushes the size of the return data buffer onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_RETURNDATASIZE)

    # OPERATION
    push(evm.stack, U256(len(evm.return_data)))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def returndatacopy(evm: Evm) -> None:
    """
    Copies data from the return data buffer to memory.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    memory_start_index = pop(evm.stack)
    return_data_start_position = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // Uint(32)
    copy_gas_cost = GasCosts.OPCODE_RETURNDATACOPY_PER_WORD * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(
        evm,
        GasCosts.OPCODE_RETURNDATACOPY_BASE
        + copy_gas_cost
        + extend_memory.cost,
    )
    if Uint(return_data_start_position) + Uint(size) > ulen(evm.return_data):
        raise OutOfBoundsRead

    evm.memory += b"\x00" * extend_memory.expand_by
    value = evm.return_data[
        return_data_start_position : return_data_start_position + size
    ]
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def extcodehash(evm: Evm) -> None:
    """
    Returns the keccak256 hash of a contract’s bytecode.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    address = to_address_masked(pop(evm.stack))

    # GAS
    if address in evm.accessed_addresses:
        access_gas_cost = GasCosts.WARM_ACCESS
    else:
        evm.accessed_addresses.add(address)
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS

    charge_gas(evm, access_gas_cost)

    # OPERATION
    tx_state = evm.message.tx_env.state
    account = get_account(tx_state, address)

    if account == EMPTY_ACCOUNT:
        codehash = U256(0)
    else:
        codehash = U256.from_be_bytes(account.code_hash)

    push(evm.stack, codehash)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def self_balance(evm: Evm) -> None:
    """
    Pushes the balance of the current address to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.FAST_STEP)

    # OPERATION
    # Non-existent accounts default to EMPTY_ACCOUNT, which has balance 0.
    balance = get_account(
        evm.message.tx_env.state, evm.message.current_target
    ).balance

    push(evm.stack, balance)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def base_fee(evm: Evm) -> None:
    """
    Pushes the base fee of the current block on to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_BASEFEE)

    # OPERATION
    push(evm.stack, U256(evm.message.block_env.base_fee_per_gas))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def blob_hash(evm: Evm) -> None:
    """
    Pushes the versioned hash at a particular index on to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    index = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_BLOBHASH)

    # OPERATION
    if int(index) < len(evm.message.tx_env.blob_versioned_hashes):
        blob_hash = evm.message.tx_env.blob_versioned_hashes[index]
    else:
        blob_hash = Bytes32(b"\x00" * 32)
    push(evm.stack, U256.from_be_bytes(blob_hash))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def blob_base_fee(evm: Evm) -> None:
    """
    Pushes the blob base fee on to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_BLOBBASEFEE)

    # OPERATION
    blob_base_fee = calculate_blob_gas_price(
        evm.message.block_env.excess_blob_gas
    )
    push(evm.stack, U256(blob_base_fee))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def active_frame_transaction_context(evm: Evm) -> FrameTransactionContext:
    """
    Return the context of the executing frame transaction.

    An exceptional halt occurs when the current transaction is not a
    frame transaction.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    frame_context = evm.message.tx_env.frame_context
    if frame_context is None:
        raise InvalidParameter("no frame transaction context")
    return frame_context


def txparam(evm: Evm) -> None:
    """
    Push a transaction-scoped parameter of the executing frame
    transaction onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    param = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_TXPARAM)

    # OPERATION
    frame_context = active_frame_transaction_context(evm)
    tx = frame_context.tx
    if param == U256(0x00):
        value = U256(0x06)
    elif param == U256(0x01):
        value = U256(tx.nonce)
    elif param == U256(0x02):
        value = U256.from_be_bytes(tx.sender)
    elif param == U256(0x03):
        value = U256(tx.max_priority_fee_per_gas)
    elif param == U256(0x04):
        value = U256(tx.max_fee_per_gas)
    elif param == U256(0x05):
        value = tx.max_fee_per_blob_gas
    elif param == U256(0x06):
        value = U256(frame_context.max_cost)
    elif param == U256(0x07):
        value = U256(len(tx.blob_versioned_hashes))
    elif param == U256(0x08):
        value = U256.from_be_bytes(frame_context.sig_hash)
    elif param == U256(0x09):
        value = U256(len(tx.frames))
    elif param == U256(0x0A):
        value = U256(frame_context.current_frame_index)
    elif param == U256(0x0B):
        value = U256(len(tx.signatures))
    else:
        raise InvalidParameter("undefined TXPARAM parameter")
    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def framedataload(evm: Evm) -> None:
    """
    Push a word (32 bytes) of the data of the chosen frame onto the
    stack, with `CALLDATALOAD` semantics.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_index = pop(evm.stack)
    frame_index = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_FRAMEDATALOAD)

    # OPERATION
    frame_context = active_frame_transaction_context(evm)
    if Uint(frame_index) >= ulen(frame_context.tx.frames):
        raise OutOfBoundsRead("frame index out of bounds")
    frame = frame_context.tx.frames[int(frame_index)]
    value = buffer_read(frame.data, start_index, U256(32))
    push(evm.stack, U256.from_be_bytes(value))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def framedatacopy(evm: Evm) -> None:
    """
    Copy a portion of the data of the chosen frame to memory, with
    `CALLDATACOPY` semantics.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    memory_start_index = pop(evm.stack)
    data_start_index = pop(evm.stack)
    size = pop(evm.stack)
    frame_index = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // Uint(32)
    copy_gas_cost = GasCosts.OPCODE_COPY_PER_WORD * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(
        evm,
        GasCosts.OPCODE_FRAMEDATACOPY_BASE
        + copy_gas_cost
        + extend_memory.cost,
    )

    # OPERATION
    frame_context = active_frame_transaction_context(evm)
    if Uint(frame_index) >= ulen(frame_context.tx.frames):
        raise OutOfBoundsRead("frame index out of bounds")
    frame = frame_context.tx.frames[int(frame_index)]
    evm.memory += b"\x00" * extend_memory.expand_by
    value = buffer_read(frame.data, data_start_index, size)
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def frameparam(evm: Evm) -> None:
    """
    Push a frame-scoped parameter of the chosen frame onto the stack.

    Accessing the return status of the current frame or a future frame
    results in an exceptional halt.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    frame_index = pop(evm.stack)
    param = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_FRAMEPARAM)

    # OPERATION
    frame_context = active_frame_transaction_context(evm)
    if Uint(frame_index) >= ulen(frame_context.tx.frames):
        raise OutOfBoundsRead("frame index out of bounds")
    frame = frame_context.tx.frames[int(frame_index)]
    if param == U256(0x00):
        value = U256.from_be_bytes(
            resolve_frame_target(frame_context.tx, frame)
        )
    elif param == U256(0x01):
        value = U256(frame.gas_limit)
    elif param == U256(0x02):
        value = U256(frame.mode)
    elif param == U256(0x03):
        value = U256(frame.flags)
    elif param == U256(0x04):
        value = U256(len(frame.data))
    elif param == U256(0x05):
        if Uint(frame_index) >= frame_context.current_frame_index:
            raise OutOfBoundsRead("status of current or future frame")
        value = U256(frame_context.frame_statuses[int(frame_index)])
    elif param == U256(0x06):
        value = U256(frame.flags & APPROVE_SCOPE_MASK)
    elif param == U256(0x07):
        value = U256((frame.flags & ATOMIC_BATCH_FLAG) >> Uint(2))
    elif param == U256(0x08):
        value = frame.value
    else:
        raise InvalidParameter("undefined FRAMEPARAM parameter")
    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sigparam(evm: Evm) -> None:
    """
    Push signature-scoped metadata of the chosen signature entry onto
    the stack, or copy the raw bytes of an `ARBITRARY` signature entry
    to memory.

    The raw signature bytes of protocol-validated schemes are not
    accessible from the EVM.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    signature_index = pop(evm.stack)
    param = pop(evm.stack)

    if param == U256(0x04):
        size = pop(evm.stack)
        data_start_index = pop(evm.stack)
        memory_start_index = pop(evm.stack)

        # GAS
        words = ceil32(Uint(size)) // Uint(32)
        copy_gas_cost = GasCosts.OPCODE_COPY_PER_WORD * words
        extend_memory = calculate_gas_extend_memory(
            evm.memory, [(memory_start_index, size)]
        )
        charge_gas(
            evm,
            GasCosts.OPCODE_SIGPARAM_COPY_BASE
            + copy_gas_cost
            + extend_memory.cost,
        )

        # OPERATION
        frame_context = active_frame_transaction_context(evm)
        if Uint(signature_index) >= ulen(frame_context.tx.signatures):
            raise OutOfBoundsRead("signature index out of bounds")
        sig = frame_context.tx.signatures[int(signature_index)]
        if sig.scheme != SIGNATURE_SCHEME_ARBITRARY:
            raise InvalidParameter(
                "signature bytes of protocol-validated schemes are not "
                "accessible"
            )
        evm.memory += b"\x00" * extend_memory.expand_by
        value = buffer_read(sig.signature, data_start_index, size)
        memory_write(evm.memory, memory_start_index, value)

        # PROGRAM COUNTER
        evm.pc += Uint(1)
        return

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SIGPARAM)

    # OPERATION
    frame_context = active_frame_transaction_context(evm)
    if Uint(signature_index) >= ulen(frame_context.tx.signatures):
        raise OutOfBoundsRead("signature index out of bounds")
    sig = frame_context.tx.signatures[int(signature_index)]
    if param == U256(0x00):
        if not tx_signature_scheme_is_protocol_validated(sig):
            raise InvalidParameter(
                "arbitrary signature entries have no effective signer"
            )
        result = U256.from_be_bytes(sig.signer)
    elif param == U256(0x01):
        result = U256(sig.scheme)
    elif param == U256(0x02):
        if len(sig.msg) == 0:
            result = U256(0)
        else:
            result = U256.from_be_bytes(sig.msg)
    elif param == U256(0x03):
        result = U256(len(sig.signature))
    else:
        raise InvalidParameter("undefined SIGPARAM parameter")
    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)
