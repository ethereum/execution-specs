"""
Ethereum Virtual Machine (EVM) Gas.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

EVM gas constants and calculators.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, List, Tuple, final

from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.forks.bpo5.blocks import Header as PreviousHeader
from ethereum.trace import GasAndRefund, StateGasAndRefund, evm_trace
from ethereum.utils.numeric import ceil32, taylor_exponential

from ..blocks import Header
from ..fork_types import StateGas, StateGasPerByte
from ..transactions import (
    TX_MAX_GAS_LIMIT,
    BlobTransaction,
    IntrinsicGasCost,
    Transaction,
)
from .exceptions import OutOfGasError

if TYPE_CHECKING:
    from . import Evm


# These may be patched at runtime by a future gas repricing utility to
# fast-iterate on state-byte costs.
class StateGasCosts:
    """
    EIP-8037 state-gas constants.

    Kept separate from `GasCosts` because these carry a different unit:
    state-byte counts that convert into gas via `COST_PER_STATE_BYTE`.
    """

    COST_PER_STATE_BYTE: Final[StateGasPerByte] = StateGasPerByte(Uint(1530))
    STATE_BYTES_PER_NEW_ACCOUNT: Final[Uint] = Uint(120)
    STATE_BYTES_PER_STORAGE_SET: Final[Uint] = Uint(64)
    STATE_BYTES_PER_AUTH_BASE: Final[Uint] = Uint(23)
    STORAGE_SET: Final[StateGas] = (
        STATE_BYTES_PER_STORAGE_SET * COST_PER_STATE_BYTE
    )
    NEW_ACCOUNT: Final[StateGas] = (
        STATE_BYTES_PER_NEW_ACCOUNT * COST_PER_STATE_BYTE
    )
    AUTH_BASE: Final[StateGas] = (
        STATE_BYTES_PER_AUTH_BASE * COST_PER_STATE_BYTE
    )


# These values may be patched at runtime by a future gas repricing utility
class GasCosts:
    """
    Constant gas values for the EVM.
    """

    # Tiers
    BASE: Final[Uint] = Uint(2)
    VERY_LOW: Final[Uint] = Uint(3)
    LOW: Final[Uint] = Uint(5)
    MID: Final[Uint] = Uint(8)
    HIGH: Final[Uint] = Uint(10)

    # Access
    WARM_ACCESS: Final[Uint] = Uint(100)
    COLD_ACCOUNT_ACCESS: Final[Uint] = Uint(3000)
    COLD_STORAGE_ACCESS: Final[Uint] = Uint(3000)

    # Storage
    STORAGE_WRITE: Final[Uint] = Uint(10000)

    # Call
    CALL_VALUE: Final[Uint] = Uint(10300)  # ACCOUNT_WRITE + CALL_STIPEND
    CALL_STIPEND: Final[Uint] = Uint(2300)
    ACCOUNT_WRITE: Final[Uint] = Uint(8000)

    # Contract Creation
    CODE_DEPOSIT_PER_BYTE: Final[Uint] = Uint(200)
    CODE_INIT_PER_WORD: Final[Uint] = Uint(2)
    CREATE_ACCESS: Final[Uint] = ACCOUNT_WRITE + COLD_STORAGE_ACCESS

    # Utility
    ZERO: Final[Uint] = Uint(0)
    MEMORY_PER_WORD: Final[Uint] = Uint(3)
    FAST_STEP: Final[Uint] = Uint(5)

    # Refunds
    REFUND_STORAGE_CLEAR: Final[int] = int(
        (STORAGE_WRITE + COLD_STORAGE_ACCESS) * Uint(4800) // Uint(5000)
    )

    # Precompiles
    PRECOMPILE_ECRECOVER: Final[Uint] = Uint(3000)
    PRECOMPILE_P256VERIFY: Final[Uint] = Uint(6900)
    PRECOMPILE_SHA256_BASE: Final[Uint] = Uint(60)
    PRECOMPILE_SHA256_PER_WORD: Final[Uint] = Uint(12)
    PRECOMPILE_RIPEMD160_BASE: Final[Uint] = Uint(600)
    PRECOMPILE_RIPEMD160_PER_WORD: Final[Uint] = Uint(120)
    PRECOMPILE_IDENTITY_BASE: Final[Uint] = Uint(15)
    PRECOMPILE_IDENTITY_PER_WORD: Final[Uint] = Uint(3)
    PRECOMPILE_BLAKE2F_PER_ROUND: Final[Uint] = Uint(1)
    PRECOMPILE_POINT_EVALUATION: Final[Uint] = Uint(50000)
    PRECOMPILE_BLS_G1ADD: Final[Uint] = Uint(375)
    PRECOMPILE_BLS_G1MUL: Final[Uint] = Uint(12000)
    PRECOMPILE_BLS_G1MAP: Final[Uint] = Uint(5500)
    PRECOMPILE_BLS_G2ADD: Final[Uint] = Uint(600)
    PRECOMPILE_BLS_G2MUL: Final[Uint] = Uint(22500)
    PRECOMPILE_BLS_G2MAP: Final[Uint] = Uint(23800)
    PRECOMPILE_ECADD: Final[Uint] = Uint(150)
    PRECOMPILE_ECMUL: Final[Uint] = Uint(6000)
    PRECOMPILE_ECPAIRING_BASE: Final[Uint] = Uint(45000)
    PRECOMPILE_ECPAIRING_PER_POINT: Final[Uint] = Uint(34000)

    # Blobs
    PER_BLOB: Final[U64] = U64(2**17)
    BLOB_SCHEDULE_TARGET: Final[U64] = U64(14)
    BLOB_TARGET_GAS_PER_BLOCK: Final[U64] = PER_BLOB * BLOB_SCHEDULE_TARGET
    BLOB_BASE_COST: Final[Uint] = Uint(2**13)
    BLOB_SCHEDULE_MAX: Final[U64] = U64(21)
    BLOB_MIN_GASPRICE: Final[Uint] = Uint(1)
    BLOB_BASE_FEE_UPDATE_FRACTION: Final[Uint] = Uint(11684671)

    # Block Access Lists
    BLOCK_ACCESS_LIST_ITEM: Final[Uint] = Uint(2000)

    # Transactions
    TX_BASE: Final[Uint] = Uint(12000)
    TX_CREATE: Final[Uint] = Uint(32000)
    TX_VALUE_COST: Final[Uint] = Uint(4244)
    TRANSFER_LOG_COST: Final[Uint] = Uint(1756)
    TX_DATA_TOKEN_STANDARD: Final[Uint] = Uint(4)
    TX_DATA_TOKEN_FLOOR: Final[Uint] = Uint(16)
    TX_ACCESS_LIST_ADDRESS: Final[Uint] = COLD_ACCOUNT_ACCESS
    TX_ACCESS_LIST_STORAGE_KEY: Final[Uint] = COLD_STORAGE_ACCESS

    # Authorization
    AUTH_TUPLE_BYTES: Final[Uint] = Uint(101)
    REGULAR_PER_AUTH_BASE_COST: Final[Uint] = (
        AUTH_TUPLE_BYTES * TX_DATA_TOKEN_FLOOR
        + PRECOMPILE_ECRECOVER
        + COLD_ACCOUNT_ACCESS
        + Uint(2) * WARM_ACCESS
    )

    # Block
    LIMIT_ADJUSTMENT_FACTOR: Final[Uint] = Uint(1024)
    LIMIT_MINIMUM: Final[Uint] = Uint(5000)

    # Static Opcodes
    OPCODE_ADD: Final[Uint] = VERY_LOW
    OPCODE_SUB: Final[Uint] = VERY_LOW
    OPCODE_MUL: Final[Uint] = LOW
    OPCODE_DIV: Final[Uint] = LOW
    OPCODE_SDIV: Final[Uint] = LOW
    OPCODE_MOD: Final[Uint] = LOW
    OPCODE_SMOD: Final[Uint] = LOW
    OPCODE_ADDMOD: Final[Uint] = MID
    OPCODE_MULMOD: Final[Uint] = MID
    OPCODE_SIGNEXTEND: Final[Uint] = LOW
    OPCODE_LT: Final[Uint] = VERY_LOW
    OPCODE_GT: Final[Uint] = VERY_LOW
    OPCODE_SLT: Final[Uint] = VERY_LOW
    OPCODE_SGT: Final[Uint] = VERY_LOW
    OPCODE_EQ: Final[Uint] = VERY_LOW
    OPCODE_ISZERO: Final[Uint] = VERY_LOW
    OPCODE_AND: Final[Uint] = VERY_LOW
    OPCODE_OR: Final[Uint] = VERY_LOW
    OPCODE_XOR: Final[Uint] = VERY_LOW
    OPCODE_NOT: Final[Uint] = VERY_LOW
    OPCODE_BYTE: Final[Uint] = VERY_LOW
    OPCODE_SHL: Final[Uint] = VERY_LOW
    OPCODE_SHR: Final[Uint] = VERY_LOW
    OPCODE_SAR: Final[Uint] = VERY_LOW
    OPCODE_CLZ: Final[Uint] = LOW
    OPCODE_JUMP: Final[Uint] = MID
    OPCODE_JUMPI: Final[Uint] = HIGH
    OPCODE_JUMPDEST: Final[Uint] = Uint(1)
    OPCODE_CALLDATALOAD: Final[Uint] = VERY_LOW
    OPCODE_BLOCKHASH: Final[Uint] = Uint(20)
    OPCODE_COINBASE: Final[Uint] = BASE
    OPCODE_POP: Final[Uint] = BASE
    OPCODE_MSIZE: Final[Uint] = BASE
    OPCODE_PC: Final[Uint] = BASE
    OPCODE_GAS: Final[Uint] = BASE
    OPCODE_ADDRESS: Final[Uint] = BASE
    OPCODE_ORIGIN: Final[Uint] = BASE
    OPCODE_CALLER: Final[Uint] = BASE
    OPCODE_CALLVALUE: Final[Uint] = BASE
    OPCODE_CALLDATASIZE: Final[Uint] = BASE
    OPCODE_CODESIZE: Final[Uint] = BASE
    OPCODE_GASPRICE: Final[Uint] = BASE
    OPCODE_TIMESTAMP: Final[Uint] = BASE
    OPCODE_NUMBER: Final[Uint] = BASE
    OPCODE_GASLIMIT: Final[Uint] = BASE
    OPCODE_PREVRANDAO: Final[Uint] = BASE
    OPCODE_RETURNDATASIZE: Final[Uint] = BASE
    OPCODE_CHAINID: Final[Uint] = BASE
    OPCODE_BASEFEE: Final[Uint] = BASE
    OPCODE_BLOBBASEFEE: Final[Uint] = BASE
    OPCODE_SLOTNUM: Final[Uint] = BASE
    OPCODE_BLOBHASH: Final[Uint] = Uint(3)
    OPCODE_PUSH: Final[Uint] = VERY_LOW
    OPCODE_PUSH0: Final[Uint] = BASE
    OPCODE_DUP: Final[Uint] = VERY_LOW
    OPCODE_SWAP: Final[Uint] = VERY_LOW
    OPCODE_DUPN: Final[Uint] = VERY_LOW
    OPCODE_SWAPN: Final[Uint] = VERY_LOW
    OPCODE_EXCHANGE: Final[Uint] = VERY_LOW
    OPCODE_TLOAD: Final[Uint] = Uint(100)
    OPCODE_TSTORE: Final[Uint] = Uint(100)

    # Dynamic Opcode Components
    OPCODE_RETURNDATACOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_RETURNDATACOPY_PER_WORD: Final[Uint] = Uint(3)
    OPCODE_CALLDATACOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_CODECOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_MCOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_MLOAD_BASE: Final[Uint] = VERY_LOW
    OPCODE_MSTORE_BASE: Final[Uint] = VERY_LOW
    OPCODE_MSTORE8_BASE: Final[Uint] = VERY_LOW
    OPCODE_COPY_PER_WORD: Final[Uint] = Uint(3)
    OPCODE_EXP_BASE: Final[Uint] = Uint(10)
    OPCODE_EXP_PER_BYTE: Final[Uint] = Uint(50)
    OPCODE_KECCAK256_BASE: Final[Uint] = Uint(30)
    OPCODE_KECCAK256_PER_WORD: Final[Uint] = Uint(6)
    OPCODE_LOG_BASE: Final[Uint] = Uint(375)
    OPCODE_LOG_DATA_PER_BYTE: Final[Uint] = Uint(8)
    OPCODE_LOG_TOPIC: Final[Uint] = Uint(375)
    OPCODE_SELFDESTRUCT_BASE: Final[Uint] = Uint(5000)


@final
@dataclass
class GasMeter:
    """
    Track a frame's gas consumption across both gas dimensions.

    Bundle every mutable gas quantity a frame maintains, so the frame
    and its settlement work against one object instead of a scatter of
    fields on the [`Evm`].

    [`Evm`]: ref:ethereum.forks.amsterdam.vm.Evm
    """

    gas_left: Uint
    """
    Gas still available from the frame's regular grant. Pays regular
    charges, and state charges as [spill] once the reservoir empties.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_spilled
    """

    state_gas_left: Uint
    """
    State gas still available in the frame's reservoir. Charges draw
    from here first and spill into `gas_left` once it is empty.
    """

    state_gas_baseline: Uint
    """
    Reservoir level a rollback refills to: the frame's grant at entry,
    moved down by [`commit_state_gas`][commit] when charges become
    non-refillable.

    [commit]: ref:ethereum.forks.amsterdam.vm.gas.commit_state_gas
    """

    refund_counter: int = 0
    """Gas eligible for refund at the end of the transaction."""

    state_gas_spilled: Uint = Uint(0)
    """
    Regular gas spent covering state charges after the reservoir
    emptied. Credited back to `gas_left` first, in LIFO order, on a
    refund or failure. [EIP-8037] names this quantity
    `state_gas_from_gas_left`.

    [EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
    """

    state_gas_committed_spill: Uint = Uint(0)
    """
    [Spill] that [`commit_state_gas`][commit] marked non-refillable.
    It outlives the rollbacks [`restore_state_gas`][restore] performs;
    only [`restore_state_gas_to_entry`][entry] credits it back to
    `gas_left`. Committed reservoir draw needs no counter of its own:
    each commit lowers the baseline, so it is the frame's grant minus
    `state_gas_baseline`.

    [Spill]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_spilled
    [commit]: ref:ethereum.forks.amsterdam.vm.gas.commit_state_gas
    [restore]: ref:ethereum.forks.amsterdam.vm.gas.restore_state_gas
    [entry]: ref:ethereum.forks.amsterdam.vm.gas.restore_state_gas_to_entry
    """


@final
@dataclass
class ExtendMemory:
    """
    Define the parameters for memory extension in opcodes.

    `cost`: `ethereum.base_types.Uint`
        The gas required to perform the extension
    `expand_by`: `ethereum.base_types.Uint`
        The size by which the memory will be extended
    """

    cost: Uint
    expand_by: Uint


@final
@dataclass
class MessageCallGas:
    """
    Define the gas cost and gas given to the sub-call for executing the call
    opcodes.

    `cost`: `ethereum.base_types.Uint`
        The gas required to execute the call opcode, excludes
        memory expansion costs.
    `sub_call`: `ethereum.base_types.Uint`
        The portion of gas available to sub-calls that is refundable
        if not consumed.
    """

    cost: Uint
    sub_call: Uint


def check_gas(evm: "Evm", amount: Uint) -> None:
    """
    Checks if `amount` gas is available without charging it.
    Raises OutOfGasError if insufficient gas.

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of gas to check.

    """
    if evm.gas_meter.gas_left < amount:
        raise OutOfGasError


def charge_gas(evm: "Evm", amount: Uint) -> None:
    """
    Subtracts `amount` from `gas_left` (regular gas).

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of regular gas the current operation requires.

    """
    evm_trace(evm, GasAndRefund(int(amount)))

    gas_meter = evm.gas_meter
    if gas_meter.gas_left < amount:
        raise OutOfGasError
    gas_meter.gas_left -= amount


def charge_state_gas(evm: "Evm", amount: StateGas) -> None:
    """
    Subtracts `amount` from the state gas reservoir, then from
    `gas_left` when the reservoir is empty, tracking any [spill].

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of state gas the current operation requires.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_spilled

    """
    evm_trace(evm, StateGasAndRefund(int(amount)))

    gas_meter = evm.gas_meter
    if gas_meter.state_gas_left >= amount:
        gas_meter.state_gas_left -= amount
    elif gas_meter.state_gas_left + gas_meter.gas_left >= amount:
        remainder = amount - gas_meter.state_gas_left
        gas_meter.state_gas_left = Uint(0)
        gas_meter.gas_left -= remainder
        gas_meter.state_gas_spilled += remainder
    else:
        raise OutOfGasError


def commit_state_gas(gas_meter: GasMeter) -> None:
    """
    Mark the state gas spent so far as non-refillable.

    A later rollback via [`restore_state_gas`][restore] leaves the
    state bought so far in place, so it must not credit this gas back.
    In the top frame that protects the delegations applied by
    [`set_delegation`][sd], which survive a failure of the dispatched
    code. A failure that reverts the committed state as well -- one
    raised before dispatch -- must instead undo the commit with
    [`restore_state_gas_to_entry`][entry].

    Move the baseline down to the current reservoir level and fold the
    spill into `state_gas_committed_spill`, so later refunds route to
    the reservoir instead of back into `gas_left`.

    Parameters
    ----------
    gas_meter :
        The frame's gas meter.

    [sd]: ref:ethereum.forks.amsterdam.vm.eoa_delegation.set_delegation
    [restore]: ref:ethereum.forks.amsterdam.vm.gas.restore_state_gas
    [entry]: ref:ethereum.forks.amsterdam.vm.gas.restore_state_gas_to_entry

    """
    # Only charges precede a commit, so no refund has pushed the
    # reservoir above the baseline: a commit only ever lowers it.
    assert gas_meter.state_gas_left <= gas_meter.state_gas_baseline
    gas_meter.state_gas_committed_spill += gas_meter.state_gas_spilled
    gas_meter.state_gas_baseline = gas_meter.state_gas_left
    gas_meter.state_gas_spilled = Uint(0)


def restore_state_gas(gas_meter: GasMeter) -> None:
    """
    Roll the frame's state gas back to the baseline on revert or halt.

    The frame's state changes are undone, so the state gas consumed
    since the [baseline] is credited back in LIFO order: the [spill]
    returns to `gas_left` first, then the reservoir resets to the
    baseline. The refunds accrued on the undone changes are discarded
    with them. State gas committed as non-refillable stays charged.

    Parameters
    ----------
    gas_meter :
        The frame's gas meter.

    [baseline]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_baseline
    [spill]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_spilled

    """  # noqa: E501
    gas_meter.gas_left += gas_meter.state_gas_spilled
    gas_meter.state_gas_spilled = Uint(0)
    gas_meter.state_gas_left = gas_meter.state_gas_baseline
    gas_meter.refund_counter = 0


def restore_state_gas_to_entry(
    gas_meter: GasMeter, state_gas_reservoir: Uint
) -> None:
    """
    Roll the frame's state gas back to frame entry, undoing any commit.

    Used when the transaction-state rollback also reverts the applied
    delegations a [`commit_state_gas`][commit] protected: every state
    charge refills -- all spill, committed or not, returns to
    `gas_left` -- and the baseline resets to the frame's [grant].

    Parameters
    ----------
    gas_meter :
        The frame's gas meter.
    state_gas_reservoir :
        The frame's immutable state gas grant.

    [commit]: ref:ethereum.forks.amsterdam.vm.gas.commit_state_gas
    [grant]: ref:ethereum.forks.amsterdam.vm.Message.state_gas_reservoir

    """
    # The baseline starts at the grant and only ever moves down.
    assert gas_meter.state_gas_baseline <= state_gas_reservoir
    # Only pre-dispatch failures roll back to entry, and no refund
    # accrues before dispatch.
    assert gas_meter.refund_counter == 0
    gas_meter.gas_left += (
        gas_meter.state_gas_spilled + gas_meter.state_gas_committed_spill
    )
    gas_meter.state_gas_spilled = Uint(0)
    gas_meter.state_gas_committed_spill = Uint(0)
    gas_meter.state_gas_left = state_gas_reservoir
    gas_meter.state_gas_baseline = state_gas_reservoir


def tx_state_gas_used(gas_meter: GasMeter, state_gas_reservoir: Uint) -> int:
    """
    Return the net state gas a transaction's execution consumed.

    Measured off the top frame's finished gas meter: the reservoir
    drawn down since the transaction's grant plus the [spill],
    outstanding or committed. May be negative when refunds exceed
    charges.

    Parameters
    ----------
    gas_meter :
        The top frame's finished gas meter.
    state_gas_reservoir :
        The transaction's immutable state gas grant.

    Returns
    -------
    state_gas_used : `int`
        The net state gas consumed.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_spilled

    """
    # The baseline starts at the grant and only ever moves down.
    assert gas_meter.state_gas_baseline <= state_gas_reservoir
    return (
        int(state_gas_reservoir)
        - int(gas_meter.state_gas_left)
        + int(gas_meter.state_gas_spilled)
        + int(gas_meter.state_gas_committed_spill)
    )


def credit_state_gas_refund(gas_meter: GasMeter, amount: StateGas) -> None:
    """
    Credit a state gas refund to the local frame, in LIFO order.

    State-gas charges draw from the reservoir first and from `gas_left`
    last, so refunds credit the pool charged last first: `gas_left` up
    to the [spill], then the reservoir. This restores the exact pools
    the charge drew from, so the two never drift.

    Parameters
    ----------
    gas_meter :
        The gas meter crediting the refund.
    amount :
        The refund amount to credit.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_spilled

    """
    from_gas_left = min(amount, gas_meter.state_gas_spilled)
    gas_meter.gas_left += from_gas_left
    gas_meter.state_gas_spilled -= from_gas_left
    gas_meter.state_gas_left += amount - from_gas_left


def forfeit_remaining_gas(gas_meter: GasMeter) -> None:
    """
    Consume all remaining regular gas on an exceptional halt.

    Parameters
    ----------
    gas_meter :
        The halted frame's gas meter.

    """
    # A rollback owes any outstanding spill back to `gas_left`; it
    # must be restored before the remainder burns.
    assert gas_meter.state_gas_spilled == Uint(0)
    gas_meter.gas_left = Uint(0)


def withhold_create_gas(gas_meter: GasMeter) -> Uint:
    """
    Withhold and return the gas made available to a `CREATE*` child.

    Deduct the all-but-one-64th share from the frame's `gas_left` and
    return it as the child frame's regular gas grant.

    Parameters
    ----------
    gas_meter :
        The creating frame's gas meter.

    Returns
    -------
    child_gas : `ethereum.base_types.Uint`
        The regular gas granted to the child frame.

    """
    child_gas = max_message_call_gas(gas_meter.gas_left)
    gas_meter.gas_left -= child_gas
    return child_gas


def drain_state_gas_reservoir(gas_meter: GasMeter) -> Uint:
    """
    Empty the frame's state gas reservoir for a child frame.

    A child frame receives the parent's entire reservoir; there is no
    all-but-one-64th rule for state gas. The parent's reservoir is
    restored when the child returns.

    Parameters
    ----------
    gas_meter :
        The parent frame's gas meter.

    Returns
    -------
    reservoir : `ethereum.base_types.Uint`
        The state gas granted to the child frame.

    """
    reservoir = gas_meter.state_gas_left
    gas_meter.state_gas_left = Uint(0)
    return reservoir


def restore_child_gas(
    gas_meter: GasMeter, gas: Uint, state_gas_reservoir: Uint
) -> None:
    """
    Return a child frame's unused gas grant to the parent.

    Used when the child frame is never entered (for example, a stack
    depth or balance check fails): the withheld regular gas and drained
    reservoir are returned untouched.

    Parameters
    ----------
    gas_meter :
        The parent frame's gas meter.
    gas :
        The regular gas grant to return.
    state_gas_reservoir :
        The state gas reservoir to return.

    """
    gas_meter.gas_left += gas
    gas_meter.state_gas_left += state_gas_reservoir


def calculate_memory_gas_cost(size_in_bytes: Uint) -> Uint:
    """
    Calculates the gas cost for allocating memory
    to the smallest multiple of 32 bytes,
    such that the allocated size is at least as big as the given size.

    Parameters
    ----------
    size_in_bytes :
        The size of the data in bytes.

    Returns
    -------
    total_gas_cost : `ethereum.base_types.Uint`
        The gas cost for storing data in memory.

    """
    size_in_words = ceil32(size_in_bytes) // Uint(32)
    linear_cost = size_in_words * GasCosts.MEMORY_PER_WORD
    quadratic_cost = size_in_words ** Uint(2) // Uint(512)
    total_gas_cost = linear_cost + quadratic_cost
    try:
        return total_gas_cost
    except ValueError as e:
        raise OutOfGasError from e


def calculate_gas_extend_memory(
    memory: bytearray, extensions: List[Tuple[U256, U256]]
) -> ExtendMemory:
    """
    Calculates the gas amount to extend memory.

    Parameters
    ----------
    memory :
        Memory contents of the EVM.
    extensions:
        List of extensions to be made to the memory.
        Consists of a tuple of start position and size.

    Returns
    -------
    extend_memory: `ExtendMemory`

    """
    size_to_extend = Uint(0)
    to_be_paid = Uint(0)
    current_size = ulen(memory)
    for start_position, size in extensions:
        if size == 0:
            continue
        before_size = ceil32(current_size)
        after_size = ceil32(Uint(start_position) + Uint(size))
        if after_size <= before_size:
            continue

        size_to_extend += after_size - before_size
        already_paid = calculate_memory_gas_cost(before_size)
        total_cost = calculate_memory_gas_cost(after_size)
        to_be_paid += total_cost - already_paid

        current_size = after_size

    return ExtendMemory(to_be_paid, size_to_extend)


def calculate_message_call_gas(
    value: U256,
    gas: Uint,
    gas_left: Uint,
    memory_cost: Uint,
    extra_gas: Uint,
    call_stipend: Uint = GasCosts.CALL_STIPEND,
) -> MessageCallGas:
    """
    Calculates the MessageCallGas (cost and gas made available to the sub-call)
    for executing call Opcodes.

    Parameters
    ----------
    value:
        The amount of `ETH` that needs to be transferred.
    gas :
        The amount of gas provided to the message-call.
    gas_left :
        The amount of gas left in the current frame.
    memory_cost :
        The amount needed to extend the memory in the current frame.
    extra_gas :
        The amount of gas needed for transferring value + creating a new
        account inside a message call.
    call_stipend :
        The amount of stipend provided to a message call to execute code while
        transferring value (ETH).

    Returns
    -------
    message_call_gas: `MessageCallGas`

    """
    call_stipend = Uint(0) if value == 0 else call_stipend
    if gas_left < extra_gas + memory_cost:
        return MessageCallGas(gas + extra_gas, gas + call_stipend)

    gas = min(gas, max_message_call_gas(gas_left - memory_cost - extra_gas))

    return MessageCallGas(gas + extra_gas, gas + call_stipend)


def max_message_call_gas(gas: Uint) -> Uint:
    """
    Calculates the maximum gas that is allowed for making a message call.

    Parameters
    ----------
    gas :
        The amount of gas provided to the message-call.

    Returns
    -------
    max_allowed_message_call_gas: `ethereum.base_types.Uint`
        The maximum gas allowed for making the message-call.

    """
    return gas - (gas // Uint(64))


def init_code_cost(init_code_length: Uint) -> Uint:
    """
    Calculates the gas to be charged for the init code in CREATE*
    opcodes as well as create transactions.

    Parameters
    ----------
    init_code_length :
        The length of the init code provided to the opcode
        or a create transaction

    Returns
    -------
    init_code_gas: `ethereum.base_types.Uint`
        The gas to be charged for the init code.

    """
    return GasCosts.CODE_INIT_PER_WORD * ceil32(init_code_length) // Uint(32)


def calculate_excess_blob_gas(
    parent_header: Header | PreviousHeader,
) -> U64:
    """
    Calculates the excess blob gas for the current block based
    on the gas used in the parent block.

    Parameters
    ----------
    parent_header :
        The parent block of the current block.

    Returns
    -------
    excess_blob_gas: `ethereum.base_types.U64`
        The excess blob gas for the current block.

    """
    # At the fork block, these are defined as zero.
    excess_blob_gas = U64(0)
    blob_gas_used = U64(0)
    base_fee_per_gas = Uint(0)

    if isinstance(parent_header, Header):
        # After the fork block, read them from the parent header.
        excess_blob_gas = parent_header.excess_blob_gas
        blob_gas_used = parent_header.blob_gas_used
        base_fee_per_gas = parent_header.base_fee_per_gas

    parent_blob_gas = excess_blob_gas + blob_gas_used
    if parent_blob_gas < GasCosts.BLOB_TARGET_GAS_PER_BLOCK:
        return U64(0)

    target_blob_gas_price = Uint(GasCosts.PER_BLOB)
    target_blob_gas_price *= calculate_blob_gas_price(excess_blob_gas)

    base_blob_tx_price = GasCosts.BLOB_BASE_COST * base_fee_per_gas
    if base_blob_tx_price > target_blob_gas_price:
        blob_schedule_delta = (
            GasCosts.BLOB_SCHEDULE_MAX - GasCosts.BLOB_SCHEDULE_TARGET
        )
        return (
            excess_blob_gas
            + blob_gas_used * blob_schedule_delta // GasCosts.BLOB_SCHEDULE_MAX
        )

    return parent_blob_gas - GasCosts.BLOB_TARGET_GAS_PER_BLOCK


def calculate_total_blob_gas(tx: Transaction) -> U64:
    """
    Calculate the total blob gas for a transaction.

    Parameters
    ----------
    tx :
        The transaction for which the blob gas is to be calculated.

    Returns
    -------
    total_blob_gas: `ethereum.base_types.Uint`
        The total blob gas for the transaction.

    """
    if isinstance(tx, BlobTransaction):
        return GasCosts.PER_BLOB * U64(len(tx.blob_versioned_hashes))
    else:
        return U64(0)


def calculate_blob_gas_price(excess_blob_gas: U64) -> Uint:
    """
    Calculate the blob gasprice for a block.

    Parameters
    ----------
    excess_blob_gas :
        The excess blob gas for the block.

    Returns
    -------
    blob_gasprice: `Uint`
        The blob gasprice.

    """
    return taylor_exponential(
        GasCosts.BLOB_MIN_GASPRICE,
        Uint(excess_blob_gas),
        GasCosts.BLOB_BASE_FEE_UPDATE_FRACTION,
    )


def calculate_data_fee(excess_blob_gas: U64, tx: Transaction) -> Uint:
    """
    Calculate the blob data fee for a transaction.

    Parameters
    ----------
    excess_blob_gas :
        The excess_blob_gas for the execution.
    tx :
        The transaction for which the blob data fee is to be calculated.

    Returns
    -------
    data_fee: `Uint`
        The blob data fee.

    """
    return Uint(calculate_total_blob_gas(tx)) * calculate_blob_gas_price(
        excess_blob_gas
    )


@final
@dataclass
class ExecutionGasAllocation:
    """
    Split of a transaction's execution gas across the two dimensions.
    """

    regular_gas: Uint
    """Regular gas granted to the top frame, capped by the budget."""

    state_gas_reservoir: Uint
    """State gas set aside for the top frame's reservoir."""


def allocate_execution_gas(
    tx_gas: Uint, intrinsic: IntrinsicGasCost
) -> ExecutionGasAllocation:
    """
    Split execution gas into a regular grant and a state reservoir.

    After the intrinsic cost is removed, the remaining execution gas is
    divided into regular gas -- capped by the regular-gas budget that
    remains below `TX_MAX_GAS_LIMIT` -- and a state gas reservoir that
    holds whatever exceeds that cap.

    Only valid once `validate_transaction` has confirmed the transaction
    can afford its intrinsic cost, which guarantees the subtractions
    below do not underflow.

    Parameters
    ----------
    tx_gas :
        The transaction's gas limit.
    intrinsic :
        The transaction's intrinsic gas cost.

    Returns
    -------
    allocation : `ExecutionGasAllocation`
        The regular gas grant and state gas reservoir.

    """
    execution_gas = tx_gas - Uint(intrinsic.regular)
    regular_gas_budget = TX_MAX_GAS_LIMIT - intrinsic.regular
    regular_gas = min(regular_gas_budget, execution_gas)
    state_gas_reservoir = Uint(execution_gas - regular_gas)
    return ExecutionGasAllocation(regular_gas, state_gas_reservoir)


@final
@dataclass
class TransactionGasSettlement:
    """
    Settled gas amounts for a finished transaction.

    Hold only gas figures; the caller turns them into fee payments and
    block-accounting updates.
    """

    gas_used: Uint
    """Total gas charged to the sender, after refund and floor."""

    gas_left: Uint
    """Gas returned to the sender, priced at the effective gas price."""

    regular_gas_used: Uint
    """Regular gas the transaction contributes to the block total."""

    state_gas_used: Uint
    """State gas the transaction contributes to the block total."""


def settle_transaction_gas(
    tx_gas: Uint,
    intrinsic: IntrinsicGasCost,
    gas_left: Uint,
    state_gas_left: Uint,
    refund_counter: U256,
    state_gas_used: int,
) -> TransactionGasSettlement:
    """
    Settle a transaction's gas after execution.

    Compute, in order:

    - the gas used before refunds, from the gas limit less the regular
      gas and reservoir the top frame returned;
    - the refund, capped at one fifth of that pre-refund usage;
    - the gas used, taken as the larger of the post-refund usage and the
      calldata floor, so a transaction never pays below the floor; and
    - the per-dimension block amounts: the state gas used (clamped to
      zero, since refunds can drive it negative) and the regular gas
      used, which carries the floor because the floor binds the regular
      dimension. Unlike the sender-facing `gas_used`, it ignores
      refunds: block accounting counts pre-refund gas ([EIP-7778]).

    Parameters
    ----------
    tx_gas :
        The transaction's gas limit.
    intrinsic :
        The transaction's intrinsic gas cost.
    gas_left :
        Regular gas the top frame returned.
    state_gas_left :
        State gas reservoir the top frame returned.
    refund_counter :
        The refund the top frame accrued.
    state_gas_used :
        Net state gas the top frame consumed, possibly negative.

    Returns
    -------
    settlement : `TransactionGasSettlement`
        The settled gas amounts.

    [EIP-7778]: https://eips.ethereum.org/EIPS/eip-7778

    """
    gas_used_before_refund = tx_gas - gas_left - state_gas_left
    gas_refund = min(gas_used_before_refund // Uint(5), Uint(refund_counter))
    gas_used_after_refund = gas_used_before_refund - gas_refund
    gas_used = max(gas_used_after_refund, intrinsic.calldata_floor)

    settled_state_gas_used = Uint(max(0, state_gas_used))
    regular_gas_used = max(
        gas_used_before_refund - settled_state_gas_used,
        intrinsic.calldata_floor,
    )
    return TransactionGasSettlement(
        gas_used=gas_used,
        gas_left=tx_gas - gas_used,
        regular_gas_used=regular_gas_used,
        state_gas_used=settled_state_gas_used,
    )
