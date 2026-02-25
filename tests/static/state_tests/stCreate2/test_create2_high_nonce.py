"""
Ported from:
tests/static/state_tests/stCreate2/CREATE2_HighNonceFiller.yml

contract code:
    push5 0x60016000f3
    push1 0xd8
    shl
    push1 0x00
    swap1
    dup2
    mstore
    push1 0x05
    dup2
    dup1
    create2
    push1 0x00
    sstore
    push1 0x01
    dup1
    sstore
    stop
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
    ["tests/static/state_tests/stCreate2/CREATE2_HighNonceFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_high_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3b9aca00, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=18446744073709551615,
        code=(
        Op.PUSH5[0x60016000f3] + Op.PUSH1[0xd8] + Op.SHL + Op.PUSH1[0x0] + Op.SWAP1
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x5] + Op.DUP2 + Op.DUP1 + Op.CREATE2
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.DUP1 + Op.SSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
