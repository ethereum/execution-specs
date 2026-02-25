"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml

callee code:
    push2 0xde57
    selfdestruct
    stop

contract code:
    push1 0xff
    push2 0x0100
    mstore
    push1 0xff
    push2 0x0120
    mstore
    push2 0xca11
    balance
    pop
    push1 0x31
    push1 0x04
    calldataload
    eq
    push2 0x21
    jumpi
    push1 0x00
    push2 0x26
    jump
    jumpdest
    push2 0xde57
    ... (169 more instructions)
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
    ["tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000031",
        "693c613900000000000000000000000000000000000000000000000000000000000000f1",
        "693c613900000000000000000000000000000000000000000000000000000000000000f2",
        "693c613900000000000000000000000000000000000000000000000000000000000000f4",
        "693c6139000000000000000000000000000000000000000000000000000000000000003c",
        "693c6139000000000000000000000000000000000000000000000000000000000000003f",
        "693c6139000000000000000000000000000000000000000000000000000000000000003b",
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c613900000000000000000000000000000000000000000000000000000000000000fa",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8'],
)
@pytest.mark.pre_alloc_mutable
def test_eip2929_ff(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x000000000000000000000000000000000000ca11")
    callee_1 = Address("0x000000000000000000000000000000000000de57")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH2[0xde57] + Op.SELFDESTRUCT + Op.STOP,
    )
    pre[callee_1] = Account(balance=0, nonce=0, code=bytes.fromhex("00"))
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH2[0x100] + Op.MSTORE + Op.PUSH1[0xff]
        + Op.PUSH2[0x120] + Op.MSTORE + Op.PUSH2[0xca11] + Op.BALANCE + Op.POP
        + Op.PUSH1[0x31] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ + Op.PUSH2[0x21]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH2[0x26] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0xde57] + Op.BALANCE + Op.JUMPDEST + Op.POP + Op.PUSH1[0x3b]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ + Op.PUSH2[0x38] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.PUSH2[0x3d] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0xde57]
        + Op.EXTCODESIZE + Op.JUMPDEST + Op.POP + Op.PUSH1[0x3c] + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.EQ + Op.PUSH2[0x50] + Op.JUMPI + Op.PUSH1[0x0] + Op.POP
        + Op.PUSH2[0x5b] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xde57] + Op.EXTCODECOPY + Op.JUMPDEST
        + Op.PUSH1[0x3f] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ + Op.PUSH2[0x6c]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH2[0x71] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0xde57] + Op.EXTCODEHASH + Op.JUMPDEST + Op.POP + Op.PUSH1[0xf1]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ + Op.PUSH2[0x83] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.PUSH2[0x96] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xde57] + Op.PUSH3[0x10000] + Op.CALL + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0xf2] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ + Op.PUSH2[0xa8]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH2[0xbb] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xde57] + Op.PUSH3[0x10000] + Op.CALLCODE
        + Op.JUMPDEST + Op.POP + Op.PUSH1[0xf4] + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.EQ + Op.PUSH2[0xcd] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH2[0xde] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xde57] + Op.PUSH3[0x10000] + Op.DELEGATECALL + Op.JUMPDEST
        + Op.POP + Op.PUSH1[0xfa] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ
        + Op.PUSH2[0xf0] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH2[0x101] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xde57] + Op.PUSH3[0x10000] + Op.STATICCALL + Op.JUMPDEST + Op.POP
        + Op.GAS + Op.PUSH2[0x100] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xca11]
        + Op.PUSH4[0x1000000] + Op.CALL + Op.POP + Op.GAS + Op.PUSH2[0x120]
        + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x120] + Op.MLOAD + Op.PUSH2[0x100]
        + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS
        + Op.PUSH2[0x100] + Op.MSTORE + Op.PUSH2[0xde57] + Op.BALANCE + Op.POP
        + Op.GAS + Op.PUSH2[0x120] + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x120]
        + Op.MLOAD + Op.PUSH2[0x100] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
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
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
