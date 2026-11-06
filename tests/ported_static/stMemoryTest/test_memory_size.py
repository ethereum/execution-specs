"""
Test MSIZE after a single MSTORE or MSTORE8 around 32-byte boundaries.

Ported from:
state_tests/stMemoryTest/mem0b_singleByteFiller.json
state_tests/stMemoryTest/mem31b_singleByteFiller.json
state_tests/stMemoryTest/mem32b_singleByteFiller.json
state_tests/stMemoryTest/mem32kbFiller.json
state_tests/stMemoryTest/mem32kb-1Filler.json
state_tests/stMemoryTest/mem32kb-31Filler.json
state_tests/stMemoryTest/mem32kb-32Filler.json
state_tests/stMemoryTest/mem32kb-33Filler.json
state_tests/stMemoryTest/mem32kb+1Filler.json
state_tests/stMemoryTest/mem32kb+31Filler.json
state_tests/stMemoryTest/mem32kb+32Filler.json
state_tests/stMemoryTest/mem32kb+33Filler.json
state_tests/stMemoryTest/mem32kb_singleByteFiller.json
state_tests/stMemoryTest/mem32kb_singleByte-1Filler.json
state_tests/stMemoryTest/mem32kb_singleByte-31Filler.json
state_tests/stMemoryTest/mem32kb_singleByte-32Filler.json
state_tests/stMemoryTest/mem32kb_singleByte-33Filler.json
state_tests/stMemoryTest/mem32kb_singleByte+1Filler.json
state_tests/stMemoryTest/mem32kb_singleByte+31Filler.json
state_tests/stMemoryTest/mem32kb_singleByte+32Filler.json
state_tests/stMemoryTest/mem32kb_singleByte+33Filler.json
state_tests/stMemoryTest/mem33b_singleByteFiller.json
state_tests/stMemoryTest/mem64kbFiller.json
state_tests/stMemoryTest/mem64kb-1Filler.json
state_tests/stMemoryTest/mem64kb-31Filler.json
state_tests/stMemoryTest/mem64kb-32Filler.json
state_tests/stMemoryTest/mem64kb-33Filler.json
state_tests/stMemoryTest/mem64kb+1Filler.json
state_tests/stMemoryTest/mem64kb+31Filler.json
state_tests/stMemoryTest/mem64kb+32Filler.json
state_tests/stMemoryTest/mem64kb+33Filler.json
state_tests/stMemoryTest/mem64kb_singleByteFiller.json
state_tests/stMemoryTest/mem64kb_singleByte-1Filler.json
state_tests/stMemoryTest/mem64kb_singleByte-31Filler.json
state_tests/stMemoryTest/mem64kb_singleByte-32Filler.json
state_tests/stMemoryTest/mem64kb_singleByte-33Filler.json
state_tests/stMemoryTest/mem64kb_singleByte+1Filler.json
state_tests/stMemoryTest/mem64kb_singleByte+31Filler.json
state_tests/stMemoryTest/mem64kb_singleByte+32Filler.json
state_tests/stMemoryTest/mem64kb_singleByte+33Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

STORED_VALUE = 42


@pytest.mark.ported_from(
    [
        "state_tests/stMemoryTest/mem0b_singleByteFiller.json",
        "state_tests/stMemoryTest/mem31b_singleByteFiller.json",
        "state_tests/stMemoryTest/mem32b_singleByteFiller.json",
        "state_tests/stMemoryTest/mem32kbFiller.json",
        "state_tests/stMemoryTest/mem32kb-1Filler.json",
        "state_tests/stMemoryTest/mem32kb-31Filler.json",
        "state_tests/stMemoryTest/mem32kb-32Filler.json",
        "state_tests/stMemoryTest/mem32kb-33Filler.json",
        "state_tests/stMemoryTest/mem32kb+1Filler.json",
        "state_tests/stMemoryTest/mem32kb+31Filler.json",
        "state_tests/stMemoryTest/mem32kb+32Filler.json",
        "state_tests/stMemoryTest/mem32kb+33Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByteFiller.json",
        "state_tests/stMemoryTest/mem32kb_singleByte-1Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByte-31Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByte-32Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByte-33Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByte+1Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByte+31Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByte+32Filler.json",
        "state_tests/stMemoryTest/mem32kb_singleByte+33Filler.json",
        "state_tests/stMemoryTest/mem33b_singleByteFiller.json",
        "state_tests/stMemoryTest/mem64kbFiller.json",
        "state_tests/stMemoryTest/mem64kb-1Filler.json",
        "state_tests/stMemoryTest/mem64kb-31Filler.json",
        "state_tests/stMemoryTest/mem64kb-32Filler.json",
        "state_tests/stMemoryTest/mem64kb-33Filler.json",
        "state_tests/stMemoryTest/mem64kb+1Filler.json",
        "state_tests/stMemoryTest/mem64kb+31Filler.json",
        "state_tests/stMemoryTest/mem64kb+32Filler.json",
        "state_tests/stMemoryTest/mem64kb+33Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByteFiller.json",
        "state_tests/stMemoryTest/mem64kb_singleByte-1Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByte-31Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByte-32Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByte-33Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByte+1Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByte+31Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByte+32Filler.json",
        "state_tests/stMemoryTest/mem64kb_singleByte+33Filler.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "opcode, offset",
    [
        pytest.param(Op.MSTORE8, 0, id="mem0b_single_byte"),
        pytest.param(Op.MSTORE8, 30, id="mem31b_single_byte"),
        pytest.param(Op.MSTORE8, 31, id="mem32b_single_byte"),
        pytest.param(Op.MSTORE, 31968, id="mem32kb"),
        pytest.param(Op.MSTORE, 31967, id="mem32kb_minus_1"),
        pytest.param(Op.MSTORE, 31937, id="mem32kb_minus_31"),
        pytest.param(Op.MSTORE, 31936, id="mem32kb_minus_32"),
        pytest.param(Op.MSTORE, 31935, id="mem32kb_minus_33"),
        pytest.param(Op.MSTORE, 31969, id="mem32kb_plus_1"),
        pytest.param(Op.MSTORE, 31999, id="mem32kb_plus_31"),
        pytest.param(Op.MSTORE, 32000, id="mem32kb_plus_32"),
        pytest.param(Op.MSTORE, 32001, id="mem32kb_plus_33"),
        pytest.param(Op.MSTORE8, 31999, id="mem32kb_single_byte"),
        pytest.param(Op.MSTORE8, 31998, id="mem32kb_single_byte_minus_1"),
        pytest.param(Op.MSTORE8, 31968, id="mem32kb_single_byte_minus_31"),
        pytest.param(Op.MSTORE8, 31967, id="mem32kb_single_byte_minus_32"),
        pytest.param(Op.MSTORE8, 31966, id="mem32kb_single_byte_minus_33"),
        pytest.param(Op.MSTORE8, 32000, id="mem32kb_single_byte_plus_1"),
        pytest.param(Op.MSTORE8, 32030, id="mem32kb_single_byte_plus_31"),
        pytest.param(Op.MSTORE8, 32031, id="mem32kb_single_byte_plus_32"),
        pytest.param(Op.MSTORE8, 32032, id="mem32kb_single_byte_plus_33"),
        pytest.param(Op.MSTORE8, 32, id="mem33b_single_byte"),
        pytest.param(Op.MSTORE, 63968, id="mem64kb"),
        pytest.param(Op.MSTORE, 63967, id="mem64kb_minus_1"),
        pytest.param(Op.MSTORE, 63937, id="mem64kb_minus_31"),
        pytest.param(Op.MSTORE, 63936, id="mem64kb_minus_32"),
        pytest.param(Op.MSTORE, 63935, id="mem64kb_minus_33"),
        pytest.param(Op.MSTORE, 63969, id="mem64kb_plus_1"),
        pytest.param(Op.MSTORE, 63999, id="mem64kb_plus_31"),
        pytest.param(Op.MSTORE, 64000, id="mem64kb_plus_32"),
        pytest.param(Op.MSTORE, 64001, id="mem64kb_plus_33"),
        pytest.param(Op.MSTORE8, 63999, id="mem64kb_single_byte"),
        pytest.param(Op.MSTORE8, 63998, id="mem64kb_single_byte_minus_1"),
        pytest.param(Op.MSTORE8, 63968, id="mem64kb_single_byte_minus_31"),
        pytest.param(Op.MSTORE8, 63967, id="mem64kb_single_byte_minus_32"),
        pytest.param(Op.MSTORE8, 63966, id="mem64kb_single_byte_minus_33"),
        pytest.param(Op.MSTORE8, 64000, id="mem64kb_single_byte_plus_1"),
        pytest.param(Op.MSTORE8, 64030, id="mem64kb_single_byte_plus_31"),
        pytest.param(Op.MSTORE8, 64031, id="mem64kb_single_byte_plus_32"),
        pytest.param(Op.MSTORE8, 64032, id="mem64kb_single_byte_plus_33"),
    ],
)
def test_memory_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    offset: int,
) -> None:
    """Store a value at `offset` and record MSIZE."""
    sender = pre.fund_eoa()

    width = 32 if opcode == Op.MSTORE else 1
    expected_msize = (offset + width + 31) // 32 * 32
    storage = {0: expected_msize}
    code = opcode(offset=offset, value=STORED_VALUE)
    if opcode == Op.MSTORE:
        code += Op.SSTORE(key=1, value=Op.MLOAD(offset=offset))
        storage[1] = STORED_VALUE
    target = pre.deploy_contract(
        code=code + Op.SSTORE(key=0, value=Op.MSIZE) + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        protected=fork.supports_protected_txs(),
    )

    post = {target: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)
