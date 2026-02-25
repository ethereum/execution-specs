"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter_2Filler.json

callee code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x335c5531b84765a7626e6e76688f18b81be5259c
    push2 0x4e34
    callcode
    pop
    push1 0x01
    push1 0x20
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    mstore
    stop

callee_2 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x1e28daa61ad32aac8383a1f7b17986c69f0c3273
    push2 0x9c90
    callcode
    pop
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x45
    jumpi
    ... (13 more instructions)

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    calldataload
    push2 0xeaf6
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x1e28daa61ad32aac8383a1f7b17986c69f0c3273
    push2 0x9c90
    callcode
    pop
    push1 0x01
    push1 0x03
    sstore
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
    ["tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000007da35806c36ef9661efa1128809b18a8ed9c78f0",
        "00000000000000000000000045445092b290295fb6c954103ff2ce24cf3cfaf5",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_oogm_after_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x652a62e8338e91a46aa8387a2c205f35f79347ab")
    callee = Address("0x1e28daa61ad32aac8383a1f7b17986c69f0c3273")
    callee_1 = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_2 = Address("0x45445092b290295fb6c954103ff2ce24cf3cfaf5")
    callee_3 = Address("0x7da35806c36ef9661efa1128809b18a8ed9c78f0")

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
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH2[0x4e34]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1e28daa61ad32aac8383a1f7b17986c69f0c3273] + Op.PUSH2[0x9c90]
        + Op.CALLCODE + Op.POP + Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.LT + Op.ISZERO + Op.PUSH1[0x45] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.EXTCODESIZE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD
        + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x29] + Op.JUMP + Op.JUMPDEST
        + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH2[0xeaf6] + Op.STATICCALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1e28daa61ad32aac8383a1f7b17986c69f0c3273] + Op.PUSH2[0x9c90]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
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
        gas_limit=172000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
