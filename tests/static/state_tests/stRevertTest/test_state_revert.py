"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stRevertTest/stateRevertFiller.yml

callee code:
    push2 0x1001
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xdead
    push2 0x7530
    gas
    sub
    delegatecall
    pop
    jumpdest
    push1 0x01
    iszero
    push1 0x2b
    jumpi
    push4 0x01000000
    push1 0x00
    ... (6 more instructions)

contract code:
    push2 0x60a7
    push1 0x00
    sstore
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

callee_2 code:
    push2 0x60a7
    push1 0x02
    sstore
    stop

callee_3 code:
    push2 0x1000
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xdead
    push2 0x7530
    gas
    sub
    delegatecall
    pop
    push1 0x10
    push1 0x00
    revert
    stop

callee_4 code:
    push2 0x0105
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xdead
    push2 0x7530
    gas
    sub
    delegatecall
    pop
    add
    add
    add

callee_5 code:
    push2 0x0104
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xdead
    push2 0x7530
    gas
    sub
    delegatecall
    pop
    push1 0x00
    jump

callee_6 code:
    push2 0x0106
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xdead
    push2 0x7530
    gas
    sub
    delegatecall
    pop
    jumpdest
    pc
    push1 0x04
    pc
    sub
    jump

callee_7 code:
    push2 0x1002
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xdead
    push2 0x7530
    gas
    sub
    delegatecall
    pop
    push1 0x01
    push1 0x00
    sub
    push1 0x00
    sha3
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
    ["tests/static/state_tests/stRevertTest/stateRevertFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c61390000000000000000000000000000000000000000000000000000000000000006",
        "693c61390000000000000000000000000000000000000000000000000000000000000005",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6'],
)
@pytest.mark.pre_alloc_mutable
def test_state_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x64a703f9294edbbf778201f3c2a87c7f91be5a8c")
    contract = Address("0x3559afe49654b532b7e67e6acd87deb8c569e7ad")
    callee = Address("0x16d83da4c22c26f92c5a8d4cedf367e171f60977")
    callee_1 = Address("0x1985064d96baaf3305fee248de22965fbf7fbab6")
    callee_2 = Address("0x4edc28ff01c9f8731ede6d0fd953da91f749a659")
    callee_3 = Address("0x71a06d553f1ac38b5e568ce5a1b5df253ad08d73")
    callee_4 = Address("0xbf0fc73e06f3b2eca8cb8094bdb81d4d2aa2f9b0")
    callee_5 = Address("0xdd77382f06bfeea4258e6f7bffc6d9d31b885815")
    callee_6 = Address("0xe08a8de27b3798640d504f1431a360f276b9f2ae")
    callee_7 = Address("0xebe3a4514feca3eb2819bf83ebd926c5e4143739")

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
        Op.PUSH2[0x1001] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.PUSH2[0x7530] + Op.GAS
        + Op.SUB + Op.DELEGATECALL + Op.POP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.ISZERO
        + Op.PUSH1[0x2b] + Op.JUMPI + Op.PUSH4[0x1000000] + Op.PUSH1[0x0] + Op.SHA3
        + Op.POP + Op.PUSH1[0x18] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=bytes.fromhex("610103600155600060006000600061dead6175305a03f450ba"),
    )
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x60a7] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH2[0x1000] + Op.ADD + Op.GAS + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH2[0x60a7] + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x1000] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.PUSH2[0x7530] + Op.GAS
        + Op.SUB + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x10] + Op.PUSH1[0x0]
        + Op.REVERT + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x105] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.PUSH2[0x7530] + Op.GAS
        + Op.SUB + Op.DELEGATECALL + Op.POP + Op.ADD + Op.ADD + Op.ADD
    ),
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x104] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.PUSH2[0x7530] + Op.GAS
        + Op.SUB + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0] + Op.JUMP
    ),
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x106] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.PUSH2[0x7530] + Op.GAS
        + Op.SUB + Op.DELEGATECALL + Op.POP + Op.JUMPDEST + Op.PC + Op.PUSH1[0x4]
        + Op.PC + Op.SUB + Op.JUMP
    ),
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x1002] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.PUSH2[0x7530] + Op.GAS
        + Op.SUB + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SUB
        + Op.PUSH1[0x0] + Op.SHA3 + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xa62d63f95900b04ccd3fee13360de78966f24695945e8b2c09e646352bc5af94"
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
