"""
LOG0-LOG4 in a STATICCALL frame.

Ported from:
state_tests/stStaticCall/static_log0_emptyMemFiller.json
state_tests/stStaticCall/static_log0_logMemStartTooHighFiller.json
state_tests/stStaticCall/static_log0_logMemsizeTooHighFiller.json
state_tests/stStaticCall/static_log0_logMemsizeZeroFiller.json
state_tests/stStaticCall/static_log0_nonEmptyMemFiller.json
state_tests/stStaticCall/static_log0_nonEmptyMem_logMemSize1Filler.json
state_tests/stStaticCall/static_log0_nonEmptyMem_logMemSize1_logMemStart31Filler.json
state_tests/stStaticCall/static_log1_emptyMemFiller.json
state_tests/stStaticCall/static_log1_logMemStartTooHighFiller.json
state_tests/stStaticCall/static_log1_logMemsizeTooHighFiller.json
state_tests/stStaticCall/static_log1_logMemsizeZeroFiller.json
state_tests/stStaticCall/static_log1_MaxTopicFiller.json
state_tests/stStaticCall/static_log_CallerFiller.json

@manually-enhanced: Do not overwrite. Merged; the failed call is observable.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MEMORY_WORD = (
    0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD
)
HUGE = 2**256 - 1
RESULT_SLOT = 0
RESULT_SENTINEL = 0xFF
DONE_SLOT = 1

LOG_OPCODES = [Op.LOG0, Op.LOG1, Op.LOG2, Op.LOG3, Op.LOG4]


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_log0_emptyMemFiller.json",
        "state_tests/stStaticCall/static_log0_logMemStartTooHighFiller.json",
        "state_tests/stStaticCall/static_log0_logMemsizeTooHighFiller.json",
        "state_tests/stStaticCall/static_log0_logMemsizeZeroFiller.json",
        "state_tests/stStaticCall/static_log0_nonEmptyMemFiller.json",
        "state_tests/stStaticCall/static_log0_nonEmptyMem_logMemSize1Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_log0_nonEmptyMem_logMemSize1_logMemStart31Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_log1_emptyMemFiller.json",
        "state_tests/stStaticCall/static_log1_logMemStartTooHighFiller.json",
        "state_tests/stStaticCall/static_log1_logMemsizeTooHighFiller.json",
        "state_tests/stStaticCall/static_log1_logMemsizeZeroFiller.json",
        "state_tests/stStaticCall/static_log1_MaxTopicFiller.json",
        "state_tests/stStaticCall/static_log_CallerFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "topic_count, offset, size, last_topic",
    [
        pytest.param(0, 0, 0, None, id="log0_empty_mem"),
        pytest.param(0, HUGE, 1, None, id="log0_mem_start_too_high"),
        pytest.param(0, 1, HUGE, None, id="log0_memsize_too_high"),
        pytest.param(0, 1, 0, None, id="log0_memsize_zero"),
        pytest.param(0, 0, 32, None, id="log0_non_empty_mem"),
        pytest.param(0, 0, 1, None, id="log0_mem_size1"),
        pytest.param(0, 31, 1, None, id="log0_mem_size1_start31"),
        pytest.param(1, 0, 0, 0, id="log1_empty_mem"),
        pytest.param(1, HUGE, 1, 0, id="log1_mem_start_too_high"),
        pytest.param(1, 1, HUGE, 0, id="log1_memsize_too_high"),
        pytest.param(1, 1, 0, 0, id="log1_memsize_zero"),
        pytest.param(1, 0, 32, HUGE, id="log1_max_topic"),
        pytest.param(1, 0, 32, Op.CALLER, id="log1_caller"),
        pytest.param(2, 0, 32, Op.CALLER, id="log2_caller"),
        pytest.param(3, 0, 32, Op.CALLER, id="log3_caller"),
        pytest.param(4, 0, 32, Op.CALLER, id="log4_caller"),
    ],
)
def test_static_log(
    state_test: StateTestFiller,
    pre: Alloc,
    topic_count: int,
    offset: int,
    size: int,
    last_topic: int | Bytecode | None,
) -> None:
    """
    Verify a LOG in a STATICCALL frame fails the call, for every topic
    count and memory range.

    The result slot is seeded with a sentinel, so the stored 0 is
    observable, and a final store shows the caller completed.
    """
    topics = [0] * (topic_count - 1) + [last_topic] if topic_count else []
    log = LOG_OPCODES[topic_count](offset, size, *topics)
    callee = pre.deploy_contract(
        code=Op.MSTORE(0, MEMORY_WORD) + log + Op.STOP
    )
    caller = pre.deploy_contract(
        code=Op.SSTORE(RESULT_SLOT, Op.STATICCALL(address=callee))
        + Op.SSTORE(DONE_SLOT, 1)
        + Op.STOP,
        storage={RESULT_SLOT: RESULT_SENTINEL},
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {caller: Account(storage={RESULT_SLOT: 0, DONE_SLOT: 1})}

    state_test(pre=pre, post=post, tx=tx)
