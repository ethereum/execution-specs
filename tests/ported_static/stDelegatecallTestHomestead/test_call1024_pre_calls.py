"""
Test_call1024_pre_calls.

Ported from:
state_tests/stDelegatecallTestHomestead/Call1024PreCallsFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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


@pytest.mark.ported_from(
    ["state_tests/stDelegatecallTestHomestead/Call1024PreCallsFiller.json"],
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
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
        pytest.param(
            0,
            2,
            0,
            id="-g2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_call1024_pre_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_call1024_pre_calls."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    addr = Address(0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0)
    sender = EOA(
        key=0xCC381C83857B17CA629268ED418E2915A0287B84EFE9CF2204C020302E83CDA0
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre[addr] = Account(balance=7000)
    # Source: lll
    # { [[ 2 ]] (CALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) [[ 3 ]] (CALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0)  [[ 0 ]] (ADD @@0 1) [[ 1 ]] (DELEGATECALL 0xfffffffffff <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0xFFFF,
                address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x3,
            value=Op.CALL(
                gas=0xFFFF,
                address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=0xFFFFFFFFFFF,
                address=0x515E9A6500C10F0DB92754D10136694BB188153B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=2024,
        nonce=0,
        address=Address(0x515E9A6500C10F0DB92754D10136694BB188153B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={0: 1025, 1: 1, 2: 0, 3: 0})},
        },
        {
            "indexes": {"data": -1, "gas": 2, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={0: 989, 1: 1, 2: 1, 3: 1})},
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {target: Account(storage={0: 1025, 1: 1, 2: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [11937600034817, 9214364837600034817, 9381323795670]
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
