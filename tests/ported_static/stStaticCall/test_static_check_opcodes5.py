"""
Test_static_check_opcodes5.

Ported from:
state_tests/stStaticCall/static_CheckOpcodes5Filler.json
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
    "0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b",
    "0000000000000000000000007761311ee56479da378519606cc4da58e17251ab",
    "0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3",
    "0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb",
    "00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5",
]
TX_GAS = [50000, 335000]
TX_VALUE = [0, 100]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CheckOpcodes5Filler.json"],
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
            4,
            0,
            0,
            id="d4-g0-v0",
        ),
        pytest.param(
            4,
            0,
            1,
            id="d4-g0-v1",
        ),
        pytest.param(
            4,
            1,
            0,
            id="d4-g1-v0",
        ),
        pytest.param(
            4,
            1,
            1,
            id="d4-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes5(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_check_opcodes5."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[1]] (CALL 250000 (CALLDATALOAD 0) 0 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        nonce=0,
        address=Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xb000000000000000000000000000000000000002>) (CALL 100000 <contract:0xa000000000000000000000000000000000000002> 0 0 32 0 0) }  # noqa: E501
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0xDF047446304BC9145D7BA20CD326E1097DA151FF
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
        + Op.STOP,
        nonce=0,
        address=Address("0x2c073c9d611d927ca91e4819bbb2dff859a8732b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xb000000000000000000000000000000000000002>) (CALL 100000 <contract:0xa000000000000000000000000000000000000002> 10 0 32 0 0) }  # noqa: E501
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0xDF047446304BC9145D7BA20CD326E1097DA151FF
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
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x7761311ee56479da378519606cc4da58e17251ab"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xc300000000000000000000000000000000000002>) (CALLCODE 100000 <contract:0xa000000000000000000000000000000000000002> 0 0 32 0 0) }  # noqa: E501
    addr_0x3000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x3F1AFEC0E6911FF45E18F4286F10DD905CD18F29
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
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x9c40928b20ac4236f0f3920567f28539c2e158b3"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xc400000000000000000000000000000000000002>) (CALLCODE 100000 <contract:0xa000000000000000000000000000000000000002> 1 0 32 0 0) }  # noqa: E501
    addr_0x4000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x19473707238EF04C4550E6EEE0D12BC0E3A7A02A
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
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x8a6781f0d54ed3cb8963ffc233e98041de8bdadb"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xc500000000000000000000000000000000000002>) (DELEGATECALL 100000 <contract:0xa000000000000000000000000000000000000002> 0 32 0 0) }  # noqa: E501
    addr_0x5000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x972F33115B9E8BE9C87412A04CE61E6C3A84D15D
        )
        + Op.DELEGATECALL(
            gas=0x186A0,
            address=0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x09fce828cbd5c5bdc742fe5a63776e2a76a111e5"),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (STATICCALL 50000 (CALLDATALOAD 0) 0 0 0 0) }
    addr_0xa000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        nonce=0,
        address=Address("0x8eeb303e1e7e2bb67d778526e009014a5daead81"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa000000000000000000000000000000000000002> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xb000000000000000000000000000000000000002> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xb000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x22,
            condition=Op.EQ(
                0xFAA10B404AB607779993C016CD5DA73AE1F29D7E, Op.ORIGIN
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
                0x8EEB303E1E7E2BB67D778526E009014A5DAEAD81, Op.CALLER
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
                0xDF047446304BC9145D7BA20CD326E1097DA151FF, Op.ADDRESS
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
        + Op.STOP,
        nonce=0,
        address=Address("0xdf047446304bc9145d7ba20cd326e1097da151ff"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x3000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xc300000000000000000000000000000000000002> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xc300000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x22,
            condition=Op.EQ(
                0xFAA10B404AB607779993C016CD5DA73AE1F29D7E, Op.ORIGIN
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
                0x9C40928B20AC4236F0F3920567F28539C2E158B3, Op.CALLER
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
                0x3F1AFEC0E6911FF45E18F4286F10DD905CD18F29, Op.ADDRESS
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
        + Op.STOP,
        nonce=0,
        address=Address("0x3f1afec0e6911ff45e18f4286f10dd905cd18f29"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x4000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xc400000000000000000000000000000000000002> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xc400000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x22,
            condition=Op.EQ(
                0xFAA10B404AB607779993C016CD5DA73AE1F29D7E, Op.ORIGIN
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
                0x8A6781F0D54ED3CB8963FFC233E98041DE8BDADB, Op.CALLER
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
                0x19473707238EF04C4550E6EEE0D12BC0E3A7A02A, Op.ADDRESS
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
        + Op.STOP,
        nonce=0,
        address=Address("0x19473707238ef04c4550e6eee0d12bc0e3a7a02a"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x5000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xc500000000000000000000000000000000000002> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xc500000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x22,
            condition=Op.EQ(
                0xFAA10B404AB607779993C016CD5DA73AE1F29D7E, Op.ORIGIN
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
                0x9FCE828CBD5C5BDC742FE5A63776E2A76A111E5, Op.CALLER
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
                0x972F33115B9E8BE9C87412A04CE61E6C3A84D15D, Op.ADDRESS
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
        + Op.STOP,
        nonce=0,
        address=Address("0x972f33115b9e8be9c87412a04ce61e6c3a84d15d"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_0xa000000000000000000000000000000000000002: Account(
                    storage={0: 0}
                ),
            },
        },
        {
            "indexes": {"data": [0, 1], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_0xa000000000000000000000000000000000000002: Account(
                    storage={0: 1}
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_0x3000000000000000000000000000000000000001: Account(
                    storage={0: 1}
                ),
            },
        },
        {
            "indexes": {"data": [3], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_0x4000000000000000000000000000000000000001: Account(
                    storage={0: 1}
                ),
            },
        },
        {
            "indexes": {"data": [4], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                addr_0x5000000000000000000000000000000000000001: Account(
                    storage={0: 1}
                ),
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
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
