"""
Test LOG0-LOG4 over memory ranges and topic values from a sub-call.

Ported from:
state_tests/stLogTests/log0_emptyMemFiller.json
state_tests/stLogTests/log0_logMemStartTooHighFiller.json
state_tests/stLogTests/log0_logMemsizeTooHighFiller.json
state_tests/stLogTests/log0_logMemsizeZeroFiller.json
state_tests/stLogTests/log0_nonEmptyMemFiller.json
state_tests/stLogTests/log0_nonEmptyMem_logMemSize1Filler.json
state_tests/stLogTests/log0_nonEmptyMem_logMemSize1_logMemStart31Filler.json
state_tests/stLogTests/log1_CallerFiller.json
state_tests/stLogTests/log1_MaxTopicFiller.json
state_tests/stLogTests/log1_emptyMemFiller.json
state_tests/stLogTests/log1_logMemStartTooHighFiller.json
state_tests/stLogTests/log1_logMemsizeTooHighFiller.json
state_tests/stLogTests/log1_logMemsizeZeroFiller.json
state_tests/stLogTests/log1_nonEmptyMemFiller.json
state_tests/stLogTests/log1_nonEmptyMem_logMemSize1Filler.json
state_tests/stLogTests/log1_nonEmptyMem_logMemSize1_logMemStart31Filler.json
state_tests/stLogTests/log2_CallerFiller.json
state_tests/stLogTests/log2_MaxTopicFiller.json
state_tests/stLogTests/log2_emptyMemFiller.json
state_tests/stLogTests/log2_logMemStartTooHighFiller.json
state_tests/stLogTests/log2_logMemsizeTooHighFiller.json
state_tests/stLogTests/log2_logMemsizeZeroFiller.json
state_tests/stLogTests/log2_nonEmptyMemFiller.json
state_tests/stLogTests/log2_nonEmptyMem_logMemSize1Filler.json
state_tests/stLogTests/log2_nonEmptyMem_logMemSize1_logMemStart31Filler.json
state_tests/stLogTests/log3_CallerFiller.json
state_tests/stLogTests/log3_MaxTopicFiller.json
state_tests/stLogTests/log3_PCFiller.json
state_tests/stLogTests/log3_emptyMemFiller.json
state_tests/stLogTests/log3_logMemStartTooHighFiller.json
state_tests/stLogTests/log3_logMemsizeTooHighFiller.json
state_tests/stLogTests/log3_logMemsizeZeroFiller.json
state_tests/stLogTests/log3_nonEmptyMemFiller.json
state_tests/stLogTests/log3_nonEmptyMem_logMemSize1Filler.json
state_tests/stLogTests/log3_nonEmptyMem_logMemSize1_logMemStart31Filler.json
state_tests/stLogTests/log4_CallerFiller.json
state_tests/stLogTests/log4_MaxTopicFiller.json
state_tests/stLogTests/log4_PCFiller.json
state_tests/stLogTests/log4_emptyMemFiller.json
state_tests/stLogTests/log4_logMemStartTooHighFiller.json
state_tests/stLogTests/log4_logMemsizeTooHighFiller.json
state_tests/stLogTests/log4_logMemsizeZeroFiller.json
state_tests/stLogTests/log4_nonEmptyMemFiller.json
state_tests/stLogTests/log4_nonEmptyMem_logMemSize1Filler.json
state_tests/stLogTests/log4_nonEmptyMem_logMemSize1_logMemStart31Filler.json
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CANARY = 0xC0DE
MAX_WORD = 2**256 - 1
MEMORY_WORD = (
    0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD
)
LOG_OPCODES = [Op.LOG0, Op.LOG1, Op.LOG2, Op.LOG3, Op.LOG4]
CASES_WITHOUT_TOPICS = [
    "empty_mem",
    "log_mem_start_too_high",
    "log_memsize_too_high",
    "log_memsize_zero",
    "non_empty_mem",
    "non_empty_mem_log_mem_size1",
    "non_empty_mem_log_mem_size1_log_mem_start31",
]
CASES_WITH_TOPICS = ["max_topic", "caller", "pc"]


def logger_code(topic_count: int, case: str) -> Bytecode:
    """Return the logger code for a case."""
    topics: List[int | Bytecode] = [0] * topic_count
    memory = Op.MSTORE(offset=0, value=MEMORY_WORD)
    offset, size = 0, 32
    if case == "empty_mem":
        memory, size = Bytecode(), 0
    elif case == "log_mem_start_too_high":
        offset, size = MAX_WORD, 1
    elif case == "log_memsize_too_high":
        offset, size = 1, MAX_WORD
    elif case == "log_memsize_zero":
        offset, size = 1, 0
    elif case == "non_empty_mem":
        memory = Op.MSTORE(offset=0, value=MAX_WORD)
    elif case == "non_empty_mem_log_mem_size1":
        size = 1
    elif case == "non_empty_mem_log_mem_size1_log_mem_start31":
        offset, size = 31, 1
    elif case == "max_topic":
        topics = [MAX_WORD] * topic_count
    elif case == "caller":
        memory = Op.MSTORE8(offset=0, value=0xFF)
        topics[-1] = Op.CALLER
    elif case == "pc":
        memory = Op.MSTORE8(offset=0, value=0xFF)
        topics = [Op.PC] * topic_count
    else:
        raise ValueError(f"Unknown case: {case}")
    log = LOG_OPCODES[topic_count](offset, size, *topics)
    return memory + log + Op.STOP


@pytest.mark.ported_from(
    [
        "state_tests/stLogTests/log0_emptyMemFiller.json",
        "state_tests/stLogTests/log0_logMemStartTooHighFiller.json",
        "state_tests/stLogTests/log0_logMemsizeTooHighFiller.json",
        "state_tests/stLogTests/log0_logMemsizeZeroFiller.json",
        "state_tests/stLogTests/log0_nonEmptyMemFiller.json",
        "state_tests/stLogTests/log0_nonEmptyMem_logMemSize1Filler.json",
        "state_tests/stLogTests/log0_nonEmptyMem_logMemSize1_logMemStart31Filler.json",
        "state_tests/stLogTests/log1_CallerFiller.json",
        "state_tests/stLogTests/log1_MaxTopicFiller.json",
        "state_tests/stLogTests/log1_emptyMemFiller.json",
        "state_tests/stLogTests/log1_logMemStartTooHighFiller.json",
        "state_tests/stLogTests/log1_logMemsizeTooHighFiller.json",
        "state_tests/stLogTests/log1_logMemsizeZeroFiller.json",
        "state_tests/stLogTests/log1_nonEmptyMemFiller.json",
        "state_tests/stLogTests/log1_nonEmptyMem_logMemSize1Filler.json",
        "state_tests/stLogTests/log1_nonEmptyMem_logMemSize1_logMemStart31Filler.json",
        "state_tests/stLogTests/log2_CallerFiller.json",
        "state_tests/stLogTests/log2_MaxTopicFiller.json",
        "state_tests/stLogTests/log2_emptyMemFiller.json",
        "state_tests/stLogTests/log2_logMemStartTooHighFiller.json",
        "state_tests/stLogTests/log2_logMemsizeTooHighFiller.json",
        "state_tests/stLogTests/log2_logMemsizeZeroFiller.json",
        "state_tests/stLogTests/log2_nonEmptyMemFiller.json",
        "state_tests/stLogTests/log2_nonEmptyMem_logMemSize1Filler.json",
        "state_tests/stLogTests/log2_nonEmptyMem_logMemSize1_logMemStart31Filler.json",
        "state_tests/stLogTests/log3_CallerFiller.json",
        "state_tests/stLogTests/log3_MaxTopicFiller.json",
        "state_tests/stLogTests/log3_PCFiller.json",
        "state_tests/stLogTests/log3_emptyMemFiller.json",
        "state_tests/stLogTests/log3_logMemStartTooHighFiller.json",
        "state_tests/stLogTests/log3_logMemsizeTooHighFiller.json",
        "state_tests/stLogTests/log3_logMemsizeZeroFiller.json",
        "state_tests/stLogTests/log3_nonEmptyMemFiller.json",
        "state_tests/stLogTests/log3_nonEmptyMem_logMemSize1Filler.json",
        "state_tests/stLogTests/log3_nonEmptyMem_logMemSize1_logMemStart31Filler.json",
        "state_tests/stLogTests/log4_CallerFiller.json",
        "state_tests/stLogTests/log4_MaxTopicFiller.json",
        "state_tests/stLogTests/log4_PCFiller.json",
        "state_tests/stLogTests/log4_emptyMemFiller.json",
        "state_tests/stLogTests/log4_logMemStartTooHighFiller.json",
        "state_tests/stLogTests/log4_logMemsizeTooHighFiller.json",
        "state_tests/stLogTests/log4_logMemsizeZeroFiller.json",
        "state_tests/stLogTests/log4_nonEmptyMemFiller.json",
        "state_tests/stLogTests/log4_nonEmptyMem_logMemSize1Filler.json",
        "state_tests/stLogTests/log4_nonEmptyMem_logMemSize1_logMemStart31Filler.json",
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
@pytest.mark.parametrize(
    "topic_count, case",
    [
        pytest.param(n, case, id=f"log{n}_{case}")
        for n in range(len(LOG_OPCODES))
        for case in CASES_WITHOUT_TOPICS + (CASES_WITH_TOPICS if n else [])
    ],
)
def test_log(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    topic_count: int,
    case: str,
) -> None:
    """Call a logger contract and store whether the call succeeded."""
    sender = pre.fund_eoa()
    logger = pre.deploy_contract(code=logger_code(topic_count, case))
    caller = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=Op.CALL(address=logger))
        + Op.SSTORE(key=1, value=CANARY)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        protected=fork.supports_protected_txs(),
    )

    succeeds = case not in ("log_mem_start_too_high", "log_memsize_too_high")
    post = {caller: Account(storage={0: int(succeeds), 1: CANARY})}

    state_test(pre=pre, post=post, tx=tx)
