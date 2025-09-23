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
    The class describes the EVM interface for pre-byzantium forks trace.
    """

    pc: Uint
    stack: list[U256]
    memory: bytearray
    code: Bytes
    gas_left: Uint
    refund_counter: int
    running: bool
    message: Message


@runtime_checkable
class EvmWithReturnData(Evm, Protocol):
    """
    The class describes the EVM interface for post-byzantium forks trace.
    """

    return_data: Bytes
