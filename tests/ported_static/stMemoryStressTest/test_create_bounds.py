"""
Test CREATE with an init code region using huge bounds.

Ported from:
state_tests/stMemoryStressTest/CREATE_BoundsFiller.json
state_tests/stMemoryStressTest/CREATE_Bounds2Filler.json
state_tests/stMemoryStressTest/CREATE_Bounds3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

INITIAL_RESULT = 0xDEAD
CANARY = 0xC0DE
CREATE_VALUE = 1
BOUNDS = {
    "2^28-1": 2**28 - 1,
    "2^32-1": 2**32 - 1,
    "2^64-1": 2**64 - 1,
    "2^128-1": 2**128 - 1,
    "2^256-1": 2**256 - 1,
}


@pytest.mark.ported_from(
    [
        "state_tests/stMemoryStressTest/CREATE_BoundsFiller.json",
        "state_tests/stMemoryStressTest/CREATE_Bounds2Filler.json",
        "state_tests/stMemoryStressTest/CREATE_Bounds3Filler.json",
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
@pytest.mark.parametrize(
    "offset, size",
    [
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
    ],
)
def test_create_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    offset: int,
    size: int,
) -> None:
    """Call a contract that runs CREATE over memory[offset:offset+size]."""
    sender = pre.fund_eoa()
    creator = pre.deploy_contract(
        code=Op.CREATE(value=CREATE_VALUE, offset=offset, size=size) + Op.STOP,
        balance=CREATE_VALUE,
    )
    entry = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=Op.CALL(address=creator))
        + Op.SSTORE(key=1, value=CANARY)
        + Op.STOP,
        storage={0: INITIAL_RESULT},
    )

    tx = Transaction(
        sender=sender,
        to=entry,
        protected=fork.supports_protected_txs(),
    )

    succeeds = size == 0
    created = compute_create_address(address=creator, nonce=1)
    post = {
        entry: Account(storage={0: int(succeeds), 1: CANARY}),
        created: Account(balance=CREATE_VALUE)
        if succeeds
        else Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
