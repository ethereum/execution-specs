"""
Implementations of the [EIP-7906] instructions, which expose the
executing frame transaction's state diff to its `POST_TX` assertion
frames. Executing any of them outside a `POST_TX` frame's call
subtree, in a legacy transaction or in a frame of any other mode,
results in an exceptional halt.

[EIP-7906]: https://eips.ethereum.org/EIPS/eip-7906
"""

from typing import Sequence, TypeVar

from ethereum_types.numeric import U256, Uint, ulen

from ethereum.crypto.hash import Hash32
from ethereum.state import EMPTY_CODE_HASH
from ethereum.utils.numeric import ceil32

from ...blocks import Log
from ...fork_types import ExecutionGas
from ...state_tracker import get_account_optional, get_storage
from ...transactions.frame_transaction import FrameMode
from ...utils.address import to_address_masked
from ...vm.memory import memory_write
from .. import Evm, FrameContext
from ..exceptions import InvalidParameter
from ..gas import GasCosts, calculate_gas_extend_memory, charge_gas
from ..stack import pop, push
from ..transaction_diff import (
    account_change_flags,
    event_indices_of,
    event_indices_with_topic,
    pre_state_account,
    pre_state_storage,
    slot_indices_of,
    transaction_diff,
)
from .frame import frame_transaction_context

T = TypeVar("T")


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

    The count parameters (`0x00`, `0x01`, `0x02`, `0x0C`) and the gas
    payment parameters (`0x14`, `0x15`) take no index and halt on a
    non-zero one. The gas pre-charge is the payer's escrow, the
    transaction's maximum cost with blob fees included. The payer is
    the address that approved payment, read as zero by a `POST_TX`
    frame executing before any frame approved payment, which leaves
    the transaction invalid regardless.
    """
    # STACK
    param = pop(evm.stack)
    index = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_TXTRACE)

    # OPERATION
    frame_context = post_tx_frame_context(evm)
    diff = transaction_diff(evm.tx_env.state, frame_context)

    if param == U256(0x00):
        require_reserved_zero(index)
        value = U256(len(diff.balances))
    elif param == U256(0x01):
        require_reserved_zero(index)
        value = U256(len(diff.slots))
    elif param == U256(0x02):
        require_reserved_zero(index)
        value = U256(len(diff.deployed))
    elif param == U256(0x03):
        value = U256.from_be_bytes(table_entry(diff.balances, index).address)
    elif param == U256(0x04):
        value = table_entry(diff.balances, index).before
    elif param == U256(0x05):
        value = table_entry(diff.balances, index).after
    elif param == U256(0x06):
        value = U256.from_be_bytes(table_entry(diff.slots, index).address)
    elif param == U256(0x07):
        value = U256.from_be_bytes(table_entry(diff.slots, index).key)
    elif param == U256(0x08):
        value = table_entry(diff.slots, index).before
    elif param == U256(0x09):
        value = table_entry(diff.slots, index).after
    elif param == U256(0x0A):
        value = U256.from_be_bytes(table_entry(diff.deployed, index).address)
    elif param == U256(0x0B):
        value = U256.from_be_bytes(table_entry(diff.deployed, index).code_hash)
    elif param == U256(0x0C):
        require_reserved_zero(index)
        value = U256(len(diff.events))
    elif param == U256(0x0D):
        value = U256.from_be_bytes(table_entry(diff.events, index).address)
    elif param == U256(0x0E):
        value = U256(len(table_entry(diff.events, index).topics))
    elif param == U256(0x0F):
        value = event_topic(table_entry(diff.events, index), 0)
    elif param == U256(0x10):
        value = event_topic(table_entry(diff.events, index), 1)
    elif param == U256(0x11):
        value = event_topic(table_entry(diff.events, index), 2)
    elif param == U256(0x12):
        value = event_topic(table_entry(diff.events, index), 3)
    elif param == U256(0x13):
        value = U256(len(table_entry(diff.events, index).data))
    elif param == U256(0x14):
        require_reserved_zero(index)
        value = U256(frame_context.max_cost)
    elif param == U256(0x15):
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


def txdiff(evm: Evm) -> None:
    """
    Push one keyed lookup into the executing transaction's state diff
    onto the stack, selected by the parameter operand, an address or
    topic value, and a slot key, per-address index, or zero.

    Parameters `0x00` to `0x05` read one account's slot, balance, or
    code hash before and after the transaction. They may fall back to
    the live state for a key the transaction never wrote, so they are
    priced and recorded like any other state read: a cold or warm
    access per [EIP-2929]. The access warms the key for the rest of the
    frame and, once the frame succeeds, for later frames. Parameters
    `0x06` to `0x0C` are per-address and per-topic views over the
    enumeration tables and the account change flags, answered from the
    transaction-local diff alone at the flat `TXTRACE` cost.

    [EIP-2929]: https://eips.ethereum.org/EIPS/eip-2929
    """
    # STACK
    param = pop(evm.stack)
    key_operand = pop(evm.stack)
    index_operand = pop(evm.stack)

    # GAS (STATE-INDEPENDENT)
    address = to_address_masked(key_operand)
    slot_key = index_operand.to_be_bytes32()
    if param == U256(0x00) or param == U256(0x01):
        # STATE ACCESS (STATE-DEPENDENT GAS)
        if (address, slot_key) in evm.accessed_storage_keys:
            charge_gas(evm, GasCosts.WARM_ACCESS)
        else:
            evm.accessed_storage_keys.add((address, slot_key))
            charge_gas(evm, GasCosts.COLD_STORAGE_ACCESS)
    elif U256(0x02) <= param <= U256(0x05):
        # STATE ACCESS (STATE-DEPENDENT GAS)
        if address in evm.accessed_addresses:
            charge_gas(evm, GasCosts.WARM_ACCESS)
        else:
            evm.accessed_addresses.add(address)
            charge_gas(evm, GasCosts.COLD_ACCOUNT_ACCESS)
    else:
        charge_gas(evm, GasCosts.OPCODE_TXTRACE)

    # OPERATION
    frame_context = post_tx_frame_context(evm)
    tx_state = evm.tx_env.state

    if param == U256(0x00) or param == U256(0x01):
        # The live read records the access. An unwritten slot reads the
        # same value before and after.
        live_value = get_storage(tx_state, address, slot_key)
        if param == U256(0x00):
            value = pre_state_storage(tx_state, address, slot_key)
        else:
            value = live_value
    elif U256(0x02) <= param <= U256(0x05):
        require_reserved_zero(index_operand)
        live_account = get_account_optional(tx_state, address)
        before = pre_state_account(tx_state, address)
        if param == U256(0x02):
            value = before.balance
        elif param == U256(0x03):
            if live_account is None:
                value = U256(0)
            else:
                value = live_account.balance
        elif param == U256(0x04):
            value = U256.from_be_bytes(before.code_hash)
        else:
            if live_account is None:
                value = U256.from_be_bytes(EMPTY_CODE_HASH)
            else:
                value = U256.from_be_bytes(live_account.code_hash)
    else:
        diff = transaction_diff(tx_state, frame_context)
        if param == U256(0x06):
            require_reserved_zero(index_operand)
            value = U256(len(slot_indices_of(diff, address)))
        elif param == U256(0x07):
            value = U256(
                table_entry(slot_indices_of(diff, address), index_operand)
            )
        elif param == U256(0x08):
            require_reserved_zero(index_operand)
            value = U256(len(event_indices_of(diff, address)))
        elif param == U256(0x09):
            value = U256(
                table_entry(event_indices_of(diff, address), index_operand)
            )
        elif param == U256(0x0A):
            require_reserved_zero(index_operand)
            value = account_change_flags(tx_state, diff, address)
        elif param == U256(0x0B):
            require_reserved_zero(index_operand)
            topic = Hash32(key_operand.to_be_bytes32())
            value = U256(len(event_indices_with_topic(diff, topic)))
        elif param == U256(0x0C):
            topic = Hash32(key_operand.to_be_bytes32())
            value = U256(
                table_entry(
                    event_indices_with_topic(diff, topic), index_operand
                )
            )
        else:
            raise InvalidParameter("undefined TXDIFF parameter")

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
