"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_1Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x677db155fab75972f19732afb328a0ea6472a6ab
    push3 0x061ad0
    staticcall
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    mstore
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x18dc408f6983f318529a93583ee12f590c537820
    push3 0x0aaef6
    callcode
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_3 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xb126c622075b1189fb6c45e851641cfaddf65b36
    push3 0x01d4d4
    callcode
    pop
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
    push20 0x335c5531b84765a7626e6e76688f18b81be5259c
    push3 0x01d4d4
    callcode
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    gas
    callcode
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_5 code:
    push1 0x01
    push1 0x03
    sstore
    stop

callee_6 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xf4645c150a8060778ad94dffe302081fc222dedb
    push3 0x0aaef6
    callcode
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_7 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x858db7418c9e1c32811e5bc39366bdf6e2ed2492
    push3 0x061ad0
    staticcall
    pop
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x3f
    jumpi
    push1 0x01
    extcodesize
    pop
    push1 0x01
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
    ["tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000b9abd0ef44ae2df9f408d150c5b6fb6a181be9cf",
        "0000000000000000000000006486b0cd8779006e5cd706484b0d890b9a220805",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_101_oogm_after_1(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xaab59f13d96113334fab5c68e4e62b61f6cbf647")
    callee = Address("0x18dc408f6983f318529a93583ee12f590c537820")
    callee_1 = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_2 = Address("0x6486b0cd8779006e5cd706484b0d890b9a220805")
    callee_3 = Address("0x677db155fab75972f19732afb328a0ea6472a6ab")
    callee_4 = Address("0x858db7418c9e1c32811e5bc39366bdf6e2ed2492")
    callee_5 = Address("0xb126c622075b1189fb6c45e851641cfaddf65b36")
    callee_6 = Address("0xb9abd0ef44ae2df9f408d150c5b6fb6a181be9cf")
    callee_7 = Address("0xf4645c150a8060778ad94dffe302081fc222dedb")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x677db155fab75972f19732afb328a0ea6472a6ab] + Op.PUSH3[0x61ad0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x18dc408f6983f318529a93583ee12f590c537820]
        + Op.PUSH3[0xaaef6] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xb126c622075b1189fb6c45e851641cfaddf65b36]
        + Op.PUSH3[0x1d4d4] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c]
        + Op.PUSH3[0x1d4d4] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALLCODE
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
    )
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xf4645c150a8060778ad94dffe302081fc222dedb]
        + Op.PUSH3[0xaaef6] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x858db7418c9e1c32811e5bc39366bdf6e2ed2492] + Op.PUSH3[0x61ad0]
        + Op.STATICCALL + Op.POP + Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.LT + Op.ISZERO + Op.PUSH1[0x3f] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.EXTCODESIZE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD
        + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x23] + Op.JUMP + Op.JUMPDEST
        + Op.STOP
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
