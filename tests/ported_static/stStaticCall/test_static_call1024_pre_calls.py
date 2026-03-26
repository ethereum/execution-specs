"""
test_static_call1024_pre_calls

Ported from:
state_tests/stStaticCall/static_Call1024PreCallsFiller.json
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
    "0000000000000000000000002806e7553f3585d821f91d679a254abbf002f6f2",
    "0000000000000000000000007c546b69d5bda111c03c8d7b51b41a8d55b843ca",
]
TX_GAS = [9214364837600034817]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Call1024PreCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call1024_pre_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call1024_pre_calls"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")  # noqa: E501
    sender = EOA(
        key=0xcc381c83857b17ca629268ed418e2915a0287b84efe9cf2204c020302e83cda0
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xfffffffffffffffffffffffffffffffff)
    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    pre[addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=7000)
    # Source: lll
    # { [[ 2 ]] (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[ 3 ]] (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0)  [[ 0 ]] (ADD @@0 1) [[ 1 ]] (STATICCALL 0xfffffffffff <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }
    addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.STATICCALL(gas=0xffff, address=0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x3, value=Op.STATICCALL(gas=0xffff, address=0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0xfffffffffff, address=0x2806e7553f3585d821f91d679a254abbf002f6f2, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=2024,
        nonce=0,
        address=Address("0x2806e7553f3585d821f91d679a254abbf002f6f2"),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0)  (MSTORE 0 (ADD (MLOAD 0) 1)) (STATICCALL 0xfffffffffff <contract:0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }
    addr_0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0xffff, address=0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)) * 2
        + Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.STATICCALL(gas=0xfffffffffff, address=0x7c546b69d5bda111c03c8d7b51b41a8d55b843ca, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=2024,
        nonce=0,
        address=Address("0x7c546b69d5bda111c03c8d7b51b41a8d55b843ca"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 1, 1: 0, 2: 1, 3: 1}),
        target: Account(storage={0: 1, 1: 1}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        addr_0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 0, 1: 0, 2: 0, 3: 0}),
        target: Account(storage={0: 1, 1: 1}),
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
