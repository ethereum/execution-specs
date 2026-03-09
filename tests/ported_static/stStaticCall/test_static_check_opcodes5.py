"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodes5Filler.json
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
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes5Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, expected_post",
    [
        (
            "0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b",
            50000,
            0,
            {},
        ),
        (
            "0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b",
            50000,
            100,
            {},
        ),
        (
            "0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b",
            335000,
            0,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x8eeb303e1e7e2bb67d778526e009014a5daead81"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b",
            335000,
            100,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x8eeb303e1e7e2bb67d778526e009014a5daead81"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "0000000000000000000000007761311ee56479da378519606cc4da58e17251ab",
            50000,
            0,
            {},
        ),
        (
            "0000000000000000000000007761311ee56479da378519606cc4da58e17251ab",
            50000,
            100,
            {},
        ),
        (
            "0000000000000000000000007761311ee56479da378519606cc4da58e17251ab",
            335000,
            0,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x8eeb303e1e7e2bb67d778526e009014a5daead81"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "0000000000000000000000007761311ee56479da378519606cc4da58e17251ab",
            335000,
            100,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x8eeb303e1e7e2bb67d778526e009014a5daead81"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3",
            50000,
            0,
            {},
        ),
        (
            "0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3",
            50000,
            100,
            {},
        ),
        (
            "0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3",
            335000,
            0,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x9c40928b20ac4236f0f3920567f28539c2e158b3"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3",
            335000,
            100,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x9c40928b20ac4236f0f3920567f28539c2e158b3"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb",
            50000,
            0,
            {},
        ),
        (
            "0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb",
            50000,
            100,
            {},
        ),
        (
            "0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb",
            335000,
            0,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x8a6781f0d54ed3cb8963ffc233e98041de8bdadb"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb",
            335000,
            100,
            {
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
                Address("0x8a6781f0d54ed3cb8963ffc233e98041de8bdadb"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5",
            50000,
            0,
            {},
        ),
        (
            "00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5",
            50000,
            100,
            {},
        ),
        (
            "00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5",
            335000,
            0,
            {
                Address("0x09fce828cbd5c5bdc742fe5a63776e2a76a111e5"): Account(
                    storage={0: 1}
                ),
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5",
            335000,
            100,
            {
                Address("0x09fce828cbd5c5bdc742fe5a63776e2a76a111e5"): Account(
                    storage={0: 1}
                ),
                Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"): Account(
                    storage={1: 1}
                ),
            },
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
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_check_opcodes5(
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
            Op.MSTORE(
                offset=0x0,
                value=0x972F33115B9E8BE9C87412A04CE61E6C3A84D15D,
            )
            + Op.DELEGATECALL(
                gas=0x186A0,
                address=0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0x09fce828cbd5c5bdc742fe5a63776e2a76a111e5"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x8A6781F0D54ED3CB8963FFC233E98041DE8BDADB,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0x19473707238EF04C4550E6EEE0D12BC0E3A7A02A,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x19473707238ef04c4550e6eee0d12bc0e3a7a02a"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] (CALL 250000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x3D090,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xDF047446304BC9145D7BA20CD326E1097DA151FF,
            )
            + Op.CALL(
                gas=0x186A0,
                address=0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2c073c9d611d927ca91e4819bbb2dff859a8732b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x9C40928B20AC4236F0F3920567F28539C2E158B3,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0x3F1AFEC0E6911FF45E18F4286F10DD905CD18F29,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3f1afec0e6911ff45e18f4286f10dd905cd18f29"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xDF047446304BC9145D7BA20CD326E1097DA151FF,
            )
            + Op.CALL(
                gas=0x186A0,
                address=0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81,
                value=0xA,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0x7761311ee56479da378519606cc4da58e17251ab"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x19473707238EF04C4550E6EEE0D12BC0E3A7A02A,
            )
            + Op.CALLCODE(
                gas=0x186A0,
                address=0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81,
                value=0x1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0x8a6781f0d54ed3cb8963ffc233e98041de8bdadb"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0xC350,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8eeb303e1e7e2bb67d778526e009014a5daead81"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x9FCE828CBD5C5BDC742FE5A63776E2A76A111E5,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0x972F33115B9E8BE9C87412A04CE61E6C3A84D15D,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x972f33115b9e8be9c87412a04ce61e6c3a84d15d"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x3F1AFEC0E6911FF45E18F4286F10DD905CD18F29,
            )
            + Op.CALLCODE(
                gas=0x186A0,
                address=0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0x9c40928b20ac4236f0f3920567f28539c2e158b3"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0xDF047446304BC9145D7BA20CD326E1097DA151FF,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xdf047446304bc9145d7ba20cd326e1097da151ff"),  # noqa: E501
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
