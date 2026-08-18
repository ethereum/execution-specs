"""
Implementations of the EVM instructions defined only during the
execution of an [EIP-8141] frame transaction. Executing any of them in
the context of any other transaction type results in an exceptional
halt.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ethereum.utils.numeric import ceil32

from ...fork_types import ExecutionGas
from ...transactions.frame_transaction import (
    APPROVE_SCOPE_MASK,
    FrameFlag,
    FrameSignatureScheme,
    resolve_frame_target,
)
from ...vm.memory import buffer_read, memory_read_bytes, memory_write
from .. import Evm, FrameContext, attempt_approval
from ..exceptions import InvalidParameter, Revert
from ..gas import GasCosts, calculate_gas_extend_memory, charge_gas
from ..stack import pop, push


def frame_transaction_context(evm: Evm) -> FrameContext:
    """
    Return the executing frame transaction's context, or exceptionally
    halt when the current transaction is not a frame transaction.
    """
    frame_context = evm.tx_env.frame_context
    if frame_context is None:
        raise InvalidParameter("not a frame transaction")
    return frame_context


def approve(evm: Evm) -> None:
    """
    Exit the current call frame successfully, updating the
    transaction-scoped approval context based on the scope operand.

    The memory region designated by the offset and length operands
    becomes the frame's return data, following `RETURN` semantics —
    only the memory expansion is charged. A refused approval — an
    `ADDRESS` other than the frame's resolved target, a scope outside
    the frame's allowed flags, or a failed precondition — reverts the
    frame instead. The approval's writes deliberately bypass the
    `VERIFY` static restriction: only `APPROVE` may mutate state
    there.
    """
    # STACK
    offset = pop(evm.stack)
    length = pop(evm.stack)
    scope = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(evm.memory, [(offset, length)])
    charge_gas(evm, GasCosts.ZERO + extend_memory.cost)

    # OPERATION
    frame_context = frame_transaction_context(evm)
    tx = frame_context.tx
    frame = tx.frames[int(frame_context.current_frame_index)]
    resolved_target = resolve_frame_target(tx, frame)

    evm.memory += b"\x00" * extend_memory.expand_by

    # Only the frame's resolved target may approve.
    if evm.current_target != resolved_target:
        raise Revert
    # A scope with bits beyond the approval mask is never allowed.
    if scope & ~U256(APPROVE_SCOPE_MASK) != U256(0):
        raise Revert
    if not attempt_approval(evm.tx_env, FrameFlag(Uint(scope))):
        raise Revert

    evm.output = Bytes(memory_read_bytes(evm.memory, offset, length))
    evm.running = False

    # PROGRAM COUNTER
    pass


def txparam(evm: Evm) -> None:
    """
    Push transaction-scoped information of the executing frame
    transaction onto the stack, selected by the parameter operand.
    """
    # STACK
    param = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_TXPARAM)

    # OPERATION
    frame_context = frame_transaction_context(evm)
    tx = frame_context.tx

    if param == U256(0x00):
        # The frame transaction's type identifier.
        value = U256(0x06)
    elif param == U256(0x01):
        value = U256(tx.nonce)
    elif param == U256(0x02):
        value = U256.from_be_bytes(tx.sender)
    elif param == U256(0x03):
        value = U256(tx.fees.max_priority_fee_per_gas)
    elif param == U256(0x04):
        value = U256(tx.fees.max_fee_per_gas)
    elif param == U256(0x05):
        value = tx.fees.max_fee_per_blob_gas
    elif param == U256(0x06):
        value = U256(frame_context.max_cost)
    elif param == U256(0x07):
        value = U256(len(tx.blob_versioned_hashes))
    elif param == U256(0x08):
        value = U256.from_be_bytes(frame_context.signature_hash)
    elif param == U256(0x09):
        value = U256(len(tx.frames))
    elif param == U256(0x0A):
        value = U256(frame_context.current_frame_index)
    elif param == U256(0x0B):
        value = U256(len(tx.signatures))
    elif param == U256(0x0C):
        # State gas remaining in the executing frame's pool.
        value = U256(frame_context.state_gas_left)
    else:
        raise InvalidParameter("undefined TXPARAM parameter")

    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def framedataload(evm: Evm) -> None:
    """
    Push a word (32 bytes) of the chosen frame's data onto the stack.

    The operation semantics match `CALLDATALOAD`: bytes beyond the end
    of the frame's data read as zeroes.
    """
    # STACK
    offset = pop(evm.stack)
    frame_index = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_FRAMEDATALOAD)

    # OPERATION
    frame_context = frame_transaction_context(evm)
    frames = frame_context.tx.frames
    if frame_index >= U256(len(frames)):
        raise InvalidParameter("frame index out of bounds")
    data = frames[int(frame_index)].data

    value = buffer_read(data, offset, U256(32))
    push(evm.stack, U256.from_be_bytes(value))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def framedatacopy(evm: Evm) -> None:
    """
    Copy a portion of the chosen frame's data to memory.

    The operation semantics and gas match `CALLDATACOPY`: bytes beyond
    the end of the frame's data are copied as zeroes, and the memory
    is expanded as needed.
    """
    # STACK
    memory_offset = pop(evm.stack)
    data_offset = pop(evm.stack)
    length = pop(evm.stack)
    frame_index = pop(evm.stack)

    # GAS
    words = ceil32(Uint(length)) // Uint(32)
    copy_gas_cost = ExecutionGas(GasCosts.OPCODE_COPY_PER_WORD * words)
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_offset, length)]
    )
    charge_gas(
        evm,
        GasCosts.OPCODE_FRAMEDATACOPY_BASE
        + copy_gas_cost
        + extend_memory.cost,
    )

    # OPERATION
    frame_context = frame_transaction_context(evm)
    frames = frame_context.tx.frames
    if frame_index >= U256(len(frames)):
        raise InvalidParameter("frame index out of bounds")
    data = frames[int(frame_index)].data

    evm.memory += b"\x00" * extend_memory.expand_by
    value = buffer_read(data, data_offset, length)
    memory_write(evm.memory, memory_offset, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def frameparam(evm: Evm) -> None:
    """
    Push frame-scoped information of the chosen frame onto the stack,
    selected by the parameter operand.

    A frame's status and gas usage are read from its receipt, which
    exists only once the frame has completed: requesting them for the
    current or a subsequent frame results in an exceptional halt. The
    receipt values are live, not final — a completed frame's state gas
    usage decreases when a later frame refills a state charge
    attributed to it, and is restored when that refill rolls back.
    """
    # STACK
    frame_index = pop(evm.stack)
    param = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_FRAMEPARAM)

    # OPERATION
    frame_context = frame_transaction_context(evm)
    tx = frame_context.tx
    if frame_index >= U256(len(tx.frames)):
        raise InvalidParameter("frame index out of bounds")
    frame = tx.frames[int(frame_index)]

    if param == U256(0x00):
        value = U256.from_be_bytes(resolve_frame_target(tx, frame))
    elif param == U256(0x01):
        value = U256(frame.gas_limits.execution)
    elif param == U256(0x02):
        value = U256(frame.mode)
    elif param == U256(0x03):
        value = U256(frame.flags)
    elif param == U256(0x04):
        value = U256(len(frame.data))
    elif param == U256(0x05):
        if frame_index >= U256(frame_context.current_frame_index):
            raise InvalidParameter(
                "status of the current or a subsequent frame"
            )
        receipt = frame_context.frame_receipts[int(frame_index)]
        value = U256(receipt.status)
    elif param == U256(0x06):
        value = U256(frame.flags & APPROVE_SCOPE_MASK)
    elif param == U256(0x07):
        if FrameFlag.ATOMIC_BATCH in frame.flags:
            value = U256(1)
        else:
            value = U256(0)
    elif param == U256(0x08):
        value = frame.value
    elif param == U256(0x09):
        value = U256(frame.gas_limits.state)
    elif param == U256(0x0A):
        if frame_index >= U256(frame_context.current_frame_index):
            raise InvalidParameter(
                "gas usage of the current or a subsequent frame"
            )
        receipt = frame_context.frame_receipts[int(frame_index)]
        value = U256(receipt.gas_used.execution)
    elif param == U256(0x0B):
        if frame_index >= U256(frame_context.current_frame_index):
            raise InvalidParameter(
                "gas usage of the current or a subsequent frame"
            )
        receipt = frame_context.frame_receipts[int(frame_index)]
        value = U256(receipt.gas_used.state)
    else:
        raise InvalidParameter("undefined FRAMEPARAM parameter")

    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sigparam(evm: Evm) -> None:
    """
    Access signature-scoped metadata of the chosen signature entry.

    The raw signature bytes of protocol-validated schemes are
    intentionally not accessible: the copy operation is defined only
    for `ARBITRARY` entries, whose bytes the protocol does not
    validate, and the resolved signer only for protocol-validated
    entries, to which the protocol assigns one.
    """
    # STACK
    signature_index = pop(evm.stack)
    param = pop(evm.stack)

    if param == U256(0x04):
        # STACK (copy operation)
        memory_offset = pop(evm.stack)
        data_offset = pop(evm.stack)
        length = pop(evm.stack)

        # GAS
        words = ceil32(Uint(length)) // Uint(32)
        copy_gas_cost = ExecutionGas(GasCosts.OPCODE_COPY_PER_WORD * words)
        extend_memory = calculate_gas_extend_memory(
            evm.memory, [(memory_offset, length)]
        )
        charge_gas(
            evm,
            GasCosts.OPCODE_SIGPARAM_COPY_BASE
            + copy_gas_cost
            + extend_memory.cost,
        )

        # OPERATION
        frame_context = frame_transaction_context(evm)
        signatures = frame_context.tx.signatures
        if signature_index >= U256(len(signatures)):
            raise InvalidParameter("signature index out of bounds")
        signature = signatures[int(signature_index)]
        if signature.scheme != FrameSignatureScheme.ARBITRARY:
            raise InvalidParameter(
                "signature bytes of a protocol-validated scheme"
            )

        evm.memory += b"\x00" * extend_memory.expand_by
        signature_bytes = buffer_read(signature.signature, data_offset, length)
        memory_write(evm.memory, memory_offset, signature_bytes)
    else:
        # GAS
        charge_gas(evm, GasCosts.OPCODE_SIGPARAM)

        # OPERATION
        frame_context = frame_transaction_context(evm)
        signatures = frame_context.tx.signatures
        if signature_index >= U256(len(signatures)):
            raise InvalidParameter("signature index out of bounds")
        signature = signatures[int(signature_index)]

        if param == U256(0x00):
            resolved_signer = frame_context.resolved_signers[
                int(signature_index)
            ]
            if resolved_signer is None:
                raise InvalidParameter("resolved signer of an ARBITRARY entry")
            value = U256.from_be_bytes(resolved_signer)
        elif param == U256(0x01):
            value = U256(signature.scheme)
        elif param == U256(0x02):
            if len(signature.message) == 0:
                value = U256(0)
            else:
                value = U256.from_be_bytes(signature.message)
        elif param == U256(0x03):
            value = U256(len(signature.signature))
        else:
            raise InvalidParameter("undefined SIGPARAM parameter")

        push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)
