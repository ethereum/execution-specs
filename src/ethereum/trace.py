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

from typing import Any


def capture_tx_start(env: Any) -> None:
    """
    Capture the state at the beginning of a transaction.
    """
    pass


def capture_tx_end(
    env: Any, gas_used: int, output: bytes, has_erred: bool
) -> None:
    """
    Capture the state at the end of a transaction.
    """
    pass


def capture_precompile_start(evm: Any, address: Any) -> None:
    """
    Create a new trace instance before precompile execution.
    """
    pass


def capture_precompile_end(evm: Any) -> None:
    """Capture the state at the end of a precompile execution."""
    pass


def capture_op_start(evm: Any, op: Any) -> None:
    """
    Create a new trace instance before opcode execution.
    """
    pass


def capture_op_end(evm: Any) -> None:
    """Capture the state at the end of an opcode execution."""
    pass


def capture_op_exception(evm: Any) -> None:
    """Capture the state in case of exceptions."""
    pass


def output_traces(
    traces: Any, tx_hash: bytes, output_basedir: str = "."
) -> None:
    """
    Output the traces to a json file.
    """
    pass


def capture_evm_stop(evm: Any, op: Any) -> None:
    """
    Capture the state at the end of an EVM execution.
    A stop opcode is captured.
    """
    pass


def capture_gas_and_refund(evm: Any, gas_cost: Any) -> None:
    """
    Capture the gas cost and refund during opcode execution.
    """
    pass
