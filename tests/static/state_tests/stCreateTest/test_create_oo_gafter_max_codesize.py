"""
Ported from:
tests/static/state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml

callee code:
    codesize
    push1 0x00
    sstore
    push1 0x00
    calldatasize
    gt
    push1 0x0c
    jumpi
    stop
    jumpdest
    push1 0x00
    selfdestruct

callee_1 code:
    push3 0x0c0de0
    push1 0x00
    dup1
    dup3
    extcodesize
    swap3
    extcodecopy
    push2 0x6000
    push1 0x00
    return

contract code:
    push1 0x04
    calldataload
    push1 0x24
    calldataload
    push1 0x44
    calldataload
    swap1
    push1 0x64
    calldataload
    swap3
    dup1
    push1 0x00
    mstore
    push1 0x00
    push1 0x20
    mstore
    push1 0x00
    push1 0x40
    push1 0x20
    dup4
    ... (125 more instructions)

callee_2 code:
    push1 0x01
    dup1
    sstore
    push1 0x00
    dup1
    calldataload
    push1 0x20
    calldataload
    push3 0x0c0de1
    dup4
    dup2
    extcodesize
    swap5
    dup6
    swap3
    extcodecopy
    push1 0x00
    jumpdest
    dup3
    dup2
    ... (30 more instructions)
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
    ["tests/static/state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "a6f227c000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",
        "a6f227c000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001ee",
        "a6f227c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",
        "a6f227c0000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",
        "a6f227c0000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e",
        "a6f227c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5'],
)
@pytest.mark.pre_alloc_mutable
def test_create_oo_gafter_max_codesize(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x00000000000000000000000000000000000c0dea")
    callee = Address("0x00000000000000000000000000000000000c0de0")
    callee_1 = Address("0x00000000000000000000000000000000000c0de1")
    callee_2 = Address("0x00000000000000000000000000000000000c0deb")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.CODESIZE + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.CALLDATASIZE
        + Op.GT + Op.PUSH1[0xc] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.SELFDESTRUCT
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH3[0xc0de0] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP3 + Op.EXTCODESIZE
        + Op.SWAP3 + Op.EXTCODECOPY + Op.PUSH2[0x6000] + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x24] + Op.CALLDATALOAD
        + Op.PUSH1[0x44] + Op.CALLDATALOAD + Op.SWAP1 + Op.PUSH1[0x64]
        + Op.CALLDATALOAD + Op.SWAP3 + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH1[0x20] + Op.DUP4 + Op.MUL + Op.SWAP1 + Op.PUSH1[0x40] + Op.DUP4
        + Op.PUSH3[0xc0deb] + Op.PUSH1[0x2] + Op.GAS + Op.DIV + Op.DELEGATECALL
        + Op.EQ + Op.PUSH1[0xbf] + Op.JUMPI + Op.DUP2 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.DUP3 + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.DUP3 + Op.MUL + Op.PUSH1[0x40] + Op.ADD + Op.PUSH1[0x20] + Op.DUP5
        + Op.MUL + Op.SWAP1 + Op.PUSH1[0x40] + Op.DUP4 + Op.DUP1 + Op.PUSH3[0xc0deb]
        + Op.PUSH1[0x2] + Op.GAS + Op.DIV + Op.CALL + Op.EQ + Op.PUSH1[0xba]
        + Op.JUMPI + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP2 + Op.SWAP4 + Op.EQ
        + Op.PUSH1[0xb1] + Op.JUMPI + Op.JUMPDEST + Op.POP + Op.POP + Op.PUSH1[0x0]
        + Op.JUMPDEST + Op.DUP2 + Op.DUP2 + Op.LT + Op.PUSH1[0x94] + Op.JUMPI
        + Op.DUP3 + Op.PUSH1[0x0] + Op.JUMPDEST + Op.DUP2 + Op.DUP2 + Op.LT
        + Op.PUSH1[0x77] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x1] + Op.DUP2 + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP4
        + Op.SWAP8 + Op.MUL + Op.PUSH1[0x40] + Op.ADD + Op.MLOAD + Op.PUSH2[0x3e8]
        + Op.GAS + Op.SUB + Op.CALL + Op.POP + Op.ADD + Op.PUSH1[0x6f] + Op.JUMP
        + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.PUSH1[0x20] + Op.PUSH1[0x1] + Op.SWAP8 + Op.MUL
        + Op.PUSH1[0x40] + Op.ADD + Op.MLOAD + Op.PUSH2[0x3e8] + Op.GAS + Op.SUB
        + Op.CALL + Op.POP + Op.ADD + Op.PUSH1[0x65] + Op.JUMP + Op.JUMPDEST + Op.ADD
        + Op.SWAP1 + Op.POP + Op.CODESIZE + Op.DUP1 + Op.PUSH1[0x60] + Op.JUMP
        + Op.JUMPDEST + Op.DUP3 + Op.PUSH1[0x57] + Op.JUMPI + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.DUP1 + Op.REVERT
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x1] + Op.DUP1 + Op.SSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.CALLDATALOAD + Op.PUSH3[0xc0de1]
        + Op.DUP4 + Op.DUP2 + Op.EXTCODESIZE + Op.SWAP5 + Op.DUP6 + Op.SWAP3
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.JUMPDEST + Op.DUP3 + Op.DUP2 + Op.LT
        + Op.PUSH1[0x2d] + Op.JUMPI + Op.POP + Op.PUSH1[0x0] + Op.LT + Op.PUSH1[0x2b]
        + Op.JUMPI + Op.PUSH1[0x20] + Op.MUL + Op.SWAP1 + Op.RETURN + Op.JUMPDEST
        + Op.INVALID + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SWAP1 + Op.DUP5
        + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE + Op.PUSH1[0x20] + Op.DUP3 + Op.MUL
        + Op.DUP7 + Op.ADD + Op.MSTORE + Op.ADD + Op.PUSH1[0x18] + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=4294967296,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
