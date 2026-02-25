"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallRecursiveBombPreCall2Filler.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xbad304eb96065b2a98b57a48a06ae28d285a71b5
    push3 0x0186a0
    staticcall
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xed136edce8f08ef121c25430e7dec4ed3feb511d
    push8 0x07ffffffffffffff
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    ... (1 more instructions)

callee code:
    push1 0x01
    push1 0x00
    mload
    add
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    address
    push3 0x036b00
    gas
    sub
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_CallRecursiveBombPreCall2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb_pre_call2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x9f583f1fdfa7e94974bff973b2abcd0ad513af0b")
    contract = Address("0x5e01fe5d73a471c61018a02f7cf7d8f977343093")
    callee = Address("0xed136edce8f08ef121c25430e7dec4ed3feb511d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=0xfffffffffffffffffffffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xbad304eb96065b2a98b57a48a06ae28d285a71b5] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xed136edce8f08ef121c25430e7dec4ed3feb511d]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xfffffffffffffffffffffffffffffff, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.ADDRESS + Op.PUSH3[0x36b00] + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x77f65b71f1f16a75476f469f7106d1b60bfec266ae25b8da16a9091d223aa24a"
        ),
        to=contract,
        data=b"",
        gas_limit=9214364837600034817,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
