"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stCreateTest/createFailResultFiller.yml

callee code:
    push6 0x0bad0bad0bad
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    revert

callee_1 code:
    push2 0x600d
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return

callee_2 code:
    push4 0xdeadbeef
    push1 0x00
    mstore
    push2 0x60a7
    push1 0x20
    mstore
    push1 0x40
    push1 0x00
    return

callee_3 code:
    push1 0x40
    push2 0x0100
    push1 0x00
    dup1
    dup1
    push2 0xda7a
    gas
    call
    push1 0x10
    sstore
    returndatasize
    push1 0x11
    sstore
    push2 0x0100
    mload
    push1 0x12
    sstore
    push2 0x0120
    mload
    push1 0x13
    ... (32 more instructions)

callee_4 code:
    push1 0x40
    push2 0x0100
    push1 0x00
    dup1
    dup1
    push2 0xda7a
    gas
    call
    push1 0x10
    sstore
    returndatasize
    push1 0x11
    sstore
    push2 0x0100
    mload
    push1 0x12
    sstore
    push2 0x0120
    mload
    push1 0x13
    ... (32 more instructions)

callee_5 code:
    push1 0x40
    push2 0x0100
    push1 0x00
    dup1
    dup1
    push2 0xda7a
    gas
    call
    push1 0x10
    sstore
    returndatasize
    push1 0x11
    sstore
    push2 0x0100
    mload
    push1 0x12
    sstore
    push2 0x0120
    mload
    push1 0x13
    ... (33 more instructions)

callee_6 code:
    push1 0x40
    push2 0x0100
    push1 0x00
    dup1
    dup1
    push2 0xda7a
    gas
    call
    push1 0x10
    sstore
    returndatasize
    push1 0x11
    sstore
    push2 0x0100
    mload
    push1 0x12
    sstore
    push2 0x0120
    mload
    push1 0x13
    ... (33 more instructions)

callee_7 code:
    push1 0x01
    stop

callee_8 code:
    push1 0x01
    stop

contract code:
    push1 0x20
    push2 0x0200
    dup2
    push1 0x00
    dup1
    push3 0xc0de00
    push1 0x04
    calldataload
    add
    push1 0x24
    calldataload
    push1 0x40
    push2 0x0100
    dup5
    dup1
    dup1
    push2 0xda7a
    gas
    call
    push1 0x10
    ... (39 more instructions)

callee_9 code:
    push1 0x01
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
    ["tests/static/state_tests/stCreateTest/createFailResultFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "1a8451e600000000000000000000000000000000000000000000000000000000000000ee0000000000000000000000000000000000000000000000000000000000000bad",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000bad",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000ee000000000000000000000000000000000000000000000000000000000000600d",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000600d",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000006",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000bad",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000bad",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000600d",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000600d",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000006",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9'],
)
@pytest.mark.pre_alloc_mutable
def test_create_fail_result(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x0000000000000000000000000000000000000bad")
    callee_1 = Address("0x000000000000000000000000000000000000600d")
    callee_2 = Address("0x000000000000000000000000000000000000da7a")
    callee_3 = Address("0x0000000000000000000000000000000000c0deee")
    callee_4 = Address("0x0000000000000000000000000000000000c0def0")
    callee_5 = Address("0x0000000000000000000000000000000000c0def5")
    callee_6 = Address("0x0000000000000000000000000000000000c0deff")
    callee_7 = Address("0x13c950f8740ffaea1869a88d70b029e8b0c9a8da")
    callee_8 = Address("0xbb0237ab04970e3cf3e813c02064662adc89336b")
    callee_9 = Address("0xf9d1ea8eab6963659ee85b3e0b4d8a57e7edba2b")

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
        Op.PUSH6[0xbad0bad0bad] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.REVERT
    ),
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH4[0xdeadbeef] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x60a7]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x40] + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xda7a] + Op.GAS + Op.CALL + Op.PUSH1[0x10] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x11] + Op.SSTORE + Op.PUSH2[0x100] + Op.MLOAD
        + Op.PUSH1[0x12] + Op.SSTORE + Op.PUSH2[0x120] + Op.MLOAD + Op.PUSH1[0x13]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.CALLDATALOAD + Op.DUP2 + Op.DUP2
        + Op.EXTCODESIZE + Op.SWAP3 + Op.DUP4 + Op.SWAP3 + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x1] + Op.SSTORE + Op.RETURNDATASIZE
        + Op.PUSH1[0x0] + Op.PUSH2[0x200] + Op.RETURNDATACOPY + Op.PUSH2[0x200]
        + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH2[0x220] + Op.MLOAD
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x40] + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xda7a] + Op.GAS + Op.CALL + Op.PUSH1[0x10] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x11] + Op.SSTORE + Op.PUSH2[0x100] + Op.MLOAD
        + Op.PUSH1[0x12] + Op.SSTORE + Op.PUSH2[0x120] + Op.MLOAD + Op.PUSH1[0x13]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.CALLDATALOAD + Op.DUP2 + Op.DUP2
        + Op.EXTCODESIZE + Op.SWAP3 + Op.DUP4 + Op.SWAP3 + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x1] + Op.SSTORE + Op.RETURNDATASIZE
        + Op.PUSH1[0x0] + Op.PUSH2[0x200] + Op.RETURNDATACOPY + Op.PUSH2[0x200]
        + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH2[0x220] + Op.MLOAD
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x40] + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xda7a] + Op.GAS + Op.CALL + Op.PUSH1[0x10] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x11] + Op.SSTORE + Op.PUSH2[0x100] + Op.MLOAD
        + Op.PUSH1[0x12] + Op.SSTORE + Op.PUSH2[0x120] + Op.MLOAD + Op.PUSH1[0x13]
        + Op.SSTORE + Op.PUSH2[0x5a17] + Op.PUSH1[0x0] + Op.DUP1 + Op.CALLDATALOAD
        + Op.DUP2 + Op.DUP2 + Op.EXTCODESIZE + Op.SWAP3 + Op.DUP4 + Op.SWAP3
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x0] + Op.PUSH2[0x200] + Op.RETURNDATACOPY
        + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH2[0x220]
        + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x40] + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xda7a] + Op.GAS + Op.CALL + Op.PUSH1[0x10] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x11] + Op.SSTORE + Op.PUSH2[0x100] + Op.MLOAD
        + Op.PUSH1[0x12] + Op.SSTORE + Op.PUSH2[0x120] + Op.MLOAD + Op.PUSH1[0x13]
        + Op.SSTORE + Op.PUSH4[0xbad05a17] + Op.PUSH1[0x0] + Op.DUP1 + Op.CALLDATALOAD
        + Op.DUP2 + Op.DUP2 + Op.EXTCODESIZE + Op.SWAP3 + Op.DUP4 + Op.SWAP3
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x0] + Op.PUSH2[0x200] + Op.RETURNDATACOPY
        + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH2[0x220]
        + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(balance=0x600d, nonce=1, code=Op.PUSH1[0x1] + Op.STOP)
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[callee_8] = Account(balance=0x600d, nonce=1, code=Op.PUSH1[0x1] + Op.STOP)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x20] + Op.PUSH2[0x200] + Op.DUP2 + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH3[0xc0de00] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.ADD
        + Op.PUSH1[0x24] + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.PUSH2[0x100]
        + Op.DUP5 + Op.DUP1 + Op.DUP1 + Op.PUSH2[0xda7a] + Op.GAS + Op.CALL
        + Op.PUSH1[0x10] + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x11] + Op.SSTORE
        + Op.PUSH2[0x100] + Op.MLOAD + Op.PUSH1[0x12] + Op.SSTORE + Op.PUSH2[0x120]
        + Op.MLOAD + Op.PUSH1[0x13] + Op.SSTORE + Op.GAS + Op.SWAP1 + Op.PUSH1[0x6]
        + Op.DUP2 + Op.EQ + Op.PUSH1[0x52] + Op.JUMPI + Op.JUMPDEST + Op.DUP4
        + Op.MSTORE + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.RETURNDATASIZE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH1[0x2]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH3[0x1ce80] + Op.SWAP2 + Op.POP
        + Op.PUSH1[0x3f] + Op.JUMP
    ),
    )
    pre[callee_9] = Account(balance=0x600d, nonce=1, code=Op.PUSH1[0x1] + Op.STOP)

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
