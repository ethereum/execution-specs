"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml

callee code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x10
    push1 0x20
    mul
    jump
    jumpdest
    stop

callee_1 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x01
    push1 0x10
    push1 0x20
    mul
    jumpi
    jumpdest
    stop

callee_2 code:
    push1 0x04
    jump
    stop
    jumpdest
    push2 0x600d
    push1 0x00
    sstore
    stop

callee_3 code:
    push2 0x600d
    push1 0x00
    sstore
    push4 0x0fffffff
    jump
    stop

callee_4 code:
    push1 0x23
    push1 0x08
    jump
    push1 0x01
    jumpdest
    push1 0x02
    sstore

callee_5 code:
    push2 0x600d
    push1 0x00
    sstore
    jumpdest
    push1 0x06
    jump

callee_6 code:
    push2 0x600d
    push1 0x08
    jump
    push1 0xff
    jumpdest
    push1 0x00
    sstore

callee_7 code:
    push1 0x0b
    jump
    jumpdest
    push2 0x600d
    push1 0x00
    sstore
    stop
    jumpdest
    push1 0x03
    jump

callee_8 code:
    push1 0x02
    push1 0x05
    add
    jump
    stop
    jumpdest
    push2 0x600d
    push1 0x00
    sstore

callee_9 code:
    push1 0x05
    jump
    stop
    push1 0x5b
    push2 0x600d
    push1 0x00
    sstore

callee_10 code:
    push1 0x05
    jump
    stop
    push1 0x01
    push2 0x600d
    push1 0x00
    sstore

callee_11 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x0b
    jump
    gas
    jumpdest
    gas
    push1 0x01
    sstore

callee_12 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x09
    jump
    gas
    jumpdest
    gas
    push1 0x01
    sstore

callee_13 code:
    push9 0x01000000000000000b
    jump
    jumpdest
    jumpdest
    push1 0x01
    push1 0x01
    sstore

callee_14 code:
    push5 0x0100000007
    jump
    jumpdest
    jumpdest
    push1 0x01
    push1 0x01
    sstore

callee_15 code:
    push1 0x00
    mload
    pop
    push1 0x01
    push1 0x00
    sub
    pop
    push1 0x00
    mload
    jump
    push2 0x600d
    push1 0x00
    sstore
    stop

callee_16 code:
    push1 0x0e
    jump
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    jumpdest
    push2 0x600d
    push1 0x00
    ... (1 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
    push2 0x1000
    add
    push3 0x010000
    delegatecall
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
    ["tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000005",
        "693c6139000000000000000000000000000000000000000000000000000000000000000a",
        "693c61390000000000000000000000000000000000000000000000000000000000000009",
        "693c61390000000000000000000000000000000000000000000000000000000000000007",
        "693c61390000000000000000000000000000000000000000000000000000000000000006",
        "693c61390000000000000000000000000000000000000000000000000000000000000008",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c6139000000000000000000000000000000000000000000000000000000000000000d",
        "693c6139000000000000000000000000000000000000000000000000000000000000000e",
        "693c6139000000000000000000000000000000000000000000000000000000000000000f",
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c6139000000000000000000000000000000000000000000000000000000000000000b",
        "693c6139000000000000000000000000000000000000000000000000000000000000000c",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
        "693c61390000000000000000000000000000000000000000000000000000000000000010",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16'],
)
@pytest.mark.pre_alloc_mutable
def test_jump(
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
    callee_10 = Address("0x000000000000000000000000000000000000100a")
    callee_11 = Address("0x000000000000000000000000000000000000100b")
    callee_12 = Address("0x000000000000000000000000000000000000100c")
    callee_13 = Address("0x000000000000000000000000000000000000100d")
    callee_14 = Address("0x000000000000000000000000000000000000100e")
    callee_15 = Address("0x000000000000000000000000000000000000100f")
    callee_16 = Address("0x0000000000000000000000000000000000001010")

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
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x10]
        + Op.PUSH1[0x20] + Op.MUL + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x10] + Op.PUSH1[0x20] + Op.MUL + Op.JUMPI + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x4] + Op.JUMP + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x600d]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH4[0xfffffff] + Op.JUMP
        + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x23] + Op.PUSH1[0x8] + Op.JUMP + Op.PUSH1[0x1] + Op.JUMPDEST
        + Op.PUSH1[0x2] + Op.SSTORE
    ),
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x6]
        + Op.JUMP
    ),
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x8] + Op.JUMP + Op.PUSH1[0xff] + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0xb] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3] + Op.JUMP
    ),
    )
    pre[callee_8] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x2] + Op.PUSH1[0x5] + Op.ADD + Op.JUMP + Op.STOP + Op.JUMPDEST
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_9] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x5] + Op.JUMP + Op.STOP + Op.PUSH1[0x5b] + Op.PUSH2[0x600d]
        + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_10] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x5] + Op.JUMP + Op.STOP + Op.PUSH1[0x1] + Op.PUSH2[0x600d]
        + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_11] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xb] + Op.JUMP
        + Op.GAS + Op.JUMPDEST + Op.GAS + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[callee_12] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.GAS + Op.JUMPDEST + Op.GAS + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[callee_13] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH9[0x1000000000000000b] + Op.JUMP + Op.JUMPDEST + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[callee_14] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH5[0x100000007] + Op.JUMP + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[callee_15] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.MLOAD + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SUB
        + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.JUMP + Op.PUSH2[0x600d]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_16] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0xe] + Op.JUMP + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST
        + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST
        + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST
        + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0]
        + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD
        + Op.PUSH3[0x10000] + Op.DELEGATECALL + Op.STOP
    ),
        storage={0x0: 0xbad},
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
