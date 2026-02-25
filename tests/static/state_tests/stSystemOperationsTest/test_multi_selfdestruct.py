"""
Implements: SUC000, SUC001, SUC002, SUC003, SUC004, SUC005


Ported from:
tests/static/state_tests/stSystemOperationsTest/multiSelfdestructFiller.yml

callee code:
    push1 0x00
    calldataload
    push1 0xf8
    shr
    push2 0xffff
    push1 0x00
    calldataload
    push1 0xe8
    shr
    and
    push1 0x00
    dup3
    eq
    push1 0x34
    jumpi
    push1 0xff
    dup3
    eq
    push1 0x32
    jumpi
    ... (21 more instructions)

contract code:
    push1 0xff
    push1 0x00
    mstore8
    push1 0x10
    push1 0x01
    mstore8
    push1 0x00
    push1 0x02
    mstore8
    push1 0x00
    dup1
    push1 0x03
    dup2
    dup1
    push2 0xdead
    gas
    call
    push1 0x00
    sstore
    push2 0x1000
    ... (126 more instructions)
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
    ["tests/static/state_tests/stSystemOperationsTest/multiSelfdestructFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "01",
        "02",
        "03",
        "04",
        "05",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4'],
)
@pytest.mark.pre_alloc_mutable
def test_multi_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Implements: SUC000, SUC001, SUC002, SUC003, SUC004, SUC005
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x000000000000000000000000000000000000dead")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    pre[callee] = Account(
        balance=3,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xf8] + Op.SHR + Op.PUSH2[0xffff]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe8] + Op.SHR + Op.AND
        + Op.PUSH1[0x0] + Op.DUP3 + Op.EQ + Op.PUSH1[0x34] + Op.JUMPI + Op.PUSH1[0xff]
        + Op.DUP3 + Op.EQ + Op.PUSH1[0x32] + Op.JUMPI + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.SWAP5 + Op.DUP2 + Op.SWAP5 + Op.GAS + Op.CALL + Op.EQ
        + Op.PUSH1[0x2d] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP1
        + Op.REVERT + Op.JUMPDEST + Op.SELFDESTRUCT + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    pre[contract] = Account(
        balance=0x5f5e100,
        nonce=1,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.PUSH1[0x10] + Op.PUSH1[0x1]
        + Op.MSTORE8 + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.MSTORE8 + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x3] + Op.DUP2 + Op.DUP1 + Op.PUSH2[0xdead] + Op.GAS
        + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH2[0x1000] + Op.BALANCE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0xdead] + Op.BALANCE + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xf8] + Op.SHR
        + Op.DUP1 + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0xce] + Op.JUMPI + Op.DUP1
        + Op.PUSH1[0x2] + Op.EQ + Op.PUSH1[0xbc] + Op.JUMPI + Op.DUP1 + Op.PUSH1[0x3]
        + Op.EQ + Op.PUSH1[0xa5] + Op.JUMPI + Op.DUP1 + Op.PUSH1[0x4] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x5] + Op.EQ + Op.PUSH1[0x58]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.DUP1 + Op.REVERT + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.MSTORE8 + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE8
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x3] + Op.DUP2 + Op.PUSH1[0x2]
        + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.JUMPDEST + Op.PUSH1[0x10]
        + Op.SSTORE + Op.PUSH2[0x1000] + Op.BALANCE + Op.PUSH1[0x11] + Op.SSTORE
        + Op.PUSH2[0xdead] + Op.BALANCE + Op.PUSH1[0x12] + Op.SSTORE
        + Op.PUSH2[0x1001] + Op.BALANCE + Op.PUSH1[0x13] + Op.SSTORE + Op.STOP
        + Op.JUMPDEST + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE8
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE8 + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x3] + Op.DUP2 + Op.DUP1 + Op.PUSH2[0xdead] + Op.GAS + Op.CALL
        + Op.PUSH1[0x70] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MSTORE8 + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x3]
        + Op.DUP2 + Op.PUSH1[0x2] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL
        + Op.PUSH1[0x70] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x3] + Op.DUP2 + Op.PUSH1[0x2] + Op.PUSH2[0xdead] + Op.GAS
        + Op.CALL + Op.PUSH1[0x70] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x3] + Op.DUP1 + Op.PUSH1[0x2] + Op.PUSH2[0xdead]
        + Op.GAS + Op.CALL + Op.PUSH1[0x70] + Op.JUMP
    ),
        storage={0x0: 0x60a7, 0x1: 0x60a7, 0x10: 0x60a7, 0x11: 0x60a7, 0x12: 0x60a7, 0x13: 0x60a7},
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=10000000,
        gas_price=1000,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
