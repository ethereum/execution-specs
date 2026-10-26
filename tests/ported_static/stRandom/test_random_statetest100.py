"""
Test_random_statetest100.

Ported from:
state_tests/stRandom/randomStatetest100Filler.json
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
    ["state_tests/stRandom/randomStatetest100Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest100(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest100."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x414243444342444283f24455
    target_code = (
        Op.COINBASE
        + Op.TIMESTAMP
        + Op.SSTORE(
            key=Op.PREVRANDAO,
            value=Op.CALLCODE(
                gas=Op.DUP4,
                address=Op.TIMESTAMP,
                value=Op.PREVRANDAO,
                args_offset=Op.TIMESTAMP,
                args_size=Op.NUMBER,
                ret_offset=Op.PREVRANDAO,
                ret_size=Op.NUMBER,
            ),
        )
    )
    target = pre.deploy_contract(
        code=target_code,
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
            storage={0x20000: 1},
            code=target_code,
            balance=0xDE0B6B3A76586A0,
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
