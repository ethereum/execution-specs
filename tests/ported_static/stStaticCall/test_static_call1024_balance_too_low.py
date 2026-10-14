"""
Test_static_call1024_balance_too_low.

Ported from:
state_tests/stStaticCall/static_Call1024BalanceTooLowFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT
from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Call1024BalanceTooLowFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
def test_static_call1024_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call1024_balance_too_low."""
    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    addr = pre.fund_eoa(amount=7000)  # noqa: F841
    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
    )
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (STATICCALL 0xfffffffffff <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> @@0 0 0 0) }  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0xFFFFFFFFFFF,
                address=Op.ADDRESS,
                args_offset=Op.SLOAD(key=0x0),
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=1024,
    )
    # Source: lll
    # { (MSTORE 0 (ADD (MLOAD 0) 1)) (MSTORE 32 (STATICCALL 0xfffffffffff <contract:0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b> (MLOAD 0) 0 0 0)) }  # noqa: E501
    addr_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.MSTORE(
            offset=0x20,
            value=Op.STATICCALL(
                gas=0xFFFFFFFFFFF,
                address=Op.ADDRESS,
                args_offset=Op.MLOAD(offset=0x0),
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=1024,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                addr_2: Account(storage={0: 1, 1: 0}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                addr_3: Account(storage={0: 0, 1: 0}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [17592186099592]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
