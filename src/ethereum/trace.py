"""
Defines the functions required for creating EVM traces during execution.

A _trace_ is a log of operations that took place during an event or period of
time. In the case of an EVM trace, the log is built from a series of
[`TraceEvent`]s emitted during the execution of a transaction.

Note that this module _does not_ contain a trace implementation. Instead, it
defines only the events that can be collected into a trace by some other
package. See [`EvmTracer`].

See [EIP-3155] for more details on EVM traces.

[`EvmTracer`]: ref:ethereum.trace.EvmTracer
[`TraceEvent`]: ref:ethereum.trace.TraceEvent
[EIP-3155]: https://eips.ethereum.org/EIPS/eip-3155
"""

import enum
from dataclasses import dataclass
from typing import Optional, Protocol, Union

from ethereum.exceptions import EthereumException


@dataclass
class TransactionStart:
    """
    Trace event that is triggered at the start of a transaction.
    """


@dataclass
class TransactionEnd:
    """
    Trace event that is triggered at the end of a transaction.
    """

    gas_used: int
    """
    Total gas consumed by this transaction.
    """

    output: bytes
    """
    Return value or revert reason of the outermost frame of execution.
    """

    error: Optional[EthereumException]
    """
    The exception, if any, that caused the transaction to fail.

    See [`ethereum.exceptions`] as well as fork-specific modules like
    [`ethereum.frontier.vm.exceptions`][vm] for details.

    [`ethereum.exceptions`]: ref:ethereum.exceptions
    [vm]: ref:ethereum.frontier.vm.exceptions
    """


@dataclass
class PrecompileStart:
    """
    Trace event that is triggered before executing a precompile.
    """

    address: bytes
    """
    Precompile that is about to be executed.
    """


@dataclass
class PrecompileEnd:
    """
    Trace event that is triggered after executing a precompile.
    """


@dataclass
class OpStart:
    """
    Trace event that is triggered before executing an opcode.
    """

    op: enum.Enum
    """
    Opcode that is about to be executed.

    Will be an instance of a fork-specific type like, for example,
    [`ethereum.frontier.vm.instructions.Ops`][ops].

    [ops]: ref:ethereum.frontier.vm.instructions.Ops
    """


@dataclass
class OpEnd:
    """
    Trace event that is triggered after executing an opcode.
    """


@dataclass
class OpException:
    """
    Trace event that is triggered when an opcode raises an exception.
    """

    error: Exception
    """
    Exception that was raised.

    See [`ethereum.exceptions`] as well as fork-specific modules like
    [`ethereum.frontier.vm.exceptions`][vm] for examples of exceptions that
    might be raised.

    [`ethereum.exceptions`]: ref:ethereum.exceptions
    [vm]: ref:ethereum.frontier.vm.exceptions
    """


@dataclass
class EvmStop:
    """
    Trace event that is triggered when the EVM stops.
    """

    op: enum.Enum
    """
    Last opcode executed.

    Will be an instance of a fork-specific type like, for example,
    [`ethereum.frontier.vm.instructions.Ops`][ops].

    [ops]: ref:ethereum.frontier.vm.instructions.Ops
    """


@dataclass
class GasAndRefund:
    """
    Trace event that is triggered when gas is deducted.
    """

    gas_cost: int
    """
    Amount of gas charged or refunded.
    """


TraceEvent = Union[
    TransactionStart,
    TransactionEnd,
    PrecompileStart,
    PrecompileEnd,
    OpStart,
    OpEnd,
    OpException,
    EvmStop,
    GasAndRefund,
]
"""
All possible types of events that an [`EvmTracer`] is expected to handle.

[`EvmTracer`]: ref:ethereum.trace.EvmTracer
"""


def discard_evm_trace(
    evm: object,
    event: TraceEvent,
    trace_memory: bool = False,
    trace_stack: bool = True,
    trace_return_data: bool = False,
) -> None:
    """
    An [`EvmTracer`] that discards all events.

    [`EvmTracer`]: ref:ethereum.trace.EvmTracer
    """


class EvmTracer(Protocol):
    """
    [`Protocol`] that describes tracer functions.

    See [`ethereum.trace`] for details about tracing in general, and
    [`__call__`] for more on how to implement a tracer.

    [`Protocol`]: https://docs.python.org/3/library/typing.html#typing.Protocol
    [`ethereum.trace`]: ref:ethereum.trace
    [`__call__`]: ref:ethereum.trace.EvmTracer.__call__
    """

    def __call__(
        self,
        evm: object,
        event: TraceEvent,
        /,
        trace_memory: bool = False,
        trace_stack: bool = True,
        trace_return_data: bool = False,
    ) -> None:
        """
        Call `self` as a function, recording a trace event.

        `evm` is the live state of the EVM, and will be a fork-specific type
        like [`ethereum.frontier.vm.Evm`][evm].

        `event`, a [`TraceEvent`], is the reason why the tracer was triggered.

        `trace_memory` requests a full memory dump in the resulting trace.

        `trace_stack` requests the full stack in the resulting trace.

        `trace_return_data` requests that return data be included in the
        resulting trace.

        See [`discard_evm_trace`] for an example function implementing this
        protocol.

        [`discard_evm_trace`]: ref:ethereum.trace.discard_evm_trace
        [evm]: ref:ethereum.frontier.vm.Evm
        [`TraceEvent`]: ref:ethereum.trace.TraceEvent
        """


evm_trace: EvmTracer = discard_evm_trace
"""
Active [`EvmTracer`] that is used for generating traces.

[`EvmTracer`]: ref:ethereum.trace.EvmTracer
"""
