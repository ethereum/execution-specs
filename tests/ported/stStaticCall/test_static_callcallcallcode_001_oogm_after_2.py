"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter_2Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x335c5531b84765a7626e6e76688f18b81be5259c
    push3 0x01d4d4
    delegatecall
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
    push20 0x1067d2b507295358055ed9f68f74245839d6339f
    push3 0x061ad5
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

callee_3 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x1067d2b507295358055ed9f68f74245839d6339f
    push3 0x061ad5
    staticcall
    pop
    push1 0x01
    push1 0x03
    sstore
    stop

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
    ["tests/static/state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000004fde3a9b8985c447bc5071ee2818f0feee56052f",
        "0000000000000000000000003cc8446e7643b49561a6d83a5e699b9ad4c97854",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_001_oogm_after_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xf346244d7b72784053a685f7b1531b0d914911ca")
    callee = Address("0x1067d2b507295358055ed9f68f74245839d6339f")
    callee_1 = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_2 = Address("0x3cc8446e7643b49561a6d83a5e699b9ad4c97854")
    callee_3 = Address("0x4fde3a9b8985c447bc5071ee2818f0feee56052f")

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
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH3[0x1d4d4]
        + Op.DELEGATECALL + Op.STOP
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
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1067d2b507295358055ed9f68f74245839d6339f] + Op.PUSH3[0x61ad5]
        + Op.STATICCALL + Op.POP + Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.LT + Op.ISZERO + Op.PUSH1[0x3f] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.EXTCODESIZE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD
        + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x23] + Op.JUMP + Op.JUMPDEST
        + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1067d2b507295358055ed9f68f74245839d6339f] + Op.PUSH3[0x61ad5]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
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
