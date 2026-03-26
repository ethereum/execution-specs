"""
DIV/SDIV/MOD/SMOD by zero tests

Ported from:
state_tests/stSolidityTest/ByZeroFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "600160006001045500",
    "600160006001055500",
    "600160006001065500",
    "600160006001075500",
]
TX_GAS = [400000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stSolidityTest/ByZeroFiller.json"],
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
def test_by_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """DIV/SDIV/MOD/SMOD by zero tests"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x8ac7230489e80000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(storage={0: 1}, code=b"", balance=0),  # noqa: E501
        sender: Account(storage={}, code=b"", nonce=1),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
