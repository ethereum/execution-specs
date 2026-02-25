"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stBadOpcode/measureGasFiller.yml

callee_1 code:
    push2 0xbeef
    push1 0x00
    sha3
    stop

callee_2 code:
    push2 0xca11
    push1 0x00
    dup1
    dup3
    extcodesize
    swap3
    extcodecopy
    stop

callee_3 code:
    push2 0xb000
    mload
    stop

callee_4 code:
    push1 0xff
    push2 0xb000
    mstore
    stop

callee_5 code:
    push1 0xff
    push2 0xb000
    mstore8
    stop

callee_6 code:
    push2 0x0200
    push1 0x00
    dup1
    create
    stop

callee_7 code:
    push2 0x0100
    push1 0x00
    dup2
    dup2
    dup1
    push2 0xca11
    gas
    call
    stop

callee_8 code:
    push2 0x0100
    push1 0x00
    dup2
    dup2
    dup1
    push2 0xca11
    gas
    callcode
    stop

callee_9 code:
    push2 0x0100
    push1 0x00
    dup2
    dup2
    push2 0xca11
    gas
    delegatecall
    stop

callee_10 code:
    gas
    push2 0x5a17
    add
    push2 0x0200
    push1 0x00
    dup1
    create2
    stop

callee_11 code:
    push2 0x0100
    push1 0x00
    dup2
    dup2
    push2 0xca11
    gas
    staticcall
    stop

contract code:
    push2 0xea60
    push3 0xc0de00
    push1 0x04
    calldataload
    add
    push1 0x00
    jumpdest
    push1 0x01
    dup2
    dup5
    sub
    gt
    push1 0x1c
    jumpi
    dup3
    push1 0x00
    sstore
    stop
    jumpdest
    push1 0x02
    ... (39 more instructions)
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
    ["tests/static/state_tests/stBadOpcode/measureGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c613900000000000000000000000000000000000000000000000000000000000000f2",
        "693c613900000000000000000000000000000000000000000000000000000000000000f1",
        "693c613900000000000000000000000000000000000000000000000000000000000000f5",
        "693c613900000000000000000000000000000000000000000000000000000000000000f0",
        "693c613900000000000000000000000000000000000000000000000000000000000000f4",
        "693c6139000000000000000000000000000000000000000000000000000000000000003b",
        "693c61390000000000000000000000000000000000000000000000000000000000000051",
        "693c61390000000000000000000000000000000000000000000000000000000000000053",
        "693c61390000000000000000000000000000000000000000000000000000000000000052",
        "693c61390000000000000000000000000000000000000000000000000000000000000020",
        "693c613900000000000000000000000000000000000000000000000000000000000000fa",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10'],
)
@pytest.mark.pre_alloc_mutable
def test_measure_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x000000000000000000000000000000000000ca11")
    callee_1 = Address("0x0000000000000000000000000000000000c0de20")
    callee_2 = Address("0x0000000000000000000000000000000000c0de3b")
    callee_3 = Address("0x0000000000000000000000000000000000c0de51")
    callee_4 = Address("0x0000000000000000000000000000000000c0de52")
    callee_5 = Address("0x0000000000000000000000000000000000c0de53")
    callee_6 = Address("0x0000000000000000000000000000000000c0def0")
    callee_7 = Address("0x0000000000000000000000000000000000c0def1")
    callee_8 = Address("0x0000000000000000000000000000000000c0def2")
    callee_9 = Address("0x0000000000000000000000000000000000c0def4")
    callee_10 = Address("0x0000000000000000000000000000000000c0def5")
    callee_11 = Address("0x0000000000000000000000000000000000c0defa")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1, code=bytes.fromhex("00"))
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=Op.PUSH2[0xbeef] + Op.PUSH1[0x0] + Op.SHA3 + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0xca11] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP3 + Op.EXTCODESIZE
        + Op.SWAP3 + Op.EXTCODECOPY + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=Op.PUSH2[0xb000] + Op.MLOAD + Op.STOP,
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=Op.PUSH1[0xff] + Op.PUSH2[0xb000] + Op.MSTORE + Op.STOP,
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=Op.PUSH1[0xff] + Op.PUSH2[0xb000] + Op.MSTORE8 + Op.STOP,
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=Op.PUSH2[0x200] + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE + Op.STOP,
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.DUP1
        + Op.PUSH2[0xca11] + Op.GAS + Op.CALL + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.DUP1
        + Op.PUSH2[0xca11] + Op.GAS + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.PUSH2[0xca11]
        + Op.GAS + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[callee_10] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.GAS + Op.PUSH2[0x5a17] + Op.ADD + Op.PUSH2[0x200] + Op.PUSH1[0x0]
        + Op.DUP1 + Op.CREATE2 + Op.STOP
    ),
    )
    pre[callee_11] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.PUSH2[0xca11]
        + Op.GAS + Op.STATICCALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0xea60] + Op.PUSH3[0xc0de00] + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.ADD + Op.PUSH1[0x0] + Op.JUMPDEST + Op.PUSH1[0x1] + Op.DUP2 + Op.DUP5
        + Op.SUB + Op.GT + Op.PUSH1[0x1c] + Op.JUMPI + Op.DUP3 + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x2] + Op.DUP4 + Op.DUP3
        + Op.ADD + Op.DIV + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP8 + Op.DUP7 + Op.CALL + Op.DUP1 + Op.ISZERO + Op.PUSH1[0x44]
        + Op.JUMPI + Op.JUMPDEST + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x3d] + Op.JUMPI
        + Op.JUMPDEST + Op.POP + Op.PUSH1[0xd] + Op.JUMP + Op.JUMPDEST + Op.SWAP3
        + Op.POP + Op.CODESIZE + Op.PUSH1[0x38] + Op.JUMP + Op.JUMPDEST + Op.SWAP1
        + Op.SWAP2 + Op.POP + Op.DUP2 + Op.SWAP1 + Op.PUSH1[0x31] + Op.JUMP
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
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
