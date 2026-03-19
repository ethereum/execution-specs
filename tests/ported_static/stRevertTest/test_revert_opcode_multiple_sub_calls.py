"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
    "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
    "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
    "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
]

TX_GAS = [800000, 126200, 160000, 50000]

TX_VALUE = [0, 10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 0, 1, id="case1"),
        pytest.param(0, 1, 0, id="case2"),
        pytest.param(0, 1, 1, id="case3"),
        pytest.param(0, 2, 0, id="case4"),
        pytest.param(0, 2, 1, id="case5"),
        pytest.param(0, 3, 0, id="case6"),
        pytest.param(0, 3, 1, id="case7"),
        pytest.param(1, 0, 0, id="case8"),
        pytest.param(1, 0, 1, id="case9"),
        pytest.param(1, 1, 0, id="case10"),
        pytest.param(1, 1, 1, id="case11"),
        pytest.param(1, 2, 0, id="case12"),
        pytest.param(1, 2, 1, id="case13"),
        pytest.param(1, 3, 0, id="case14"),
        pytest.param(1, 3, 1, id="case15"),
        pytest.param(2, 0, 0, id="case16"),
        pytest.param(2, 0, 1, id="case17"),
        pytest.param(2, 1, 0, id="case18"),
        pytest.param(2, 1, 1, id="case19"),
        pytest.param(2, 2, 0, id="case20"),
        pytest.param(2, 2, 1, id="case21"),
        pytest.param(2, 3, 0, id="case22"),
        pytest.param(2, 3, 1, id="case23"),
        pytest.param(3, 0, 0, id="case24"),
        pytest.param(3, 0, 1, id="case25"),
        pytest.param(3, 1, 0, id="case26"),
        pytest.param(3, 1, 1, id="case27"),
        pytest.param(3, 2, 0, id="case28"),
        pytest.param(3, 2, 1, id="case29"),
        pytest.param(3, 3, 0, id="case30"),
        pytest.param(3, 3, 1, id="case31"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_multiple_sub_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0xA,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x86C575F296A8A021A2A64972E57A20B06FE8B897,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xB,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x3D2496D905CF0E9C77473CBFB6E100062B5AF57F,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xC,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x83BAC26DD305C061381C042D0BAC07B08D15BBCE,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.SSTORE(key=0x5, value=0xC)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1302fd3b212e7e634f82ed6d00ac14544e8b1cab"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3d2496d905cf0e9c77473cbfb6e100062b5af57f"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0xA,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x86C575F296A8A021A2A64972E57A20B06FE8B897,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xB,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x3D2496D905CF0E9C77473CBFB6E100062B5AF57F,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xC,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x83BAC26DD305C061381C042D0BAC07B08D15BBCE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.SSTORE(key=0x5, value=0xC)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x68cf97c6ca41ecfc5623d8a7e9b6f72068213e95"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x3, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x83bac26dd305c061381c042d0bac07b08d15bbce"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x86c575f296a8a021a2a64972e57a20b06fe8b897"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 260000 (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x3F7A0,
                address=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x89ab420962193a25593b5663462b75c083d56148"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0xA,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x86C575F296A8A021A2A64972E57A20B06FE8B897,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xB,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x3D2496D905CF0E9C77473CBFB6E100062B5AF57F,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xC,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x83BAC26DD305C061381C042D0BAC07B08D15BBCE,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.SSTORE(key=0x5, value=0xC)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xd7e294f032a5cc430e9e6c4148220867e9704dcd"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0xA,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x86C575F296A8A021A2A64972E57A20B06FE8B897,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xB,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x3D2496D905CF0E9C77473CBFB6E100062B5AF57F,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xC,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x83BAC26DD305C061381C042D0BAC07B08D15BBCE,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.SSTORE(key=0x5, value=0xC)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 3, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 3, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 3, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={4: 12, 5: 12},
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 3, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600c60025560016000fd00")
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f4600a556000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f4600b5560006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f4600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60035560016000fd00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("600c60015560016000fd00")
                ),
                contract: Account(
                    code=bytes.fromhex("6000600060006000346000356203f7a0f100")
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f1600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f1600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f1600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "600060006000600060007386c575f296a8a021a2a64972e57a20b06fe8b89761c350f2600a5560006000600060006000733d2496d905cf0e9c77473cbfb6e100062b5af57f61c350f2600b55600060006000600060007383bac26dd305c061381c042d0bac07b08d15bbce61c350f2600c55600c600455600c60055500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
