"""
Implementations of the [EIP-7906] instructions, which expose the
executing frame transaction's state diff to its `POST_TX` assertion
frames. Executing any of them outside a `POST_TX` frame's call
subtree, in a legacy transaction or in a frame of any other mode,
results in an exceptional halt.

[EIP-7906]: https://eips.ethereum.org/EIPS/eip-7906
"""

from typing import Sequence, TypeVar, final

from ethereum_types.enum import UintEnum
from ethereum_types.numeric import U256, Uint, ulen

from ethereum.utils.numeric import ceil32

from ...blocks import Log
from ...fork_types import ExecutionGas
from ...transactions.frame_transaction import FrameMode
from ...vm.memory import memory_write
from .. import Evm, FrameContext
from ..exceptions import InvalidParameter
from ..gas import GasCosts, calculate_gas_extend_memory, charge_gas
from ..stack import pop, push
from ..transaction_diff import transaction_diff
from .frame import frame_transaction_context

T = TypeVar("T")


@final
class TraceParameter(UintEnum):
    """
    Values of the `TXTRACE` parameter operand.
    """

    BALANCES_CHANGED = Uint(0x00)
    SLOTS_CHANGED = Uint(0x01)
    CODES_CHANGED = Uint(0x02)
    NONCES_CHANGED = Uint(0x03)
    BALANCE_ADDRESS = Uint(0x04)
    BALANCE_BEFORE = Uint(0x05)
    BALANCE_AFTER = Uint(0x06)
    SLOT_ADDRESS = Uint(0x07)
    SLOT_BEFORE = Uint(0x08)
    SLOT_AFTER = Uint(0x09)
    SLOT_KEY = Uint(0x0A)
    CODE_ADDRESS = Uint(0x0B)
    CODE_BEFORE = Uint(0x0C)
    CODE_AFTER = Uint(0x0D)
    NONCE_ADDRESS = Uint(0x0E)
    NONCE_BEFORE = Uint(0x0F)
    NONCE_AFTER = Uint(0x10)
    EVENTS_COUNT = Uint(0x11)
    EVENT_ADDRESS = Uint(0x12)
    EVENT_TOPIC_COUNT = Uint(0x13)
    EVENT_TOPIC0 = Uint(0x14)
    EVENT_TOPIC1 = Uint(0x15)
    EVENT_TOPIC2 = Uint(0x16)
    EVENT_TOPIC3 = Uint(0x17)
    EVENT_DATA_LEN = Uint(0x18)
    GAS_PRE_CHARGE = Uint(0x19)
    GAS_PAYER = Uint(0x1A)


def post_tx_frame_context(evm: Evm) -> FrameContext:
    """
    Return the executing frame transaction's context, or exceptionally
    halt unless the executing frame is a `POST_TX` frame.

    The check keys on the frame, not the call depth, so the diff
    instructions are valid anywhere in a `POST_TX` frame's call subtree
    and nowhere else.
    """
    frame_context = frame_transaction_context(evm)
    frame = frame_context.tx.frames[int(frame_context.current_frame_index)]
    if frame.mode != FrameMode.POST_TX:
        raise InvalidParameter("not a POST_TX frame")
    return frame_context


def require_reserved_zero(operand: U256) -> None:
    """
    Exceptionally halt unless an operand the parameter tables mark
    *must be 0* is zero.
    """
    if operand != U256(0):
        raise InvalidParameter("reserved input must be zero")


def table_entry(table: Sequence[T], index: U256) -> T:
    """
    Return the entry of a diff table at an index, or exceptionally halt
    when the index is out of bounds.
    """
    if index >= U256(len(table)):
        raise InvalidParameter("index out of bounds")
    return table[int(index)]


def event_topic(event: Log, position: int) -> U256:
    """
    Return one topic of an event, or exceptionally halt when the event
    carries no topic at that position.
    """
    if position >= len(event.topics):
        raise InvalidParameter("event has no such topic")
    return U256.from_be_bytes(event.topics[position])


def txtrace(evm: Evm) -> None:
    """
    Push one value of the executing transaction's state diff onto the
    stack, selected by the parameter operand and, for the per-entry
    parameters, an index into the table the parameter enumerates.

    The count parameters and the gas payment parameters take no index
    and halt on a non-zero one. The gas pre-charge is the payer's
    escrow, the transaction's maximum cost with blob fees included.
    The payer is the address that approved payment, read as zero by a
    `POST_TX` frame executing before any frame approved payment, which
    leaves the transaction invalid regardless.
    """
    # STACK
    param = pop(evm.stack)
    index = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_TXTRACE)

    # OPERATION
    frame_context = post_tx_frame_context(evm)
    diff = transaction_diff(evm.tx_env.state, frame_context)

    if param == TraceParameter.BALANCES_CHANGED:
        require_reserved_zero(index)
        value = U256(len(diff.balances))
    elif param == TraceParameter.SLOTS_CHANGED:
        require_reserved_zero(index)
        value = U256(len(diff.slots))
    elif param == TraceParameter.CODES_CHANGED:
        require_reserved_zero(index)
        value = U256(len(diff.codes))
    elif param == TraceParameter.NONCES_CHANGED:
        require_reserved_zero(index)
        value = U256(len(diff.nonces))
    elif param == TraceParameter.BALANCE_ADDRESS:
        value = U256.from_be_bytes(table_entry(diff.balances, index).address)
    elif param == TraceParameter.BALANCE_BEFORE:
        value = table_entry(diff.balances, index).before
    elif param == TraceParameter.BALANCE_AFTER:
        value = table_entry(diff.balances, index).after
    elif param == TraceParameter.SLOT_ADDRESS:
        value = U256.from_be_bytes(table_entry(diff.slots, index).address)
    elif param == TraceParameter.SLOT_BEFORE:
        value = table_entry(diff.slots, index).before
    elif param == TraceParameter.SLOT_AFTER:
        value = table_entry(diff.slots, index).after
    elif param == TraceParameter.SLOT_KEY:
        value = U256.from_be_bytes(table_entry(diff.slots, index).key)
    elif param == TraceParameter.CODE_ADDRESS:
        value = U256.from_be_bytes(table_entry(diff.codes, index).address)
    elif param == TraceParameter.CODE_BEFORE:
        value = U256.from_be_bytes(table_entry(diff.codes, index).before)
    elif param == TraceParameter.CODE_AFTER:
        value = U256.from_be_bytes(table_entry(diff.codes, index).after)
    elif param == TraceParameter.NONCE_ADDRESS:
        value = U256.from_be_bytes(table_entry(diff.nonces, index).address)
    elif param == TraceParameter.NONCE_BEFORE:
        value = U256(table_entry(diff.nonces, index).before)
    elif param == TraceParameter.NONCE_AFTER:
        value = U256(table_entry(diff.nonces, index).after)
    elif param == TraceParameter.EVENTS_COUNT:
        require_reserved_zero(index)
        value = U256(len(diff.events))
    elif param == TraceParameter.EVENT_ADDRESS:
        value = U256.from_be_bytes(table_entry(diff.events, index).address)
    elif param == TraceParameter.EVENT_TOPIC_COUNT:
        value = U256(len(table_entry(diff.events, index).topics))
    elif param == TraceParameter.EVENT_TOPIC0:
        value = event_topic(table_entry(diff.events, index), 0)
    elif param == TraceParameter.EVENT_TOPIC1:
        value = event_topic(table_entry(diff.events, index), 1)
    elif param == TraceParameter.EVENT_TOPIC2:
        value = event_topic(table_entry(diff.events, index), 2)
    elif param == TraceParameter.EVENT_TOPIC3:
        value = event_topic(table_entry(diff.events, index), 3)
    elif param == TraceParameter.EVENT_DATA_LEN:
        value = U256(len(table_entry(diff.events, index).data))
    elif param == TraceParameter.GAS_PRE_CHARGE:
        require_reserved_zero(index)
        value = U256(frame_context.max_cost)
    elif param == TraceParameter.GAS_PAYER:
        require_reserved_zero(index)
        if frame_context.payer is None:
            value = U256(0)
        else:
            value = U256.from_be_bytes(frame_context.payer)
    else:
        raise InvalidParameter("undefined TXTRACE parameter")

    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def eventdatacopy(evm: Evm) -> None:
    """
    Copy a portion of one event's non-indexed data into memory, with
    `CALLDATACOPY` pricing.

    Unlike `CALLDATACOPY`, a range reaching past the end of the event's
    data is not zero-padded but exceptionally halts, as does an event
    index beyond the transaction's event count.
    """
    # STACK
    event_index = pop(evm.stack)
    memory_start_index = pop(evm.stack)
    data_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // Uint(32)
    copy_gas_cost = ExecutionGas(GasCosts.OPCODE_COPY_PER_WORD * words)
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(
        evm,
        GasCosts.OPCODE_EVENTDATACOPY_BASE
        + copy_gas_cost
        + extend_memory.cost,
    )

    # OPERATION
    frame_context = post_tx_frame_context(evm)
    diff = transaction_diff(evm.tx_env.state, frame_context)
    event = table_entry(diff.events, event_index)
    if Uint(data_start_index) + Uint(size) > ulen(event.data):
        raise InvalidParameter("event data range out of bounds")

    evm.memory += b"\x00" * extend_memory.expand_by
    start = int(data_start_index)
    memory_write(
        evm.memory,
        memory_start_index,
        event.data[start : start + int(size)],
    )

    # PROGRAM COUNTER
    evm.pc += Uint(1)
