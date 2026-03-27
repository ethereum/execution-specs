"""
Test_revert_precompiled_touch_exact_oog_paris.

Ported from:
state_tests/stRevertTest/RevertPrecompiledTouchExactOOG_ParisFiller.json
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
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
]
TX_GAS = [22500, 120000, 69000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    [
        "state_tests/stRevertTest/RevertPrecompiledTouchExactOOG_ParisFiller.json"  # noqa: E501
    ],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch_exact_oog_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_precompiled_touch_exact_oog_paris."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    addr_0x0000000000000000000000000000000000000001 = Address(
        "0x6eb9afcb5d985b12549b7ac2e65c093f7113a0c7"
    )
    addr_0x0000000000000000000000000000000000000002 = Address(
        "0xf07a794e0f8aab4242b86368503d3c1de15481f8"
    )
    addr_0x0000000000000000000000000000000000000003 = Address(
        "0x9e6c35deced6e05eb21d3465b5bbbb57b9cd57d6"
    )
    addr_0x0000000000000000000000000000000000000004 = Address(
        "0x1688023d9ae9e25ea02a2447a77b9cc9d22ce57b"
    )
    addr_0x0000000000000000000000000000000000000005 = Address(
        "0xd085ab47bc36d1238fc092679b21b10792746640"
    )
    addr_0x0000000000000000000000000000000000000006 = Address(
        "0xad3df2901b7c6642e397c35e0e9f3dea5d098238"
    )
    addr_0x0000000000000000000000000000000000000007 = Address(
        "0xbe44b82021b08cfecc33a2e57ff5adcb7fe3b049"
    )
    addr_0x0000000000000000000000000000000000000008 = Address(
        "0x85fdde91fd0ce22a2968e1f1b2ebb9f9e5a180ba"
    )
    sender = EOA(
        key=0xFF8D58222F34F6890DDAA468C023B77D6691ED7D3C4DCDDAE38336212FAF54B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    # Source: lll
    # {  (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 (CALLDATALOAD 32) 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=Op.CALLDATALOAD(offset=0x20),
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address("0x6c7fac59c79986689878e37545df629f68278098"),  # noqa: E501
    )
    # Source: lll
    # { (CALL (GAS) (CALLDATASIZE) 0 0 0 0 0) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address("0xa2f144d2206204d88e039b31bb7db14a28a06fed"),  # noqa: E501
    )
    # Source: lll
    # { (DELEGATECALL (GAS) (CALLDATASIZE) 0 0 0 0) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address("0x81f666fdc784482530048e74cee651ea98a0733d"),  # noqa: E501
    )
    # Source: lll
    # { (CALLCODE (GAS) (CALLDATASIZE) 0 0 0 0 0) }
    addr_0x3000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address("0x33506407e929a3834ea7bfa65f86b41c7b7e57b9"),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL (GAS) (CALLDATASIZE) 0 0 0 0)  }
    addr_0x4000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address("0xc02fff115e5eee4ff4420eba1cb7cb8772e0598e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    pre[addr_0x0000000000000000000000000000000000000001] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000002] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000003] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000004] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000005] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000006] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000007] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000008] = Account(balance=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 8, 16, 24], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000001: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [1, 25, 9, 17], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000002: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [18, 26, 2, 10], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000003: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [11, 19, 3, 27], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000004: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [20, 28, 4, 12], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000005: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [29, 13, 21, 5], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000006: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [22, 30, 6, 14], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000007: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [31, 15, 23, 7], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000008: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [8, 16], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000001: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [0, 24], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000001: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [9, 17], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000002: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [1, 25], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000002: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [10, 18], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000003: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [2, 26], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000003: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [19, 11], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000004: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [27, 3], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000004: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [12, 20], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000005: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [4, 28], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000005: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [21, 13], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000006: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [29, 5], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000006: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [14, 22], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000007: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [6, 30], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000007: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [23, 15], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000008: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [31, 7], "gas": 2, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000008: Account(
                    nonce=0
                )
            },
        },
        {
            "indexes": {"data": [31, 7], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0x0000000000000000000000000000000000000008: Account(
                    nonce=0
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
