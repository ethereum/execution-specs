"""
Fuzzed input discovered by Guido.

Ported from:
state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json
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
    "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000",  # noqa: E501
    "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
]
TX_GAS = [710000, 7000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_random_input(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Fuzzed input discovered by Guido."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=Address("0x0000000000000000000000000000000000000005"),
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
