"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml

callee code:
    push1 0x40
    push1 0x00
    push1 0x00
    codecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    mload
    push1 0x01
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x00
    sub
    push1 0x00
    push1 0x00
    codecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    mload
    push1 0x01
    sstore
    stop

callee_2 code:
    push2 0x1000
    push1 0x00
    push1 0x00
    codecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    mload
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x10
    push1 0x0f
    push1 0x0e
    push1 0x0d
    push1 0x0c
    push1 0x0b
    push1 0x0a
    push1 0x09
    push1 0x08
    push1 0x07
    push1 0x06
    push1 0x05
    push1 0x04
    push1 0x03
    push1 0x02
    push1 0x01
    add
    add
    add
    add
    ... (34 more instructions)

callee_4 code:
    codesize
    push1 0xff
    sstore
    push1 0xff
    sload
    push1 0x00
    push1 0x00
    codecopy
    push2 0x60a7
    push1 0x00
    sstore
    push2 0x60a7
    push1 0x01
    sstore
    push2 0x60a7
    push1 0x02
    sstore
    push1 0x00
    mload
    push1 0x00
    ... (36 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
    push2 0x1000
    add
    push3 0xffffff
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
    ["tests/static/state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4'],
)
@pytest.mark.pre_alloc_mutable
def test_codecopy(
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
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SUB + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x1000] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x10] + Op.PUSH1[0xf] + Op.PUSH1[0xe] + Op.PUSH1[0xd]
        + Op.PUSH1[0xc] + Op.PUSH1[0xb] + Op.PUSH1[0xa] + Op.PUSH1[0x9]
        + Op.PUSH1[0x8] + Op.PUSH1[0x7] + Op.PUSH1[0x6] + Op.PUSH1[0x5]
        + Op.PUSH1[0x4] + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.ADD
        + Op.ADD + Op.ADD + Op.ADD + Op.ADD + Op.ADD + Op.ADD + Op.ADD + Op.ADD
        + Op.ADD + Op.ADD + Op.ADD + Op.ADD + Op.ADD + Op.ADD + Op.PUSH2[0x100]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x40] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.CODESIZE + Op.PUSH1[0xff] + Op.SSTORE + Op.PUSH1[0xff] + Op.SLOAD
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x60a7]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH2[0x60a7] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH2[0x60a7] + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH1[0x60] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x4] + Op.SSTORE + Op.PUSH1[0xa0] + Op.MLOAD
        + Op.PUSH1[0x5] + Op.SSTORE + Op.STOP + Op.PUSH2[0xdead] + Op.SELFDESTRUCT
        + Op.PUSH1[0xff] + Op.SLOAD + Op.PUSH1[0x0] + Op.RETURN + Op.PUSH1[0xaa]
        + Op.PUSH1[0xbb] + Op.PUSH1[0xcc] + Op.PUSH1[0xdd] + Op.PUSH1[0xee]
        + Op.PUSH1[0xff] + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD
        + Op.PUSH3[0xffffff] + Op.DELEGATECALL + Op.STOP
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
