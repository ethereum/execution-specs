"""
Test_modexp.

Ported from:
state_tests/stPreCompiledContracts/modexpFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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
    ["state_tests/stPreCompiledContracts/modexpFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
def test_modexp(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_modexp."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)
    # Source: lll
    # { (CALLDATACOPY 0 0 (CALLDATASIZE)) [[1]] (CALLCODE (GAS) 5 0 0 (CALLDATASIZE) 1000 32) [[2]](MLOAD 1000) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x5,
                value=0x0,
                args_offset=0x0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x3E8,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3E8))
        + Op.STOP,
        nonce=0,
        address=Address(0x2D06AD61919840E4E00F80782DEDCE12ADA1E859),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 6, 7], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={1: 1, 2: 1})},
        },
        {
            "indexes": {"data": [29], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={1: 1, 2: 0})},
        },
        {
            "indexes": {
                "data": [
                    1,
                    5,
                    8,
                    9,
                    10,
                    12,
                    13,
                    15,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    30,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={1: 1, 2: 0})},
        },
        {
            "indexes": {"data": [2, 28], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={1: 0, 2: 0})},
        },
        {
            "indexes": {"data": [31], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={1: 1, 2: 0x100000000000000000000000000000000},
                ),
            },
        },
        {
            "indexes": {"data": [32], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [33], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [34], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [35], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={1: 1, 2: 0x10000000000000000000000000000}
                )
            },
        },
        {
            "indexes": {"data": [3, 4], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [25, 26, 11, 14], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [16, 27], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [17], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(
                    storage={
                        1: 1,
                        2: 0x200000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [36, 37], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={1: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(
            "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002003fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f"  # noqa: E501
        ),
        Hash(0x0)
        + Hash(0x20)
        + Hash(0x20)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2E
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
        ),
        Hash(0x0)
        + Hash(0x20)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD
        ),
        Bytes("00000000")
        + Hash(0x100000000)
        + Hash(0x200000000)
        + Hash(0x2003FFFF80)
        + Hash(0x7),
        Bytes("00000000")
        + Hash(0x100000000)
        + Hash(0x200000000)
        + Hash(0x2003FFFF80),
        Bytes(
            "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000002003"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020038000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000080"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000101"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000304"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001020004"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001020300"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010304"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010204"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000203"  # noqa: E501
        ),
        Bytes("00000000")
        + Hash(0x100000000)
        + Hash(0x100000000)
        + Hash(0x202030006),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001020306"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002020300"  # noqa: E501
        ),
        Bytes("00000000")
        + Hash(0x100000000)
        + Hash(0x100000000)
        + Hash(0x202030000),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020203"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002023003"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020230"  # noqa: E501
        ),
        Bytes(
            "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000202"  # noqa: E501
        ),
        Hash(0x1) + Hash(0x2) + Hash(0x2),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001001001010010"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000064"  # noqa: E501
        ),
        Bytes("00000000")
        + Hash(0x100000000)
        + Hash(0x10100000000)
        + Hash(0x202000000)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x30006),
        Hash(0x40000000000) + Hash(0x0),
        Hash(0x0) + Hash(0x40000000000),
        Hash(0x0)
        + Hash(
            0x8000000000000000000000000000000000000000000000000000000000000000
        )
        + Hash(0x0),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010035ee4e488f45e64d2f07becd54646357381d32f30b74c299a8c25d5202c04938ef6c4764a04f10fc908b78c4486886000f6d290251a79681a83b950c7e5c37351"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000005000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000cd935b43e42204fcbfb734a6e27735e8e90204fcc1fd2727bb040f9eecb"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000060846813a8d2d451387340fa0597c6545ae63"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000005000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d02534f82b1013f20d9c7d18d62cd95674d2e013f20d9c7d18d62cd95674d2f"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001200000000000000000000000000000000000000000000000000000000000000120785e45de3d6be050ba3c4d33ff0bb2d010ace3b1dfe9c49f4c7a8075102fa19a86c010ace3b1dfe9c49f4c7a8075102fa19a86d"  # noqa: E501
        ),
        Hash(0xFF)
        + Hash(
            0x2A1E530000000000000000000000000000000000000000000000000000000000
        )
        + Hash(0x0),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001200000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000010001"  # noqa: E501
        ),
    ]
    tx_gas = [100000000, 90000, 110000, 200000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
