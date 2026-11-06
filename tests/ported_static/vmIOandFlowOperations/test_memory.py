"""
Test MLOAD, MSTORE, MSTORE8 and MSIZE.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/mloadFiller.yml
state_tests/VMTests/vmIOandFlowOperations/mstoreFiller.yml
state_tests/VMTests/vmIOandFlowOperations/mstore8Filler.yml
state_tests/VMTests/vmIOandFlowOperations/msizeFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1
FAR_OFFSET = 0x200000
TX_GAS_LIMIT = 2**24

CASES = [
    # mload
    pytest.param(
        Op.MSTORE(
            offset=0x0,
            value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        {0: 0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF},
        id="mload-mload",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0xFFFFFFF)) + Op.STOP,
        {0: SENTINEL},
        id="mload-mloadOOG_1",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x724825)) + Op.STOP,
        {0: SENTINEL},
        id="mload-mloadOOG_2",
    ),
    # mstore
    pytest.param(
        Op.MSTORE(offset=0x1, value=MAX_UINT)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        {0: MAX_UINT},
        id="mstore-mstore_allF",
    ),
    pytest.param(
        Op.MSTORE(offset=0x1, value=Op.ADD(0x2, MAX_UINT))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        {0: 1},
        id="mstore-mstore_one",
    ),
    pytest.param(
        Op.MSTORE(offset=0x1, value=Op.SUB(0x0, 0x1))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        {0: MAX_UINT},
        id="mstore-mstore_neg1",
    ),
    pytest.param(
        Op.MSTORE(offset=0x1, value=0xFF)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        {0: 0},
        id="mstore-mstore_byte32",
    ),
    pytest.param(
        Op.MSTORE(offset=0x1, value=0xFF00)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        {0: 255},
        id="mstore-mstore_byte31",
    ),
    # mstore8
    pytest.param(
        Op.MSTORE8(offset=0x1, value=0x112233445566778899AABBCCDDEEFF)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        {0: 0xFF << 248},
        id="mstore8-mstore8_onebyte",
    ),
    pytest.param(
        Op.MSTORE8(offset=0x1, value=0xFF)
        + Op.MSTORE8(offset=0x2, value=0xEE)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        {0: 0xFFEE0000000000000000000000000000000000000000000000000000000000},
        id="mstore8-mstore8_twobytes",
    ),
    pytest.param(
        Op.MSTORE8(offset=0x1, value=Op.SUB(0x0, 0x1))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        {0: 0xFF << 248},
        id="mstore8-mstore8_neg1",
    ),
    # msize
    pytest.param(
        Op.MSTORE(offset=0x0, value=0xFF)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        {0: 32},
        id="msize-msize0",
    ),
    pytest.param(
        Op.MSTORE(offset=0x0, value=0xFFFFFFFFFF)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        {0: 32},
        id="msize-msize1",
    ),
    pytest.param(
        Op.MSTORE(offset=0x0, value=0xFFFFFFFFFF)
        + Op.MSTORE(offset=0x20, value=0xEEEE)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        {0: 64},
        id="msize-msize2",
    ),
    pytest.param(
        Op.MSTORE(offset=0x0, value=0xFFFFFFFFFF)
        + Op.MSTORE(offset=0x5A, value=0xEEEE)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        {0: 128},
        id="msize-msize3",
    ),
    pytest.param(
        Op.MSTORE8(offset=0x1F, value=0x1)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.MSTORE8(offset=0x20, value=0x1)
        + Op.SSTORE(key=0x1, value=Op.MSIZE)
        + Op.MSTORE8(offset=0x20, value=0x0)
        + Op.SSTORE(key=0x2, value=Op.MSIZE)
        + Op.STOP,
        {0: 32, 1: 64, 2: 64},
        id="msize-chunks",
    ),
    pytest.param(
        Op.MSTORE8(offset=FAR_OFFSET, value=0x1)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        {0: FAR_OFFSET + 32},
        id="msize-farChunk",
    ),
]


@pytest.mark.ported_from(
    [
        "state_tests/VMTests/vmIOandFlowOperations/mloadFiller.yml",
        "state_tests/VMTests/vmIOandFlowOperations/mstoreFiller.yml",
        "state_tests/VMTests/vmIOandFlowOperations/mstore8Filler.yml",
        "state_tests/VMTests/vmIOandFlowOperations/msizeFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("code, storage", CASES)
def test_memory(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    storage: dict,
) -> None:
    """Run a memory case and check the storage it leaves."""
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
