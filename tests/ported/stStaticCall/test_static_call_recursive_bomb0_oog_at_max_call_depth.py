"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xbb09bb747bb11897420c59cacb65853142c67bb7
    gas
    callcode
    pop
    push1 0x01
    push1 0x01
    sstore
    stop

callee code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    mstore
    push10 0x0fffffffffffffffffff
    push2 0x0402
    push1 0x00
    mload
    div
    mul
    push1 0x02
    mstore
    push1 0x00
    push1 0x00
    push10 0x0fffffffffffffffffff
    push2 0x0402
    push1 0x00
    mload
    ... (9 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb0_oog_at_max_call_depth(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x4a20a569d7008020c8cd630cff560f3e627522d3")
    callee = Address("0xbb09bb747bb11897420c59cacb65853142c67bb7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=110000000000,
    )

    pre[contract] = Account(
        balance=0x1312d00,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xbb09bb747bb11897420c59cacb65853142c67bb7]
        + Op.GAS + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0x1312d00,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH10[0xfffffffffffffffffff] + Op.PUSH2[0x402]
        + Op.PUSH1[0x0] + Op.MLOAD + Op.DIV + Op.MUL + Op.PUSH1[0x2] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH10[0xfffffffffffffffffff]
        + Op.PUSH2[0x402] + Op.PUSH1[0x0] + Op.MLOAD + Op.DIV + Op.MUL + Op.PUSH1[0x0]
        + Op.ADDRESS + Op.PUSH2[0x400] + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=100000000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
