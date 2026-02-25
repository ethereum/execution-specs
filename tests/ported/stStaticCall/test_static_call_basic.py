"""
Ported from:
tests/static/state_tests/stStaticCall/static_callBasicFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0186a0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee code:
    push1 0x0a
    push1 0x01
    log0
    push1 0x01
    push1 0x01
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x01
    mstore
    stop

callee_2 code:
    push1 0x01
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xc93c7a588b13699e562b3933e8f2b1c15e610781
    push2 0x9c40
    callcode
    pop
    push1 0x01
    push1 0x01
    mstore
    stop

callee_4 code:
    push1 0x00
    push1 0x01
    sstore
    stop

callee_5 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x2e0dd8abe4e68c5b602f3c65051f4b30c6d018da
    push2 0x9c40
    call
    pop
    push1 0x01
    push1 0x01
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
    ["tests/static/state_tests/stStaticCall/static_callBasicFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000d3c0847ca0222f22dcfb4a433a378ff58ad6a881",
        "000000000000000000000000ead198f480fb91a5fbedcf5eb28cd369ee4c6cf2",
        "000000000000000000000000eb015f637a39c63f8b6db67505f5c02c613defc1",
        "000000000000000000000000d5b64fa2ca1e471b45b639a5e9c259ca24c28ace",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_basic(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x13670d6bd41acd42d75e7c4c25df7384a6fbd752")
    callee = Address("0x2e0dd8abe4e68c5b602f3c65051f4b30c6d018da")
    callee_1 = Address("0xc93c7a588b13699e562b3933e8f2b1c15e610781")
    callee_2 = Address("0xd3c0847ca0222f22dcfb4a433a378ff58ad6a881")
    callee_3 = Address("0xd5b64fa2ca1e471b45b639a5e9c259ca24c28ace")
    callee_4 = Address("0xead198f480fb91a5fbedcf5eb28cd369ee4c6cf2")
    callee_5 = Address("0xeb015f637a39c63f8b6db67505f5c02c613defc1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x186a0] + Op.STATICCALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0xa] + Op.PUSH1[0x1] + Op.LOG0 + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=23,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=23,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
        storage={0x1: 0x1},
    )
    pre[callee_3] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xc93c7a588b13699e562b3933e8f2b1c15e610781]
        + Op.PUSH2[0x9c40] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=23,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
        storage={0x1: 0x0},
    )
    pre[callee_5] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x2e0dd8abe4e68c5b602f3c65051f4b30c6d018da]
        + Op.PUSH2[0x9c40] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
