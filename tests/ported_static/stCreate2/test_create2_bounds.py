"""
CREATE2 with init code offsets and sizes at memory bounds.

Ported from:
state_tests/stCreate2/CREATE2_BoundsFiller.json
state_tests/stCreate2/CREATE2_Bounds2Filler.json
state_tests/stCreate2/CREATE2_Bounds3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

BOUNDS = {
    "0": 0,
    "2^28-1": 2**28 - 1,
    "2^32-1": 2**32 - 1,
    "2^64-1": 2**64 - 1,
    "2^128-1": 2**128 - 1,
    "2^256-1": 2**256 - 1,
}
OFFSET_SIZE_PAIRS = [
    ("0", "0"),
    ("0", "2^28-1"),
    ("0", "2^32-1"),
    ("0", "2^64-1"),
    ("0", "2^128-1"),
    ("0", "2^256-1"),
    ("2^28-1", "0"),
    ("2^32-1", "0"),
    ("2^64-1", "0"),
    ("2^128-1", "0"),
    ("2^256-1", "0"),
    ("2^28-1", "2^28-1"),
    ("2^32-1", "2^32-1"),
    ("2^64-1", "2^64-1"),
    ("2^128-1", "2^128-1"),
    ("2^256-1", "2^256-1"),
]


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/CREATE2_BoundsFiller.json",
        "state_tests/stCreate2/CREATE2_Bounds2Filler.json",
        "state_tests/stCreate2/CREATE2_Bounds3Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "offset, size",
    [
        pytest.param(BOUNDS[o], BOUNDS[s], id=f"offset_{o}-size_{s}")
        for o, s in OFFSET_SIZE_PAIRS
    ],
)
def test_create2_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    offset: int,
    size: int,
) -> None:
    """CREATE2 with init code offsets and sizes at memory bounds."""
    sender = pre.fund_eoa()
    creator_balance = 100
    create_value = 1

    creator = pre.deploy_contract(
        code=Op.CREATE2(value=create_value, offset=offset, size=size, salt=0)
        + Op.STOP,
        balance=creator_balance,
    )
    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(address=creator)) + Op.SSTORE(1, 1)
    )

    tx = Transaction(sender=sender, to=caller)

    created = compute_create_address(
        address=creator, salt=0, initcode=b"", opcode=Op.CREATE2
    )
    post: dict
    if size == 0:
        post = {
            caller: Account(storage={0: 1, 1: 1}),
            creator: Account(balance=creator_balance - create_value, nonce=2),
            created: Account(balance=create_value, nonce=1, code=b""),
        }
    else:
        post = {
            caller: Account(storage={0: 0, 1: 1}),
            creator: Account(balance=creator_balance, nonce=1),
            created: Account.NONEXISTENT,
        }

    state_test(pre=pre, post=post, tx=tx)
