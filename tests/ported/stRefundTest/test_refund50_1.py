"""
Ported from:
tests/static/state_tests/stRefundTest/refund50_1Filler.json

contract code:
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
    ["tests/static/state_tests/stRefundTest/refund50_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund50_1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0xabbef90b4b6d86caa8d6d6cd7f673a15a8de2d61")
    contract = Address("0x6737eac10f0b6ff19a1c903cafc30b26752a5af4")

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
        Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x4] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x1: 0x1, 0x2: 0x1, 0x3: 0x1, 0x4: 0x1, 0x5: 0x1},
    )
    pre[sender] = Account(balance=0x989680, nonce=0)
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0xdc4efa209aecdd4c2d5201a419ea27506151b4ec687f14a613229e310932491b"
        ),
        to=contract,
        data=b"",
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
