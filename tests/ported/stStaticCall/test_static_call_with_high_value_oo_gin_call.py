"""
Ported from:
tests/static/state_tests/stStaticCall/static_callWithHighValueOOGinCallFiller.json

contract code:
    push1 0x01
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xd5d9e9e0158920b17b6df82fac474b3e2691ee99
    push1 0x0a
    staticcall
    add
    push1 0x00
    sstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee code:
    push1 0x37
    push1 0x00
    mstore8
    push1 0x02
    push1 0x00
    return
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
    ["tests/static/state_tests/stStaticCall/static_callWithHighValueOOGinCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_with_high_value_oo_gin_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x211d767449420e452c129490ca6ad58adad11530")
    callee = Address("0xd5d9e9e0158920b17b6df82fac474b3e2691ee99")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xd5d9e9e0158920b17b6df82fac474b3e2691ee99]
        + Op.PUSH1[0xa] + Op.STATICCALL + Op.ADD + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x37] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.RETURN
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
