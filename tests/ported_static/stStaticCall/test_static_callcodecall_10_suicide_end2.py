"""
Test_static_callcodecall_10_suicide_end2.

Ported from:
state_tests/stStaticCall/static_callcodecall_10_SuicideEnd2Filler.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stStaticCall/static_callcodecall_10_SuicideEnd2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecall_10_suicide_end2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcodecall_10_suicide_end2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  (MSTORE 2 1) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x2, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xCFB5784A5E49924BECC2D5C5D2EE0A9B141E6216),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 ) [[ 1 ]] (GAS) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x249F0,
                address=0xB60789F240AC9F12FCDE1E4BBD5042A7F30932D4,
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x44D09DDF088DD88C0E91FA7EF74973FF94AD7414),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 50000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0xCFB5784A5E49924BECC2D5C5D2EE0A9B141E6216,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SELFDESTRUCT(address=0x44D09DDF088DD88C0E91FA7EF74973FF94AD7414)
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xB60789F240AC9F12FCDE1E4BBD5042A7F30932D4),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": 0},
            "network": [">=Cancun"],
            "result": {target: Account(balance=0xDE0B6B3A7640000)},
        },
        {
            "indexes": {"data": -1, "gas": -1, "value": 1},
            "network": [">=Cancun"],
            "result": {target: Account(balance=0xDE0B6B3A7640001)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [3000000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
