"""
Test LOG0-LOG4 memory ranges and topic values.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmLogTest/log0Filler.yml
state_tests/VMTests/vmLogTest/log1Filler.yml
state_tests/VMTests/vmLogTest/log2Filler.yml
state_tests/VMTests/vmLogTest/log3Filler.yml
state_tests/VMTests/vmLogTest/log4Filler.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

Every test runs each LOG opcode that its case applies to, reads the
offset, size and topic values from PUSH data (static) or calldata
(dynamic), and checks the logs in the transaction receipt. The expected
data comes from a byte-level model of memory, which holds one stored
word. `test_log_data` logs a range of that memory, `test_log_topics`
logs zero, maximal, distinct or CALLER topics, and `test_log_twice` logs
two records from one frame. `test_log_memory_out_of_gas` logs a range
whose memory expansion cannot be paid for, so no log is emitted. Each
contract writes `DONE` over a `SENTINEL` after its logs, proving the
frame completed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)
from execution_testing.vm import Op, Opcode

from tests.ported_static.helpers import Memory, Operands

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/VMTests/vmLogTest/log0Filler.yml",
            "state_tests/VMTests/vmLogTest/log1Filler.yml",
            "state_tests/VMTests/vmLogTest/log2Filler.yml",
            "state_tests/VMTests/vmLogTest/log3Filler.yml",
            "state_tests/VMTests/vmLogTest/log4Filler.yml",
        ],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize("operand_source", list(Operands.Source), ids=str),
]

LOG_OPCODES: list[Opcode] = [Op.LOG0, Op.LOG1, Op.LOG2, Op.LOG3, Op.LOG4]
TOPIC_LOG_OPCODES = LOG_OPCODES[1:]

DONE_SLOT = 0
SENTINEL = 0x0BAD
DONE = 0x600D
MAX_UINT = 2**256 - 1
WORD = 0x0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF
# Each topic differs from the others and from its own byte reversal.
DISTINCT_TOPICS = [
    int.from_bytes(bytes(range(start, start + 32)))
    for start in (0x10, 0x30, 0x50, 0x70)
]


def opcode_id(opcode: Opcode) -> str:
    """Return the lower-case mnemonic of `opcode`."""
    return opcode._name_.lower()


def topic_count(log_op: Opcode) -> int:
    """Return how many topics `log_op` takes after its offset and size."""
    return log_op.popped_stack_items - 2


@pytest.fixture
def operands(operand_source: Operands.Source) -> Operands:
    """Return the operand supplier for the parametrized source."""
    return Operands(operand_source)


@pytest.fixture
def memory() -> Memory:
    """Return a memory model holding `WORD` at offset 0."""
    memory = Memory()
    memory.store(0, WORD)
    return memory


@pytest.mark.parametrize("log_op", LOG_OPCODES, ids=opcode_id)
@pytest.mark.parametrize(
    "offset, size, store_word",
    [
        # No instruction touches memory before the LOG.
        pytest.param(0, 0, False, id="empty_untouched_memory"),
        pytest.param(0, 0, True, id="empty"),
        pytest.param(1, 0, True, id="empty_unaligned"),
        pytest.param(MAX_UINT, 0, True, id="empty_at_max_offset"),
        pytest.param(0, 32, True, id="word"),
        pytest.param(0, 1, True, id="first_byte"),
        pytest.param(31, 1, True, id="last_byte"),
        # Ends in memory past the stored word, which reads as zero.
        pytest.param(16, 32, True, id="past_stored_word"),
    ],
)
def test_log_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    log_op: Opcode,
    offset: int,
    size: int,
    store_word: bool,
    operands: Operands,
    memory: Memory,
) -> None:
    """Verify the data a LOG copies from a range of memory."""
    topics = [0] * topic_count(log_op)
    code = Bytecode()
    if store_word:
        code += Op.MSTORE(0, WORD)
    else:
        # Model untouched memory, without the fixture's stored word.
        memory = Memory()
    code += (
        log_op(
            operands(offset),
            operands(size),
            *[operands(topic) for topic in topics],
        )
        + Op.SSTORE(DONE_SLOT, DONE)
        + Op.STOP
    )

    contract = pre.deploy_contract(code=code, storage={DONE_SLOT: SENTINEL})
    log = TransactionLog(
        address=contract,
        topics=[Hash(topic) for topic in topics],
        data=memory.read(offset, size),
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
        expected_receipt=TransactionReceipt(logs=[log]),
    )
    post = {contract: Account(storage={DONE_SLOT: DONE})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("log_op", LOG_OPCODES, ids=opcode_id)
@pytest.mark.parametrize(
    "offset, size",
    [
        pytest.param(MAX_UINT, 1, id="offset_too_high"),
        pytest.param(1, MAX_UINT, id="size_too_high"),
    ],
)
def test_log_memory_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    log_op: Opcode,
    offset: int,
    size: int,
    operands: Operands,
) -> None:
    """Emit no log when a LOG cannot pay for its memory expansion."""
    topics = [0] * topic_count(log_op)
    code = (
        Op.MSTORE(0, WORD)
        + log_op(
            operands(offset),
            operands(size),
            *[operands(topic) for topic in topics],
        )
        + Op.SSTORE(DONE_SLOT, DONE)
        + Op.STOP
    )

    contract = pre.deploy_contract(code=code, storage={DONE_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
        expected_receipt=TransactionReceipt(logs=[]),
    )
    post = {contract: Account(storage={DONE_SLOT: SENTINEL})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("log_op", TOPIC_LOG_OPCODES, ids=opcode_id)
@pytest.mark.parametrize("topic_kind", ["zero", "max", "distinct", "caller"])
def test_log_topics(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    log_op: Opcode,
    topic_kind: str,
    operands: Operands,
    memory: Memory,
) -> None:
    """Verify the topics a LOG records, in the order they are given."""
    sender = pre.fund_eoa()
    count = topic_count(log_op)
    topic_code: list[int | Bytecode]
    if topic_kind == "zero":
        topics = [0] * count
        topic_code = [operands(topic) for topic in topics]
    elif topic_kind == "max":
        topics = [MAX_UINT] * count
        topic_code = [operands(topic) for topic in topics]
    elif topic_kind == "distinct":
        topics = DISTINCT_TOPICS[:count]
        topic_code = [operands(topic) for topic in topics]
    elif topic_kind == "caller":
        # The last topic is the CALLER, the others are zero.
        topics = [0] * (count - 1) + [int.from_bytes(sender)]
        topic_code = [operands(0) for _ in range(count - 1)] + [Op.CALLER]
    else:
        raise ValueError(f"Unknown topic kind: {topic_kind}")

    code = (
        Op.MSTORE(0, WORD)
        + log_op(operands(0), operands(32), *topic_code)
        + Op.SSTORE(DONE_SLOT, DONE)
        + Op.STOP
    )

    contract = pre.deploy_contract(code=code, storage={DONE_SLOT: SENTINEL})
    log = TransactionLog(
        address=contract,
        topics=[Hash(topic) for topic in topics],
        data=memory.read(0, 32),
    )
    tx = Transaction(
        sender=sender,
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
        expected_receipt=TransactionReceipt(logs=[log]),
    )
    post = {contract: Account(storage={DONE_SLOT: DONE})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("log_op", LOG_OPCODES, ids=opcode_id)
def test_log_twice(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    log_op: Opcode,
    operands: Operands,
    memory: Memory,
) -> None:
    """Verify two LOGs from one frame are both recorded, in order."""
    topics = DISTINCT_TOPICS[: topic_count(log_op)]
    # (offset, size) of each log, in the order they are emitted.
    ranges = [(0, 32), (2, 16)]
    code = Op.MSTORE(0, WORD)
    for offset, size in ranges:
        code += log_op(
            operands(offset),
            operands(size),
            *[operands(topic) for topic in topics],
        )
    code += Op.SSTORE(DONE_SLOT, DONE) + Op.STOP

    contract = pre.deploy_contract(code=code, storage={DONE_SLOT: SENTINEL})
    logs = [
        TransactionLog(
            address=contract,
            topics=[Hash(topic) for topic in topics],
            data=memory.read(offset, size),
        )
        for offset, size in ranges
    ]
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
        expected_receipt=TransactionReceipt(logs=logs),
    )
    post = {contract: Account(storage={DONE_SLOT: DONE})}
    state_test(pre=pre, post=post, tx=tx)
