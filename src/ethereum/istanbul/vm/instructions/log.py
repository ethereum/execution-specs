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

from ethereum.base_types import U256
from ethereum.utils.ensure import ensure

from ...eth_types import Log
from .. import Evm
from ..exceptions import WriteInStaticContext
from ..gas import GAS_LOG, GAS_LOG_DATA, GAS_LOG_TOPIC, charge_gas
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
    :py:class:`~ethereum.istanbul.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2 + num_topics`.
    """
    # STACK
    memory_start_index = pop(evm.stack)
    size = pop(evm.stack)

    topics = []
    for _ in range(num_topics):
        topic = pop(evm.stack).to_be_bytes32()
        topics.append(topic)

    # GAS
    extend_memory(evm, memory_start_index, size)
    charge_gas(evm, GAS_LOG + GAS_LOG_DATA * size + GAS_LOG_TOPIC * num_topics)

    # OPERATION
    ensure(not evm.message.is_static, WriteInStaticContext)
    log_entry = Log(
        address=evm.message.current_target,
        topics=tuple(topics),
        data=memory_read_bytes(evm.memory, memory_start_index, size),
    )

    evm.logs = evm.logs + (log_entry,)

    # PROGRAM COUNTER
    evm.pc += 1


log0 = partial(log_n, num_topics=0)
log1 = partial(log_n, num_topics=1)
log2 = partial(log_n, num_topics=2)
log3 = partial(log_n, num_topics=3)
log4 = partial(log_n, num_topics=4)
