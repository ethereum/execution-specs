"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcall_00Filler.json

callee code:
    push1 0x01
    push1 0x00
    mstore
    caller
    push1 0x20
    mstore
    callvalue
    push1 0x40
    mstore
    address
    push1 0x60
    mstore
    origin
    push1 0x80
    mstore
    calldatasize
    push1 0xa0
    mstore
    codesize
    push1 0xc0
    ... (5 more instructions)

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x620b442c84d5068e6b57d390a1ac99130205406e
    push3 0x055730
    staticcall
    push1 0x00
    sstore
    stop

callee_2 code:
    push1 0x01
    push1 0x02
    sstore
    caller
    push1 0x04
    sstore
    callvalue
    push1 0x07
    sstore
    address
    push1 0xe6
    sstore
    origin
    push1 0xe8
    sstore
    calldatasize
    push1 0xec
    sstore
    codesize
    push1 0xee
    ... (5 more instructions)

callee_3 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x33f368f0b54063613cf5944941e8e0e4eeb64697
    push3 0x03d090
    staticcall
    stop

callee_4 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xdcc76191e9f918ecfe9fba5414884d5ee621ae00
    push3 0x055730
    staticcall
    push1 0x00
    sstore
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

callee_5 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x29736372c0fab51db4556614ef27d74a89acfe21
    push3 0x03d090
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
    ["tests/static/state_tests/stStaticCall/static_callcall_00Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000002f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd",
        "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcall_00(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x29736372c0fab51db4556614ef27d74a89acfe21")
    callee_1 = Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd")
    callee_2 = Address("0x33f368f0b54063613cf5944941e8e0e4eeb64697")
    callee_3 = Address("0x620b442c84d5068e6b57d390a1ac99130205406e")
    callee_4 = Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105")
    callee_5 = Address("0xdcc76191e9f918ecfe9fba5414884d5ee621ae00")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE + Op.CALLER + Op.PUSH1[0x20]
        + Op.MSTORE + Op.CALLVALUE + Op.PUSH1[0x40] + Op.MSTORE + Op.ADDRESS
        + Op.PUSH1[0x60] + Op.MSTORE + Op.ORIGIN + Op.PUSH1[0x80] + Op.MSTORE
        + Op.CALLDATASIZE + Op.PUSH1[0xa0] + Op.MSTORE + Op.CODESIZE + Op.PUSH1[0xc0]
        + Op.MSTORE + Op.GASPRICE + Op.PUSH1[0xe0] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x620b442c84d5068e6b57d390a1ac99130205406e] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SSTORE + Op.CALLER + Op.PUSH1[0x4]
        + Op.SSTORE + Op.CALLVALUE + Op.PUSH1[0x7] + Op.SSTORE + Op.ADDRESS
        + Op.PUSH1[0xe6] + Op.SSTORE + Op.ORIGIN + Op.PUSH1[0xe8] + Op.SSTORE
        + Op.CALLDATASIZE + Op.PUSH1[0xec] + Op.SSTORE + Op.CODESIZE + Op.PUSH1[0xee]
        + Op.SSTORE + Op.GASPRICE + Op.PUSH1[0xf0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x33f368f0b54063613cf5944941e8e0e4eeb64697] + Op.PUSH3[0x3d090]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xdcc76191e9f918ecfe9fba5414884d5ee621ae00] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
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
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x29736372c0fab51db4556614ef27d74a89acfe21] + Op.PUSH3[0x3d090]
        + Op.STATICCALL + Op.STOP
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
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
