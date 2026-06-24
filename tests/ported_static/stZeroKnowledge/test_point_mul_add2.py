"""
Test_point_mul_add2.

Ported from:
state_tests/stZeroKnowledge/pointMulAdd2Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
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


@pytest.mark.ported_from(
    ["state_tests/stZeroKnowledge/pointMulAdd2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            0,
            2,
            0,
            id="d0-g2",
        ),
        pytest.param(
            0,
            3,
            0,
            id="d0-g3",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            1,
            2,
            0,
            id="d1-g2",
        ),
        pytest.param(
            1,
            3,
            0,
            id="d1-g3",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
        pytest.param(
            2,
            2,
            0,
            id="d2-g2",
        ),
        pytest.param(
            2,
            3,
            0,
            id="d2-g3",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1",
        ),
        pytest.param(
            3,
            2,
            0,
            id="d3-g2",
        ),
        pytest.param(
            3,
            3,
            0,
            id="d3-g3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4-g0",
        ),
        pytest.param(
            4,
            1,
            0,
            id="d4-g1",
        ),
        pytest.param(
            4,
            2,
            0,
            id="d4-g2",
        ),
        pytest.param(
            4,
            3,
            0,
            id="d4-g3",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5-g0",
        ),
        pytest.param(
            5,
            1,
            0,
            id="d5-g1",
        ),
        pytest.param(
            5,
            2,
            0,
            id="d5-g2",
        ),
        pytest.param(
            5,
            3,
            0,
            id="d5-g3",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6-g0",
        ),
        pytest.param(
            6,
            1,
            0,
            id="d6-g1",
        ),
        pytest.param(
            6,
            2,
            0,
            id="d6-g2",
        ),
        pytest.param(
            6,
            3,
            0,
            id="d6-g3",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7-g0",
        ),
        pytest.param(
            7,
            1,
            0,
            id="d7-g1",
        ),
        pytest.param(
            7,
            2,
            0,
            id="d7-g2",
        ),
        pytest.param(
            7,
            3,
            0,
            id="d7-g3",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8-g0",
        ),
        pytest.param(
            8,
            1,
            0,
            id="d8-g1",
        ),
        pytest.param(
            8,
            2,
            0,
            id="d8-g2",
        ),
        pytest.param(
            8,
            3,
            0,
            id="d8-g3",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9-g0",
        ),
        pytest.param(
            9,
            1,
            0,
            id="d9-g1",
        ),
        pytest.param(
            9,
            2,
            0,
            id="d9-g2",
        ),
        pytest.param(
            9,
            3,
            0,
            id="d9-g3",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10-g0",
        ),
        pytest.param(
            10,
            1,
            0,
            id="d10-g1",
        ),
        pytest.param(
            10,
            2,
            0,
            id="d10-g2",
        ),
        pytest.param(
            10,
            3,
            0,
            id="d10-g3",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11-g0",
        ),
        pytest.param(
            11,
            1,
            0,
            id="d11-g1",
        ),
        pytest.param(
            11,
            2,
            0,
            id="d11-g2",
        ),
        pytest.param(
            11,
            3,
            0,
            id="d11-g3",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12-g0",
        ),
        pytest.param(
            12,
            1,
            0,
            id="d12-g1",
        ),
        pytest.param(
            12,
            2,
            0,
            id="d12-g2",
        ),
        pytest.param(
            12,
            3,
            0,
            id="d12-g3",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13-g0",
        ),
        pytest.param(
            13,
            1,
            0,
            id="d13-g1",
        ),
        pytest.param(
            13,
            2,
            0,
            id="d13-g2",
        ),
        pytest.param(
            13,
            3,
            0,
            id="d13-g3",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14-g0",
        ),
        pytest.param(
            14,
            1,
            0,
            id="d14-g1",
        ),
        pytest.param(
            14,
            2,
            0,
            id="d14-g2",
        ),
        pytest.param(
            14,
            3,
            0,
            id="d14-g3",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15-g0",
        ),
        pytest.param(
            15,
            1,
            0,
            id="d15-g1",
        ),
        pytest.param(
            15,
            2,
            0,
            id="d15-g2",
        ),
        pytest.param(
            15,
            3,
            0,
            id="d15-g3",
        ),
        pytest.param(
            16,
            0,
            0,
            id="d16-g0",
        ),
        pytest.param(
            16,
            1,
            0,
            id="d16-g1",
        ),
        pytest.param(
            16,
            2,
            0,
            id="d16-g2",
        ),
        pytest.param(
            16,
            3,
            0,
            id="d16-g3",
        ),
        pytest.param(
            17,
            0,
            0,
            id="d17-g0",
        ),
        pytest.param(
            17,
            1,
            0,
            id="d17-g1",
        ),
        pytest.param(
            17,
            2,
            0,
            id="d17-g2",
        ),
        pytest.param(
            17,
            3,
            0,
            id="d17-g3",
        ),
        pytest.param(
            18,
            0,
            0,
            id="d18-g0",
        ),
        pytest.param(
            18,
            1,
            0,
            id="d18-g1",
        ),
        pytest.param(
            18,
            2,
            0,
            id="d18-g2",
        ),
        pytest.param(
            18,
            3,
            0,
            id="d18-g3",
        ),
        pytest.param(
            19,
            0,
            0,
            id="d19-g0",
        ),
        pytest.param(
            19,
            1,
            0,
            id="d19-g1",
        ),
        pytest.param(
            19,
            2,
            0,
            id="d19-g2",
        ),
        pytest.param(
            19,
            3,
            0,
            id="d19-g3",
        ),
        pytest.param(
            20,
            0,
            0,
            id="d20-g0",
        ),
        pytest.param(
            20,
            1,
            0,
            id="d20-g1",
        ),
        pytest.param(
            20,
            2,
            0,
            id="d20-g2",
        ),
        pytest.param(
            20,
            3,
            0,
            id="d20-g3",
        ),
        pytest.param(
            21,
            0,
            0,
            id="d21-g0",
        ),
        pytest.param(
            21,
            1,
            0,
            id="d21-g1",
        ),
        pytest.param(
            21,
            2,
            0,
            id="d21-g2",
        ),
        pytest.param(
            21,
            3,
            0,
            id="d21-g3",
        ),
        pytest.param(
            22,
            0,
            0,
            id="d22-g0",
        ),
        pytest.param(
            22,
            1,
            0,
            id="d22-g1",
        ),
        pytest.param(
            22,
            2,
            0,
            id="d22-g2",
        ),
        pytest.param(
            22,
            3,
            0,
            id="d22-g3",
        ),
        pytest.param(
            23,
            0,
            0,
            id="d23-g0",
        ),
        pytest.param(
            23,
            1,
            0,
            id="d23-g1",
        ),
        pytest.param(
            23,
            2,
            0,
            id="d23-g2",
        ),
        pytest.param(
            23,
            3,
            0,
            id="d23-g3",
        ),
        pytest.param(
            24,
            0,
            0,
            id="d24-g0",
        ),
        pytest.param(
            24,
            1,
            0,
            id="d24-g1",
        ),
        pytest.param(
            24,
            2,
            0,
            id="d24-g2",
        ),
        pytest.param(
            24,
            3,
            0,
            id="d24-g3",
        ),
        pytest.param(
            25,
            0,
            0,
            id="d25-g0",
        ),
        pytest.param(
            25,
            1,
            0,
            id="d25-g1",
        ),
        pytest.param(
            25,
            2,
            0,
            id="d25-g2",
        ),
        pytest.param(
            25,
            3,
            0,
            id="d25-g3",
        ),
        pytest.param(
            26,
            0,
            0,
            id="d26-g0",
        ),
        pytest.param(
            26,
            1,
            0,
            id="d26-g1",
        ),
        pytest.param(
            26,
            2,
            0,
            id="d26-g2",
        ),
        pytest.param(
            26,
            3,
            0,
            id="d26-g3",
        ),
        pytest.param(
            27,
            0,
            0,
            id="d27-g0",
        ),
        pytest.param(
            27,
            1,
            0,
            id="d27-g1",
        ),
        pytest.param(
            27,
            2,
            0,
            id="d27-g2",
        ),
        pytest.param(
            27,
            3,
            0,
            id="d27-g3",
        ),
        pytest.param(
            28,
            0,
            0,
            id="d28-g0",
        ),
        pytest.param(
            28,
            1,
            0,
            id="d28-g1",
        ),
        pytest.param(
            28,
            2,
            0,
            id="d28-g2",
        ),
        pytest.param(
            28,
            3,
            0,
            id="d28-g3",
        ),
        pytest.param(
            29,
            0,
            0,
            id="d29-g0",
        ),
        pytest.param(
            29,
            1,
            0,
            id="d29-g1",
        ),
        pytest.param(
            29,
            2,
            0,
            id="d29-g2",
        ),
        pytest.param(
            29,
            3,
            0,
            id="d29-g3",
        ),
        pytest.param(
            30,
            0,
            0,
            id="d30-g0",
        ),
        pytest.param(
            30,
            1,
            0,
            id="d30-g1",
        ),
        pytest.param(
            30,
            2,
            0,
            id="d30-g2",
        ),
        pytest.param(
            30,
            3,
            0,
            id="d30-g3",
        ),
        pytest.param(
            31,
            0,
            0,
            id="d31-g0",
        ),
        pytest.param(
            31,
            1,
            0,
            id="d31-g1",
        ),
        pytest.param(
            31,
            2,
            0,
            id="d31-g2",
        ),
        pytest.param(
            31,
            3,
            0,
            id="d31-g3",
        ),
        pytest.param(
            32,
            0,
            0,
            id="d32-g0",
        ),
        pytest.param(
            32,
            1,
            0,
            id="d32-g1",
        ),
        pytest.param(
            32,
            2,
            0,
            id="d32-g2",
        ),
        pytest.param(
            32,
            3,
            0,
            id="d32-g3",
        ),
        pytest.param(
            33,
            0,
            0,
            id="d33-g0",
        ),
        pytest.param(
            33,
            1,
            0,
            id="d33-g1",
        ),
        pytest.param(
            33,
            2,
            0,
            id="d33-g2",
        ),
        pytest.param(
            33,
            3,
            0,
            id="d33-g3",
        ),
        pytest.param(
            34,
            0,
            0,
            id="d34-g0",
        ),
        pytest.param(
            34,
            1,
            0,
            id="d34-g1",
        ),
        pytest.param(
            34,
            2,
            0,
            id="d34-g2",
        ),
        pytest.param(
            34,
            3,
            0,
            id="d34-g3",
        ),
        pytest.param(
            35,
            0,
            0,
            id="d35-g0",
        ),
        pytest.param(
            35,
            1,
            0,
            id="d35-g1",
        ),
        pytest.param(
            35,
            2,
            0,
            id="d35-g2",
        ),
        pytest.param(
            35,
            3,
            0,
            id="d35-g3",
        ),
        pytest.param(
            36,
            0,
            0,
            id="d36-g0",
        ),
        pytest.param(
            36,
            1,
            0,
            id="d36-g1",
        ),
        pytest.param(
            36,
            2,
            0,
            id="d36-g2",
        ),
        pytest.param(
            36,
            3,
            0,
            id="d36-g3",
        ),
        pytest.param(
            37,
            0,
            0,
            id="d37-g0",
        ),
        pytest.param(
            37,
            1,
            0,
            id="d37-g1",
        ),
        pytest.param(
            37,
            2,
            0,
            id="d37-g2",
        ),
        pytest.param(
            37,
            3,
            0,
            id="d37-g3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_point_mul_add2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_point_mul_add2."""
    coinbase = Address(0x68795C4AA09D6F4ED3E5DEDDF8C2AD3049A601DA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    # Source: lll
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96))  (MSTORE 128 (CALLDATALOAD 128)) (MSTORE 160 (CALLDATALOAD 160)) (MSTORE 192 (CALLDATALOAD 192)) [[0]](CALLCODE 500000 6 0 0 128 300 64)  [[1]](CALLCODE 500000 7 0 128 96 400 64) [[10]] (MLOAD 300)  [[11]] (MLOAD 332) [[20]] (MLOAD 400)  [[21]] (MLOAD 432) [[2]] (EQ (SLOAD 10) (SLOAD 20)) [[3]] (EQ (SLOAD 11) (SLOAD 21))}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
        + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x80))
        + Op.MSTORE(offset=0xA0, value=Op.CALLDATALOAD(offset=0xA0))
        + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0xC0))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x12C,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x7,
                value=0x0,
                args_offset=0x80,
                args_size=0x60,
                ret_offset=0x190,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x12C))
        + Op.SSTORE(key=0xB, value=Op.MLOAD(offset=0x14C))
        + Op.SSTORE(key=0x14, value=Op.MLOAD(offset=0x190))
        + Op.SSTORE(key=0x15, value=Op.MLOAD(offset=0x1B0))
        + Op.SSTORE(
            key=0x2, value=Op.EQ(Op.SLOAD(key=0xA), Op.SLOAD(key=0x14))
        )
        + Op.SSTORE(
            key=0x3, value=Op.EQ(Op.SLOAD(key=0xB), Op.SLOAD(key=0x15))
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 26],
                "gas": [0],
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
        {
            "indexes": {"data": [10], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,  # noqa: E501
                        11: 0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,  # noqa: E501
                        20: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,  # noqa: E501
                        21: 0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [11], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,  # noqa: E501
                        11: 0x5ACB4B400E90C0063006A39F478F3E865E306DD5CD56F356E2E8CD8FE7EDAE6,  # noqa: E501
                        20: 0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,  # noqa: E501
                        21: 0x5ACB4B400E90C0063006A39F478F3E865E306DD5CD56F356E2E8CD8FE7EDAE6,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [13, 15], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,  # noqa: E501
                        11: 0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4,  # noqa: E501
                        20: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,  # noqa: E501
                        21: 0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [14], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 1,
                        11: 2,
                        20: 1,
                        21: 2,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [16], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 1,
                        11: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,  # noqa: E501
                        20: 1,
                        21: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [17], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x113AECCECDAF57CD8C0AACE591774949DCDAF892555FA86726FA7E679B89C067,  # noqa: E501
                        11: 0xBFFBA84127A19ABDE488A8251A9A3FCE33B34A76F96AAFB11AB4A6CEF3E9979,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [18], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,  # noqa: E501
                        11: 0x29CE3D80A74DDC13784BEB25CA9FBFD048A3265A32C6F38B92060C5093A0E7A7,  # noqa: E501
                        20: 0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,  # noqa: E501
                        21: 0x29CE3D80A74DDC13784BEB25CA9FBFD048A3265A32C6F38B92060C5093A0E7A7,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [19], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628,  # noqa: E501
                        11: 0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD,  # noqa: E501
                        20: 0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628,  # noqa: E501
                        21: 0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [20], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,  # noqa: E501
                        11: 0x29CE3D80A74DDC13784BEB25CA9FBFD048A3265A32C6F38B92060C5093A0E7A7,  # noqa: E501
                        20: 0x2C15ED1902E189486AB6B625AA982510AEF6246B21A1E1BCEA382DA4D735E8BA,  # noqa: E501
                        21: 0x2103E58CBD2FA8081763442AB46C26A9B8051E9B049C3948C8D7D0E139C5E3F,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [21], "gas": [0, 3], "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x1D78954C630B3895FBBFAFAC1294F2C0158879FDC70BFE18222890E7BFB66FBA,  # noqa: E501
                        11: 0x101C3346E98B136A7078AEBD427DCED763722D77E3D7985342E0BFFCC6EA4D56,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [22], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,  # noqa: E501
                        11: 0x1EED5D5325C31FC89DD541A13D7F63B981FAE8D4BF78A6B08A38A601FCFEA97B,  # noqa: E501
                        20: 0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,  # noqa: E501
                        21: 0x1EED5D5325C31FC89DD541A13D7F63B981FAE8D4BF78A6B08A38A601FCFEA97B,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [23], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352,  # noqa: E501
                        11: 0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0,  # noqa: E501
                        20: 0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352,  # noqa: E501
                        21: 0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [24], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,  # noqa: E501
                        11: 0x1EED5D5325C31FC89DD541A13D7F63B981FAE8D4BF78A6B08A38A601FCFEA97B,  # noqa: E501
                        20: 0x8E2142845DB159BD105879A109FE7A6F254ED3DDAE0E9CD8A2AEAE05E5F647B,  # noqa: E501
                        21: 0x221108EE615499D2E0A1113CA1A858A34E055F9DA2D30E6E6AB392B049944A92,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [25], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,  # noqa: E501
                        11: 0x2AB799BEE0489429554FDB7C8D086475319E63B40B9C5B57CDF1FF3DD9FE2261,  # noqa: E501
                        20: 0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,  # noqa: E501
                        21: 0x2AB799BEE0489429554FDB7C8D086475319E63B40B9C5B57CDF1FF3DD9FE2261,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [27], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 1,
                        11: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,  # noqa: E501
                        20: 1,
                        21: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [28], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,  # noqa: E501
                        11: 0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,  # noqa: E501
                        20: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,  # noqa: E501
                        21: 0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [29], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 1,
                        11: 2,
                        20: 1,
                        21: 2,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [30], "gas": [0, 3], "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x113AECCECDAF57CD8C0AACE591774949DCDAF892555FA86726FA7E679B89C067,  # noqa: E501
                        11: 0x246493EECEB7867DDA07BB342FD7B460B44635E9F8DB1F922A7541A9E93E63CE,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [31], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,  # noqa: E501
                        11: 0x69610F239E3C41640045A90B6E1988D4EDE443735AAD701AA1A7FC644DC15A0,  # noqa: E501
                        20: 0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,  # noqa: E501
                        21: 0x69610F239E3C41640045A90B6E1988D4EDE443735AAD701AA1A7FC644DC15A0,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [32], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628,  # noqa: E501
                        11: 0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A,  # noqa: E501
                        20: 0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628,  # noqa: E501
                        21: 0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [33], "gas": [0], "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,  # noqa: E501
                        11: 0x69610F239E3C41640045A90B6E1988D4EDE443735AAD701AA1A7FC644DC15A0,  # noqa: E501
                        20: 0x2C15ED1902E189486AB6B625AA982510AEF6246B21A1E1BCEA382DA4D735E8BA,  # noqa: E501
                        21: 0x2E54101A155EA5A936DA1173D63A95F2FC0118A7B82806F8AF930F08C4E09F08,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [34], "gas": [0, 3], "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x1D78954C630B3895FBBFAFAC1294F2C0158879FDC70BFE18222890E7BFB66FBA,  # noqa: E501
                        11: 0x20481B2BF7A68CBF47D796F93F038986340F3D19849A3239F93FCC1A1192AFF1,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [35], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,  # noqa: E501
                        11: 0x1176F11FBB6E80611A7B04154401F4A4158681BCA8F923DCB1E7E614DB7E53CC,  # noqa: E501
                        20: 0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,  # noqa: E501
                        21: 0x1176F11FBB6E80611A7B04154401F4A4158681BCA8F923DCB1E7E614DB7E53CC,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [36], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352,  # noqa: E501
                        11: 0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97,  # noqa: E501
                        20: 0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352,  # noqa: E501
                        21: 0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [37], "gas": [0], "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,  # noqa: E501
                        11: 0x1176F11FBB6E80611A7B04154401F4A4158681BCA8F923DCB1E7E614DB7E53CC,  # noqa: E501
                        20: 0x8E2142845DB159BD105879A109FE7A6F254ED3DDAE0E9CD8A2AEAE05E5F647B,  # noqa: E501
                        21: 0xE5345847FDD0656D7AF3479DFD8FFBA497C0AF3C59EBC1ED16CF9668EE8B2B5,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={})},
        },
        {
            "indexes": {
                "data": [
                    32,
                    35,
                    36,
                    10,
                    11,
                    13,
                    14,
                    15,
                    16,
                    18,
                    19,
                    22,
                    23,
                    25,
                    27,
                    28,
                    29,
                ],
                "gas": [3],
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={})},
        },
        {
            "indexes": {
                "data": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 26],
                "gas": [3],
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
        {
            "indexes": {"data": [17], "gas": [3], "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x113AECCECDAF57CD8C0AACE591774949DCDAF892555FA86726FA7E679B89C067,  # noqa: E501
                        11: 0xBFFBA84127A19ABDE488A8251A9A3FCE33B34A76F96AAFB11AB4A6CEF3E9979,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [33, 37, 20, 24, 31], "gas": [3], "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x2),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x3),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000000
        ),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593EFFFFFFF
        ),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD46
        ),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        ),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x2),
        Hash(0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3)
        + Hash(
            0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x3),
        Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x0),
        Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x2),
        Hash(0x1)
        + Hash(0x2)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000000
        ),
        Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593EFFFFFFF
        ),
        Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x0),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD
        )
        + Hash(
            0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628
        )
        + Hash(
            0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD
        )
        + Hash(
            0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628
        )
        + Hash(
            0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD
        )
        + Hash(0x2),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD46
        ),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD
        )
        + Hash(
            0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628
        )
        + Hash(
            0x69EF5E376C0A1EA82F9DFC2E0001A7F385D655EEF9A6F976C7A5D2C493EA3AD
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        ),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x0),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0
        )
        + Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0
        )
        + Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0
        )
        + Hash(0x2),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0
        )
        + Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x1D701EC9E3FCA50E84777F0F68CAFF5BFF48CF6A6BD4428462AE9366CF0582B0
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Hash(0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3)
        + Hash(
            0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x3),
        Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x0),
        Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000000
        ),
        Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593EFFFFFFF
        ),
        Hash(0x1)
        + Hash(0x2)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x0),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A
        )
        + Hash(
            0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628
        )
        + Hash(
            0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A
        )
        + Hash(
            0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628
        )
        + Hash(
            0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A
        )
        + Hash(0x2),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD46
        ),
        Hash(0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628)
        + Hash(
            0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A
        )
        + Hash(
            0xCCBEC17235F5B9CC5E42F3DF6364A76ECDD0101DDDA8FC5DC0BA0B59C0E5628
        )
        + Hash(
            0x29C5588F6A70FE3F355665F3A1813DDE5F24053278D75AF5CFA62EEA8F3E599A
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        ),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x0),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97
        )
        + Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97
        )
        + Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97
        )
        + Hash(0x2),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97
        )
        + Hash(
            0x2F588CFFE99DB877A4434B598AB28F81E0522910EA52B45F0ADAA772B2D5D352
        )
        + Hash(
            0x12F42FA8FD34FB1B33D8C6A718B6590198389B26FC9D8808D971F8B009777A97
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
    ]
    tx_gas = [2000000, 90000, 110000, 150000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
