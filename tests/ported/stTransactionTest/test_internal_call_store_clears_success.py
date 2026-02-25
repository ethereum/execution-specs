"""
Ported from:
tests/static/state_tests/stTransactionTest/InternalCallStoreClearsSuccessFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xd61e0564fab2b0da5136f75db579b663bd9f2bd8
    push3 0x0186a0
    call
    stop

callee code:
    push1 0x00
    push1 0x00
    sstore
    push1 0x00
    push1 0x01
    sstore
    push1 0x00
    push1 0x02
    sstore
    push1 0x00
    push1 0x03
    sstore
    push1 0x00
    push1 0x04
    sstore
    push1 0x00
    push1 0x05
    sstore
    push1 0x00
    push1 0x06
    ... (11 more instructions)
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
    ["tests/static/state_tests/stTransactionTest/InternalCallStoreClearsSuccessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_internal_call_store_clears_success(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xc4a2ca1058df329e5da4755f9921ddaf05cbaa06")
    contract = Address("0x4583a4f45bcb657469d752196a99ed546c8464ef")
    callee = Address("0xd61e0564fab2b0da5136f75db579b663bd9f2bd8")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xd61e0564fab2b0da5136f75db579b663bd9f2bd8]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x3b9aca00, nonce=0)
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x6]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x9] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x0: 0xc, 0x1: 0xc, 0x2: 0xc, 0x3: 0xc, 0x4: 0xc, 0x5: 0xc, 0x6: 0xc, 0x7: 0xc, 0x8: 0xc, 0x9: 0xc},
    )

    tx = Transaction(
        secret_key=Hash(
            "0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf"
        ),
        to=contract,
        data=b"",
        gas_limit=160000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
