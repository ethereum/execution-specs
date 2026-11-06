"""
CREATE/CREATE2 from a contract at the maximum nonce and one below it.

Ported from:
state_tests/stCreateTest/CREATE_HighNonceFiller.yml
state_tests/stCreateTest/CREATE_HighNonceMinus1Filler.yml
state_tests/stCreate2/CREATE2_HighNonceFiller.yml
state_tests/stCreate2/CREATE2_HighNonceMinus1Filler.yml
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

MAX_NONCE = 2**64 - 1


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_HighNonceFiller.yml",
        "state_tests/stCreateTest/CREATE_HighNonceMinus1Filler.yml",
        "state_tests/stCreate2/CREATE2_HighNonceFiller.yml",
        "state_tests/stCreate2/CREATE2_HighNonceMinus1Filler.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "creator_nonce",
    [
        pytest.param(MAX_NONCE, id="max_nonce"),
        pytest.param(MAX_NONCE - 1, id="max_nonce_minus1"),
    ],
)
def test_create_high_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    creator_nonce: int,
) -> None:
    """CREATE/CREATE2 from a contract at and below the maximum nonce."""
    sender = pre.fund_eoa()
    # initcode: { return(0, 1) }
    initcode = bytes.fromhex("60016000f3")
    if opcode == Op.CREATE2:
        create = Op.CREATE2(value=0, offset=0, size=len(initcode), salt=0)
    else:
        create = Op.CREATE(value=0, offset=0, size=len(initcode))
    creator = pre.deploy_contract(
        code=Op.MSTORE(offset=0, value=initcode.ljust(32, b"\0"))
        + Op.SSTORE(key=0, value=create)
        + Op.SSTORE(key=1, value=1)
        + Op.STOP,
        nonce=creator_nonce,
    )
    created = compute_create_address(
        address=creator,
        nonce=creator_nonce,
        salt=0,
        initcode=initcode,
        opcode=opcode,
    )

    post: dict = {sender: Account(nonce=1)}
    if creator_nonce == MAX_NONCE:
        post[creator] = Account(storage={0: 0, 1: 1}, nonce=MAX_NONCE)
        post[created] = Account.NONEXISTENT
    else:
        post[creator] = Account(storage={0: created, 1: 1}, nonce=MAX_NONCE)
        post[created] = Account(code=b"\0", nonce=1)

    tx = Transaction(sender=sender, to=creator)

    state_test(pre=pre, post=post, tx=tx)
