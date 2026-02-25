"""
Ported from:
tests/static/state_tests/stTransactionTest/StoreGasOnCreateFiller.json

coinbase code:
    push4 0x5a60fd55
    push1 0x00
    mstore
    push1 0x04
    push1 0x1c
    push1 0x00
    create
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
    ["tests/static/state_tests/stTransactionTest/StoreGasOnCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_store_gas_on_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x17d78400, nonce=0)
    pre[coinbase] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH4[0x5a60fd55] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x4]
        + Op.PUSH1[0x1c] + Op.PUSH1[0x0] + Op.CREATE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=coinbase,
        data=b"",
        gas_limit=131882,
        gas_price=10,
        nonce=0,
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
