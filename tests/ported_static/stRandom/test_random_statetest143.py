"""
Test_random_statetest143.

Ported from:
state_tests/stRandom/randomStatetest143Filler.json
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
    ["state_tests/stRandom/randomStatetest143Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest143(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest143."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x414341414243421a2055
    target = pre.deploy_contract(
        code=Op.COINBASE
        + Op.NUMBER
        + Op.COINBASE
        + Op.SSTORE(
            key=Op.SHA3(
                offset=Op.BYTE(Op.TIMESTAMP, Op.NUMBER), size=Op.TIMESTAMP
            ),
            value=Op.COINBASE,
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
        target: Account(
            storage={
                0xAE72E2BF2302EBCD309E003E5BE58830F96DEDDAF87BB89EEEA159388BFE3EC1: coinbase,  # noqa: E501
            },
            balance=0xDE0B6B3A76586A0,
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
