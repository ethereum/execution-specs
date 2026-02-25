"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml

callee code:
    push1 0x01
    push1 0x0e
    jumpi
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
    ... (2 more instructions)

callee_1 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x10
    push1 0x00
    mstore
    jumpdest
    push1 0x01
    push1 0x00
    mload
    sub
    dup1
    push1 0x00
    mstore
    push1 0x0b
    jumpi

callee_2 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x00
    push1 0x10
    push1 0x20
    mul
    jumpi
    jumpdest
    stop

callee_3 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x00
    push1 0x10
    push1 0x20
    mul
    jumpi
    jumpdest
    stop

callee_4 code:
    push1 0x00
    push1 0x06
    jumpi
    stop
    jumpdest
    push2 0x600d
    push1 0x00
    sstore
    stop

callee_5 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x00
    push4 0x0fffffff
    jumpi
    stop

callee_6 code:
    push1 0x00
    push1 0x04
    push1 0x05
    add
    jumpi
    stop
    jumpdest
    push2 0x600d
    push1 0x00
    sstore

callee_7 code:
    push1 0x00
    push9 0x01000000000000000d
    jumpi
    jumpdest
    jumpdest
    push2 0x600d
    push1 0x00
    sstore

callee_8 code:
    push1 0x00
    push5 0x0100000009
    jumpi
    jumpdest
    jumpdest
    push2 0x600d
    push1 0x00
    sstore

callee_9 code:
    push1 0x00
    mload
    pop
    push1 0x01
    push1 0x00
    sub
    pop
    push1 0x00
    push1 0x00
    mload
    jumpi
    push2 0x600d
    push1 0x00
    sstore
    stop

callee_10 code:
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

callee_11 code:
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

callee_12 code:
    push1 0x01
    push1 0x06
    jumpi
    stop
    jumpdest
    push2 0x600d
    push1 0x00
    sstore
    stop

callee_13 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0xff
    push4 0x0fffffff
    jumpi
    stop

callee_14 code:
    push1 0x23
    push1 0x01
    push1 0x08
    jumpi
    push1 0x01
    jumpdest
    push1 0x02
    sstore

callee_15 code:
    push2 0x600d
    push1 0x00
    sstore
    jumpdest
    push1 0x06
    push1 0x06
    jumpi

callee_16 code:
    push2 0x600d
    push1 0x01
    push1 0x0a
    jumpi
    push1 0xff
    jumpdest
    push1 0x00
    sstore

callee_17 code:
    push1 0x0b
    jump
    jumpdest
    push2 0x600d
    push1 0x00
    sstore
    stop
    jumpdest
    push1 0x01
    push1 0x03
    jumpi

callee_18 code:
    push1 0x01
    push1 0x04
    push1 0x05
    add
    jumpi
    stop
    jumpdest
    push2 0x600d
    push1 0x00
    sstore

callee_19 code:
    push1 0x01
    push1 0x07
    jumpi
    stop
    push1 0x5b
    push2 0x600d
    push1 0x00
    sstore

callee_20 code:
    push1 0x01
    push1 0x07
    jumpi
    stop
    push1 0x01
    push2 0x600d
    push1 0x00
    sstore

callee_21 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x01
    push1 0x0d
    jumpi
    gas
    jumpdest
    gas
    push1 0x01
    sstore

callee_22 code:
    push2 0x600d
    push1 0x00
    sstore
    push1 0x01
    push1 0x0b
    jumpi
    gas
    jumpdest
    gas
    push1 0x01
    sstore

callee_23 code:
    push1 0x11
    push9 0x01000000000000000d
    jumpi
    jumpdest
    jumpdest
    push2 0x600d
    push1 0x00
    sstore

callee_24 code:
    push1 0x11
    push5 0x0100000009
    jumpi
    jumpdest
    jumpdest
    push2 0x600d
    push1 0x00
    sstore

callee_25 code:
    push1 0x00
    mload
    pop
    push1 0x01
    push1 0x00
    sub
    pop
    push1 0x01
    push1 0x00
    mload
    jumpi
    push2 0x600d
    push1 0x00
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
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
    ["tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000001005",
        "693c6139000000000000000000000000000000000000000000000000000000000000100a",
        "693c61390000000000000000000000000000000000000000000000000000000000001009",
        "693c61390000000000000000000000000000000000000000000000000000000000001007",
        "693c61390000000000000000000000000000000000000000000000000000000000001006",
        "693c61390000000000000000000000000000000000000000000000000000000000001008",
        "693c61390000000000000000000000000000000000000000000000000000000000001001",
        "693c61390000000000000000000000000000000000000000000000000000000000001003",
        "693c6139000000000000000000000000000000000000000000000000000000000000100d",
        "693c6139000000000000000000000000000000000000000000000000000000000000100e",
        "693c6139000000000000000000000000000000000000000000000000000000000000100f",
        "693c61390000000000000000000000000000000000000000000000000000000000001000",
        "693c6139000000000000000000000000000000000000000000000000000000000000100b",
        "693c6139000000000000000000000000000000000000000000000000000000000000100c",
        "693c61390000000000000000000000000000000000000000000000000000000000001004",
        "693c61390000000000000000000000000000000000000000000000000000000000001002",
        "693c61390000000000000000000000000000000000000000000000000000000000000110",
        "693c61390000000000000000000000000000000000000000000000000000000000000111",
        "693c61390000000000000000000000000000000000000000000000000000000000000208",
        "693c61390000000000000000000000000000000000000000000000000000000000000201",
        "693c61390000000000000000000000000000000000000000000000000000000000000203",
        "693c6139000000000000000000000000000000000000000000000000000000000000020d",
        "693c6139000000000000000000000000000000000000000000000000000000000000020e",
        "693c6139000000000000000000000000000000000000000000000000000000000000020f",
        "693c61390000000000000000000000000000000000000000000000000000000000000200",
        "693c61390000000000000000000000000000000000000000000000000000000000000202",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25'],
)
@pytest.mark.pre_alloc_mutable
def test_jumpi(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x0000000000000000000000000000000000000110")
    callee_1 = Address("0x0000000000000000000000000000000000000111")
    callee_2 = Address("0x0000000000000000000000000000000000000200")
    callee_3 = Address("0x0000000000000000000000000000000000000201")
    callee_4 = Address("0x0000000000000000000000000000000000000202")
    callee_5 = Address("0x0000000000000000000000000000000000000203")
    callee_6 = Address("0x0000000000000000000000000000000000000208")
    callee_7 = Address("0x000000000000000000000000000000000000020d")
    callee_8 = Address("0x000000000000000000000000000000000000020e")
    callee_9 = Address("0x000000000000000000000000000000000000020f")
    callee_10 = Address("0x0000000000000000000000000000000000001000")
    callee_11 = Address("0x0000000000000000000000000000000000001001")
    callee_12 = Address("0x0000000000000000000000000000000000001002")
    callee_13 = Address("0x0000000000000000000000000000000000001003")
    callee_14 = Address("0x0000000000000000000000000000000000001004")
    callee_15 = Address("0x0000000000000000000000000000000000001005")
    callee_16 = Address("0x0000000000000000000000000000000000001006")
    callee_17 = Address("0x0000000000000000000000000000000000001007")
    callee_18 = Address("0x0000000000000000000000000000000000001008")
    callee_19 = Address("0x0000000000000000000000000000000000001009")
    callee_20 = Address("0x000000000000000000000000000000000000100a")
    callee_21 = Address("0x000000000000000000000000000000000000100b")
    callee_22 = Address("0x000000000000000000000000000000000000100c")
    callee_23 = Address("0x000000000000000000000000000000000000100d")
    callee_24 = Address("0x000000000000000000000000000000000000100e")
    callee_25 = Address("0x000000000000000000000000000000000000100f")

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
        Op.PUSH1[0x1] + Op.PUSH1[0xe] + Op.JUMPI + Op.JUMPDEST + Op.JUMPDEST
        + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST
        + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST
        + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH2[0x600d]
        + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x10]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xb]
        + Op.JUMPI
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x10] + Op.PUSH1[0x20] + Op.MUL + Op.JUMPI + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x10] + Op.PUSH1[0x20] + Op.MUL + Op.JUMPI + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x6] + Op.JUMPI + Op.STOP + Op.JUMPDEST
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH4[0xfffffff] + Op.JUMPI + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x5] + Op.ADD + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH9[0x1000000000000000d] + Op.JUMPI + Op.JUMPDEST
        + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_8] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH5[0x100000009] + Op.JUMPI + Op.JUMPDEST + Op.JUMPDEST
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_9] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.MLOAD + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SUB
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MLOAD + Op.JUMPI
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_10] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x10] + Op.PUSH1[0x20] + Op.MUL + Op.JUMPI + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_11] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x10] + Op.PUSH1[0x20] + Op.MUL + Op.JUMPI + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_12] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x6] + Op.JUMPI + Op.STOP + Op.JUMPDEST
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_13] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xff]
        + Op.PUSH4[0xfffffff] + Op.JUMPI + Op.STOP
    ),
    )
    pre[callee_14] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x23] + Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.JUMPDEST + Op.PUSH1[0x2] + Op.SSTORE
    ),
    )
    pre[callee_15] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x6]
        + Op.PUSH1[0x6] + Op.JUMPI
    ),
    )
    pre[callee_16] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x1] + Op.PUSH1[0xa] + Op.JUMPI + Op.PUSH1[0xff]
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_17] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0xb] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.JUMPI
    ),
    )
    pre[callee_18] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x4] + Op.PUSH1[0x5] + Op.ADD + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_19] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x7] + Op.JUMPI + Op.STOP + Op.PUSH1[0x5b]
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_20] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x7] + Op.JUMPI + Op.STOP + Op.PUSH1[0x1]
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_21] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xd]
        + Op.JUMPI + Op.GAS + Op.JUMPDEST + Op.GAS + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[callee_22] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xb]
        + Op.JUMPI + Op.GAS + Op.JUMPDEST + Op.GAS + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[callee_23] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x11] + Op.PUSH9[0x1000000000000000d] + Op.JUMPI + Op.JUMPDEST
        + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_24] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x11] + Op.PUSH5[0x100000009] + Op.JUMPI + Op.JUMPDEST
        + Op.JUMPDEST + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[callee_25] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.MLOAD + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SUB
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.JUMPI
        + Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH3[0x10000] + Op.DELEGATECALL
        + Op.STOP
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
