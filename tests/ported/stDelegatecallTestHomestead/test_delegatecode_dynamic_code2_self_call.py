"""
Ported from:
tests/static/state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCode2SelfCallFiller.json

contract code:
    push32 0x60406000604060007313136008b64ff592819b2fa6d43f2835c452020e620186
    push1 0x00
    mstore
    push32 0xa0f4600b5533600c550000000000000000000000000000000000000000000000
    push1 0x20
    mstore
    push1 0x40
    push1 0x00
    push1 0x01
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
    ["tests/static/state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCode2SelfCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecode_dynamic_code2_self_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0x10c8e0,
        nonce=0,
        code=(
        Op.PUSH32[0x60406000604060007313136008b64ff592819b2fa6d43f2835c452020e620186]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0xa0f4600b5533600c550000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.CREATE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x2386f26fc10000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=453081,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
