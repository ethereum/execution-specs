"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP2930/variedContextFiller.yml

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xc057
    gas
    delegatecall
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xc057
    gas
    call
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xc057
    gas
    callcode
    stop

callee_3 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push4 0xead0c057
    gas
    staticcall
    pop
    push1 0x00
    mload
    push1 0x00
    sstore
    stop

callee_4 code:
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
    gas
    push1 0x20
    mstore
    push2 0x60a7
    sload
    push1 0x40
    ... (13 more instructions)

callee_5 code:
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push4 0xdead0111
    gas
    call
    pop
    push2 0x7fe8
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    sstore
    ... (1 more instructions)

callee_6 code:
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push4 0xdead0112
    gas
    call
    pop
    push2 0x7fe8
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    sstore
    ... (1 more instructions)

callee_7 code:
    push2 0x0bad
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xf113
    gas
    staticcall
    pop
    push1 0x00
    mload
    push1 0x00
    sstore
    stop

callee_8 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xf114
    push2 0x0b65
    call
    stop

callee_9 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xf115
    push2 0x1800
    call
    stop

callee_10 code:
    push1 0x00
    sload
    pop
    gas
    push1 0x00
    mstore
    push1 0x02
    push2 0xbeef
    sstore
    push1 0x11
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    gas
    push1 0x20
    mstore
    ... (100 more instructions)

callee_11 code:
    push1 0x06
    dup1
    push1 0x33
    push2 0x0100
    codecopy
    push2 0x0200
    mstore
    push1 0x21
    dup1
    push1 0x39
    push1 0x00
    codecopy
    push2 0x0220
    mstore
    push2 0x0200
    mload
    push2 0x0100
    add
    push1 0x00
    push1 0x00
    ... (33 more instructions)

callee_12 code:
    push1 0x06
    dup1
    push1 0x36
    push2 0x0100
    codecopy
    push2 0x0200
    mstore
    push1 0x21
    dup1
    push1 0x3c
    push1 0x00
    codecopy
    push2 0x0220
    mstore
    push2 0x5a17
    push2 0x0200
    mload
    push2 0x0100
    add
    push1 0x00
    ... (34 more instructions)

callee_13 code:
    push1 0x13
    dup1
    push1 0x44
    push2 0x0100
    codecopy
    push2 0x0200
    mstore
    push1 0x0f
    dup1
    push1 0x57
    push1 0x00
    codecopy
    push2 0x0220
    mstore
    push2 0x0200
    mload
    push2 0x0100
    add
    push1 0x00
    push1 0x00
    ... (40 more instructions)

callee_14 code:
    push1 0x13
    dup1
    push1 0x47
    push2 0x0100
    codecopy
    push2 0x0200
    mstore
    push1 0x0f
    dup1
    push1 0x5a
    push1 0x00
    codecopy
    push2 0x0220
    mstore
    push2 0x5a17
    push2 0x0200
    mload
    push2 0x0100
    add
    push1 0x00
    ... (41 more instructions)

callee_15 code:
    push1 0x13
    dup1
    push1 0x44
    push2 0x0100
    codecopy
    push2 0x0200
    mstore
    push1 0x21
    dup1
    push1 0x57
    push1 0x00
    codecopy
    push2 0x0220
    mstore
    push2 0x0200
    mload
    push2 0x0100
    add
    push1 0x00
    push1 0x00
    ... (52 more instructions)

callee_16 code:
    push1 0x13
    dup1
    push1 0x47
    push2 0x0100
    codecopy
    push2 0x0200
    mstore
    push1 0x21
    dup1
    push1 0x5a
    push1 0x00
    codecopy
    push2 0x0220
    mstore
    push2 0x5a17
    push2 0x0200
    mload
    push2 0x0100
    add
    push1 0x00
    ... (53 more instructions)

callee_17 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xf126
    gas
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xf126
    gas
    call
    stop

callee_18 code:
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
    gas
    push1 0x00
    ... (18 more instructions)

callee_19 code:
    push4 0xdead60a7
    push1 0x00
    sstore
    push2 0x600d
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop

callee_20 code:
    push2 0x600d
    push1 0x00
    sstore
    stop

callee_21 code:
    push2 0x60a7
    sload
    push1 0x00
    mstore
    push2 0x600d
    push1 0x00
    sstore
    stop

callee_22 code:
    gas
    push1 0x00
    mstore
    push2 0x60a7
    push1 0x00
    sstore
    gas
    push1 0x00
    mload
    sub
    push1 0x00
    mstore
    push1 0x00
    push1 0x01
    sload
    eq
    push1 0x24
    jumpi
    push1 0x00
    mload
    ... (11 more instructions)

callee_23 code:
    push2 0xdead
    push1 0x00
    sstore
    push1 0x00
    selfdestruct
    stop

callee_24 code:
    push1 0x00
    sload
    pop
    push1 0x00
    selfdestruct
    stop

callee_25 code:
    gas
    push1 0x00
    mstore
    push2 0x60a7
    sload
    push1 0x20
    mstore
    push1 0x13
    gas
    push1 0x00
    mload
    sub
    sub
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop

contract code:
    push1 0x40
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
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    mload
    push1 0x01
    sstore
    ... (1 more instructions)
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
    ["tests/static/state_tests/stEIP2930/variedContextFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_access_list",
    [
        ("693c61390000000000000000000000000000000000000000000000000000000000000001", [AccessList(address=Address("0x000000000000000000000000000000000000c057"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000001", [AccessList(address=Address("0x0000000000000000000000000000000000001001"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000023", [AccessList(address=Address("0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000000ffff")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000023", [AccessList(address=Address("0x530508498d2aa75d8e591612809fec3d37a45615"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000022", [AccessList(address=Address("0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000000ffff")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000022", [AccessList(address=Address("0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000012", [AccessList(address=Address("0x0000000000000000000000000000000000001012"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000012", [AccessList(address=Address("0x00000000000000000000000000000000dead0112"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000010", [AccessList(address=Address("0x0000000000000000000000000000000000001010"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000010", [AccessList(address=Address("0xcccccccccccccccccccccccccccccccccccccccc"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000026", [AccessList(address=Address("0x000000000000000000000000000000000000f126"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000020")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000026", [AccessList(address=Address("0x000000000000000000000000000000000000f126"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000011", [AccessList(address=Address("0x0000000000000000000000000000000000001011"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000011", [AccessList(address=Address("0x00000000000000000000000000000000dead0111"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000002", [AccessList(address=Address("0x000000000000000000000000000000000000c057"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000002", [AccessList(address=Address("0x0000000000000000000000000000000000001002"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000025", [AccessList(address=Address("0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000000ffff")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000025", [AccessList(address=Address("0x83fbdae70258ac0fa837b701cc63cedf48d4b6bf"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000021", [AccessList(address=Address("0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000021", [AccessList(address=Address("0xd82f21135ed7d7d833a9f2a0f1cf6c3da214b8e3"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000024", [AccessList(address=Address("0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"), storage_keys=[Hash("0x000000000000000000000000000000000000000000000000000000000000ffff")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000024", [AccessList(address=Address("0xb76ab2d646c4df221edd345957d0a396a2ab1b6d"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000020", [AccessList(address=Address("0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000001")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000020", [AccessList(address=Address("0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000000", [AccessList(address=Address("0x000000000000000000000000000000000000c057"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000000", [AccessList(address=Address("0x0000000000000000000000000000000000001000"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000015", [AccessList(address=Address("0x0000000000000000000000000000000000001015"), storage_keys=[Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000015", [AccessList(address=Address("0x000000000000000000000000000000000000f115"), storage_keys=[Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000016", [AccessList(address=Address("0xf000000000000000000000000000000000000116"), storage_keys=[Hash("0x00000000000000000000000000000000000000000000000000000000000060a7"), Hash("0x000000000000000000000000000000000000000000000000000000000000beef")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000016", [AccessList(address=Address("0x0000000000000000000000000000000000001016"), storage_keys=[Hash("0x00000000000000000000000000000000000000000000000000000000000060a7"), Hash("0x000000000000000000000000000000000000000000000000000000000000beef"), Hash("0x000000000000000000000000000000000000000000000000000000000000f000"), Hash("0x000000000000000000000000000000000000000000000000000000000000f001"), Hash("0x000000000000000000000000000000000000000000000000000000000000f002"), Hash("0x000000000000000000000000000000000000000000000000000000000000f003"), Hash("0x000000000000000000000000000000000000000000000000000000000000f004"), Hash("0x000000000000000000000000000000000000000000000000000000000000f005"), Hash("0x000000000000000000000000000000000000000000000000000000000000f006"), Hash("0x000000000000000000000000000000000000000000000000000000000000f007"), Hash("0x000000000000000000000000000000000000000000000000000000000000f008"), Hash("0x000000000000000000000000000000000000000000000000000000000000f009"), Hash("0x000000000000000000000000000000000000000000000000000000000000f00a"), Hash("0x000000000000000000000000000000000000000000000000000000000000f00b"), Hash("0x000000000000000000000000000000000000000000000000000000000000f00c"), Hash("0x000000000000000000000000000000000000000000000000000000000000f00d"), Hash("0x000000000000000000000000000000000000000000000000000000000000f00e"), Hash("0x000000000000000000000000000000000000000000000000000000000000f00f"), Hash("0x000000000000000000000000000000000000000000000000000000000000f010"), Hash("0x000000000000000000000000000000000000000000000000000000000000f011"), Hash("0x000000000000000000000000000000000000000000000000000000000000f012"), Hash("0x000000000000000000000000000000000000000000000000000000000000f013"), Hash("0x000000000000000000000000000000000000000000000000000000000000f014"), Hash("0x000000000000000000000000000000000000000000000000000000000000f015"), Hash("0x000000000000000000000000000000000000000000000000000000000000f016"), Hash("0x000000000000000000000000000000000000000000000000000000000000f017"), Hash("0x000000000000000000000000000000000000000000000000000000000000f018"), Hash("0x000000000000000000000000000000000000000000000000000000000000f019"), Hash("0x000000000000000000000000000000000000000000000000000000000000f01a"), Hash("0x000000000000000000000000000000000000000000000000000000000000f01b"), Hash("0x000000000000000000000000000000000000000000000000000000000000f01c"), Hash("0x000000000000000000000000000000000000000000000000000000000000f01d"), Hash("0x000000000000000000000000000000000000000000000000000000000000f01e"), Hash("0x000000000000000000000000000000000000000000000000000000000000f01f")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000013", [AccessList(address=Address("0x0000000000000000000000000000000000000000"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000013", [AccessList(address=Address("0x000000000000000000000000000000000000f113"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000003", [AccessList(address=Address("0x00000000000000000000000000000000ead0c057"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000003", [AccessList(address=Address("0x0000000000000000000000000000000000001003"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x00000000000000000000000000000000000000000000000000000000000060a7")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000014", [AccessList(address=Address("0x0000000000000000000000000000000000001014"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
        ("693c61390000000000000000000000000000000000000000000000000000000000000014", [AccessList(address=Address("0x000000000000000000000000000000000000f114"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])]),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25', 'case26', 'case27', 'case28', 'case29', 'case30', 'case31', 'case32', 'case33', 'case34', 'case35'],
)
@pytest.mark.pre_alloc_mutable
def test_varied_context(
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
    callee_4 = Address("0x0000000000000000000000000000000000001010")
    callee_5 = Address("0x0000000000000000000000000000000000001011")
    callee_6 = Address("0x0000000000000000000000000000000000001012")
    callee_7 = Address("0x0000000000000000000000000000000000001013")
    callee_8 = Address("0x0000000000000000000000000000000000001014")
    callee_9 = Address("0x0000000000000000000000000000000000001015")
    callee_10 = Address("0x0000000000000000000000000000000000001016")
    callee_11 = Address("0x0000000000000000000000000000000000001020")
    callee_12 = Address("0x0000000000000000000000000000000000001021")
    callee_13 = Address("0x0000000000000000000000000000000000001022")
    callee_14 = Address("0x0000000000000000000000000000000000001023")
    callee_15 = Address("0x0000000000000000000000000000000000001024")
    callee_16 = Address("0x0000000000000000000000000000000000001025")
    callee_17 = Address("0x0000000000000000000000000000000000001026")
    callee_18 = Address("0x000000000000000000000000000000000000c057")
    callee_19 = Address("0x000000000000000000000000000000000000f113")
    callee_20 = Address("0x000000000000000000000000000000000000f114")
    callee_21 = Address("0x000000000000000000000000000000000000f115")
    callee_22 = Address("0x000000000000000000000000000000000000f126")
    callee_23 = Address("0x00000000000000000000000000000000dead0111")
    callee_24 = Address("0x00000000000000000000000000000000dead0112")
    callee_25 = Address("0x00000000000000000000000000000000ead0c057")

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
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xc057] + Op.GAS + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xc057] + Op.GAS + Op.CALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xc057] + Op.GAS + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH4[0xead0c057] + Op.GAS + Op.STATICCALL + Op.POP + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.GAS + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH2[0x60a7] + Op.SLOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x1a]
        + Op.GAS + Op.PUSH1[0x20] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.REVERT + Op.STOP
    ),
        storage={0x60a7: 0xbeef},
    )
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH4[0xdead0111]
        + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x7fe8] + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH4[0xdead0112]
        + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x7fe8] + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH2[0xbad] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xf113] + Op.GAS + Op.STATICCALL
        + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee_8] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xf114] + Op.PUSH2[0xb65] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xf115] + Op.PUSH2[0x1800] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_10] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.SLOAD + Op.POP + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x2] + Op.PUSH2[0xbeef] + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE
        + Op.GAS + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH2[0x60a7] + Op.SLOAD
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x23] + Op.GAS + Op.PUSH1[0x20]
        + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x20] + Op.MSTORE + Op.GAS
        + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH2[0xbeef] + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH2[0xf000] + Op.ADD + Op.SSTORE + Op.PUSH1[0x78] + Op.GAS
        + Op.PUSH1[0x40] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x40] + Op.MSTORE
        + Op.GAS + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH2[0xf010] + Op.ADD + Op.SLOAD + Op.POP + Op.PUSH1[0x7a] + Op.GAS
        + Op.PUSH1[0x60] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH2[0x100]
        + Op.ADD + Op.SSTORE + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH2[0x200] + Op.ADD + Op.SSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH2[0x300] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x60] + Op.MLOAD + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH2[0x400]
        + Op.ADD + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SLOAD + Op.GT
        + Op.PUSH1[0x9b] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0xb4] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.SUB
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x1016] + Op.GAS + Op.CALL
        + Op.JUMPDEST + Op.STOP
    ),
        storage={0x0: 0xf, 0x60a7: 0xdead},
    )
    pre[callee_11] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x6] + Op.DUP1 + Op.PUSH1[0x33] + Op.PUSH2[0x100] + Op.CODECOPY
        + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH1[0x21] + Op.DUP1 + Op.PUSH1[0x39]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH2[0x200]
        + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP + Op.INVALID + Op.PUSH1[0xff]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0x100]
        + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x10]
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_12] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x6] + Op.DUP1 + Op.PUSH1[0x36] + Op.PUSH2[0x100] + Op.CODECOPY
        + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH1[0x21] + Op.DUP1 + Op.PUSH1[0x3c]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH2[0x5a17]
        + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP + Op.INVALID + Op.PUSH1[0xff]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0x100]
        + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x10]
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_13] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x13] + Op.DUP1 + Op.PUSH1[0x44] + Op.PUSH2[0x100] + Op.CODECOPY
        + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH1[0xf] + Op.DUP1 + Op.PUSH1[0x57]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH2[0x200]
        + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x240] + Op.MLOAD
        + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x240] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP + Op.INVALID + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP + Op.PUSH2[0x100]
        + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x80]
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_14] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x13] + Op.DUP1 + Op.PUSH1[0x47] + Op.PUSH2[0x100] + Op.CODECOPY
        + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH1[0xf] + Op.DUP1 + Op.PUSH1[0x5a]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH2[0x5a17]
        + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0x240] + Op.MLOAD + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x240]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP + Op.INVALID + Op.GAS
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP + Op.PUSH2[0x100] + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_15] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x13] + Op.DUP1 + Op.PUSH1[0x44] + Op.PUSH2[0x100] + Op.CODECOPY
        + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH1[0x21] + Op.DUP1 + Op.PUSH1[0x57]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH2[0x200]
        + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x240] + Op.MLOAD
        + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x240] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP + Op.INVALID + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP + Op.GAS
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH2[0x100] + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_16] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x13] + Op.DUP1 + Op.PUSH1[0x47] + Op.PUSH2[0x100] + Op.CODECOPY
        + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH1[0x21] + Op.DUP1 + Op.PUSH1[0x5a]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH2[0x5a17]
        + Op.PUSH2[0x200] + Op.MLOAD + Op.PUSH2[0x100] + Op.ADD + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0x240] + Op.MLOAD + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x240]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP + Op.INVALID + Op.GAS
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x2] + Op.SSTORE
        + Op.STOP + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0xffff]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0x100] + Op.PUSH2[0x100]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_17] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xf126] + Op.GAS + Op.CALL + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xf126] + Op.GAS + Op.CALL + Op.STOP
    ),
    )
    pre[callee_18] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x11] + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH2[0x60a7] + Op.SLOAD + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x10]
        + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
        storage={0x60a7: 0xdead},
    )
    pre[callee_19] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH4[0xdead60a7] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH2[0x600d]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_20] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH2[0x600d] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
        storage={0x0: 0xbad},
    )
    pre[callee_21] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH2[0x60a7] + Op.SLOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x600d]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0xbad, 0x60a7: 0xdead},
    )
    pre[callee_22] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x60a7] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SLOAD + Op.EQ
        + Op.PUSH1[0x24] + Op.JUMPI + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x2b] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_23] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH2[0xdead] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.SELFDESTRUCT + Op.STOP
    ),
    )
    pre[callee_24] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.SLOAD + Op.POP + Op.PUSH1[0x0] + Op.SELFDESTRUCT + Op.STOP,
        storage={0x0: 0xdead0060a7},
    )
    pre[callee_25] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x60a7] + Op.SLOAD
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x13] + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
        storage={0x60a7: 0xdead},
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD
        + Op.GAS + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
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
        value=100000,
        access_list=tx_access_list,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
