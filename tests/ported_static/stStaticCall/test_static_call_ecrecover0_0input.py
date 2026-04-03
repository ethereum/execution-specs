"""
Test_static_call_ecrecover0_0input.

Ported from:
state_tests/stStaticCall/static_CallEcrecover0_0inputFiller.json
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
    ["state_tests/stStaticCall/static_CallEcrecover0_0inputFiller.json"],
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
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_ecrecover0_0input(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call_ecrecover0_0input."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { [[ 2 ]] (STATICCALL 300000 (CALLDATALOAD 0) 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.STATICCALL(
                gas=0x493E0,
                address=Op.CALLDATALOAD(offset=0x0),
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x80,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(
            key=0x0, value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xA0))
        )
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0x1FD04A51AC69C94C58521D30E2DEFC4856A581B0),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 8, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={2: 0})},
        },
        {
            "indexes": {"data": [0, 1, 4, 5, 6, 7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={2: 1})},
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x8209944E898F69A7BD10A23C839D341E935FD5CA,
                        2: 1,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x4300A157335CB7C9FC9423E011D7DD51090D093F,
                        2: 1,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x0),
        Hash(0x1),
        Hash(0x2),
        Hash(0x3),
        Hash(0x4),
        Hash(0x5),
        Hash(0x6),
        Hash(0x7),
        Hash(0x8),
    ]
    tx_gas = [3652240]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
