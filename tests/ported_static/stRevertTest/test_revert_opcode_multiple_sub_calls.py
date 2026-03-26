"""
test_revert_opcode_multiple_sub_calls

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
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

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
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeMultipleSubCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0-g0-v0",
        ),
        pytest.param(
            0, 0, 1,
            id="d0-g0-v1",
        ),
        pytest.param(
            0, 1, 0,
            id="d0-g1-v0",
        ),
        pytest.param(
            0, 1, 1,
            id="d0-g1-v1",
        ),
        pytest.param(
            0, 2, 0,
            id="d0-g2-v0",
        ),
        pytest.param(
            0, 2, 1,
            id="d0-g2-v1",
        ),
        pytest.param(
            0, 3, 0,
            id="d0-g3-v0",
        ),
        pytest.param(
            0, 3, 1,
            id="d0-g3-v1",
        ),
        pytest.param(
            1, 0, 0,
            id="d1-g0-v0",
        ),
        pytest.param(
            1, 0, 1,
            id="d1-g0-v1",
        ),
        pytest.param(
            1, 1, 0,
            id="d1-g1-v0",
        ),
        pytest.param(
            1, 1, 1,
            id="d1-g1-v1",
        ),
        pytest.param(
            1, 2, 0,
            id="d1-g2-v0",
        ),
        pytest.param(
            1, 2, 1,
            id="d1-g2-v1",
        ),
        pytest.param(
            1, 3, 0,
            id="d1-g3-v0",
        ),
        pytest.param(
            1, 3, 1,
            id="d1-g3-v1",
        ),
        pytest.param(
            2, 0, 0,
            id="d2-g0-v0",
        ),
        pytest.param(
            2, 0, 1,
            id="d2-g0-v1",
        ),
        pytest.param(
            2, 1, 0,
            id="d2-g1-v0",
        ),
        pytest.param(
            2, 1, 1,
            id="d2-g1-v1",
        ),
        pytest.param(
            2, 2, 0,
            id="d2-g2-v0",
        ),
        pytest.param(
            2, 2, 1,
            id="d2-g2-v1",
        ),
        pytest.param(
            2, 3, 0,
            id="d2-g3-v0",
        ),
        pytest.param(
            2, 3, 1,
            id="d2-g3-v1",
        ),
        pytest.param(
            3, 0, 0,
            id="d3-g0-v0",
        ),
        pytest.param(
            3, 0, 1,
            id="d3-g0-v1",
        ),
        pytest.param(
            3, 1, 0,
            id="d3-g1-v0",
        ),
        pytest.param(
            3, 1, 1,
            id="d3-g1-v1",
        ),
        pytest.param(
            3, 2, 0,
            id="d3-g2-v0",
        ),
        pytest.param(
            3, 2, 1,
            id="d3-g2-v1",
        ),
        pytest.param(
            3, 3, 0,
            id="d3-g3-v0",
        ),
        pytest.param(
            3, 3, 1,
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
    """test_revert_opcode_multiple_sub_calls"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { (CALL 260000 (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.CALL(gas=0x3f7a0, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x89ab420962193a25593b5663462b75c083d56148"),  # noqa: E501
    )
    # Source: lll
    # { [[10]](CALL 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[11]](CALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0) [[12]](CALL 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0) [[4]]12 [[5]]12 }
    addr_0xa000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0xa, value=Op.CALL(gas=0xc350, address=0x86c575f296a8a021a2a64972e57a20b06fe8b897, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xb, value=Op.CALL(gas=0xc350, address=0x3d2496d905cf0e9c77473cbfb6e100062b5af57f, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xc, value=Op.CALL(gas=0xc350, address=0x83bac26dd305c061381c042d0bac07b08d15bbce, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x4, value=0xc) + Op.SSTORE(key=0x5, value=0xc) + Op.STOP,  # noqa: E501
        nonce=0,
        address=Address("0xd7e294f032a5cc430e9e6c4148220867e9704dcd"),  # noqa: E501
    )
    # Source: lll
    # { [[10]](CALLCODE 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[11]](CALLCODE 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0) [[12]](CALLCODE 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0) [[4]]12 [[5]]12 }
    addr_0xa100000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0xa, value=Op.CALLCODE(gas=0xc350, address=0x86c575f296a8a021a2a64972e57a20b06fe8b897, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xb, value=Op.CALLCODE(gas=0xc350, address=0x3d2496d905cf0e9c77473cbfb6e100062b5af57f, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xc, value=Op.CALLCODE(gas=0xc350, address=0x83bac26dd305c061381c042d0bac07b08d15bbce, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x4, value=0xc) + Op.SSTORE(key=0x5, value=0xc) + Op.STOP,  # noqa: E501
        nonce=0,
        address=Address("0xee88dfd8455d7d9d6d33231f3daf6d9a4526d5cf"),  # noqa: E501
    )
    # Source: lll
    # { [[10]](DELEGATECALL 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) [[11]](DELEGATECALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) [[12]](DELEGATECALL 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0) [[4]]12 [[5]]12 }
    addr_0xa200000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0xa, value=Op.DELEGATECALL(gas=0xc350, address=0x86c575f296a8a021a2a64972e57a20b06fe8b897, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xb, value=Op.DELEGATECALL(gas=0xc350, address=0x3d2496d905cf0e9c77473cbfb6e100062b5af57f, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xc, value=Op.DELEGATECALL(gas=0xc350, address=0x83bac26dd305c061381c042d0bac07b08d15bbce, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x4, value=0xc) + Op.SSTORE(key=0x5, value=0xc) + Op.STOP,  # noqa: E501
        nonce=0,
        address=Address("0x68cf97c6ca41ecfc5623d8a7e9b6f72068213e95"),  # noqa: E501
    )
    # Source: lll
    # { [[10]](CALL 50000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[11]](DELEGATECALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) [[12]](CALLCODE 50000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0) [[4]]12 [[5]]12 }
    addr_0xa300000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0xa, value=Op.CALL(gas=0xc350, address=0x86c575f296a8a021a2a64972e57a20b06fe8b897, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xb, value=Op.DELEGATECALL(gas=0xc350, address=0x3d2496d905cf0e9c77473cbfb6e100062b5af57f, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xc, value=Op.CALLCODE(gas=0xc350, address=0x83bac26dd305c061381c042d0bac07b08d15bbce, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x4, value=0xc) + Op.SSTORE(key=0x5, value=0xc) + Op.STOP,  # noqa: E501
        nonce=0,
        address=Address("0x1302fd3b212e7e634f82ed6d00ac14544e8b1cab"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 (REVERT 0 1) }
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc) + Op.REVERT(offset=0x0, size=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0x86c575f296a8a021a2a64972e57a20b06fe8b897"),  # noqa: E501
    )
    # Source: lll
    # { [[2]] 12 (REVERT 0 1) }
    addr_0xc000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0xc) + Op.REVERT(offset=0x0, size=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0x3d2496d905cf0e9c77473cbfb6e100062b5af57f"),  # noqa: E501
    )
    # Source: lll
    # { [[3]] 12 (REVERT 0 1) }
    addr_0xd000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0xc) + Op.REVERT(offset=0x0, size=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0x83bac26dd305c061381c042d0bac07b08d15bbce"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        addr_0xa000000000000000000000000000000000000000: Account(
                storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                nonce=0,
            ),
        addr_0xb000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        addr_0xa100000000000000000000000000000000000000: Account(
                storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                nonce=0,
            ),
        addr_0xb000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
    },
        },
        {
            "indexes": {'data': 2, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        addr_0xa200000000000000000000000000000000000000: Account(
                storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                nonce=0,
            ),
        addr_0xb000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
    },
        },
        {
            "indexes": {'data': 3, 'gas': [0, 2], 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        addr_0xa300000000000000000000000000000000000000: Account(
                storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                nonce=0,
            ),
        addr_0xb000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
    },
        },
        {
            "indexes": {'data': [1, 2], 'gas': 2, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        addr_0xa300000000000000000000000000000000000000: Account(storage={4: 0, 5: 0, 10: 0, 11: 0, 12: 0}, nonce=0),
        addr_0xb000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
    },
        },
        {
            "indexes": {'data': 0, 'gas': [2], 'value': [0, 1]},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        addr_0xa000000000000000000000000000000000000000: Account(
                storage={4: 12, 5: 12, 10: 0, 11: 0, 12: 0},
                nonce=0,
            ),
        addr_0xa100000000000000000000000000000000000000: Account(storage={}, nonce=0),
        addr_0xa200000000000000000000000000000000000000: Account(storage={}, nonce=0),
        addr_0xa300000000000000000000000000000000000000: Account(storage={}, nonce=0),
        addr_0xb000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
    },
        },
        {
            "indexes": {'data': -1, 'gas': [1, 3], 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        addr_0xa000000000000000000000000000000000000000: Account(storage={4: 0, 5: 0, 10: 0, 11: 0, 12: 0}, nonce=0),
        addr_0xa100000000000000000000000000000000000000: Account(storage={}, nonce=0),
        addr_0xa200000000000000000000000000000000000000: Account(storage={}, nonce=0),
        addr_0xa300000000000000000000000000000000000000: Account(storage={}, nonce=0),
        addr_0xb000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={1: 0, 2: 0, 3: 0}),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
