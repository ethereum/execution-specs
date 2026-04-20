"""
Test_revert_opcode_multiple_sub_calls.

Ported from:
state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json
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
    ["state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="d0-g1-v1",
        ),
        pytest.param(
            0,
            2,
            0,
            id="d0-g2-v0",
        ),
        pytest.param(
            0,
            2,
            1,
            id="d0-g2-v1",
        ),
        pytest.param(
            0,
            3,
            0,
            id="d0-g3-v0",
        ),
        pytest.param(
            0,
            3,
            1,
            id="d0-g3-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-g0-v1",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1-v0",
        ),
        pytest.param(
            1,
            1,
            1,
            id="d1-g1-v1",
        ),
        pytest.param(
            1,
            2,
            0,
            id="d1-g2-v0",
        ),
        pytest.param(
            1,
            2,
            1,
            id="d1-g2-v1",
        ),
        pytest.param(
            1,
            3,
            0,
            id="d1-g3-v0",
        ),
        pytest.param(
            1,
            3,
            1,
            id="d1-g3-v1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0-v0",
        ),
        pytest.param(
            2,
            0,
            1,
            id="d2-g0-v1",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1-v0",
        ),
        pytest.param(
            2,
            1,
            1,
            id="d2-g1-v1",
        ),
        pytest.param(
            2,
            2,
            0,
            id="d2-g2-v0",
        ),
        pytest.param(
            2,
            2,
            1,
            id="d2-g2-v1",
        ),
        pytest.param(
            2,
            3,
            0,
            id="d2-g3-v0",
        ),
        pytest.param(
            2,
            3,
            1,
            id="d2-g3-v1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0-v0",
        ),
        pytest.param(
            3,
            0,
            1,
            id="d3-g0-v1",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1-v0",
        ),
        pytest.param(
            3,
            1,
            1,
            id="d3-g1-v1",
        ),
        pytest.param(
            3,
            2,
            0,
            id="d3-g2-v0",
        ),
        pytest.param(
            3,
            2,
            1,
            id="d3-g2-v1",
        ),
        pytest.param(
            3,
            3,
            0,
            id="d3-g3-v0",
        ),
        pytest.param(
            3,
            3,
            1,
            id="d3-g3-v1",
        ),
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
    """Test_revert_opcode_multiple_sub_calls."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (CALL 260000 (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x3F7A0,
            address=Op.CALLDATALOAD(offset=0x0),
            value=Op.CALLVALUE,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x89AB420962193A25593B5663462B75C083D56148),  # noqa: E501
    )
    # Source: lll
    # { [[10]](CALL 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[11]](CALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0) [[12]](CALL 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0) [[4]]12 [[5]]12 }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        nonce=0,
        address=Address(0xD7E294F032A5CC430E9E6C4148220867E9704DCD),  # noqa: E501
    )
    # Source: lll
    # { [[10]](CALLCODE 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[11]](CALLCODE 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0) [[12]](CALLCODE 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0) [[4]]12 [[5]]12 }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        nonce=0,
        address=Address(0xEE88DFD8455D7D9D6D33231F3DAF6D9A4526D5CF),  # noqa: E501
    )
    # Source: lll
    # { [[10]](DELEGATECALL 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) [[11]](DELEGATECALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) [[12]](DELEGATECALL 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0) [[4]]12 [[5]]12 }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        nonce=0,
        address=Address(0x68CF97C6CA41ECFC5623D8A7E9B6F72068213E95),  # noqa: E501
    )
    # Source: lll
    # { [[10]](CALL 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[11]](DELEGATECALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) [[12]](CALLCODE 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0) [[4]]12 [[5]]12 }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        nonce=0,
        address=Address(0x1302FD3B212E7E634F82ED6D00AC14544E8B1CAB),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 (REVERT 0 1) }
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x86C575F296A8A021A2A64972E57A20B06FE8B897),  # noqa: E501
    )
    # Source: lll
    # { [[2]] 12 (REVERT 0 1) }
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x3D2496D905CF0E9C77473CBFB6E100062B5AF57F),  # noqa: E501
    )
    # Source: lll
    # { [[3]] 12 (REVERT 0 1) }
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x83BAC26DD305C061381C042D0BAC07B08D15BBCE),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr: Account(
                    storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                    nonce=0,
                ),
                addr_5: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_6: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_7: Account(storage={1: 0, 2: 0, 3: 0}),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_2: Account(
                    storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                    nonce=0,
                ),
                addr_5: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_6: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_7: Account(storage={1: 0, 2: 0, 3: 0}),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_3: Account(
                    storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                    nonce=0,
                ),
                addr_5: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_6: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_7: Account(storage={1: 0, 2: 0, 3: 0}),
            },
        },
        {
            "indexes": {"data": 3, "gas": [0, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_4: Account(
                    storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                    nonce=0,
                ),
                addr_5: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_6: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_7: Account(storage={1: 0, 2: 0, 3: 0}),
            },
        },
        {
            "indexes": {"data": [1, 2], "gas": 2, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_4: Account(
                    storage={4: 0, 5: 0, 10: 0, 11: 0, 12: 0}, nonce=0
                ),
                addr_5: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_6: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_7: Account(storage={1: 0, 2: 0, 3: 0}),
            },
        },
        {
            "indexes": {"data": 0, "gas": [2], "value": [0, 1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr: Account(
                    storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                    nonce=0,
                ),
                addr_2: Account(storage={}, nonce=0),
                addr_3: Account(storage={}, nonce=0),
                addr_4: Account(storage={}, nonce=0),
                addr_5: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_6: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_7: Account(storage={1: 0, 2: 0, 3: 0}),
            },
        },
        {
            "indexes": {"data": -1, "gas": [1, 3], "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr: Account(
                    storage={4: 0, 5: 0, 10: 0, 11: 0, 12: 0}, nonce=0
                ),
                addr_2: Account(storage={}, nonce=0),
                addr_3: Account(storage={}, nonce=0),
                addr_4: Account(storage={}, nonce=0),
                addr_5: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_6: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_7: Account(storage={1: 0, 2: 0, 3: 0}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
    ]
    tx_gas = [800000, 126200, 160000, 50000]
    tx_value = [0, 10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
