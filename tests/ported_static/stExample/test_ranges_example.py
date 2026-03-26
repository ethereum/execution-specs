"""
An example how to use ranges in expect section

Ported from:
state_tests/stExample/rangesExampleFiller.yml
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
    "01",
    "01",
    "01",
    "04",
]
TX_GAS = [400000, 1400000, 2400000]
TX_VALUE = [100000, 200000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stExample/rangesExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="transaction1-g0-v0",
        ),
        pytest.param(
            0, 0, 1,
            id="transaction1-g0-v1",
        ),
        pytest.param(
            0, 1, 0,
            id="transaction1-g1-v0",
        ),
        pytest.param(
            0, 1, 1,
            id="transaction1-g1-v1",
        ),
        pytest.param(
            0, 2, 0,
            id="transaction1-g2-v0",
        ),
        pytest.param(
            0, 2, 1,
            id="transaction1-g2-v1",
        ),
        pytest.param(
            1, 0, 0,
            id="d1-g0-v0",
        ),
        pytest.param(
            1, 0, 1,
            id="d1-g0-v1",
        ),
        pytest.param(
            1, 1, 0,
            id="d1-g1-v0",
        ),
        pytest.param(
            1, 1, 1,
            id="d1-g1-v1",
        ),
        pytest.param(
            1, 2, 0,
            id="d1-g2-v0",
        ),
        pytest.param(
            1, 2, 1,
            id="d1-g2-v1",
        ),
        pytest.param(
            2, 0, 0,
            id="d2-g0-v0",
        ),
        pytest.param(
            2, 0, 1,
            id="d2-g0-v1",
        ),
        pytest.param(
            2, 1, 0,
            id="d2-g1-v0",
        ),
        pytest.param(
            2, 1, 1,
            id="d2-g1-v1",
        ),
        pytest.param(
            2, 2, 0,
            id="d2-g2-v0",
        ),
        pytest.param(
            2, 2, 1,
            id="d2-g2-v1",
        ),
        pytest.param(
            3, 0, 0,
            id="d3-g0-v0",
        ),
        pytest.param(
            3, 0, 1,
            id="d3-g0-v1",
        ),
        pytest.param(
            3, 1, 0,
            id="d3-g1-v0",
        ),
        pytest.param(
            3, 1, 1,
            id="d3-g1-v1",
        ),
        pytest.param(
            3, 2, 0,
            id="d3-g2-v0",
        ),
        pytest.param(
            3, 2, 1,
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
    """An example how to use ranges in expect section"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: lll
    # {
    #    [[0]] (CALLDATALOAD 0) 
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1, 2], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0x100000000000000000000000000000000000000000000000000000000000000,
        },
            ),
    },
        },
        {
            "indexes": {'data': [0, 1, 2], 'gas': [1, 2], 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0x100000000000000000000000000000000000000000000000000000000000000,
        },
            ),
    },
        },
        {
            "indexes": {'data': 3, 'gas': [0, 1, 2], 'value': [0, 1]},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0x400000000000000000000000000000000000000000000000000000000000000,
        },
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
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
