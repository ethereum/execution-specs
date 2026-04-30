"""
Fuzzed input discovered by Guido.

Ported from:
state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


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
def test_modexp_random_input(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Fuzzed input discovered by Guido."""
    coinbase = Address(0x3535353535353535353535353535353535353535)
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    tx_data = [
        Bytes(
            "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000"  # noqa: E501
        ),
        Bytes(
            "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a"  # noqa: E501
        ),
        Hash(0x0) + Hash(0x11470) + Hash(0x6166035) + Hash(0x8),
    ]
    tx_gas = [710000, 7000000]

    tx = Transaction(
        sender=sender,
        to=Address(0x0000000000000000000000000000000000000005),
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
