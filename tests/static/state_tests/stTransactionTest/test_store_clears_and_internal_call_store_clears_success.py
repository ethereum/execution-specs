"""
Ported from:
tests/static/state_tests/stTransactionTest/StoreClearsAndInternalCallStoreClearsSuccessFiller.json

contract code:
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
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xd61e0564fab2b0da5136f75db579b663bd9f2bd8
    push2 0xc350
    call
    ... (1 more instructions)

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
    ["tests/static/state_tests/stTransactionTest/StoreClearsAndInternalCallStoreClearsSuccessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_store_clears_and_internal_call_store_clears_success(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x01a87dcc756f6a6bd9e586598a5c1a44a1c6d945")
    contract = Address("0x8989e867016031a6730f2b84d5e47e1f0f83bdd9")
    callee = Address("0xd61e0564fab2b0da5136f75db579b663bd9f2bd8")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x1dcd6500, nonce=0)
    pre[contract] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xd61e0564fab2b0da5136f75db579b663bd9f2bd8] + Op.PUSH2[0xc350]
        + Op.CALL + Op.STOP
    ),
        storage={0x0: 0xc, 0x1: 0xc, 0x2: 0xc, 0x3: 0xc, 0x4: 0xc},
    )
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
            "0x96c07046493ec8728482079ab999d2994420d9cf4d3491dfd06871b106d9d87b"
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
