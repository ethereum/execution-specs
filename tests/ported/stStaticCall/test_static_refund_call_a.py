"""
Ported from:
tests/static/state_tests/stStaticCall/static_refund_CallAFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718
    push2 0x157c
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
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
    ["tests/static/state_tests/stStaticCall/static_refund_CallAFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_refund_call_a(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xba8b899f2f5e1a66b968ce8af2c8794026937d14")
    contract = Address("0xd15bdaf597badaa25173c995d18f65d1b514a062")
    callee = Address("0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xbebc200, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718] + Op.PUSH2[0x157c]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
        storage={0x1: 0x1},
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
        storage={0x1: 0x1},
    )

    tx = Transaction(
        secret_key=Hash(
            "0xd28ce7e8c6ca72f9b2dd5aa5c41f48198119e86e443c50de70f3fba602247fe8"
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
