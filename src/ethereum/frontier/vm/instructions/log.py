"""
Ethereum Virtual Machine (EVM) Logging Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM logging instructions.
"""
from functools import partial
from typing import List

from ethereum.base_types import U256
from ethereum.utils.safe_arithmetic import u256_safe_add, u256_safe_multiply

from ...eth_types import Log
from ...vm.error import OutOfGasError
from .. import Evm
from ..gas import GAS_LOG, GAS_LOG_DATA, GAS_LOG_TOPIC, subtract_gas
from ..memory import memory_read_bytes, touch_memory
from ..operation import Operation


def gas_log_n(
    num_topics: int, evm: Evm, stack: List[U256], *args: U256
) -> None:
    """
    Appends a log entry, having `num_topics` topics, to the evm logs.

    This will also expand the memory if the data (required by the log entry)
    corresponding to the memory is not accessible.
    """
    memory_start_index = args[-1]
    size = args[-2]

    gas_cost_log_data = u256_safe_multiply(
        GAS_LOG_DATA, size, exception_type=OutOfGasError
    )
    gas_cost_log_topic = u256_safe_multiply(
        GAS_LOG_TOPIC, U256(num_topics), exception_type=OutOfGasError
    )
    gas_cost = u256_safe_add(
        GAS_LOG,
        gas_cost_log_data,
        gas_cost_log_topic,
        exception_type=OutOfGasError,
    )
    subtract_gas(evm, gas_cost)
    touch_memory(evm, memory_start_index, size)


def do_log_n(
    num_topics: int, evm: Evm, stack: List[U256], *args: U256
) -> None:
    """
    Appends a log entry, having `num_topics` topics, to the evm logs.

    This will also expand the memory if the data (required by the log entry)
    corresponding to the memory is not accessible.
    """
    memory_start_index = args[-1]
    size = args[-2]
    topics = reversed(args[:-2])

    log_entry = Log(
        address=evm.message.current_target,
        topics=tuple((topic.to_be_bytes32() for topic in topics)),
        data=memory_read_bytes(evm, memory_start_index, size),
    )

    evm.logs = evm.logs + (log_entry,)


def log_n(num_topics: int) -> Operation:
    """
    Appends a log entry, having `num_topics` topics, to the evm logs.

    This will also expand the memory if the data (required by the log entry)
    corresponding to the memory is not accessible.
    """
    return Operation(
        partial(gas_log_n, num_topics),
        partial(do_log_n, num_topics),
        num_topics + 2,
        0,
    )
