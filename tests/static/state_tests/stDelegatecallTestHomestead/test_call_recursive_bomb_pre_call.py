"""
Ported from:
tests/static/state_tests/stDelegatecallTestHomestead/CallRecursiveBombPreCallFiller.json

callee code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x3046257c307a51f1a8ae73f6f6360937dd21138e
    push3 0x036b00
    gas
    sub
    call
    push1 0x01
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x17
    push20 0xbad304eb96065b2a98b57a48a06ae28d285a71b5
    push3 0x0186a0
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x3046257c307a51f1a8ae73f6f6360937dd21138e
    push8 0x07ffffffffffffff
    delegatecall
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
    ["tests/static/state_tests/stDelegatecallTestHomestead/CallRecursiveBombPreCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_bomb_pre_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x9f583f1fdfa7e94974bff973b2abcd0ad513af0b")
    contract = Address("0x7a11b1b8911ecccfccb030a17f9cebde63a92190")
    callee = Address("0x3046257c307a51f1a8ae73f6f6360937dd21138e")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x3046257c307a51f1a8ae73f6f6360937dd21138e]
        + Op.PUSH3[0x36b00] + Op.GAS + Op.SUB + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xfffffffffffffffffffffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x17] + Op.PUSH20[0xbad304eb96065b2a98b57a48a06ae28d285a71b5]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x3046257c307a51f1a8ae73f6f6360937dd21138e]
        + Op.PUSH8[0x7ffffffffffffff] + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xfffffffffffffffffffffffffffffff, nonce=0)

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
