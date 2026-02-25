"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP2930/storageCostsFiller.yml

callee code:
    gas
    push1 0x00
    mstore
    push1 0x02
    push1 0x00
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_1 code:
    gas
    push1 0x00
    mstore
    push1 0x00
    sload
    pop
    push1 0x13
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_2 code:
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_3 code:
    gas
    push1 0x00
    mstore
    push2 0xbeef
    push1 0x00
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_4 code:
    gas
    push1 0x00
    mstore
    push2 0x60a7
    push1 0x00
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_5 code:
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_6 code:
    push2 0x60a7
    push1 0x00
    sstore
    gas
    push1 0x00
    mstore
    push1 0x02
    push1 0x00
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    ... (2 more instructions)

callee_7 code:
    push2 0x60a7
    push1 0x00
    sstore
    gas
    push1 0x00
    mstore
    push1 0x00
    sload
    pop
    push1 0x13
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    ... (2 more instructions)

callee_8 code:
    push1 0x00
    sload
    push1 0x20
    mstore
    gas
    push1 0x00
    mstore
    push1 0x02
    push1 0x00
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    ... (3 more instructions)

callee_9 code:
    push1 0x00
    sload
    push1 0x20
    mstore
    gas
    push1 0x00
    mstore
    push1 0x00
    sload
    pop
    push1 0x13
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    ... (3 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
    push2 0x1000
    add
    gas
    call
    pop
    gas
    push1 0x00
    mstore
    push2 0x60a7
    sload
    pop
    push1 0x13
    gas
    ... (29 more instructions)
"""

import pytest
from execution_testing import (
    AccessList,
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
    ["tests/static/state_tests/stEIP2930/storageCostsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_access_list",
    [
        ("693c61390000000000000000000000000000000000000000000000000000000000000002", [AccessList(address=Address("0x0000000000000000000000000000000000001002"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000005", [AccessList(address=Address("0x0000000000000000000000000000000000001005"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000004", [AccessList(address=Address("0x0000000000000000000000000000000000001004"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000001", [AccessList(address=Address("0x0000000000000000000000000000000000001001"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000021", [AccessList(address=Address("0x0000000000000000000000000000000000001021"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000011", [AccessList(address=Address("0x0000000000000000000000000000000000001011"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000003", [AccessList(address=Address("0x0000000000000000000000000000000000001003"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000000", [
            AccessList(address=Address("0x00000000000000000000000000000000000060a7"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000fffffad"), Hash("0x00000000000000000000000000000000000000000000000000000000000000ad"), Hash("0x00000000000000000000000000000000000000000000000000000123214342ad"), Hash("0x00000000000000000000000000000000000000000000000000000000deadbeef")]),
            AccessList(address=Address("0x0000000000000000000000000000000000001000"), storage_keys=[Hash("0x00000000000000000000000000000000000000000000000000000000000fffff"), Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"), Hash("0x0000000000000000000000000000000000000000000000000000000123214342"), Hash("0x00000000000000000000000000000000000000000000000000000000deadbeef")]),
            AccessList(address=Address("0x0000000000000000000000000010000000000100"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000fffffbc"), Hash("0x00000000000000000000000000000000000000000000000000000000000000bc"), Hash("0x00000000000000000000000000000000000000000000000000000123214342bc"), Hash("0x000000000000000000000000000000000000000000000000000000deadbeefbc")]),
            AccessList(address=Address("0xffffffffffffffffffffffffffffffffffffffff"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000fffffbc"), Hash("0x00000000000000000000000000000000000000000000000000000000000000bc"), Hash("0x00000000000000000000000000000000000000000000000000000123214342bc"), Hash("0x000000000000000000000000000000000000000000000000000000deadbeefbc"), Hash("0xdeadbeef12345678deadbeef12345678deadbeef12345678deadbeef12345678"), Hash("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")]),
        ]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000000", [AccessList(address=Address("0x0000000000000000000000000000000000001000"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000020", [AccessList(address=Address("0x0000000000000000000000000000000000001020"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000010", [AccessList(address=Address("0x0000000000000000000000000000000000001010"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000fff", [AccessList(address=Address("0xcccccccccccccccccccccccccccccccccccccccc"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x0000000000000000000000000000000000000000000000000000000000000001"), Hash("0x0000000000000000000000000000000000000000000000000000000000000002"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000002", [AccessList(address=Address("0xf000000000000000000000000000000000000101"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000002", None),
        ("693c61390000000000000000000000000000000000000000000000000000000000000002", [AccessList(address=Address("0x0000000000000000000000000000000000001002"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000004", [AccessList(address=Address("0xf000000000000000000000000000000000000101"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000004", None),
        ("693c61390000000000000000000000000000000000000000000000000000000000000005", [AccessList(address=Address("0xf000000000000000000000000000000000000101"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000005", None),
        ("693c61390000000000000000000000000000000000000000000000000000000000000005", [AccessList(address=Address("0x0000000000000000000000000000000000001005"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000004", [AccessList(address=Address("0x0000000000000000000000000000000000001004"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000001", [AccessList(address=Address("0xf000000000000000000000000000000000000101"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000001", None),
        ("693c61390000000000000000000000000000000000000000000000000000000000000001", [AccessList(address=Address("0x0000000000000000000000000000000000001001"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000021", [AccessList(address=Address("0x0000000000000000000000000000000000001021"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000011", [AccessList(address=Address("0x0000000000000000000000000000000000001011"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000003", [AccessList(address=Address("0xf000000000000000000000000000000000000101"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000003", None),
        ("693c61390000000000000000000000000000000000000000000000000000000000000003", [AccessList(address=Address("0x0000000000000000000000000000000000001003"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000000", [AccessList(address=Address("0xf000000000000000000000000000000000000100"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000000", None),
        ("693c61390000000000000000000000000000000000000000000000000000000000000000", [AccessList(address=Address("0x0000000000000000000000000000000000001000"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000020", [AccessList(address=Address("0x0000000000000000000000000000000000001020"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000010", [AccessList(address=Address("0x0000000000000000000000000000000000001010"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000010")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000fff", [AccessList(address=Address("0xcccccccccccccccccccccccccccccccccccccccc"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000000f000"), Hash("0x000000000000000000000000000000000000000000000000000000000000f001"), Hash("0x000000000000000000000000000000000000000000000000000000000000f002"), Hash("0x000000000000000000000000000000000000000000000000000000000000f0a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000fff", [AccessList(address=Address("0xcccccccccccccccccccccccccccccccccc000000"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x0000000000000000000000000000000000000000000000000000000000000001"), Hash("0x0000000000000000000000000000000000000000000000000000000000000002"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25', 'case26', 'case27', 'case28', 'case29', 'case30', 'case31', 'case32', 'case33', 'case34', 'case35'],
)
@pytest.mark.pre_alloc_mutable
def test_storage_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_access_list,
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
    callee_5 = Address("0x0000000000000000000000000000000000001005")
    callee_6 = Address("0x0000000000000000000000000000000000001010")
    callee_7 = Address("0x0000000000000000000000000000000000001011")
    callee_8 = Address("0x0000000000000000000000000000000000001020")
    callee_9 = Address("0x0000000000000000000000000000000000001021")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.SLOAD + Op.POP
        + Op.PUSH1[0x13] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0xbeef] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x60a7] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x0},
    )
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH2[0x60a7] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x11]
        + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH2[0x60a7] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.SLOAD + Op.POP + Op.PUSH1[0x13] + Op.GAS
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x20] + Op.MSTORE + Op.GAS
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x20] + Op.MSTORE + Op.GAS
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.SLOAD + Op.POP
        + Op.PUSH1[0x13] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD
        + Op.GAS + Op.CALL + Op.POP + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH2[0x60a7] + Op.SLOAD + Op.POP + Op.PUSH1[0x13] + Op.GAS
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2]
        + Op.SSTORE + Op.STOP
    ),
        storage={0x60a7: 0xdead},
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=100000,
        access_list=tx_access_list,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
