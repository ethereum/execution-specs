"""
Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x86c575f296a8a021a2a64972e57a20b06fe8b897
    push2 0xc350
    call
    push1 0x0a
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x3d2496d905cf0e9c77473cbfb6e100062b5af57f
    push2 0xc350
    delegatecall
    push1 0x0b
    sstore
    push1 0x00
    ... (16 more instructions)

callee_1 code:
    push1 0x0c
    push1 0x02
    sstore
    push1 0x01
    push1 0x00
    revert
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x86c575f296a8a021a2a64972e57a20b06fe8b897
    push2 0xc350
    delegatecall
    push1 0x0a
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x3d2496d905cf0e9c77473cbfb6e100062b5af57f
    push2 0xc350
    delegatecall
    push1 0x0b
    sstore
    push1 0x00
    push1 0x00
    ... (14 more instructions)

callee_3 code:
    push1 0x0c
    push1 0x03
    sstore
    push1 0x01
    push1 0x00
    revert
    stop

callee_4 code:
    push1 0x0c
    push1 0x01
    sstore
    push1 0x01
    push1 0x00
    revert
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    push3 0x03f7a0
    call
    stop

callee_5 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x86c575f296a8a021a2a64972e57a20b06fe8b897
    push2 0xc350
    call
    push1 0x0a
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x3d2496d905cf0e9c77473cbfb6e100062b5af57f
    push2 0xc350
    call
    push1 0x0b
    sstore
    ... (17 more instructions)

callee_6 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x86c575f296a8a021a2a64972e57a20b06fe8b897
    push2 0xc350
    callcode
    push1 0x0a
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x3d2496d905cf0e9c77473cbfb6e100062b5af57f
    push2 0xc350
    callcode
    push1 0x0b
    sstore
    ... (17 more instructions)
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
    ["tests/static/state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value",
    [
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 800000, 0),
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 800000, 10),
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 126200, 0),
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 126200, 10),
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 160000, 0),
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 160000, 10),
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 50000, 0),
        ("000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd", 50000, 10),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 800000, 0),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 800000, 10),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 126200, 0),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 126200, 10),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 160000, 0),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 160000, 10),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 50000, 0),
        ("000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf", 50000, 10),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 800000, 0),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 800000, 10),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 126200, 0),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 126200, 10),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 160000, 0),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 160000, 10),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 50000, 0),
        ("00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95", 50000, 10),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 800000, 0),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 800000, 10),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 126200, 0),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 126200, 10),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 160000, 0),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 160000, 10),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 50000, 0),
        ("0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab", 50000, 10),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25', 'case26', 'case27', 'case28', 'case29', 'case30', 'case31'],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_multiple_sub_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x89ab420962193a25593b5663462b75c083d56148")
    callee = Address("0x1302fd3b212e7e634f82ed6d00ac14544e8b1cab")
    callee_1 = Address("0x3d2496d905cf0e9c77473cbfb6e100062b5af57f")
    callee_2 = Address("0x68cf97c6ca41ecfc5623d8a7e9b6f72068213e95")
    callee_3 = Address("0x83bac26dd305c061381c042d0bac07b08d15bbce")
    callee_4 = Address("0x86c575f296a8a021a2a64972e57a20b06fe8b897")
    callee_5 = Address("0xd7e294f032a5cc430e9e6c4148220867e9704dcd")
    callee_6 = Address("0xee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x86c575f296a8a021a2a64972e57a20b06fe8b897]
        + Op.PUSH2[0xc350] + Op.CALL + Op.PUSH1[0xa] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x3d2496d905cf0e9c77473cbfb6e100062b5af57f] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.PUSH1[0xb] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x83bac26dd305c061381c042d0bac07b08d15bbce] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0xc] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x4]
        + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x5] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xc] + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.REVERT + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x86c575f296a8a021a2a64972e57a20b06fe8b897] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.PUSH1[0xa] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x3d2496d905cf0e9c77473cbfb6e100062b5af57f] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.PUSH1[0xb] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x83bac26dd305c061381c042d0bac07b08d15bbce] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.PUSH1[0xc] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x4]
        + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x5] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xc] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.REVERT + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xc] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.REVERT + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x3f7a0] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x86c575f296a8a021a2a64972e57a20b06fe8b897]
        + Op.PUSH2[0xc350] + Op.CALL + Op.PUSH1[0xa] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x3d2496d905cf0e9c77473cbfb6e100062b5af57f] + Op.PUSH2[0xc350]
        + Op.CALL + Op.PUSH1[0xb] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x83bac26dd305c061381c042d0bac07b08d15bbce] + Op.PUSH2[0xc350]
        + Op.CALL + Op.PUSH1[0xc] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x4]
        + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x5] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x86c575f296a8a021a2a64972e57a20b06fe8b897]
        + Op.PUSH2[0xc350] + Op.CALLCODE + Op.PUSH1[0xa] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x3d2496d905cf0e9c77473cbfb6e100062b5af57f] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0xb] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x83bac26dd305c061381c042d0bac07b08d15bbce] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0xc] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x4]
        + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x5] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
