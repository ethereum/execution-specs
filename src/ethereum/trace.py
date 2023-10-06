"""
.. _trace:

EVM Trace
^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Defines the functions required for creating evm traces during execution.
"""

import enum
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class TransactionStart:
    """Trace event that is triggered at the start of a transaction."""

    pass


@dataclass
class TransactionEnd:
    """Trace event that is triggered at the end of a transaction."""

    gas_used: int
    output: bytes
    error: Optional[Exception]


@dataclass
class PrecompileStart:
    """Trace event that is triggered before executing a precompile."""

    address: bytes


@dataclass
class PrecompileEnd:
    """Trace event that is triggered after executing a precompile."""

    pass


@dataclass
class OpStart:
    """Trace event that is triggered before executing an opcode."""

    op: enum.Enum


@dataclass
class OpEnd:
    """Trace event that is triggered after executing an opcode."""

    pass


@dataclass
class OpException:
    """Trace event that is triggered when an opcode raises an exception."""

    error: Exception


@dataclass
class EvmStop:
    """Trace event that is triggered when the EVM stops."""

    op: enum.Enum


@dataclass
class GasAndRefund:
    """Trace event that is triggered when gas is deducted."""

    gas_cost: int


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


def evm_trace(
    evm: object,
    event: TraceEvent,
    trace_memory: bool = False,
    trace_stack: bool = True,
    trace_return_data: bool = False,
) -> None:
    """
    Create a trace of the event.
    """
    pass
