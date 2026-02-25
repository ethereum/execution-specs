"""
Ported from:
tests/static/state_tests/stStaticCall/static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json

contract code:
    push1 0x01
    push1 0x01
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x01
    mstore
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
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x4000000000000000000000000000000000000004
    push2 0x03e8
    callcode
    stop

callee_4 code:
    push1 0x01
    push1 0x01
    mstore
    stop

callee_5 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x4000000000000000000000000000000000000004
    push3 0x0f4240
    callcode
    stop

callee_6 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x1000000000000000000000000000000000000001
    push2 0xc350
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
    ["tests/static/state_tests/stStaticCall/static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "604060006040600073100000000000000000000000000000000000000161c350fa",
        "604060006040600073200000000000000000000000000000000000000161c350fa",
        "604060006040600073300000000000000000000000000000000000000161c350fa",
        "604060006040600073400000000000000000000000000000000000000161c350fa",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_static_contract_creation_make_call_that_ask_more_gas_then_transaction_provided(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1000000000000000000000000000000000000001")
    callee_1 = Address("0x2000000000000000000000000000000000000001")
    callee_2 = Address("0x3000000000000000000000000000000000000001")
    callee_3 = Address("0x4000000000000000000000000000000000000001")
    callee_4 = Address("0x4000000000000000000000000000000000000004")
    callee_5 = Address("0x5000000000000000000000000000000000000001")
    callee_6 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0x186a0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x4000000000000000000000000000000000000004]
        + Op.PUSH2[0x3e8] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0x186a0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_5] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x4000000000000000000000000000000000000004]
        + Op.PUSH3[0xf4240] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x10c8e0, nonce=0)
    pre[callee_6] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1000000000000000000000000000000000000001] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=tx_data,
        gas_limit=96000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
