"""
Test MLOAD, MSTORE and RETURN at memory offsets far past any gas budget.

Ported from:
state_tests/stMemoryStressTest/MLOAD_BoundsFiller.json
state_tests/stMemoryStressTest/MLOAD_Bounds2Filler.json
state_tests/stMemoryStressTest/MSTORE_BoundsFiller.json
state_tests/stMemoryStressTest/MSTORE_Bounds2Filler.json
state_tests/stMemoryStressTest/mload32bitBoundFiller.json
state_tests/stMemoryStressTest/mload32bitBound2Filler.json
state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json
state_tests/stMemoryStressTest/mload32bitBound_return2Filler.json
state_tests/stMemoryStressTest/mload32bitBound_returnFiller.json
"""

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

INITIAL_RESULT = 0xDEAD
CANARY = 0xC0DE


@pytest.mark.ported_from(
    [
        "state_tests/stMemoryStressTest/MLOAD_BoundsFiller.json",
        "state_tests/stMemoryStressTest/MLOAD_Bounds2Filler.json",
        "state_tests/stMemoryStressTest/MSTORE_BoundsFiller.json",
        "state_tests/stMemoryStressTest/MSTORE_Bounds2Filler.json",
        "state_tests/stMemoryStressTest/mload32bitBoundFiller.json",
        "state_tests/stMemoryStressTest/mload32bitBound2Filler.json",
        "state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json",
        "state_tests/stMemoryStressTest/mload32bitBound_return2Filler.json",
        "state_tests/stMemoryStressTest/mload32bitBound_returnFiller.json",
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
@pytest.mark.parametrize(
    "code",
    [
        pytest.param(Op.MLOAD(2**32 - 1), id="mload_2^32-1"),
        pytest.param(Op.MLOAD(2**32), id="mload_2^32"),
        pytest.param(Op.MLOAD(6294967296), id="mload_6294967296"),
        pytest.param(Op.MLOAD(2**64 - 1), id="mload_2^64-1"),
        pytest.param(Op.MLOAD(2**128 - 1), id="mload_2^128-1"),
        pytest.param(Op.MLOAD(2**256 - 1), id="mload_2^256-1"),
        pytest.param(Op.MSTORE(2**32 - 1, 1), id="mstore_2^32-1"),
        pytest.param(Op.MSTORE(2**40 - 1, 1), id="mstore_2^40-1"),
        pytest.param(Op.MSTORE(2**64 - 1, 1), id="mstore_2^64-1"),
        pytest.param(Op.RETURN(0, 2**32 - 1), id="return_size_2^32-1"),
        pytest.param(
            Op.MSTORE(0, 1) + Op.RETURN(0, 2**32 - 1),
            id="mstore_then_return_size_2^32-1",
        ),
    ],
)
def test_memory_op_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    code: Bytecode,
) -> None:
    """Call a contract that touches memory at a huge bound."""
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=code + Op.STOP)
    entry = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=Op.CALL(address=target))
        + Op.SSTORE(key=1, value=CANARY)
        + Op.STOP,
        storage={0: INITIAL_RESULT},
    )

    tx = Transaction(
        sender=sender,
        to=entry,
        protected=fork.supports_protected_txs(),
    )

    post = {entry: Account(storage={0: 0, 1: CANARY})}

    state_test(pre=pre, post=post, tx=tx)
