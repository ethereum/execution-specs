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

from ethereum.base_types import U256, Uint
from ethereum.utils.safe_arithmetic import u256_safe_add, u256_safe_multiply

from ...eth_types import Log
from .. import Evm
from ..exceptions import OutOfGasError
from ..gas import (
    GAS_LOG,
    GAS_LOG_DATA,
    GAS_LOG_TOPIC,
    calculate_gas_extend_memory,
    subtract_gas,
)
from ..memory import extend_memory, memory_read_bytes
from ..stack import pop


def log_n(evm: Evm, num_topics: U256) -> None:
    """
    Appends a log entry, having `num_topics` topics, to the evm logs.

    This will also expand the memory if the data (required by the log entry)
    corresponding to the memory is not accessible.

    Parameters
    ----------
    evm :
        The current EVM frame.
    num_topics :
        The number of topics to be included in the log entry.

    Raises
    ------
    :py:class:`~ethereum.homestead.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2 + num_topics`.
    """
    # Converting memory_start_index to Uint as memory_start_index + size - 1
    # can overflow U256.
    memory_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    gas_cost_log_data = u256_safe_multiply(
        GAS_LOG_DATA, size, exception_type=OutOfGasError
    )
    gas_cost_log_topic = u256_safe_multiply(
        GAS_LOG_TOPIC, num_topics, exception_type=OutOfGasError
    )
    gas_cost_memory_extend = calculate_gas_extend_memory(
        evm.memory, memory_start_index, size
    )
    gas_cost = u256_safe_add(
        GAS_LOG,
        gas_cost_log_data,
        gas_cost_log_topic,
        gas_cost_memory_extend,
        exception_type=OutOfGasError,
    )
    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    extend_memory(evm.memory, memory_start_index, size)

    topics = []
    for _ in range(num_topics):
        topic = pop(evm.stack).to_be_bytes32()
        topics.append(topic)

    log_entry = Log(
        address=evm.message.current_target,
        topics=tuple(topics),
        data=memory_read_bytes(evm.memory, memory_start_index, size),
    )

    evm.logs = evm.logs + (log_entry,)

    evm.pc += 1


log0 = partial(log_n, num_topics=0)
log1 = partial(log_n, num_topics=1)
log2 = partial(log_n, num_topics=2)
log3 = partial(log_n, num_topics=3)
log4 = partial(log_n, num_topics=4)
