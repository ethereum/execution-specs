"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcodecall_010_OOGE_2Filler.json

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x20
    push1 0x00
    push20 0x87b79d9a4c004a23c7a12074ba8da784e201ea8c
    push3 0x055730
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    calldataload
    push3 0x01d4d4
    staticcall
    stop

callee_1 code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0x77e67836c6a30f95e117469caefb6c1fdcad0c2e
    push3 0x030d40
    callcode
    stop

callee_2 code:
    push1 0x01
    push1 0x03
    sstore
    stop

callee_3 code:
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
    ["tests/static/state_tests/stStaticCall/static_callcallcodecall_010_OOGE_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000b126c622075b1189fb6c45e851641cfaddf65b36",
        "000000000000000000000000fbef21c5a6c2adcf3d769f085e0cc9fe9a8df954",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecall_010_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x519393d984beaf4fd226309e9f0704b2db3164b5")
    callee = Address("0x77e67836c6a30f95e117469caefb6c1fdcad0c2e")
    callee_1 = Address("0x87b79d9a4c004a23c7a12074ba8da784e201ea8c")
    callee_2 = Address("0xb126c622075b1189fb6c45e851641cfaddf65b36")
    callee_3 = Address("0xfbef21c5a6c2adcf3d769f085e0cc9fe9a8df954")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0x87b79d9a4c004a23c7a12074ba8da784e201ea8c] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x1d4d4] + Op.STATICCALL
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x77e67836c6a30f95e117469caefb6c1fdcad0c2e] + Op.PUSH3[0x30d40]
        + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.STOP
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
