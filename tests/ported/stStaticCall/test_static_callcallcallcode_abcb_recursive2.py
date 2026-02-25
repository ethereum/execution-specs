"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVE2Filler.json

contract code:
    push1 0x01
    push1 0x01
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xa340f8b0f598f6d5ad2856ffe45aadd934f37cf1
    push4 0x017d7840
    staticcall
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee code:
    push1 0x01
    push1 0x01
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xa340f8b0f598f6d5ad2856ffe45aadd934f37cf1
    push3 0x07a120
    callcode
    pop
    push1 0x01
    push1 0x02
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x01
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x812297c04813fea96b943b246d9d17ea17545526
    push3 0x0f4240
    staticcall
    pop
    push1 0x01
    push1 0x02
    mstore
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
    ["tests/static/state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVE2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_abcb_recursive2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x130e754252b72cb20aa752cb31176d9c2e9c8a21")
    callee = Address("0x812297c04813fea96b943b246d9d17ea17545526")
    callee_1 = Address("0xa340f8b0f598f6d5ad2856ffe45aadd934f37cf1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa340f8b0f598f6d5ad2856ffe45aadd934f37cf1] + Op.PUSH4[0x17d7840]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa340f8b0f598f6d5ad2856ffe45aadd934f37cf1] + Op.PUSH3[0x7a120]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x812297c04813fea96b943b246d9d17ea17545526] + Op.PUSH3[0xf4240]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
