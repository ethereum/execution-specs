"""
Ported from:
tests/static/state_tests/stRefundTest/refund_CallA_OOGFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718
    push2 0x1770
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
    ["tests/static/state_tests/stRefundTest/refund_CallA_OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_call_a_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0x14cec3675f7fa44a7f2ed836a39d58ccf0d97f8c")
    contract = Address("0x1b98d6b82e06b90c71c779925ae5b84e28401256")
    callee = Address("0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x2dc6c0, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718]
        + Op.PUSH2[0x1770] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x1: 0x1},
    )
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
        storage={0x1: 0x1},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x27b48aaa30a609c11c7aba1cb67fc191b5b59f9ff876930f0085d5faef4a4824"
        ),
        to=contract,
        data=b"",
        gas_limit=31069,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
