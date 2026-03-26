"""
test_static_check_opcodes3

Ported from:
state_tests/stStaticCall/static_CheckOpcodes3Filler.json
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
    "000000000000000000000000f697c2d8963df21523b18e96caaf6c7703a1882e",
    "0000000000000000000000009b68a6b37af295c7fd23aa2269db8c875c2b86b4",
    "000000000000000000000000ba044a82b25080bc96678b9fa77678e014605c48",
    "000000000000000000000000e541572ce4b4ccbb2b92aab0fb852f018d51c512",
    "0000000000000000000000008113f9fc0868700534ecbecf1120a812cb1af0ac",
]
TX_GAS = [335000]
TX_VALUE = [0, 100]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CheckOpcodes3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0-v0",
        ),
        pytest.param(
            0, 0, 1,
            id="d0-v1",
        ),
        pytest.param(
            1, 0, 0,
            id="d1-v0",
        ),
        pytest.param(
            1, 0, 1,
            id="d1-v1",
        ),
        pytest.param(
            2, 0, 0,
            id="d2-v0",
        ),
        pytest.param(
            2, 0, 1,
            id="d2-v1",
        ),
        pytest.param(
            3, 0, 0,
            id="d3-v0",
        ),
        pytest.param(
            3, 0, 1,
            id="d3-v1",
        ),
        pytest.param(
            4, 0, 0,
            id="d4-v0",
        ),
        pytest.param(
            4, 0, 1,
            id="d4-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_check_opcodes3"""
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
    # { [[1]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x186a0, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xa100000000000000000000000000000000000001>) (MSTORE 0 (CALL 100000 <contract:0xb000000000000000000000000000000000000001> 0 0 32 0 0))  (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xa131950507c8977b0de1790c8e76a1a28dd92805)
        + Op.MSTORE(offset=0x0, value=Op.CALL(gas=0x186a0, address=0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x50, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x56) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0xf697c2d8963df21523b18e96caaf6c7703a1882e"),  # noqa: E501
    )
    # Source: lll
    # {(MSTORE 0 <contract:0xa100000000000000000000000000000000000001>) (MSTORE 0 (CALL 100000 <contract:0xb000000000000000000000000000000000000001> 1 0 32 0 0)) (MSTORE 1 1) (MSTORE 2 1) }
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xa131950507c8977b0de1790c8e76a1a28dd92805)
        + Op.MSTORE(offset=0x0, value=Op.CALL(gas=0x186a0, address=0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35, value=0x1, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x0))
        + Op.MSTORE(offset=0x1, value=0x1) + Op.MSTORE(offset=0x2, value=0x1)
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x9b68a6b37af295c7fd23aa2269db8c875c2b86b4"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 32 <contract:0xa300000000000000000000000000000000000001>) (MSTORE 0 (CALLCODE 100000 <contract:0xb000000000000000000000000000000000000001> 0 32 64 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2)) }
    addr_0x3000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x20, value=0xb93cf5121157d61ab42345f5a5e9815b19cec2cc)
        + Op.MSTORE(offset=0x0, value=Op.CALLCODE(gas=0x186a0, address=0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35, value=0x0, args_offset=0x20, args_size=0x40, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x50, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x56) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0xba044a82b25080bc96678b9fa77678e014605c48"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xa400000000000000000000000000000000000001>) (MSTORE 0 (CALLCODE 100000 <contract:0xb000000000000000000000000000000000000001> 1 0 32 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2)) }
    addr_0x4000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6d797b6a2c5f22885c4068990f19ae845d698a79)
        + Op.MSTORE(offset=0x0, value=Op.CALLCODE(gas=0x186a0, address=0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35, value=0x1, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x50, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x56) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0xe541572ce4b4ccbb2b92aab0fb852f018d51c512"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 <contract:0xa500000000000000000000000000000000000001>) (MSTORE 0 (DELEGATECALL 100000 <contract:0xb000000000000000000000000000000000000001> 0 32 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2)) }
    addr_0x5000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9)
        + Op.MSTORE(offset=0x0, value=Op.DELEGATECALL(gas=0x186a0, address=0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x4e, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x54) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x8113f9fc0868700534ecbecf1120a812cb1af0ac"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 2)) }
    addr_0xb000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.STATICCALL(gas=0x186a0, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x24, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x2a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xb000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa100000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0xa100000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xfaa10b404ab607779993c016cd5da73ae1f29d7e, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0xa131950507c8977b0de1790c8e76a1a28dd92805, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0xa131950507c8977b0de1790c8e76a1a28dd92805"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x2000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa200000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 1 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0xa200000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xfaa10b404ab607779993c016cd5da73ae1f29d7e, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0x9b68a6b37af295c7fd23aa2269db8c875c2b86b4, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0xef6a70e5546ca5339758b2f3b819780625c233c3, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x1, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0xef6a70e5546ca5339758b2f3b819780625c233c3"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x3000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa300000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0xa300000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xfaa10b404ab607779993c016cd5da73ae1f29d7e, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0xba044a82b25080bc96678b9fa77678e014605c48, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0xb93cf5121157d61ab42345f5a5e9815b19cec2cc, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0xb93cf5121157d61ab42345f5a5e9815b19cec2cc"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x4000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa400000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0xa400000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xfaa10b404ab607779993c016cd5da73ae1f29d7e, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0xe541572ce4b4ccbb2b92aab0fb852f018d51c512, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0x6d797b6a2c5f22885c4068990f19ae845d698a79, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0x6d797b6a2c5f22885c4068990f19ae845d698a79"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x5000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0xa500000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0xa500000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xfaa10b404ab607779993c016cd5da73ae1f29d7e, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0x8113f9fc0868700534ecbecf1120a812cb1af0ac, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 2, 3, 4], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        target: Account(storage={1: 1}),
    },
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
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
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
