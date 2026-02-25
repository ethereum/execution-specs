"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stCreateTest/CreateCollisionResultsFiller.yml

callee code:
    push1 0x1d
    push1 0x00
    sstore
    stop

callee_1 code:
    push1 0x1d
    push1 0x00
    sstore
    stop

contract code:
    push1 0xf8
    push1 0x02
    exp
    push1 0x00
    calldataload
    div
    push2 0x0100
    mstore
    push1 0x15
    dup1
    push2 0x0158
    push2 0x0300
    codecopy
    push2 0x0540
    mstore
    push1 0x06
    dup1
    push2 0x016d
    push2 0x0200
    codecopy
    ... (128 more instructions)
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
    ["tests/static/state_tests/stCreateTest/CreateCollisionResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "01",
        "02",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_results(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x40f1299359ea754ac29eb2662a1900752bf8275f")
    callee_1 = Address("0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1d] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
        storage={0x0: 0x60a7},
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1d] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
        storage={0x0: 0x60a7},
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0xf8] + Op.PUSH1[0x2] + Op.EXP + Op.PUSH1[0x0] + Op.CALLDATALOAD
        + Op.DIV + Op.PUSH2[0x100] + Op.MSTORE + Op.PUSH1[0x15] + Op.DUP1
        + Op.PUSH2[0x158] + Op.PUSH2[0x300] + Op.CODECOPY + Op.PUSH2[0x540]
        + Op.MSTORE + Op.PUSH1[0x6] + Op.DUP1 + Op.PUSH2[0x16d] + Op.PUSH2[0x200]
        + Op.CODECOPY + Op.PUSH2[0x520] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH2[0x100]
        + Op.MLOAD + Op.EQ + Op.PUSH2[0x49] + Op.JUMPI + Op.PUSH2[0x5a17]
        + Op.PUSH2[0x540] + Op.MLOAD + Op.PUSH2[0x300] + Op.PUSH1[0x0] + Op.CREATE2
        + Op.PUSH2[0x600] + Op.MSTORE + Op.PUSH2[0x58] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0x540] + Op.MLOAD + Op.PUSH2[0x300] + Op.PUSH1[0x0] + Op.CREATE
        + Op.PUSH2[0x600] + Op.MSTORE + Op.JUMPDEST + Op.PC + Op.PUSH1[0x20]
        + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x10] + Op.SSTORE + Op.PUSH2[0x600]
        + Op.MLOAD + Op.PUSH1[0x11] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2] + Op.PUSH2[0xffff]
        + Op.CALL + Op.PUSH2[0x640] + Op.MSTORE + Op.PC + Op.PUSH1[0x21] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH2[0x640] + Op.MLOAD + Op.SUB + Op.PUSH1[0x12]
        + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x13] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x40f1299359ea754ac29eb2662a1900752bf8275f] + Op.PUSH2[0xffff]
        + Op.CALL + Op.PUSH2[0x640] + Op.MSTORE + Op.PC + Op.PUSH1[0x22] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH2[0x640] + Op.MLOAD + Op.SUB + Op.PUSH1[0x14]
        + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x15] + Op.SSTORE
        + Op.PUSH20[0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2] + Op.EXTCODESIZE
        + Op.PUSH1[0x30] + Op.SSTORE + Op.PUSH1[0x30] + Op.SLOAD + Op.PUSH1[0x0]
        + Op.PUSH2[0x660] + Op.PUSH20[0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2]
        + Op.EXTCODECOPY + Op.PUSH2[0x660] + Op.MLOAD + Op.PUSH1[0x31] + Op.SSTORE
        + Op.PUSH20[0x40f1299359ea754ac29eb2662a1900752bf8275f] + Op.EXTCODESIZE
        + Op.PUSH1[0x32] + Op.SSTORE + Op.PUSH1[0x32] + Op.SLOAD + Op.PUSH1[0x0]
        + Op.PUSH2[0x660] + Op.PUSH20[0x40f1299359ea754ac29eb2662a1900752bf8275f]
        + Op.EXTCODECOPY + Op.PUSH2[0x660] + Op.MLOAD + Op.PUSH1[0x33] + Op.SSTORE
        + Op.STOP + Op.INVALID + Op.PUSH1[0x6] + Op.DUP1 + Op.PUSH1[0xf]
        + Op.PUSH2[0x200] + Op.CODECOPY + Op.PUSH2[0x200] + Op.RETURN + Op.STOP
        + Op.INVALID + Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
        + Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x10: 0x60a7, 0x11: 0x60a7, 0x12: 0x60a7, 0x13: 0x60a7, 0x14: 0x60a7, 0x15: 0x60a7, 0x20: 0x60a7, 0x21: 0x60a7, 0x22: 0x60a7},
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
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
