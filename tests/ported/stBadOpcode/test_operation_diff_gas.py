"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stBadOpcode/operationDiffGasFiller.yml

callee code:
    push4 0xdeadbeef
    push1 0x00
    mstore
    push2 0x0100
    push1 0x00
    return

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
    push2 0xbeef
    mload
    stop

callee_4 code:
    push1 0xff
    push2 0xbeef
    mstore
    stop

callee_5 code:
    push1 0xff
    push2 0xbeef
    mstore8
    stop

callee_6 code:
    push2 0x0200
    push1 0x00
    dup1
    create
    push1 0x00
    sstore
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
    push2 0x5a17
    push2 0x0200
    push1 0x00
    dup1
    create2
    push1 0x00
    sstore
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
    push1 0x44
    calldataload
    push1 0x24
    calldataload
    push3 0xc0de00
    push1 0x04
    calldataload
    add
    push1 0x00
    dup1
    jumpdest
    eq
    push1 0x1c
    jumpi
    pop
    sub
    push1 0x00
    sstore
    stop
    jumpdest
    ... (15 more instructions)
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
    ["tests/static/state_tests/stBadOpcode/operationDiffGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "048071d300000000000000000000000000000000000000000000000000000000000000f200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d300000000000000000000000000000000000000000000000000000000000000f100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d300000000000000000000000000000000000000000000000000000000000000f400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d3000000000000000000000000000000000000000000000000000000000000003b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d3000000000000000000000000000000000000000000000000000000000000005100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d3000000000000000000000000000000000000000000000000000000000000005300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d3000000000000000000000000000000000000000000000000000000000000005200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
        "048071d300000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10'],
)
@pytest.mark.pre_alloc_mutable
def test_operation_diff_gas(
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

    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH4[0xdeadbeef] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x100]
        + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
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
        code=Op.PUSH2[0xbeef] + Op.MLOAD + Op.STOP,
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=Op.PUSH1[0xff] + Op.PUSH2[0xbeef] + Op.MSTORE + Op.STOP,
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=Op.PUSH1[0xff] + Op.PUSH2[0xbeef] + Op.MSTORE8 + Op.STOP,
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0x200] + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
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
        Op.PUSH2[0x5a17] + Op.PUSH2[0x200] + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE2
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
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
        Op.PUSH1[0x44] + Op.CALLDATALOAD + Op.PUSH1[0x24] + Op.CALLDATALOAD
        + Op.PUSH3[0xc0de00] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.ADD
        + Op.PUSH1[0x0] + Op.DUP1 + Op.JUMPDEST + Op.EQ + Op.PUSH1[0x1c] + Op.JUMPI
        + Op.POP + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.DUP4 + Op.DUP2 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP8 + Op.DUP10 + Op.CALL + Op.SWAP4 + Op.ADD + Op.SWAP3 + Op.PUSH1[0x11]
        + Op.JUMP
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
