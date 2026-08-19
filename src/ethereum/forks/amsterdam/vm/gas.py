"""
Ethereum Virtual Machine (EVM) Gas.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

EVM gas constants and calculators.
"""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, List, Optional, Tuple, final

from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.exceptions import GasUsedExceedsLimitError
from ethereum.forks.bpo5.blocks import Header as PreviousHeader
from ethereum.trace import GasAndRefund, StateGasAndRefund, evm_trace
from ethereum.utils.numeric import ceil32, taylor_exponential

from ..blocks import Header
from ..exceptions import (
    BlobGasLimitExceededError,
    InsufficientMaxFeePerBlobGasError,
)
from ..fork_types import (
    ExecutionGas,
    StateGas,
    StateGasPerByte,
    VersionedHash,
)
from ..transactions import (
    TX_MAX_GAS_LIMIT,
    BlobCapableTransaction,
    IntrinsicGasCost,
    Transaction,
)
from .exceptions import OutOfGasError

if TYPE_CHECKING:
    from . import BlockEnvironment, BlockOutput, Evm, FrameContext


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
    BASE: Final[ExecutionGas] = ExecutionGas(Uint(2))
    VERY_LOW: Final[ExecutionGas] = ExecutionGas(Uint(3))
    LOW: Final[ExecutionGas] = ExecutionGas(Uint(5))
    MID: Final[ExecutionGas] = ExecutionGas(Uint(8))
    HIGH: Final[ExecutionGas] = ExecutionGas(Uint(10))

    # Access
    WARM_ACCESS: Final[ExecutionGas] = ExecutionGas(Uint(100))
    COLD_ACCOUNT_ACCESS: Final[ExecutionGas] = ExecutionGas(Uint(3000))
    COLD_STORAGE_ACCESS: Final[ExecutionGas] = ExecutionGas(Uint(2100))

    # Storage
    STORAGE_WRITE: Final[ExecutionGas] = ExecutionGas(Uint(10000))

    # Call
    # ACCOUNT_WRITE + CALL_STIPEND
    CALL_VALUE: Final[ExecutionGas] = ExecutionGas(Uint(11300))
    CALL_STIPEND: Final[ExecutionGas] = ExecutionGas(Uint(2300))
    ACCOUNT_WRITE: Final[ExecutionGas] = ExecutionGas(Uint(9000))

    # Contract Creation
    CODE_DEPOSIT_PER_BYTE: Final[ExecutionGas] = ExecutionGas(Uint(200))
    CODE_INIT_PER_WORD: Final[ExecutionGas] = ExecutionGas(Uint(2))
    CREATE_ACCESS: Final[ExecutionGas] = ACCOUNT_WRITE + COLD_ACCOUNT_ACCESS

    # Utility
    ZERO: Final[ExecutionGas] = ExecutionGas(Uint(0))
    MEMORY_PER_WORD: Final[ExecutionGas] = ExecutionGas(Uint(3))
    FAST_STEP: Final[ExecutionGas] = ExecutionGas(Uint(5))

    # Refunds
    REFUND_STORAGE_CLEAR: Final[int] = int(
        (STORAGE_WRITE + COLD_STORAGE_ACCESS) * Uint(4800) // Uint(5000)
    )

    # Precompiles
    PRECOMPILE_ECRECOVER: Final[ExecutionGas] = ExecutionGas(Uint(3000))
    PRECOMPILE_P256VERIFY: Final[ExecutionGas] = ExecutionGas(Uint(6900))
    PRECOMPILE_SHA256_BASE: Final[ExecutionGas] = ExecutionGas(Uint(60))
    PRECOMPILE_SHA256_PER_WORD: Final[ExecutionGas] = ExecutionGas(Uint(12))
    PRECOMPILE_RIPEMD160_BASE: Final[ExecutionGas] = ExecutionGas(Uint(600))
    PRECOMPILE_RIPEMD160_PER_WORD: Final[ExecutionGas] = ExecutionGas(
        Uint(120)
    )
    PRECOMPILE_IDENTITY_BASE: Final[ExecutionGas] = ExecutionGas(Uint(15))
    PRECOMPILE_IDENTITY_PER_WORD: Final[ExecutionGas] = ExecutionGas(Uint(3))
    PRECOMPILE_BLAKE2F_PER_ROUND: Final[ExecutionGas] = ExecutionGas(Uint(1))
    PRECOMPILE_POINT_EVALUATION: Final[ExecutionGas] = ExecutionGas(
        Uint(50000)
    )
    PRECOMPILE_BLS_G1ADD: Final[ExecutionGas] = ExecutionGas(Uint(375))
    PRECOMPILE_BLS_G1MUL: Final[ExecutionGas] = ExecutionGas(Uint(12000))
    PRECOMPILE_BLS_G1MAP: Final[ExecutionGas] = ExecutionGas(Uint(5500))
    PRECOMPILE_BLS_G2ADD: Final[ExecutionGas] = ExecutionGas(Uint(600))
    PRECOMPILE_BLS_G2MUL: Final[ExecutionGas] = ExecutionGas(Uint(22500))
    PRECOMPILE_BLS_G2MAP: Final[ExecutionGas] = ExecutionGas(Uint(23800))
    PRECOMPILE_ECADD: Final[ExecutionGas] = ExecutionGas(Uint(150))
    PRECOMPILE_ECMUL: Final[ExecutionGas] = ExecutionGas(Uint(6000))
    PRECOMPILE_ECPAIRING_BASE: Final[ExecutionGas] = ExecutionGas(Uint(45000))
    PRECOMPILE_ECPAIRING_PER_POINT: Final[ExecutionGas] = ExecutionGas(
        Uint(34000)
    )

    # Blobs
    PER_BLOB: Final[U64] = U64(2**17)
    BLOB_SCHEDULE_TARGET: Final[U64] = U64(14)
    BLOB_TARGET_GAS_PER_BLOCK: Final[U64] = PER_BLOB * BLOB_SCHEDULE_TARGET
    BLOB_BASE_COST: Final[Uint] = Uint(2**13)
    BLOB_SCHEDULE_MAX: Final[U64] = U64(21)
    BLOB_MIN_GASPRICE: Final[Uint] = Uint(1)
    BLOB_BASE_FEE_UPDATE_FRACTION: Final[Uint] = Uint(11684671)

    # Block Access Lists
    BLOCK_ACCESS_LIST_ITEM: Final[ExecutionGas] = ExecutionGas(Uint(2000))

    # Transactions
    TX_BASE: Final[ExecutionGas] = ExecutionGas(Uint(12000))
    TX_CREATE: Final[ExecutionGas] = ExecutionGas(Uint(32000))
    TX_VALUE_COST: Final[ExecutionGas] = ExecutionGas(Uint(6000))
    TX_DATA_TOKEN_STANDARD: Final[ExecutionGas] = ExecutionGas(Uint(4))
    TX_DATA_TOKEN_FLOOR: Final[ExecutionGas] = ExecutionGas(Uint(16))
    TX_ACCESS_LIST_ADDRESS: Final[ExecutionGas] = (
        COLD_ACCOUNT_ACCESS - WARM_ACCESS
    )
    TX_ACCESS_LIST_STORAGE_KEY: Final[ExecutionGas] = (
        COLD_STORAGE_ACCESS - WARM_ACCESS
    )

    # Authorization
    AUTH_TUPLE_BYTES: Final[Uint] = Uint(101)
    EXECUTION_PER_AUTH_BASE_COST: Final[ExecutionGas] = ExecutionGas(
        AUTH_TUPLE_BYTES * TX_DATA_TOKEN_FLOOR
        + PRECOMPILE_ECRECOVER
        + COLD_ACCOUNT_ACCESS
        + Uint(2) * WARM_ACCESS
    )

    TX_FRAME_INTRINSIC: Final[Uint] = Uint(12000)
    """
    Base gas cost for [`FrameTransaction`][ftx]s, equal to [`TX_BASE`][tb].

    Frame transactions price signature recovery per signature entry, so
    the recovery component of the base cost instead covers payer
    settlement, which regular transactions do not price separately.

    [ftx]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameTransaction
    [tb]: ref:ethereum.forks.amsterdam.vm.gas.GasCosts.TX_BASE
    """  # noqa: E501

    TX_PER_FRAME: Final[Uint] = Uint(475)
    """
    Additional per-[`Frame`] gas cost for [`FrameTransaction`][ftx]s.

    [ftx]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameTransaction
    [`Frame`]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.Frame
    """  # noqa: E501

    # Frames
    FRAME_SIGNATURE_SCHEME_SECP256K1: Final[Uint] = Uint(2800)
    """
    Cost for verifying a [`SECP256K1`][s] signature in a
    [`FrameTransaction`][ftx].

    [s]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameSignatureScheme.SECP256K1
    [ftx]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameTransaction
    """  # noqa: E501

    FRAME_SIGNATURE_SCHEME_P256: Final[Uint] = Uint(6700)
    """
    Cost for verifying a [`P256`][s] signature in a [`FrameTransaction`][ftx].

    [s]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameSignatureScheme.P256
    [ftx]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameTransaction
    """  # noqa: E501

    FRAME_SIGNATURE_SCHEME_ARBITRARY: Final[Uint] = Uint(100)
    """
    Cost charged for an [`ARBITRARY`][s] signature entry in a
    [`FrameTransaction`][ftx]. The protocol does not cryptographically
    validate these entries; the charge covers making the bytes available
    for introspection.

    [s]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameSignatureScheme.ARBITRARY
    [ftx]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.FrameTransaction
    """  # noqa: E501

    # Block
    LIMIT_ADJUSTMENT_FACTOR: Final[Uint] = Uint(1024)
    LIMIT_MINIMUM: Final[Uint] = Uint(5000)

    # Static Opcodes
    OPCODE_ADD: Final[ExecutionGas] = VERY_LOW
    OPCODE_SUB: Final[ExecutionGas] = VERY_LOW
    OPCODE_MUL: Final[ExecutionGas] = LOW
    OPCODE_DIV: Final[ExecutionGas] = LOW
    OPCODE_SDIV: Final[ExecutionGas] = LOW
    OPCODE_MOD: Final[ExecutionGas] = LOW
    OPCODE_SMOD: Final[ExecutionGas] = LOW
    OPCODE_ADDMOD: Final[ExecutionGas] = MID
    OPCODE_MULMOD: Final[ExecutionGas] = MID
    OPCODE_SIGNEXTEND: Final[ExecutionGas] = LOW
    OPCODE_LT: Final[ExecutionGas] = VERY_LOW
    OPCODE_GT: Final[ExecutionGas] = VERY_LOW
    OPCODE_SLT: Final[ExecutionGas] = VERY_LOW
    OPCODE_SGT: Final[ExecutionGas] = VERY_LOW
    OPCODE_EQ: Final[ExecutionGas] = VERY_LOW
    OPCODE_ISZERO: Final[ExecutionGas] = VERY_LOW
    OPCODE_AND: Final[ExecutionGas] = VERY_LOW
    OPCODE_OR: Final[ExecutionGas] = VERY_LOW
    OPCODE_XOR: Final[ExecutionGas] = VERY_LOW
    OPCODE_NOT: Final[ExecutionGas] = VERY_LOW
    OPCODE_BYTE: Final[ExecutionGas] = VERY_LOW
    OPCODE_SHL: Final[ExecutionGas] = VERY_LOW
    OPCODE_SHR: Final[ExecutionGas] = VERY_LOW
    OPCODE_SAR: Final[ExecutionGas] = VERY_LOW
    OPCODE_CLZ: Final[ExecutionGas] = LOW
    OPCODE_JUMP: Final[ExecutionGas] = MID
    OPCODE_JUMPI: Final[ExecutionGas] = HIGH
    OPCODE_JUMPDEST: Final[ExecutionGas] = ExecutionGas(Uint(1))
    OPCODE_CALLDATALOAD: Final[ExecutionGas] = VERY_LOW
    OPCODE_BLOCKHASH: Final[ExecutionGas] = ExecutionGas(Uint(20))
    OPCODE_COINBASE: Final[ExecutionGas] = BASE
    OPCODE_POP: Final[ExecutionGas] = BASE
    OPCODE_MSIZE: Final[ExecutionGas] = BASE
    OPCODE_PC: Final[ExecutionGas] = BASE
    OPCODE_GAS: Final[ExecutionGas] = BASE
    OPCODE_ADDRESS: Final[ExecutionGas] = BASE
    OPCODE_ORIGIN: Final[ExecutionGas] = BASE
    OPCODE_CALLER: Final[ExecutionGas] = BASE
    OPCODE_CALLVALUE: Final[ExecutionGas] = BASE
    OPCODE_CALLDATASIZE: Final[ExecutionGas] = BASE
    OPCODE_CODESIZE: Final[ExecutionGas] = BASE
    OPCODE_GASPRICE: Final[ExecutionGas] = BASE
    OPCODE_TIMESTAMP: Final[ExecutionGas] = BASE
    OPCODE_NUMBER: Final[ExecutionGas] = BASE
    OPCODE_GASLIMIT: Final[ExecutionGas] = BASE
    OPCODE_PREVRANDAO: Final[ExecutionGas] = BASE
    OPCODE_RETURNDATASIZE: Final[ExecutionGas] = BASE
    OPCODE_CHAINID: Final[ExecutionGas] = BASE
    OPCODE_BASEFEE: Final[ExecutionGas] = BASE
    OPCODE_BLOBBASEFEE: Final[ExecutionGas] = BASE
    OPCODE_SLOTNUM: Final[ExecutionGas] = BASE
    OPCODE_BLOBHASH: Final[ExecutionGas] = ExecutionGas(Uint(3))
    OPCODE_PUSH: Final[ExecutionGas] = VERY_LOW
    OPCODE_PUSH0: Final[ExecutionGas] = BASE
    OPCODE_DUP: Final[ExecutionGas] = VERY_LOW
    OPCODE_SWAP: Final[ExecutionGas] = VERY_LOW
    OPCODE_DUPN: Final[ExecutionGas] = VERY_LOW
    OPCODE_SWAPN: Final[ExecutionGas] = VERY_LOW
    OPCODE_EXCHANGE: Final[ExecutionGas] = VERY_LOW
    OPCODE_TLOAD: Final[ExecutionGas] = ExecutionGas(Uint(100))
    OPCODE_TSTORE: Final[ExecutionGas] = ExecutionGas(Uint(100))
    OPCODE_TXPARAM: Final[ExecutionGas] = BASE
    OPCODE_FRAMEDATALOAD: Final[ExecutionGas] = VERY_LOW
    OPCODE_FRAMEPARAM: Final[ExecutionGas] = BASE
    OPCODE_SIGPARAM: Final[ExecutionGas] = BASE

    # Dynamic Opcode Components
    OPCODE_FRAMEDATACOPY_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_SIGDATACOPY_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_RETURNDATACOPY_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_RETURNDATACOPY_PER_WORD: Final[ExecutionGas] = ExecutionGas(Uint(3))
    OPCODE_CALLDATACOPY_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_CODECOPY_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_MCOPY_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_MLOAD_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_MSTORE_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_MSTORE8_BASE: Final[ExecutionGas] = VERY_LOW
    OPCODE_COPY_PER_WORD: Final[ExecutionGas] = ExecutionGas(Uint(3))
    OPCODE_EXP_BASE: Final[ExecutionGas] = ExecutionGas(Uint(10))
    OPCODE_EXP_PER_BYTE: Final[ExecutionGas] = ExecutionGas(Uint(50))
    OPCODE_KECCAK256_BASE: Final[ExecutionGas] = ExecutionGas(Uint(30))
    OPCODE_KECCAK256_PER_WORD: Final[ExecutionGas] = ExecutionGas(Uint(6))
    OPCODE_LOG_BASE: Final[ExecutionGas] = ExecutionGas(Uint(375))
    OPCODE_LOG_DATA_PER_BYTE: Final[ExecutionGas] = ExecutionGas(Uint(8))
    OPCODE_LOG_TOPIC: Final[ExecutionGas] = ExecutionGas(Uint(375))
    OPCODE_SELFDESTRUCT_BASE: Final[ExecutionGas] = ExecutionGas(Uint(5000))


MAX_BLOB_GAS_PER_BLOCK: Final[U64] = (
    GasCosts.BLOB_SCHEDULE_MAX * GasCosts.PER_BLOB
)


@final
@dataclass
class StateGasReservoir:
    """
    The state gas reservoir of [EIP-8037]'s single-gas-field model.

    Transaction types carrying one gas field cannot declare a state
    gas budget of their own; the gas above the transaction gas cap
    becomes a reservoir spendable only on state charges, which spill
    into execution gas once it empties. Frame transactions declare
    per-frame state budgets explicitly instead, and carry no
    reservoir: their meters hold `None` in place of this component.

    [EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
    """

    state_gas_left: StateGas
    """
    State gas still available in the frame's reservoir. Charges draw
    from here first and spill into the meter's `gas_left` once it is
    empty.
    """

    state_gas_baseline: StateGas
    """
    Reservoir level a rollback refills to: the frame's grant at entry,
    moved down by [`commit_state_gas`][commit] when charges become
    non-refillable.

    [commit]: ref:ethereum.forks.amsterdam.vm.gas.commit_state_gas
    """

    state_gas_spilled: StateGas = StateGas(Uint(0))
    """
    Execution gas spent covering state charges after the reservoir
    emptied. Credited back to the meter's `gas_left` first, in LIFO
    order, on a refund or failure. [EIP-8037] names this quantity
    `state_gas_from_gas_left`.

    [EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
    """

    state_gas_committed_spill: StateGas = StateGas(Uint(0))
    """
    [Spill] that [`commit_state_gas`][commit] marked non-refillable.
    It outlives the rollbacks [`restore_state_gas`][restore] performs;
    only [`restore_state_gas_to_entry`][entry] credits it back to
    `gas_left`. Committed reservoir draw needs no counter of its own:
    each commit lowers the baseline, so it is the frame's grant minus
    `state_gas_baseline`.

    [Spill]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_spilled
    [commit]: ref:ethereum.forks.amsterdam.vm.gas.commit_state_gas
    [restore]: ref:ethereum.forks.amsterdam.vm.gas.restore_state_gas
    [entry]: ref:ethereum.forks.amsterdam.vm.gas.restore_state_gas_to_entry
    """  # noqa: E501


@final
@dataclass
class GasMeter:
    """
    Track a frame's gas consumption across both gas dimensions.

    Bundle every mutable gas quantity a frame maintains, so the frame
    and its settlement work against one object instead of a scatter of
    fields on the [`Evm`].

    The execution dimension (`gas_left`, `refund_counter`) serves every
    transaction type. The state dimension depends on the transaction's
    model: single-gas-field transactions carry a
    [`StateGasReservoir`][r], while frame transactions carry `None`
    here and draw state gas from their frame's explicit budget on the
    frame context instead.

    [`Evm`]: ref:ethereum.forks.amsterdam.vm.Evm
    [r]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir
    """

    gas_left: ExecutionGas
    """
    Gas still available from the frame's execution-gas grant. Pays
    execution-gas charges, and state charges as [spill] once a carried
    reservoir empties.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_spilled
    """  # noqa: E501

    reservoir: Optional[StateGasReservoir]
    """
    The state gas reservoir, for transaction types whose single gas
    field funds both dimensions; `None` for frame transactions, whose
    state budgets are explicit and frame-scoped.
    """

    refund_counter: int = 0
    """Gas eligible for refund at the end of the transaction."""


@final
@dataclass
class ExtendMemory:
    """
    Define the parameters for memory extension in opcodes.

    `cost`: `ExecutionGas`
        The gas required to perform the extension
    `expand_by`: `ethereum.base_types.Uint`
        The size by which the memory will be extended
    """

    cost: ExecutionGas
    expand_by: Uint


@final
@dataclass
class MessageCallGas:
    """
    Define the gas cost and gas given to the sub-call for executing the call
    opcodes.

    `cost`: `ExecutionGas`
        The gas required to execute the call opcode, excludes
        memory expansion costs.
    `sub_call`: `ExecutionGas`
        The portion of gas available to sub-calls that is refundable
        if not consumed.
    """

    cost: ExecutionGas
    sub_call: ExecutionGas


def check_gas(evm: "Evm", amount: ExecutionGas) -> None:
    """
    Checks if `amount` gas is available without charging it.
    Raises OutOfGasError if insufficient gas.

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of execution gas to check.

    """
    if evm.gas_meter.gas_left < amount:
        raise OutOfGasError


def charge_gas_from_meter(gas_meter: GasMeter, amount: ExecutionGas) -> None:
    """
    Subtracts `amount` from `gas_left` (execution gas).

    Parameters
    ----------
    gas_meter :
        The gas meter.
    amount :
        The amount of execution gas the current operation requires.

    """
    if gas_meter.gas_left < amount:
        raise OutOfGasError
    gas_meter.gas_left -= amount


def charge_gas(evm: "Evm", amount: ExecutionGas) -> None:
    """
    Subtracts `amount` from `gas_left` (execution gas).

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of execution gas the current operation requires.

    """
    evm_trace(evm, GasAndRefund(int(amount)))

    charge_gas_from_meter(evm.gas_meter, amount)


def charge_state_gas_from_meter(gas_meter: GasMeter, amount: StateGas) -> None:
    """
    Subtracts `amount` from the state gas reservoir, then from
    `gas_left` when the reservoir is empty, tracking any [spill].

    Reservoir-model only: the meter must carry a reservoir. Frame
    transactions charge state gas against their frame's explicit
    budget through `charge_state_gas` instead.

    Parameters
    ----------
    gas_meter :
        The gas meter.
    amount :
        The amount of state gas the current operation requires.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_spilled

    """  # noqa: E501
    reservoir = gas_meter.reservoir
    assert reservoir is not None

    if reservoir.state_gas_left >= amount:
        reservoir.state_gas_left -= amount
    elif Uint(reservoir.state_gas_left) + Uint(gas_meter.gas_left) >= amount:
        remainder = amount - reservoir.state_gas_left
        reservoir.state_gas_left = StateGas(Uint(0))
        gas_meter.gas_left = ExecutionGas(gas_meter.gas_left - Uint(remainder))
        reservoir.state_gas_spilled += remainder
    else:
        raise OutOfGasError


def charge_frame_state_gas(
    frame_context: "FrameContext", amount: StateGas
) -> None:
    """
    Subtracts `amount` from the executing frame's state gas pool.

    The pool is the only source of state gas within a frame
    transaction: execution gas can never fund state charges, so a
    charge exceeding the pool is an exceptional halt of the current
    call frame, with ordinary out-of-gas semantics.

    Parameters
    ----------
    frame_context :
        The frame transaction's context.
    amount :
        The amount of state gas the current operation requires.

    """
    if frame_context.state_gas_left < amount:
        raise OutOfGasError
    frame_context.state_gas_left -= amount


def credit_frame_state_gas_refund(
    frame_context: "FrameContext", owner: Uint, amount: StateGas
) -> None:
    """
    Credit a state gas refund to the frame that paid the charge, within
    a frame transaction.

    The refund lowers the owner's attributed state gas: back into the
    executing frame's own pool when it is the owner — a frame's
    refunds can never exceed its own charges, so the pool never
    exceeds the frame's budget — or out of the owner's receipt
    otherwise, returning the amount to the payer at settlement without
    granting the executing frame budget it never declared.

    The caller identifies the owner: the frame recorded in the
    outstanding-charge ownership map for a storage slot refill, or the
    executing frame itself when undoing a charge it just paid for an
    account creation that failed or never happened.

    Parameters
    ----------
    frame_context :
        The frame transaction's context.
    owner :
        Index of the frame that paid the charge.
    amount :
        The amount of state gas the original charge paid.

    """
    if owner == frame_context.current_frame_index:
        frame_context.state_gas_left += amount
        # A refund only ever undoes a charge, so the pool never
        # exceeds the frame's declared budget.
        frame = frame_context.tx.frames[int(owner)]
        assert frame_context.state_gas_left <= Uint(frame.gas_limits.state)
    else:
        receipt = frame_context.frame_receipts[int(owner)]
        frame_context.frame_receipts[int(owner)] = replace(
            receipt,
            gas_used=replace(
                receipt.gas_used,
                state=receipt.gas_used.state - Uint(amount),
            ),
        )


def charge_state_gas(evm: "Evm", amount: StateGas) -> None:
    """
    Charge `amount` of state gas to the transaction's state gas
    source.

    This is the junction between the two state gas models: a frame
    transaction draws from the executing frame's declared pool, while
    every other transaction type draws from its meter's reservoir,
    spilling into `gas_left` once the reservoir is empty.

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of state gas the current operation requires.

    """
    evm_trace(evm, StateGasAndRefund(int(amount)))

    frame_context = evm.tx_env.frame_context
    if frame_context is None:
        charge_state_gas_from_meter(evm.gas_meter, amount)
    else:
        charge_frame_state_gas(frame_context, amount)


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
    reservoir = gas_meter.reservoir
    assert reservoir is not None

    # Only charges precede a commit, so no refund has pushed the
    # reservoir above the baseline: a commit only ever lowers it.
    assert reservoir.state_gas_left <= reservoir.state_gas_baseline
    reservoir.state_gas_committed_spill += reservoir.state_gas_spilled
    reservoir.state_gas_baseline = reservoir.state_gas_left
    reservoir.state_gas_spilled = StateGas(Uint(0))


def restore_state_gas(gas_meter: GasMeter) -> None:
    """
    Roll a failing frame's state gas back on revert or halt.

    The frame's state changes are undone, so the state gas consumed on
    them is credited back. With a reservoir, in LIFO order: the
    [spill] returns to `gas_left` first, then the reservoir resets to
    the [baseline]; state gas committed as non-refillable stays
    charged. A frame transaction's meter carries no reservoir — its
    pool and attribution roll back with the transaction state, through
    the frame-context snapshot taken alongside the state snapshot — so
    there is nothing to restore on the meter. In both models the
    refunds accrued on the undone changes are discarded with them.

    Parameters
    ----------
    gas_meter :
        The frame's gas meter.

    [baseline]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_baseline
    [spill]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_spilled

    """  # noqa: E501
    reservoir = gas_meter.reservoir
    if reservoir is not None:
        gas_meter.gas_left = ExecutionGas(
            gas_meter.gas_left + Uint(reservoir.state_gas_spilled)
        )
        reservoir.state_gas_spilled = StateGas(Uint(0))
        reservoir.state_gas_left = reservoir.state_gas_baseline
    gas_meter.refund_counter = 0


def restore_state_gas_to_entry(
    gas_meter: GasMeter, state_gas_reservoir: StateGas
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
    [grant]: ref:ethereum.forks.amsterdam.vm.TransactionEnvironment.state_gas_reservoir

    """  # noqa: E501
    reservoir = gas_meter.reservoir
    assert reservoir is not None

    # The baseline starts at the grant and only ever moves down.
    assert reservoir.state_gas_baseline <= state_gas_reservoir
    # Only pre-dispatch failures roll back to entry, and no refund
    # accrues before dispatch.
    assert gas_meter.refund_counter == 0
    gas_meter.gas_left = ExecutionGas(
        gas_meter.gas_left
        + Uint(reservoir.state_gas_spilled)
        + Uint(reservoir.state_gas_committed_spill)
    )
    reservoir.state_gas_spilled = StateGas(Uint(0))
    reservoir.state_gas_committed_spill = StateGas(Uint(0))
    reservoir.state_gas_left = state_gas_reservoir
    reservoir.state_gas_baseline = state_gas_reservoir


def tx_state_gas_used(
    gas_meter: GasMeter, state_gas_reservoir: StateGas
) -> int:
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

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_spilled

    """  # noqa: E501
    reservoir = gas_meter.reservoir
    assert reservoir is not None

    # The baseline starts at the grant and only ever moves down.
    assert reservoir.state_gas_baseline <= state_gas_reservoir
    return (
        int(state_gas_reservoir)
        - int(reservoir.state_gas_left)
        + int(reservoir.state_gas_spilled)
        + int(reservoir.state_gas_committed_spill)
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

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_spilled

    """  # noqa: E501
    reservoir = gas_meter.reservoir
    assert reservoir is not None

    from_gas_left = min(amount, reservoir.state_gas_spilled)
    gas_meter.gas_left = ExecutionGas(gas_meter.gas_left + Uint(from_gas_left))
    reservoir.state_gas_spilled -= from_gas_left
    reservoir.state_gas_left += amount - from_gas_left


def forfeit_remaining_gas(gas_meter: GasMeter) -> None:
    """
    Consume all remaining execution gas on an exceptional halt.

    Parameters
    ----------
    gas_meter :
        The halted frame's gas meter.

    """
    if gas_meter.reservoir is not None:
        # A rollback owes any outstanding spill back to `gas_left`; it
        # must be restored before the remainder burns.
        assert gas_meter.reservoir.state_gas_spilled == Uint(0)
    gas_meter.gas_left = ExecutionGas(Uint(0))


def withhold_create_gas(gas_meter: GasMeter) -> ExecutionGas:
    """
    Withhold and return the gas made available to a `CREATE*` child.

    Deduct the all-but-one-64th share from the frame's `gas_left` and
    return it as the child frame's execution-gas grant.

    Parameters
    ----------
    gas_meter :
        The creating frame's gas meter.

    Returns
    -------
    child_gas : `ExecutionGas`
        The execution gas granted to the child frame.

    """
    child_gas = max_message_call_gas(gas_meter.gas_left)
    gas_meter.gas_left -= child_gas
    return child_gas


def drain_state_gas_reservoir(gas_meter: GasMeter) -> StateGas:
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
    reservoir : `StateGas`
        The state gas granted to the child frame.

    """
    reservoir = gas_meter.reservoir
    assert reservoir is not None

    drained = reservoir.state_gas_left
    reservoir.state_gas_left = StateGas(Uint(0))
    return drained


def restore_child_gas(gas_meter: GasMeter, gas: ExecutionGas) -> None:
    """
    Return a child frame's unused execution gas grant to the parent.

    Used when the child frame is never entered (for example, a stack
    depth or balance check fails): the withheld execution gas is
    returned untouched. The state dimension needs no restoring, since
    it is handed down only after the preflight checks pass.

    Parameters
    ----------
    gas_meter :
        The parent frame's gas meter.
    gas :
        The execution gas grant to return.

    """
    gas_meter.gas_left += gas


def calculate_memory_gas_cost(size_in_bytes: Uint) -> ExecutionGas:
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
    total_gas_cost : `ExecutionGas`
        The gas cost for storing data in memory.

    """
    size_in_words = ceil32(size_in_bytes) // Uint(32)
    linear_cost = size_in_words * GasCosts.MEMORY_PER_WORD
    quadratic_cost = size_in_words ** Uint(2) // Uint(512)
    total_gas_cost = linear_cost + quadratic_cost
    try:
        return ExecutionGas(total_gas_cost)
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
    to_be_paid = GasCosts.ZERO
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
    gas: ExecutionGas,
    gas_left: ExecutionGas,
    memory_cost: ExecutionGas,
    extra_gas: ExecutionGas,
    call_stipend: ExecutionGas = GasCosts.CALL_STIPEND,
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
    call_stipend = GasCosts.ZERO if value == 0 else call_stipend
    if gas_left < extra_gas + memory_cost:
        return MessageCallGas(gas + extra_gas, gas + call_stipend)

    gas = min(gas, max_message_call_gas(gas_left - memory_cost - extra_gas))

    return MessageCallGas(gas + extra_gas, gas + call_stipend)


def max_message_call_gas(gas: ExecutionGas) -> ExecutionGas:
    """
    Calculates the maximum gas that is allowed for making a message call.

    Parameters
    ----------
    gas :
        The amount of gas provided to the message-call.

    Returns
    -------
    max_allowed_message_call_gas: `ExecutionGas`
        The maximum gas allowed for making the message-call.

    """
    return ExecutionGas(gas - (gas // Uint(64)))


def init_code_cost(init_code_length: Uint) -> ExecutionGas:
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
    init_code_gas: `ExecutionGas`
        The gas to be charged for the init code.

    """
    return ExecutionGas(
        GasCosts.CODE_INIT_PER_WORD * ceil32(init_code_length) // Uint(32)
    )


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
    # Defaults for a parent without blob gas fields.
    excess_blob_gas = U64(0)
    blob_gas_used = U64(0)
    base_fee_per_gas = Uint(0)

    if isinstance(parent_header, (Header, PreviousHeader)):
        # Read them from any parent that carries the fields, so
        # accumulated excess blob gas survives a fork transition.
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
    if isinstance(tx, BlobCapableTransaction):
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


def check_max_fee_per_blob_gas(
    blob_versioned_hashes: Tuple[VersionedHash, ...],
    max_fee_per_blob_gas: U256,
    excess_blob_gas: U64,
) -> None:
    """
    Check that a transaction carrying blobs pays at least the blob gas
    price.

    A transaction without blobs pays no blob fee, so its fee cap is not
    checked.

    Parameters
    ----------
    blob_versioned_hashes :
        The transaction's blob versioned hashes.
    max_fee_per_blob_gas :
        The transaction's fee cap per unit of blob gas.
    excess_blob_gas :
        The block's excess blob gas.

    Raises
    ------
    InsufficientMaxFeePerBlobGasError :
        If the fee cap does not cover the blob gas price.

    """
    if not blob_versioned_hashes:
        return

    blob_gas_price = calculate_blob_gas_price(excess_blob_gas)
    if Uint(max_fee_per_blob_gas) < blob_gas_price:
        raise InsufficientMaxFeePerBlobGasError(
            "insufficient max fee per blob gas"
        )


def check_block_gas_capacity(
    block_env: "BlockEnvironment",
    block_output: "BlockOutput",
    execution_reservation: Uint,
    state_reservation: Uint,
    tx_blob_gas: U64,
) -> None:
    """
    Check that the transaction fits the block's remaining gas capacity.

    Each dimension is checked against its own remaining budget:
    execution gas, state gas, and blob gas. The caller supplies the
    gas the transaction reserves in each dimension: exact per-frame
    budgets for a frame transaction, while the reservoir model of the
    regular flow reserves the whole gas limit in both dimensions.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    block_output :
        The block output for the current block.
    execution_reservation :
        The execution gas the transaction reserves.
    state_reservation :
        The state gas the transaction reserves.
    tx_blob_gas :
        The blob gas used by the transaction.

    Raises
    ------
    GasUsedExceedsLimitError :
        If the transaction exceeds the block's remaining execution or
        state gas.
    BlobGasLimitExceededError :
        If the transaction exceeds the block's remaining blob gas.

    """
    execution_gas_available = (
        block_env.block_gas_limit - block_output.block_gas_used
    )
    state_gas_available = (
        block_env.block_gas_limit - block_output.block_state_gas_used
    )
    blob_gas_available = MAX_BLOB_GAS_PER_BLOCK - block_output.blob_gas_used

    if execution_reservation > execution_gas_available:
        raise GasUsedExceedsLimitError("execution gas used exceeds limit")

    if state_reservation > state_gas_available:
        raise GasUsedExceedsLimitError("state gas used exceeds limit")

    if tx_blob_gas > blob_gas_available:
        raise BlobGasLimitExceededError("blob gas limit exceeded")


@final
@dataclass
class EvmGasAllocation:
    """
    Split of a transaction's EVM gas across the two dimensions.
    """

    execution_gas: ExecutionGas
    """Execution gas granted to the top frame, capped by the budget."""

    state_gas_reservoir: StateGas
    """State gas set aside for the top frame's reservoir."""


def allocate_evm_gas(
    tx_gas: Uint, intrinsic: IntrinsicGasCost
) -> EvmGasAllocation:
    """
    Split EVM gas into an execution-gas grant and a state reservoir.

    After the intrinsic cost is removed, the remaining EVM gas is
    divided into execution gas -- capped by the execution-gas budget
    that remains below `TX_MAX_GAS_LIMIT` -- and a state gas reservoir
    that holds whatever exceeds that cap.

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
    allocation : `EvmGasAllocation`
        The execution gas grant and state gas reservoir.

    """
    evm_gas = tx_gas - Uint(intrinsic.execution)
    execution_gas_budget = TX_MAX_GAS_LIMIT - intrinsic.execution
    execution_gas = ExecutionGas(min(execution_gas_budget, evm_gas))
    state_gas_reservoir = StateGas(evm_gas - execution_gas)
    return EvmGasAllocation(execution_gas, state_gas_reservoir)


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

    execution_gas_used: ExecutionGas
    """Execution gas the transaction contributes to the block total."""

    state_gas_used: StateGas
    """State gas the transaction contributes to the block total."""


def settle_transaction_gas(
    tx_gas: Uint,
    calldata_floor: Uint,
    gas_left: ExecutionGas,
    state_gas_left: StateGas,
    refund_counter: U256,
    state_gas_used: int,
) -> TransactionGasSettlement:
    """
    Settle a transaction's gas after execution.

    Compute, in order:

    - the gas used before refunds, from the gas limit less the
      execution gas and reservoir the top frame returned;
    - the refund, capped at one fifth of that pre-refund usage;
    - the gas used, taken as the larger of the post-refund usage and the
      calldata floor, so a transaction never pays below the floor; and
    - the per-dimension block amounts: the state gas used (clamped to
      zero, since refunds can drive it negative) and the execution gas
      used, which carries the floor because the floor binds the
      execution dimension. Unlike the sender-facing `gas_used`, it
      ignores refunds: block accounting counts pre-refund gas
      ([EIP-7778]).

    Parameters
    ----------
    tx_gas :
        The transaction's gas limit.
    calldata_floor :
        The transaction's calldata floor gas.
    gas_left :
        Execution gas the top frame returned.
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
    gas_used = max(gas_used_after_refund, calldata_floor)

    settled_state_gas_used = StateGas(Uint(max(0, state_gas_used)))
    execution_gas_used = ExecutionGas(
        max(
            gas_used_before_refund - settled_state_gas_used,
            calldata_floor,
        )
    )
    return TransactionGasSettlement(
        gas_used=gas_used,
        gas_left=tx_gas - gas_used,
        execution_gas_used=execution_gas_used,
        state_gas_used=settled_state_gas_used,
    )


@final
@dataclass
class FrameTransactionGasSettlement:
    """
    Settled per-dimension gas for a finished frame transaction.

    Hold only the two block-accounted dimensions; their sum is the
    transaction's `gas_used`, derived by the caller.
    """

    execution_gas_used: ExecutionGas
    """Execution gas the transaction contributes to the block total."""

    state_gas_used: StateGas
    """State gas the transaction contributes to the block total."""


def settle_frame_transaction_gas(
    standard_gas_limit: Uint,
    calldata_floor: Uint,
    tx_unused_gas: Uint,
    refund_counter: U256,
    tx_state_gas: StateGas,
) -> FrameTransactionGasSettlement:
    """
    Settle a frame transaction's gas after all frames have executed.

    Compute, in order:

    - the gas used before refunds, from the settlement anchor less the
      gas not charged at settlement;
    - the storage refund, capped at one fifth of the pre-refund usage
      ([EIP-3529]) — state gas refills bypass the cap by design: a
      refill reverses a charge for state that was never durably
      created, and has already reduced the owning frame's receipt, and
      with it the pre-refund usage; and
    - the execution dimension, as the post-refund usage less the final
      attributed state gas, held to the calldata floor ([EIP-7623]).
      The floor binds the execution dimension alone, so — unlike the
      regular flow — a floor-bound transaction pays the floor plus its
      state gas in full.

    The refund cap of a state-dominated transaction can exceed its
    intrinsic cost plus execution usage, driving the subtraction
    negative, so it is computed in plain integers before the floor
    clamps it.

    Parameters
    ----------
    standard_gas_limit :
        The transaction's settlement anchor: intrinsic cost plus the
        frames' budgets in both dimensions.
    calldata_floor :
        The transaction's calldata floor gas.
    tx_unused_gas :
        Gas not charged at settlement, over both dimensions: gas left
        in the frames' pools at frame exit, skipped-frame budgets, and
        state gas removed from a receipt by a later refill or
        rollback.
    refund_counter :
        The storage refund accrued across all frames.
    tx_state_gas :
        The frames' final attributed state gas: the sum of their
        receipts' state gas usage.

    Returns
    -------
    settlement : `FrameTransactionGasSettlement`
        The settled per-dimension gas.

    [EIP-3529]: https://eips.ethereum.org/EIPS/eip-3529
    [EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623

    """
    gas_used_before_refund = standard_gas_limit - tx_unused_gas
    applied_refund = min(
        Uint(refund_counter), gas_used_before_refund // Uint(5)
    )
    gas_used_after_refund = gas_used_before_refund - applied_refund

    execution_gas_used = ExecutionGas(
        Uint(
            max(
                int(gas_used_after_refund) - int(tx_state_gas),
                int(calldata_floor),
            )
        )
    )
    return FrameTransactionGasSettlement(
        execution_gas_used=execution_gas_used,
        state_gas_used=tx_state_gas,
    )
