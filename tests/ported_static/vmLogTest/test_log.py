"""
Test LOG0-LOG4 memory ranges and topic values.

Ported from:
state_tests/VMTests/vmLogTest/log0Filler.yml
state_tests/VMTests/vmLogTest/log1Filler.yml
state_tests/VMTests/vmLogTest/log2Filler.yml
state_tests/VMTests/vmLogTest/log3Filler.yml
state_tests/VMTests/vmLogTest/log4Filler.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

LOG_OPS = [Op.LOG0, Op.LOG1, Op.LOG2, Op.LOG3, Op.LOG4]
MEMORY_WORD = (
    0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD
)
MAX_UINT = 2**256 - 1
SENTINEL = 0x0BAD
DONE = 0x600D

# scenario -> (memory word, offset, size, out of gas)
RANGES = {
    "emptyMem": (None, 0, 0, False),
    "memStartTooHigh": (MEMORY_WORD, MAX_UINT, 1, True),
    "memSizeTooHigh": (MEMORY_WORD, 1, MAX_UINT, True),
    "memSizeZero": (MEMORY_WORD, 1, 0, False),
    "nonEmptyMem": (MAX_UINT, 0, 32, False),
    "log_0_1": (MEMORY_WORD, 0, 1, False),
    "log_31_1": (MEMORY_WORD, 31, 1, False),
    "caller": (MEMORY_WORD, 0, 32, False),
    "maxTopic": (None, 31, 1, False),
    "pc": (MEMORY_WORD, 31, 1, False),
}


def pc_values(code: Bytecode) -> list[int]:
    """Return the program counter of every PC opcode in `code`."""
    raw = bytes(code)
    pcs, i = [], 0
    while i < len(raw):
        if raw[i] == 0x58:
            pcs.append(i)
        if 0x60 <= raw[i] <= 0x7F:
            i += raw[i] - 0x5F
        i += 1
    return pcs


CASES = [
    pytest.param(n, scenario, id=f"log{n}-{scenario}")
    for n in range(5)
    for scenario in RANGES
    if not (n == 0 and scenario in ("caller", "maxTopic", "pc"))
    if not (n < 3 and scenario == "pc")
] + [pytest.param(0, "logTwice", id="log0-logTwice")]


@pytest.mark.ported_from(
    [
        "state_tests/VMTests/vmLogTest/log0Filler.yml",
        "state_tests/VMTests/vmLogTest/log1Filler.yml",
        "state_tests/VMTests/vmLogTest/log2Filler.yml",
        "state_tests/VMTests/vmLogTest/log3Filler.yml",
        "state_tests/VMTests/vmLogTest/log4Filler.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("topic_count, scenario", CASES)
def test_log(
    state_test: StateTestFiller,
    pre: Alloc,
    topic_count: int,
    scenario: str,
) -> None:
    """Verify the emitted LOGn record for each memory range and topic."""
    sender = pre.fund_eoa()
    log_op = LOG_OPS[topic_count]

    if scenario == "logTwice":
        memory = MEMORY_WORD.to_bytes(32, "big")
        code = (
            Op.MSTORE(0, MEMORY_WORD)
            + Op.LOG0(offset=0, size=32)
            + Op.LOG0(offset=2, size=16)
        )
        expected: list[tuple[bytes, list[int]]] = [
            (memory, []),
            (memory[2:18], []),
        ]
        oog = False
    else:
        word, offset, size, oog = RANGES[scenario]
        if scenario == "maxTopic":
            code = Op.MSTORE8(0, 0xFF)
            memory = b"\xff" + bytes(31)
        elif word is None:
            code = Bytecode()
            memory = b""
        else:
            code = Op.MSTORE(0, word)
            memory = word.to_bytes(32, "big")

        if scenario == "maxTopic":
            topics: list = [MAX_UINT] * topic_count
        elif scenario == "pc":
            topics = [Op.PC] * topic_count
        else:
            topics = [0] * topic_count
            if scenario == "caller":
                topics[-1] = Op.CALLER

        log_code = log_op(
            offset=offset,
            size=size,
            **{f"topic_{i + 1}": t for i, t in enumerate(topics)},
        )
        if scenario == "pc":
            # Topics are pushed last-to-first.
            topic_values = list(reversed(pc_values(code + log_code)))
        elif scenario == "caller":
            topic_values = [0] * (topic_count - 1) + [int.from_bytes(sender)]
        else:
            topic_values = list(topics)
        code += log_code
        data = b"" if oog else (memory + bytes(64))[offset : offset + size]
        expected = [(data, topic_values)]

    code += Op.SSTORE(0, DONE) + Op.STOP
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})

    tx = Transaction(
        sender=sender,
        to=contract,
        expected_receipt=TransactionReceipt(
            logs=[]
            if oog
            else [
                TransactionLog(
                    address=contract,
                    topics=[Hash(t) for t in topics_],
                    data=data_,
                )
                for data_, topics_ in expected
            ]
        ),
    )
    post = {contract: Account(storage={0: SENTINEL if oog else DONE})}
    state_test(pre=pre, post=post, tx=tx)
