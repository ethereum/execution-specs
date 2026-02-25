"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml

callee code:
    calldatasize
    push1 0x12
    jumpi
    jumpdest
    push1 0x0b
    push0
    push1 0x20
    jump
    jumpdest
    push0
    mstore
    push1 0x20
    push0
    return
    jumpdest
    push1 0x1c
    push2 0x60a7
    push0
    push1 0x24
    jump
    ... (10 more instructions)

callee_1 code:
    push1 0x10
    push1 0x01
    push1 0x0a
    push0
    push1 0x12
    jump
    jumpdest
    add
    push0
    push1 0x16
    jump
    jumpdest
    stop
    jumpdest
    tload
    swap1
    jump
    jumpdest
    tstore
    jump

callee_2 code:
    address
    caller
    eq
    push1 0x33
    jumpi
    jumpdest
    address
    caller
    sub
    push1 0x0e
    jumpi
    stop
    jumpdest
    push1 0x1b
    push0
    calldataload
    dup1
    push1 0x01
    sstore
    push0
    ... (96 more instructions)

callee_3 code:
    push4 0xca11bacc
    caller
    eq
    push1 0x3f
    jumpi
    jumpdest
    push4 0xca11bacc
    caller
    sub
    push1 0x16
    jumpi
    stop
    jumpdest
    push1 0x23
    push0
    calldataload
    dup1
    push1 0x01
    sstore
    push0
    ... (73 more instructions)

callee_4 code:
    push1 0x20
    push0
    push1 0x01
    dup2
    dup1
    push2 0x57a7
    gas
    call
    push1 0x10
    sstore
    push0
    mload
    push0
    sstore
    push0
    dup1
    mstore
    push1 0x20
    push0
    dup1
    ... (27 more instructions)

callee_5 code:
    address
    caller
    eq
    push1 0x33
    jumpi
    jumpdest
    address
    caller
    sub
    push1 0x0e
    jumpi
    stop
    jumpdest
    push1 0x1b
    push0
    calldataload
    dup1
    push1 0x01
    sstore
    push0
    ... (73 more instructions)

callee_6 code:
    address
    caller
    eq
    push1 0x33
    jumpi
    jumpdest
    address
    caller
    sub
    push1 0x0e
    jumpi
    stop
    jumpdest
    push1 0x1b
    push0
    calldataload
    dup1
    push1 0x01
    sstore
    push0
    ... (95 more instructions)

callee_7 code:
    push1 0x06
    push0
    push1 0x4e
    jump
    jumpdest
    push0
    sstore
    push0
    dup1
    dup1
    dup1
    dup1
    push2 0xadd1
    gas
    callcode
    push1 0x11
    sstore
    push1 0x1c
    push0
    push1 0x4e
    ... (42 more instructions)

callee_8 code:
    address
    caller
    eq
    push1 0x33
    jumpi
    jumpdest
    address
    caller
    sub
    push1 0x0e
    jumpi
    stop
    jumpdest
    push1 0x1b
    push0
    calldataload
    dup1
    push1 0x01
    sstore
    push0
    ... (72 more instructions)

callee_9 code:
    calldatasize
    iszero
    push1 0x81
    jumpi
    caller
    address
    sub
    push1 0x74
    jumpi
    jumpdest
    push0
    calldataload
    push1 0xf8
    shr
    push0
    calldataload
    push0
    mstore
    push1 0x01
    calldatasize
    ... (109 more instructions)

callee_10 code:
    push1 0x06
    push0
    push1 0x1d
    jump
    jumpdest
    push0
    sstore
    push1 0x10
    push1 0x01
    push1 0x1d
    jump
    jumpdest
    push1 0x01
    sstore
    push0
    dup1
    dup1
    dup1
    dup1
    caller
    ... (7 more instructions)

callee_11 code:
    address
    caller
    eq
    push1 0x33
    jumpi
    jumpdest
    address
    caller
    sub
    push1 0x0e
    jumpi
    stop
    jumpdest
    push1 0x1b
    push0
    calldataload
    dup1
    push1 0x01
    sstore
    push0
    ... (73 more instructions)

contract code:
    push0
    dup1
    push1 0x20
    dup2
    dup1
    dup1
    calldataload
    push1 0xe0
    shr
    push1 0x04
    calldataload
    dup2
    dup4
    sstore
    dup3
    mstore
    gas
    call
    push1 0x01
    sstore
    ... (1 more instructions)
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
    ["tests/static/state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "264bb86a0000000000000000000000000000000000000000000000000000000000000006",
        "5114e2c8000000000000000000000000000000000000000000000000000000000000000a",
        "5114e2c80000000000000000000000000000000000000000000000000000000000000032",
        "6e3a72040000000000000000000000000000000000000000000000000000000000000010",
        "c54b5829f1f1f1f1f2f2f2f2f4f4f4f4f1f1f1f1f2f2f2f2f4f4f4f4f1f1f1f1f2f2f2f2",
        "c54b5829f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1",
        "c54b5829f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1",
        "c54b5829f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2",
        "c54b5829f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4",
        "c54b5829f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f1f1",
        "7074a4860000000000000000000000000000000000000000000000000000000000000006",
        "c1c922f10000000000000000000000000000000000000000000000000000000000000010",
        "7f9317bd",
        "5d7935df",
        "ebd141d50000000000000000000000000000000000000000000000000000000000000010",
        "ebd141d50000000000000000000000000000000000000000000000000000000000000100",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15'],
)
@pytest.mark.pre_alloc_mutable
def test_trans_storage_ok(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x485fd0fd5c1d0409d2b772a66e98a6ac867b9d8b")
    contract = Address("0xdd53b677a6fd4e871a6355f283b1bd7ceb95a95e")
    callee = Address("0x00000000000000000000000000000000000057a7")
    callee_1 = Address("0x000000000000000000000000000000000000add1")
    callee_2 = Address("0x00000000000000000000000000000000264bb86a")
    callee_3 = Address("0x000000000000000000000000000000005114e2c8")
    callee_4 = Address("0x000000000000000000000000000000005d7935df")
    callee_5 = Address("0x000000000000000000000000000000006e3a7204")
    callee_6 = Address("0x000000000000000000000000000000007074a486")
    callee_7 = Address("0x000000000000000000000000000000007f9317bd")
    callee_8 = Address("0x00000000000000000000000000000000c1c922f1")
    callee_9 = Address("0x00000000000000000000000000000000c54b5829")
    callee_10 = Address("0x00000000000000000000000000000000ca11bacc")
    callee_11 = Address("0x00000000000000000000000000000000ebd141d5")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.CALLDATASIZE + Op.PUSH1[0x12] + Op.JUMPI + Op.JUMPDEST + Op.PUSH1[0xb]
        + Op.PUSH0 + Op.PUSH1[0x20] + Op.JUMP + Op.JUMPDEST + Op.PUSH0 + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH0 + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x1c]
        + Op.PUSH2[0x60a7] + Op.PUSH0 + Op.PUSH1[0x24] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x4] + Op.JUMP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x10] + Op.PUSH1[0x1] + Op.PUSH1[0xa] + Op.PUSH0 + Op.PUSH1[0x12]
        + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.PUSH0 + Op.PUSH1[0x16] + Op.JUMP
        + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.ADDRESS + Op.CALLER + Op.EQ + Op.PUSH1[0x33] + Op.JUMPI + Op.JUMPDEST
        + Op.ADDRESS + Op.CALLER + Op.SUB + Op.PUSH1[0xe] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x1b] + Op.PUSH0 + Op.CALLDATALOAD + Op.DUP1
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.PUSH1[0x8d] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS
        + Op.GAS + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2e]
        + Op.PUSH1[0x1] + Op.PUSH1[0x89] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3a] + Op.PUSH0
        + Op.PUSH1[0x89] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.ISZERO
        + Op.PUSH1[0x87] + Op.JUMPI + Op.PUSH1[0x4a] + Op.PUSH1[0x1] + Op.DUP3
        + Op.SUB + Op.PUSH0 + Op.PUSH1[0x8d] + Op.JUMP + Op.JUMPDEST + Op.PUSH0
        + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS + Op.GAS + Op.CALL
        + Op.ISZERO + Op.PUSH1[0x83] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x61]
        + Op.SWAP2 + Op.SUB + Op.PUSH0 + Op.PUSH1[0x8d] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS + Op.GAS
        + Op.CALL + Op.ISZERO + Op.PUSH1[0x83] + Op.JUMPI + Op.PUSH1[0x7f]
        + Op.PUSH1[0x1] + Op.PUSH1[0x78] + Op.DUP2 + Op.PUSH1[0x89] + Op.JUMP
        + Op.JUMPDEST + Op.ADD + Op.PUSH1[0x1] + Op.PUSH1[0x8d] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x6] + Op.JUMP + Op.JUMPDEST + Op.PUSH0 + Op.DUP1
        + Op.REVERT + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1
        + Op.JUMP + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH4[0xca11bacc] + Op.CALLER + Op.EQ + Op.PUSH1[0x3f] + Op.JUMPI
        + Op.JUMPDEST + Op.PUSH4[0xca11bacc] + Op.CALLER + Op.SUB + Op.PUSH1[0x16]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x23] + Op.PUSH0
        + Op.CALLDATALOAD + Op.DUP1 + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0
        + Op.PUSH1[0x7f] + Op.JUMP + Op.JUMPDEST + Op.PUSH0 + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca11bacc] + Op.GAS + Op.CALL + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x3a] + Op.PUSH1[0x1] + Op.PUSH1[0x7b] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP + Op.JUMPDEST
        + Op.PUSH1[0x46] + Op.PUSH0 + Op.PUSH1[0x7b] + Op.JUMP + Op.JUMPDEST + Op.DUP1
        + Op.ISZERO + Op.PUSH1[0x79] + Op.JUMPI + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x60] + Op.PUSH1[0x66] + Op.SWAP4 + Op.PUSH1[0x5a] + Op.DUP5
        + Op.PUSH1[0x7b] + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.DUP4 + Op.PUSH1[0x7f]
        + Op.JUMP + Op.JUMPDEST + Op.SUB + Op.PUSH0 + Op.PUSH1[0x7f] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH4[0xca11bacc] + Op.GAS + Op.CALL + Op.PUSH1[0xa] + Op.JUMPI
        + Op.PUSH0 + Op.DUP1 + Op.REVERT + Op.JUMPDEST + Op.STOP + Op.JUMPDEST
        + Op.TLOAD + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x20] + Op.PUSH0 + Op.PUSH1[0x1] + Op.DUP2 + Op.DUP1
        + Op.PUSH2[0x57a7] + Op.GAS + Op.CALL + Op.PUSH1[0x10] + Op.SSTORE + Op.PUSH0
        + Op.MLOAD + Op.PUSH0 + Op.SSTORE + Op.PUSH0 + Op.DUP1 + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.PUSH2[0x57a7] + Op.GAS
        + Op.STATICCALL + Op.PUSH1[0x11] + Op.SSTORE + Op.PUSH0 + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.DUP1 + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH0 + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH2[0x57a7] + Op.GAS
        + Op.STATICCALL + Op.PUSH1[0x12] + Op.SSTORE + Op.PUSH0 + Op.MLOAD
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
        storage={0x2: 0x60a7, 0x12: 0x60a7},
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.ADDRESS + Op.CALLER + Op.EQ + Op.PUSH1[0x33] + Op.JUMPI + Op.JUMPDEST
        + Op.ADDRESS + Op.CALLER + Op.SUB + Op.PUSH1[0xe] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x1b] + Op.PUSH0 + Op.CALLDATALOAD + Op.DUP1
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.PUSH1[0x6f] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS
        + Op.GAS + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2e]
        + Op.PUSH1[0x1] + Op.PUSH1[0x6b] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3a] + Op.PUSH0
        + Op.PUSH1[0x6b] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.ISZERO
        + Op.PUSH1[0x69] + Op.JUMPI + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x54]
        + Op.PUSH1[0x5a] + Op.SWAP4 + Op.PUSH1[0x4e] + Op.DUP5 + Op.PUSH1[0x6b]
        + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.DUP4 + Op.PUSH1[0x6f] + Op.JUMP
        + Op.JUMPDEST + Op.SUB + Op.PUSH0 + Op.PUSH1[0x6f] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS + Op.GAS
        + Op.CALLCODE + Op.PUSH1[0x6] + Op.JUMPI + Op.PUSH0 + Op.DUP1 + Op.REVERT
        + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.ADDRESS + Op.CALLER + Op.EQ + Op.PUSH1[0x33] + Op.JUMPI + Op.JUMPDEST
        + Op.ADDRESS + Op.CALLER + Op.SUB + Op.PUSH1[0xe] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x1b] + Op.PUSH0 + Op.CALLDATALOAD + Op.DUP1
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.PUSH1[0x8c] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS
        + Op.GAS + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2e]
        + Op.PUSH1[0x1] + Op.PUSH1[0x88] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3a] + Op.PUSH0
        + Op.PUSH1[0x88] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.ISZERO
        + Op.PUSH1[0x86] + Op.JUMPI + Op.PUSH1[0x4a] + Op.PUSH1[0x1] + Op.DUP3
        + Op.SUB + Op.PUSH0 + Op.PUSH1[0x8c] + Op.JUMP + Op.JUMPDEST + Op.PUSH0
        + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS + Op.GAS + Op.CALLCODE
        + Op.ISZERO + Op.PUSH1[0x82] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x61]
        + Op.SWAP2 + Op.SUB + Op.PUSH0 + Op.PUSH1[0x8c] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS + Op.GAS
        + Op.DELEGATECALL + Op.ISZERO + Op.PUSH1[0x82] + Op.JUMPI + Op.PUSH1[0x7e]
        + Op.PUSH1[0x1] + Op.PUSH1[0x77] + Op.DUP2 + Op.PUSH1[0x88] + Op.JUMP
        + Op.JUMPDEST + Op.ADD + Op.PUSH1[0x1] + Op.PUSH1[0x8c] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x6] + Op.JUMP + Op.JUMPDEST + Op.PUSH0 + Op.DUP1
        + Op.REVERT + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1
        + Op.JUMP + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x6] + Op.PUSH0 + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST + Op.PUSH0
        + Op.SSTORE + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xadd1] + Op.GAS + Op.CALLCODE + Op.PUSH1[0x11] + Op.SSTORE
        + Op.PUSH1[0x1c] + Op.PUSH0 + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xadd1] + Op.GAS + Op.DELEGATECALL + Op.PUSH1[0x12] + Op.SSTORE
        + Op.PUSH1[0x32] + Op.PUSH0 + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xadd1] + Op.GAS + Op.CALL + Op.PUSH1[0x13] + Op.SSTORE
        + Op.PUSH1[0x49] + Op.PUSH0 + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1
        + Op.JUMP
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee_8] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.ADDRESS + Op.CALLER + Op.EQ + Op.PUSH1[0x33] + Op.JUMPI + Op.JUMPDEST
        + Op.ADDRESS + Op.CALLER + Op.SUB + Op.PUSH1[0xe] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x1b] + Op.PUSH0 + Op.CALLDATALOAD + Op.DUP1
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.PUSH1[0x6e] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS
        + Op.GAS + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2e]
        + Op.PUSH1[0x1] + Op.PUSH1[0x6a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3a] + Op.PUSH0
        + Op.PUSH1[0x6a] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.ISZERO
        + Op.PUSH1[0x68] + Op.JUMPI + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x54]
        + Op.PUSH1[0x5a] + Op.SWAP4 + Op.PUSH1[0x4e] + Op.DUP5 + Op.PUSH1[0x6a]
        + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.DUP4 + Op.PUSH1[0x6e] + Op.JUMP
        + Op.JUMPDEST + Op.SUB + Op.PUSH0 + Op.PUSH1[0x6e] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS + Op.GAS
        + Op.DELEGATECALL + Op.PUSH1[0x6] + Op.JUMPI + Op.PUSH0 + Op.DUP1 + Op.REVERT
        + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_9] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.CALLDATASIZE + Op.ISZERO + Op.PUSH1[0x81] + Op.JUMPI + Op.CALLER
        + Op.ADDRESS + Op.SUB + Op.PUSH1[0x74] + Op.JUMPI + Op.JUMPDEST + Op.PUSH0
        + Op.CALLDATALOAD + Op.PUSH1[0xf8] + Op.SHR + Op.PUSH0 + Op.CALLDATALOAD
        + Op.PUSH0 + Op.MSTORE + Op.PUSH1[0x1] + Op.CALLDATASIZE + Op.SUB + Op.SWAP1
        + Op.PUSH1[0x1] + Op.SWAP1 + Op.DUP1 + Op.PUSH1[0xf1] + Op.EQ + Op.PUSH1[0x64]
        + Op.JUMPI + Op.DUP1 + Op.PUSH1[0xf2] + Op.EQ + Op.PUSH1[0x54] + Op.JUMPI
        + Op.PUSH1[0xf4] + Op.EQ + Op.PUSH1[0x46] + Op.JUMPI + Op.JUMPDEST + Op.POP
        + Op.POP + Op.CALLER + Op.ADDRESS + Op.SUB + Op.PUSH1[0x3b] + Op.JUMPI
        + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x42] + Op.PUSH0 + Op.PUSH1[0x94] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH0 + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH0
        + Op.SWAP2 + Op.DUP3 + Op.SWAP2 + Op.ADDRESS + Op.GAS + Op.DELEGATECALL
        + Op.POP + Op.PUSH0 + Op.DUP1 + Op.PUSH1[0x31] + Op.JUMP + Op.JUMPDEST
        + Op.POP + Op.PUSH0 + Op.SWAP2 + Op.DUP3 + Op.SWAP2 + Op.DUP3 + Op.ADDRESS
        + Op.GAS + Op.CALLCODE + Op.POP + Op.PUSH0 + Op.DUP1 + Op.PUSH1[0x31]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH0 + Op.SWAP2 + Op.DUP3 + Op.SWAP2
        + Op.DUP3 + Op.ADDRESS + Op.GAS + Op.CALL + Op.POP + Op.PUSH0 + Op.DUP1
        + Op.PUSH1[0x31] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x7d] + Op.PUSH1[0x1]
        + Op.PUSH0 + Op.PUSH1[0x98] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0xb] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x92] + Op.PUSH1[0x1] + Op.PUSH1[0x8c] + Op.PUSH0
        + Op.PUSH1[0x94] + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.PUSH0 + Op.PUSH1[0x98]
        + Op.JUMP + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1
        + Op.JUMP + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[callee_10] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x6] + Op.PUSH0 + Op.PUSH1[0x1d] + Op.JUMP + Op.JUMPDEST + Op.PUSH0
        + Op.SSTORE + Op.PUSH1[0x10] + Op.PUSH1[0x1] + Op.PUSH1[0x1d] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.CALLER + Op.GAS + Op.CALL + Op.STOP + Op.JUMPDEST
        + Op.TLOAD + Op.SWAP1 + Op.JUMP
    ),
        storage={0x0: 0x60a7, 0x1: 0x60a7},
    )
    pre[callee_11] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.ADDRESS + Op.CALLER + Op.EQ + Op.PUSH1[0x33] + Op.JUMPI + Op.JUMPDEST
        + Op.ADDRESS + Op.CALLER + Op.SUB + Op.PUSH1[0xe] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x1b] + Op.PUSH0 + Op.CALLDATALOAD + Op.DUP1
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH0 + Op.PUSH1[0x6f] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS
        + Op.GAS + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2e]
        + Op.PUSH1[0x1] + Op.PUSH1[0x6b] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3a] + Op.PUSH0
        + Op.PUSH1[0x6b] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.ISZERO
        + Op.PUSH1[0x69] + Op.JUMPI + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x54]
        + Op.PUSH1[0x5a] + Op.SWAP4 + Op.PUSH1[0x4e] + Op.DUP5 + Op.PUSH1[0x6b]
        + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.DUP4 + Op.PUSH1[0x6f] + Op.JUMP
        + Op.JUMPDEST + Op.SUB + Op.PUSH0 + Op.PUSH1[0x6f] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH0 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.ADDRESS + Op.GAS
        + Op.CALL + Op.PUSH1[0x6] + Op.JUMPI + Op.PUSH0 + Op.DUP1 + Op.REVERT
        + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.TLOAD + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.TSTORE + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH0 + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP1
        + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.SHR + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.DUP2 + Op.DUP4 + Op.SSTORE + Op.DUP3 + Op.MSTORE + Op.GAS + Op.CALL
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x48dc5a9f099caaaa557742ca3a990a94be45b9969126a1bc74e5e8be5a2b5b47"
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
