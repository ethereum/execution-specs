"""
Ported from:
tests/static/state_tests/stRefundTest/refund_CallAFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718
    push2 0x157c
    call
    push1 0x00
    sstore
    stop

callee code:
    push1 0x00
    push1 0x01
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
    ["tests/static/state_tests/stRefundTest/refund_CallAFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_call_a(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0x7e8bf4c8760bbcc2757cc0ce4e093f218862b14f")
    contract = Address("0x3d72f604b4d56320853a5ece45772dbbf419f315")
    callee = Address("0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718]
        + Op.PUSH2[0x157c] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x1: 0x1},
    )
    pre[sender] = Account(balance=0x1312d00, nonce=0)
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
        storage={0x1: 0x1},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x752660e61324e901f7231dfae39984f4d433a241d533838e4700925f477814fd"
        ),
        to=contract,
        data=b"",
        gas_limit=200000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
