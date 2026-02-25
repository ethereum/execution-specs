"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/loopsConditionalsFiller.yml

callee code:
    push1 0x00
    push1 0x01
    gt
    iszero
    push1 0x0f
    jumpi
    push2 0x600d
    push1 0x00
    sstore
    jumpdest
    stop

callee_1 code:
    push1 0x00
    push1 0x01
    lt
    iszero
    push1 0x0f
    jumpi
    push2 0x600d
    push1 0x00
    sstore
    jumpdest
    stop

callee_2 code:
    push1 0x00
    push1 0x01
    gt
    push1 0x0e
    jumpi
    push2 0x600d
    push1 0x00
    sstore
    jumpdest
    stop

callee_3 code:
    push1 0x00
    push1 0x01
    lt
    push1 0x0e
    jumpi
    push2 0x600d
    push1 0x00
    sstore
    jumpdest
    stop

callee_4 code:
    push1 0x00
    push1 0x01
    gt
    push1 0x0e
    jumpi
    push2 0x60a7
    push1 0x12
    jump
    jumpdest
    push2 0x600d
    jumpdest
    push1 0x00
    sstore
    stop

callee_5 code:
    push1 0x00
    push1 0x01
    lt
    push1 0x0e
    jumpi
    push2 0x60a7
    push1 0x12
    jump
    jumpdest
    push2 0x600d
    jumpdest
    push1 0x00
    sstore
    stop

callee_6 code:
    push1 0x10
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    jumpdest
    push1 0x00
    sload
    iszero
    push1 0x27
    jumpi
    push1 0x01
    push1 0x00
    sload
    sub
    push1 0x00
    sstore
    push1 0x02
    push1 0x01
    ... (8 more instructions)

callee_7 code:
    push1 0x10
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    jumpdest
    push1 0x00
    push1 0x00
    sload
    eq
    push1 0x29
    jumpi
    push1 0x01
    push1 0x00
    sload
    sub
    push1 0x00
    sstore
    push1 0x02
    ... (9 more instructions)

callee_8 code:
    push1 0x10
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    jumpdest
    push1 0x00
    push1 0x00
    sload
    gt
    iszero
    push1 0x2a
    jumpi
    push1 0x02
    push1 0x01
    sload
    mul
    push1 0x01
    sstore
    ... (10 more instructions)

callee_9 code:
    push1 0x0a
    push1 0x80
    mstore
    jumpdest
    push1 0x00
    push1 0x80
    mload
    gt
    iszero
    push1 0x26
    jumpi
    push1 0xa0
    mload
    push1 0x80
    mload
    add
    push1 0xa0
    mstore
    push1 0x01
    push1 0x80
    ... (12 more instructions)

callee_10 code:
    push1 0x00
    push1 0x80
    mstore
    jumpdest
    push1 0x0a
    push1 0x80
    mload
    gt
    iszero
    iszero
    push1 0x27
    jumpi
    push1 0xa0
    mload
    push1 0x80
    mload
    add
    push1 0xa0
    mstore
    push1 0x01
    ... (13 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
    push2 0x1000
    add
    gas
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
    ["tests/static/state_tests/VMTests/vmIOandFlowOperations/loopsConditionalsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000008",
        "693c61390000000000000000000000000000000000000000000000000000000000000009",
        "693c6139000000000000000000000000000000000000000000000000000000000000000a",
        "693c61390000000000000000000000000000000000000000000000000000000000000005",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c61390000000000000000000000000000000000000000000000000000000000000007",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c61390000000000000000000000000000000000000000000000000000000000000006",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10'],
)
@pytest.mark.pre_alloc_mutable
def test_loops_conditionals(
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
        Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.GT + Op.ISZERO + Op.PUSH1[0xf] + Op.JUMPI
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.LT + Op.ISZERO + Op.PUSH1[0xf] + Op.JUMPI
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.GT + Op.PUSH1[0xe] + Op.JUMPI
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.LT + Op.PUSH1[0xe] + Op.JUMPI
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.GT + Op.PUSH1[0xe] + Op.JUMPI
        + Op.PUSH2[0x60a7] + Op.PUSH1[0x12] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x600d]
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.LT + Op.PUSH1[0xe] + Op.JUMPI
        + Op.PUSH2[0x60a7] + Op.PUSH1[0x12] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x600d]
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x10] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SLOAD + Op.ISZERO
        + Op.PUSH1[0x27] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD
        + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.SLOAD + Op.MUL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xa] + Op.JUMP
        + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x10] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SLOAD + Op.EQ
        + Op.PUSH1[0x29] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD
        + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.SLOAD + Op.MUL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xa] + Op.JUMP
        + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x10] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SLOAD + Op.GT
        + Op.ISZERO + Op.PUSH1[0x2a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.SLOAD + Op.MUL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.SLOAD + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0xa] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0xa] + Op.PUSH1[0x80] + Op.MSTORE + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x80] + Op.MLOAD + Op.GT + Op.ISZERO + Op.PUSH1[0x26] + Op.JUMPI
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD
        + Op.SUB + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x5] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_10] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x80] + Op.MSTORE + Op.JUMPDEST + Op.PUSH1[0xa]
        + Op.PUSH1[0x80] + Op.MLOAD + Op.GT + Op.ISZERO + Op.ISZERO + Op.PUSH1[0x27]
        + Op.JUMPI + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD
        + Op.ADD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x5] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD + Op.GAS
        + Op.DELEGATECALL + Op.STOP
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
