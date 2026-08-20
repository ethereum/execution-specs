"""
Protocol definitions for working with EVM trace events.
"""

from typing import Optional, Protocol, runtime_checkable

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint


@runtime_checkable
class TransactionEnvironment(Protocol):
    """
    The class implements the tx_env interface for trace.
    """

    index_in_block: Uint | None
    tx_hash: Bytes | None


@runtime_checkable
class Message(Protocol):
    """
    The class implements the message interface for trace.
    """

    depth: int
    tx_env: TransactionEnvironment
    parent_evm: Optional["Evm"]


@runtime_checkable
class Evm(Protocol):
    """
    The class describes the EVM interface common to every fork's trace.

    The message-scoped fields (`depth`, `tx_env`, `parent_evm`) are
    described by the `Message` protocol in this module. Older forks
    carry them on `evm.message`; forks that merge the message into the
    frame expose them on `evm` itself, so `evm` satisfies both
    protocols. Tracers resolve the carrier with
    `getattr(evm, "message", evm)`.
    """

    # TODO: Rethink the tracer interface so it does not probe
    # fork-specific frame layouts.

    pc: Uint
    stack: list[U256]
    memory: bytearray
    code: Bytes
    running: bool


@runtime_checkable
class StateGasReservoir(Protocol):
    """
    The class describes the state gas reservoir carried by the gas
    meters of single-gas-field transactions (EIP-8037).
    """

    state_gas_left: Uint


@runtime_checkable
class GasMeter(Protocol):
    """
    The class describes the gas meter of forks that bundle gas
    accounting into a dedicated object (EIP-8037). The reservoir is
    `None` for frame transactions (EIP-8141), whose state gas budgets
    are frame-scoped.
    """

    gas_left: Uint
    reservoir: StateGasReservoir | None
    refund_counter: int


@runtime_checkable
class EvmWithFlatGas(Evm, Protocol):
    """
    The class describes the EVM interface for forks that track gas in
    flat fields on the EVM itself.
    """

    gas_left: Uint
    refund_counter: int


@runtime_checkable
class EvmWithGasMeter(Evm, Protocol):
    """
    The class describes the EVM interface for forks that track gas in a
    dedicated gas meter (EIP-8037).
    """

    gas_meter: GasMeter


@runtime_checkable
class EvmWithReturnData(Evm, Protocol):
    """
    The class describes the EVM interface for post-byzantium forks trace.
    """

    return_data: Bytes


def evm_gas_left(evm: Evm) -> Uint:
    """
    Read the regular gas remaining, whichever gas layout the fork uses.
    """
    if isinstance(evm, EvmWithGasMeter):
        return evm.gas_meter.gas_left
    assert isinstance(evm, EvmWithFlatGas)
    return evm.gas_left


def evm_refund_counter(evm: Evm) -> int:
    """
    Read the refund counter, whichever gas layout the fork uses.
    """
    if isinstance(evm, EvmWithGasMeter):
        return evm.gas_meter.refund_counter
    assert isinstance(evm, EvmWithFlatGas)
    return evm.refund_counter


def evm_state_gas_left(evm: Evm) -> Uint | None:
    """
    Read the state gas remaining, or `None` for forks without state gas.

    Reads the meter's reservoir; a meter without one belongs to a frame
    transaction (EIP-8141), whose executing frame's state gas pool
    lives on the frame context instead.
    """
    if isinstance(evm, EvmWithGasMeter):
        reservoir = evm.gas_meter.reservoir
        if reservoir is not None:
            return reservoir.state_gas_left
        frame_context = getattr(
            getattr(evm, "tx_env", None), "frame_context", None
        )
        if frame_context is not None:
            return Uint(frame_context.state_gas_left)
    return None
