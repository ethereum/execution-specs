"""
test_static_call_basic

Ported from:
state_tests/stStaticCall/static_callBasicFiller.json
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
    "000000000000000000000000d3c0847ca0222f22dcfb4a433a378ff58ad6a881",
    "000000000000000000000000ead198f480fb91a5fbedcf5eb28cd369ee4c6cf2",
    "000000000000000000000000eb015f637a39c63f8b6db67505f5c02c613defc1",
    "000000000000000000000000d5b64fa2ca1e471b45b639a5e9c259ca24c28ace",
]
TX_GAS = [1000000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callBasicFiller.json"],
)
@pytest.mark.valid_from("Cancun")
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
        pytest.param(
            2, 0, 0,
            id="d2",
        ),
        pytest.param(
            3, 0, 0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_basic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call_basic"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
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

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x186a0, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x13670d6bd41acd42d75e7c4c25df7384a6fbd752"),  # noqa: E501
    )
    # Source: lll
    # { [[ 1 ]] 1 }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={1: 1},
        balance=23,
        nonce=0,
        address=Address("0xd3c0847ca0222f22dcfb4a433a378ff58ad6a881"),  # noqa: E501
    )
    # Source: lll
    # { [[ 1 ]] 0 }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 0},
        balance=23,
        nonce=0,
        address=Address("0xead198f480fb91a5fbedcf5eb28cd369ee4c6cf2"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 40000 <contract:0x2000000000000000000000000000000000000003> 0 0 0 0 0) (MSTORE 1 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x9c40, address=0x2e0dd8abe4e68c5b602f3c65051f4b30c6d018da, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0xeb015f637a39c63f8b6db67505f5c02c613defc1"),  # noqa: E501
    )
    # Source: lll
    # { (LOG0 1 10) (MSTORE 1 1) }
    addr_0x2000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.LOG0(offset=0x1, size=0xa) + Op.MSTORE(offset=0x1, value=0x1)
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0x2e0dd8abe4e68c5b602f3c65051f4b30c6d018da"),  # noqa: E501
    )
    # Source: lll
    # { (CALLCODE 40000 <contract:0x3000000000000000000000000000000000000003> 1 0 0 0 0) (MSTORE 1 1) }
    addr_0x1000000000000000000000000000000000000004 = pre.deploy_contract(
        code=Op.POP(Op.CALLCODE(gas=0x9c40, address=0xc93c7a588b13699e562b3933e8f2b1c15e610781, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0xd5b64fa2ca1e471b45b639a5e9c259ca24c28ace"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) }
    addr_0x3000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0xc93c7a588b13699e562b3933e8f2b1c15e610781"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 0, 1: 1})},
        },
        {
            "indexes": {'data': [2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 1, 1: 1})},
        },
        {
            "indexes": {'data': [3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x3000000000000000000000000000000000000003: Account(balance=23),
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
