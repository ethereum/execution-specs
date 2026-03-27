"""
Test_static_check_opcodes2.

Ported from:
state_tests/stStaticCall/static_CheckOpcodes2Filler.json
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
    "0000000000000000000000004c9df443f25e673eac42a897aa8a234b84fb9bdd",
    "00000000000000000000000017217475f7d93fbfac2586ae993da598daead310",
    "0000000000000000000000007493ed4fd2e14f56f1f1e3022b7c3873789b2254",
    "000000000000000000000000419fea0f3da444f3e6ae0c045f83dfe2b25f161b",
    "000000000000000000000000991c2daacf958845c0a5e957b3e187238a093149",
]
TX_GAS = [335000]
TX_VALUE = [0, 100]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CheckOpcodes2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-v1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-v0",
        ),
        pytest.param(
            2,
            0,
            1,
            id="d2-v1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-v0",
        ),
        pytest.param(
            3,
            0,
            1,
            id="d3-v1",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4-v0",
        ),
        pytest.param(
            4,
            0,
            1,
            id="d4-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_check_opcodes2."""
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
    # { [[1]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=Op.CALLDATALOAD(offset=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (CALL 100000 <contract:0xa100000000000000000000000000000000000001> 0 0 0 0 0))  (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0x66FA14F32EB562EF2161C2890C73DFE43779F135,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPI(pc=0x38, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x3E)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x4c9df443f25e673eac42a897aa8a234b84fb9bdd"),  # noqa: E501
    )
    # Source: lll
    # {(MSTORE 0 0) (MSTORE 0 (CALL 100000 <contract:0xa200000000000000000000000000000000000001> 1 0 0 0 0)) (MSTORE 1 1) (MSTORE 2 1) }  # noqa: E501
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0xEF6A70E5546CA5339758B2F3B819780625C233C3,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.MSTORE(offset=0x2, value=0x1)
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x17217475f7d93fbfac2586ae993da598daead310"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (CALLCODE 100000 <contract:0xa300000000000000000000000000000000000001> 0 0 0 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2)) }  # noqa: E501
    addr_0x3000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=0x7EA8B3E1880535D9ECF543C5AF8637DE220CD5FE,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPI(pc=0x38, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x3E)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x7493ed4fd2e14f56f1f1e3022b7c3873789b2254"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (CALLCODE 100000 <contract:0xa400000000000000000000000000000000000001> 1 0 0 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2)) }  # noqa: E501
    addr_0x4000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=0xE1FC3E8FA3DEC60CC7FE8E5CF1A3BF2E23B8380,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPI(pc=0x38, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x3E)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x419fea0f3da444f3e6ae0c045f83dfe2b25f161b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (DELEGATECALL 100000 <contract:0xa500000000000000000000000000000000000001> 0 0 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2)) }  # noqa: E501
    addr_0x5000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=Op.DELEGATECALL(
                gas=0x186A0,
                address=0x58D6159788915466CC2BF8A6BC7284928707959B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPI(pc=0x36, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x3C)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x991c2daacf958845c0a5e957b3e187238a093149"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa100000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xa100000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
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
                0x4C9DF443F25E673EAC42A897AA8A234B84FB9BDD, Op.CALLER
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
                0x66FA14F32EB562EF2161C2890C73DFE43779F135, Op.ADDRESS
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
        address=Address("0x66fa14f32eb562ef2161c2890c73dfe43779f135"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x2000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa200000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 1 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xa200000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
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
                0x17217475F7D93FBFAC2586AE993DA598DAEAD310, Op.CALLER
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
                0xEF6A70E5546CA5339758B2F3B819780625C233C3, Op.ADDRESS
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x7A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x1, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x90)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address("0xef6a70e5546ca5339758b2f3b819780625c233c3"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x3000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x3000000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xa300000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
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
                0x7493ED4FD2E14F56F1F1E3022B7C3873789B2254, Op.CALLER
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
                0x7493ED4FD2E14F56F1F1E3022B7C3873789B2254, Op.ADDRESS
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
        address=Address("0x7ea8b3e1880535d9ecf543c5af8637de220cd5fe"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x4000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x4000000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 1 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xa400000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
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
                0x419FEA0F3DA444F3E6AE0C045F83DFE2B25F161B, Op.CALLER
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
                0x419FEA0F3DA444F3E6AE0C045F83DFE2B25F161B, Op.ADDRESS
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x7A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x1, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x90)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address("0x0e1fc3e8fa3dec60cc7fe8e5cf1a3bf2e23b8380"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:target:0x1000000000000000000000000000000000000000> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x5000000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_0xa500000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
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
                0x50F628D871A69F2DB31E98D7FBF8AE6F1FC0D55C, Op.CALLER
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
                0x991C2DAACF958845C0A5E957B3E187238A093149, Op.ADDRESS
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
        address=Address("0x58d6159788915466cc2bf8a6bc7284928707959b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 2, 3, 4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={1: 0}),
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
