"""
Test_random_statetest309.

Ported from:
state_tests/stRandom/randomStatetest309Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest309Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest309(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest309."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x43454545085a55
    target = pre.deploy_contract(
        code=Op.NUMBER
        + Op.SSTORE(
            key=Op.GAS, value=Op.ADDMOD(Op.GASLIMIT, Op.GASLIMIT, Op.GASLIMIT)
        ),
        balance=0xDE0B6B3A7640000,
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("42"),
        gas_limit=400000,
        value=0x186A0,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
