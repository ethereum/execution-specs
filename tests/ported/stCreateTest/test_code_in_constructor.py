"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stCreateTest/CodeInConstructorFiller.yml

callee code:
    push1 0x00
    calldataload
    push1 0x00
    sload
    sstore
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    stop

contract code:
    push1 0x06
    dup1
    push2 0x4c
    push2 0x0100
    codecopy
    push2 0x0200
    mstore
    push1 0xdb
    dup1
    push2 0x52
    push1 0x00
    codecopy
    push2 0x0220
    mstore
    push1 0x01
    push1 0x04
    calldataload
    eq
    push1 0x37
    jumpi
    ... (133 more instructions)
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
    ["tests/static/state_tests/stCreateTest/CodeInConstructorFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "83c7d7580000000000000000000000000000000000000000000000000000000000000001",
        "83c7d7580000000000000000000000000000000000000000000000000000000000000002",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_code_in_constructor(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0xba5e0000ba5e0000ba5e0000ba5e0000ba5e0000")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x000000000000000000000000000000000000da7a")

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
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.SLOAD + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x1},
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x6] + Op.DUP1 + Op.PUSH2[0x4c] + Op.PUSH2[0x100] + Op.CODECOPY
        + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH1[0xdb] + Op.DUP1 + Op.PUSH2[0x52]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ + Op.PUSH1[0x37] + Op.JUMPI
        + Op.PUSH2[0x5a17] + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x45] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE + Op.JUMPDEST + Op.PUSH2[0x240]
        + Op.MSTORE + Op.STOP + Op.INVALID + Op.PUSH1[0xff] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP + Op.PUSH2[0x100] + Op.PUSH2[0x100] + Op.PUSH2[0x100]
        + Op.CODECOPY + Op.PC + Op.PUSH2[0x260] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH2[0x260] + Op.PUSH1[0x0]
        + Op.PUSH2[0xda7a] + Op.PUSH3[0xffffff] + Op.CALL + Op.POP + Op.ADDRESS
        + Op.PUSH2[0x260] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.PUSH2[0x260] + Op.PUSH1[0x0] + Op.PUSH2[0xda7a] + Op.PUSH3[0xffffff]
        + Op.CALL + Op.POP + Op.CODESIZE + Op.PUSH2[0x260] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH2[0x260] + Op.PUSH1[0x0]
        + Op.PUSH2[0xda7a] + Op.PUSH3[0xffffff] + Op.CALL + Op.POP + Op.ADDRESS
        + Op.EXTCODESIZE + Op.PUSH2[0x260] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH2[0x260] + Op.PUSH1[0x0] + Op.PUSH2[0xda7a]
        + Op.PUSH3[0xffffff] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH2[0x100] + Op.CODECOPY + Op.PUSH2[0x100] + Op.MLOAD + Op.PUSH2[0x260]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH2[0x260]
        + Op.PUSH1[0x0] + Op.PUSH2[0xda7a] + Op.PUSH3[0xffffff] + Op.CALL + Op.POP
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.ADDRESS
        + Op.EXTCODECOPY + Op.PUSH2[0x100] + Op.MLOAD + Op.PUSH2[0x260] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH2[0x260]
        + Op.PUSH1[0x0] + Op.PUSH2[0xda7a] + Op.PUSH3[0xffffff] + Op.CALL + Op.POP
        + Op.PC + Op.PUSH2[0x260] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH2[0x260] + Op.PUSH1[0x0] + Op.PUSH2[0xda7a]
        + Op.PUSH3[0xffffff] + Op.CALL + Op.POP + Op.PUSH2[0x100] + Op.CODESIZE
        + Op.SUB + Op.PUSH2[0x100] + Op.RETURN + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=9437184,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
