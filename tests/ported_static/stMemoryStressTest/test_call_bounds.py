"""
Test call opcodes whose argument and return regions use huge bounds.

Ported from:
state_tests/stMemoryStressTest/CALL_BoundsFiller.json
state_tests/stMemoryStressTest/CALL_Bounds2Filler.json
state_tests/stMemoryStressTest/CALL_Bounds2aFiller.json
state_tests/stMemoryStressTest/CALL_Bounds3Filler.json
state_tests/stMemoryStressTest/CALLCODE_BoundsFiller.json
state_tests/stMemoryStressTest/CALLCODE_Bounds2Filler.json
state_tests/stMemoryStressTest/CALLCODE_Bounds3Filler.json
state_tests/stMemoryStressTest/CALLCODE_Bounds4Filler.json
state_tests/stMemoryStressTest/DELEGATECALL_BoundsFiller.json
state_tests/stMemoryStressTest/DELEGATECALL_Bounds2Filler.json
state_tests/stMemoryStressTest/DELEGATECALL_Bounds3Filler.json
state_tests/stMemoryStressTest/static_CALL_BoundsFiller.json
state_tests/stMemoryStressTest/static_CALL_Bounds2Filler.json
state_tests/stMemoryStressTest/static_CALL_Bounds2aFiller.json
state_tests/stMemoryStressTest/static_CALL_Bounds3Filler.json
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

INITIAL_RESULT = 0xDEAD
CANARY = 0xC0DE
BOUNDS = {
    "2^28-1": 2**28 - 1,
    "2^32-1": 2**32 - 1,
    "2^64-1": 2**64 - 1,
    "2^128-1": 2**128 - 1,
    "2^256-1": 2**256 - 1,
}
REGIONS = [
    pytest.param(0, 0, id="offset_0-size_0"),
    *[
        pytest.param(bound, 0, id=f"offset_{name}-size_0")
        for name, bound in BOUNDS.items()
    ],
    *[
        pytest.param(0, bound, id=f"offset_0-size_{name}")
        for name, bound in BOUNDS.items()
    ],
    *[
        pytest.param(bound, bound, id=f"offset_{name}-size_{name}")
        for name, bound in BOUNDS.items()
    ],
]


@pytest.mark.ported_from(
    [
        "state_tests/stMemoryStressTest/CALL_BoundsFiller.json",
        "state_tests/stMemoryStressTest/CALL_Bounds2Filler.json",
        "state_tests/stMemoryStressTest/CALL_Bounds2aFiller.json",
        "state_tests/stMemoryStressTest/CALL_Bounds3Filler.json",
        "state_tests/stMemoryStressTest/CALLCODE_BoundsFiller.json",
        "state_tests/stMemoryStressTest/CALLCODE_Bounds2Filler.json",
        "state_tests/stMemoryStressTest/CALLCODE_Bounds3Filler.json",
        "state_tests/stMemoryStressTest/CALLCODE_Bounds4Filler.json",
        "state_tests/stMemoryStressTest/DELEGATECALL_BoundsFiller.json",
        "state_tests/stMemoryStressTest/DELEGATECALL_Bounds2Filler.json",
        "state_tests/stMemoryStressTest/DELEGATECALL_Bounds3Filler.json",
        "state_tests/stMemoryStressTest/static_CALL_BoundsFiller.json",
        "state_tests/stMemoryStressTest/static_CALL_Bounds2Filler.json",
        "state_tests/stMemoryStressTest/static_CALL_Bounds2aFiller.json",
        "state_tests/stMemoryStressTest/static_CALL_Bounds3Filler.json",
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
@pytest.mark.parametrize("offset, size", REGIONS)
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
        pytest.param(
            Op.STATICCALL,
            id="staticcall",
            marks=pytest.mark.valid_from("Byzantium"),
        ),
    ],
)
def test_call_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    offset: int,
    size: int,
) -> None:
    """Call a storage counter with args and return data at the region."""
    sender = pre.fund_eoa()
    counter = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=Op.ADD(1, Op.SLOAD(key=0))) + Op.STOP,
    )
    target = pre.deploy_contract(
        code=opcode(
            address=counter,
            args_offset=offset,
            args_size=size,
            ret_offset=offset,
            ret_size=size,
        )
        + Op.STOP,
    )
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

    target_succeeds = size == 0
    counted = target_succeeds and opcode != Op.STATICCALL
    counter_holder = counter if opcode == Op.CALL else target
    post = {
        entry: Account(storage={0: int(target_succeeds), 1: CANARY}),
        counter_holder: Account(storage={0: int(counted)}),
    }

    state_test(pre=pre, post=post, tx=tx)
