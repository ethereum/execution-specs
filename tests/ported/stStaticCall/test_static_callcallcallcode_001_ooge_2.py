"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_001_OOGE_2Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xbda9155e6214fe759004e6fcbe736289ef800528
    push3 0x07a120
    staticcall
    push1 0x00
    sstore
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xa7c64824c59e4295a3868a2b275ad46b38f7846d
    push3 0x0493e0
    staticcall
    stop

callee_2 code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x1c
    jumpi
    push1 0x01
    extcodesize
    pop
    push1 0x01
    push1 0x80
    mload
    add
    push1 0x80
    mstore
    push1 0x00
    jump
    jumpdest
    ... (1 more instructions)

callee_3 code:
    push1 0x01
    push1 0x03
    sstore
    push1 0x01
    push1 0x03
    mstore
    stop

callee_4 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x609e4dfe6190235b9a0362084c741d9ec330fb1e
    push3 0x01d4d4
    callcode
    stop

callee_5 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xfee7d85f02f84ce8917fa8300fea57ff41ad47d7
    push3 0x0493e0
    staticcall
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    gas
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_6 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x2db6829f13013d6280c5be4f6a5e87de274a3c47
    push3 0x07a120
    staticcall
    push1 0x00
    sstore
    stop

callee_7 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x9d41ca9233d19d3202befcef33f16af7201f0eaa
    push3 0x01d4d4
    callcode
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
    ["tests/static/state_tests/stStaticCall/static_callcallcallcode_001_OOGE_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000071587c3e5f2ebf88b2a5b048733778605addb28",
        "000000000000000000000000ed9009abb678fb6e7898148dc46fa339ea580cbd",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_001_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x071587c3e5f2ebf88b2a5b048733778605addb28")
    callee_1 = Address("0x2db6829f13013d6280c5be4f6a5e87de274a3c47")
    callee_2 = Address("0x609e4dfe6190235b9a0362084c741d9ec330fb1e")
    callee_3 = Address("0x9d41ca9233d19d3202befcef33f16af7201f0eaa")
    callee_4 = Address("0xa7c64824c59e4295a3868a2b275ad46b38f7846d")
    callee_5 = Address("0xbda9155e6214fe759004e6fcbe736289ef800528")
    callee_6 = Address("0xed9009abb678fb6e7898148dc46fa339ea580cbd")
    callee_7 = Address("0xfee7d85f02f84ce8917fa8300fea57ff41ad47d7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xbda9155e6214fe759004e6fcbe736289ef800528] + Op.PUSH3[0x7a120]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa7c64824c59e4295a3868a2b275ad46b38f7846d] + Op.PUSH3[0x493e0]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x609e4dfe6190235b9a0362084c741d9ec330fb1e]
        + Op.PUSH3[0x1d4d4] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xfee7d85f02f84ce8917fa8300fea57ff41ad47d7] + Op.PUSH3[0x493e0]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x2db6829f13013d6280c5be4f6a5e87de274a3c47] + Op.PUSH3[0x7a120]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x9d41ca9233d19d3202befcef33f16af7201f0eaa]
        + Op.PUSH3[0x1d4d4] + Op.CALLCODE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1720000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
