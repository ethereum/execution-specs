"""
An example how to use ranges in expect section.

Ported from:
state_tests/stExample/rangesExampleFiller.yml
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
    ["state_tests/stExample/rangesExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="transaction1-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="transaction1-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="transaction1-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="transaction1-g1-v1",
        ),
        pytest.param(
            0,
            2,
            0,
            id="transaction1-g2-v0",
        ),
        pytest.param(
            0,
            2,
            1,
            id="transaction1-g2-v1",
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
            1,
            2,
            0,
            id="d1-g2-v0",
        ),
        pytest.param(
            1,
            2,
            1,
            id="d1-g2-v1",
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
            2,
            2,
            0,
            id="d2-g2-v0",
        ),
        pytest.param(
            2,
            2,
            1,
            id="d2-g2-v1",
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
            3,
            2,
            0,
            id="d3-g2-v0",
        ),
        pytest.param(
            3,
            2,
            1,
            id="d3-g2-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_ranges_example(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """An example how to use ranges in expect section."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # {
    #    [[0]] (CALLDATALOAD 0)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA054BC58F204030CBC0EC558A5B88AC9BD5ADED2),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1, 2], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [0, 1, 2], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": [0, 1, 2], "value": [0, 1]},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x400000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("01"),
        Bytes("01"),
        Bytes("01"),
        Bytes("04"),
    ]
    tx_gas = [400000, 1400000, 2400000]
    tx_value = [100000, 200000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
