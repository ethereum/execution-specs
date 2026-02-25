"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmTests/envInfoFiller.yml

callee code:
    address
    push1 0x00
    sstore
    stop

callee_1 code:
    push1 0x07
    push1 0x00
    push1 0x00
    codecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    codecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    stop

callee_3 code:
    push1 0x08
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa
    push1 0x00
    codecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    stop

callee_4 code:
    caller
    push1 0x00
    sstore
    stop

callee_5 code:
    callvalue
    push1 0x00
    sstore
    stop

callee_6 code:
    codesize
    push1 0x00
    sstore
    stop

callee_7 code:
    gasprice
    push1 0x00
    sstore
    stop

callee_8 code:
    origin
    push1 0x00
    sstore
    stop

callee_9 code:
    calldatasize
    push1 0x00
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x10
    push1 0x04
    calldataload
    push2 0x1000
    add
    push3 0xffffff
    call
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
    ["tests/static/state_tests/VMTests/vmTests/envInfoFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c61390000000000000000000000000000000000000000000000000000000000000009",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
        "693c61390000000000000000000000000000000000000000000000000000000000000005",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c61390000000000000000000000000000000000000000000000000000000000000006",
        "693c61390000000000000000000000000000000000000000000000000000000000000007",
        "693c61390000000000000000000000000000000000000000000000000000000000000008",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9'],
)
@pytest.mark.pre_alloc_mutable
def test_env_info(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x0000000000000000000000000000000000001000")
    callee_1 = Address("0x0000000000000000000000000000000000001001")
    callee_2 = Address("0x0000000000000000000000000000000000001002")
    callee_3 = Address("0x0000000000000000000000000000000000001003")
    callee_4 = Address("0x0000000000000000000000000000000000001004")
    callee_5 = Address("0x0000000000000000000000000000000000001005")
    callee_6 = Address("0x0000000000000000000000000000000000001006")
    callee_7 = Address("0x0000000000000000000000000000000000001007")
    callee_8 = Address("0x0000000000000000000000000000000000001008")
    callee_9 = Address("0x0000000000000000000000000000000000001009")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.ADDRESS + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x7] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x8]
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.CALLER + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.CALLVALUE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.CODESIZE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.GASPRICE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_8] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.ORIGIN + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_9] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.CALLDATASIZE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x10] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD
        + Op.PUSH3[0xffffff] + Op.CALL + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=4660,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
