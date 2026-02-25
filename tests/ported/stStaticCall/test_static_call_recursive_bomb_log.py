"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallRecursiveBombLogFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc60fab741bda8373b3905ed824826a8f6ea8fd0a
    push3 0x0186a0
    gas
    sub
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    log0
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    address
    push2 0x61a8
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
    ["tests/static/state_tests/stStaticCall/static_CallRecursiveBombLogFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb_log(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x2effe40c3fdb4abb2979bfcfb8d814f1a786576d")
    callee = Address("0xc60fab741bda8373b3905ed824826a8f6ea8fd0a")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    pre[contract] = Account(
        balance=0x1312d00,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc60fab741bda8373b3905ed824826a8f6ea8fd0a] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.LOG0
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.ADDRESS
        + Op.PUSH2[0x61a8] + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=10000000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
