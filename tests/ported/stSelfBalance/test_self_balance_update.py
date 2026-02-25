"""
Ported from:
tests/static/state_tests/stSelfBalance/selfBalanceUpdateFiller.json

contract code:
    selfbalance
    dup1
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push1 0x00
    push1 0x00
    call
    pop
    selfbalance
    dup1
    push1 0x02
    sstore
    swap1
    sub
    push1 0x03
    ... (2 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSelfBalance/selfBalanceUpdateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_self_balance_update(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xd187b36e8532efd7f15218fb1781d79330c0cda2")
    contract = Address("0xff44472f5ffdd079c61153f097871f57c1f689ca")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    pre[sender] = Account(balance=0x3635c9adc5dea00000, nonce=0)
    pre[contract] = Account(
        balance=500,
        nonce=0,
        code=(
        Op.SELFBALANCE + Op.DUP1 + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALL + Op.POP + Op.SELFBALANCE + Op.DUP1
        + Op.PUSH1[0x2] + Op.SSTORE + Op.SWAP1 + Op.SUB + Op.PUSH1[0x3] + Op.SSTORE
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x897b12d02d588d8a4fe16ff831cbd4459c6f62f8c845b0ccdd31caf068c84a26"
        ),
        to=contract,
        data=b"",
        gas_limit=200000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
