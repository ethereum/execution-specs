"""
Test RETURN with huge offset and size operands from a sub-call.

Ported from:
state_tests/stMemoryStressTest/RETURN_BoundsFiller.json
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
    "2^108-1": 2**108 - 1,
    "2^256-1": 2**256 - 1,
}


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/RETURN_BoundsFiller.json"],
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
def test_return_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    offset: int,
    size: int,
) -> None:
    """Call a contract returning memory[offset:offset+size]."""
    sender = pre.fund_eoa()
    returner = pre.deploy_contract(code=Op.RETURN(offset=offset, size=size))
    caller = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=Op.CALL(address=returner))
        + Op.SSTORE(key=1, value=CANARY)
        + Op.STOP,
        storage={0: INITIAL_RESULT},
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        protected=fork.supports_protected_txs(),
    )

    succeeds = size == 0
    post = {caller: Account(storage={0: int(succeeds), 1: CANARY})}

    state_test(pre=pre, post=post, tx=tx)
