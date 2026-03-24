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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, expected_post",
    [
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            800000,
            0,
            {
                Address("0xd7e294f032a5cc430e9e6c4148220867e9704dcd"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            800000,
            10,
            {
                Address("0xd7e294f032a5cc430e9e6c4148220867e9704dcd"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            126200,
            0,
            {},
        ),
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            126200,
            10,
            {},
        ),
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            160000,
            0,
            {
                Address("0xd7e294f032a5cc430e9e6c4148220867e9704dcd"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            160000,
            10,
            {
                Address("0xd7e294f032a5cc430e9e6c4148220867e9704dcd"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            50000,
            0,
            {},
        ),
        (
            "000000000000000000000000d7e294f032a5cc430e9e6c4148220867e9704dcd",
            50000,
            10,
            {},
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            800000,
            0,
            {
                Address("0xee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            800000,
            10,
            {
                Address("0xee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            126200,
            0,
            {},
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            126200,
            10,
            {},
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            160000,
            0,
            {
                Address("0xee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            160000,
            10,
            {
                Address("0xee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            50000,
            0,
            {},
        ),
        (
            "000000000000000000000000ee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf",
            50000,
            10,
            {},
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            800000,
            0,
            {
                Address("0x68cf97c6ca41ecfc5623d8a7e9b6f72068213e95"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            800000,
            10,
            {
                Address("0x68cf97c6ca41ecfc5623d8a7e9b6f72068213e95"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            126200,
            0,
            {},
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            126200,
            10,
            {},
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            160000,
            0,
            {
                Address("0x68cf97c6ca41ecfc5623d8a7e9b6f72068213e95"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            160000,
            10,
            {
                Address("0x68cf97c6ca41ecfc5623d8a7e9b6f72068213e95"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            50000,
            0,
            {},
        ),
        (
            "00000000000000000000000068cf97c6ca41ecfc5623d8a7e9b6f72068213e95",
            50000,
            10,
            {},
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            800000,
            0,
            {
                Address("0x1302fd3b212e7e634f82ed6d00ac14544e8b1cab"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            800000,
            10,
            {
                Address("0x1302fd3b212e7e634f82ed6d00ac14544e8b1cab"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            126200,
            0,
            {},
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            126200,
            10,
            {},
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            160000,
            0,
            {
                Address("0x1302fd3b212e7e634f82ed6d00ac14544e8b1cab"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            160000,
            10,
            {
                Address("0x1302fd3b212e7e634f82ed6d00ac14544e8b1cab"): Account(
                    storage={4: 12, 5: 12}
                )
            },
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            50000,
            0,
            {},
        ),
        (
            "0000000000000000000000001302fd3b212e7e634f82ed6d00ac14544e8b1cab",
            50000,
            10,
            {},
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
        "case10",
        "case11",
        "case12",
        "case13",
        "case14",
        "case15",
        "case16",
        "case17",
        "case18",
        "case19",
        "case20",
        "case21",
        "case22",
        "case23",
        "case24",
        "case25",
        "case26",
        "case27",
        "case28",
        "case29",
        "case30",
        "case31",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_multiple_sub_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    expected_post: dict,
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

    pre.deploy_contract(
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
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3d2496d905cf0e9c77473cbfb6e100062b5af57f"),  # noqa: E501
    )
    pre.deploy_contract(
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
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x3, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x83bac26dd305c061381c042d0bac07b08d15bbce"),  # noqa: E501
    )
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
