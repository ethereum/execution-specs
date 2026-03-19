"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stInitCodeTest
OutOfGasPrefundedContractCreationFiller.json
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
    "600980601160003960006001f0500000fe621122336000550000",
    "600980601160003960006001f0500000fe621122336000550000",
    "600980601160003960006001f0500000fe621122336000550000",
]

TX_GAS = [154000, 65000, 95000]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
        pytest.param(2, 2, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_gas_prefunded_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    contract = Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[contract] = Account(balance=1, nonce=0)
    pre[sender] = Account(balance=0xF424000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": -1, "gas": [0, 1], "value": -1},
            "network": [">=Cancun"],
            "result": {contract: Account(balance=1), sender: Account(nonce=1)},
        },
        {
            "indexes": {"data": -1, "gas": [2], "value": -1},
            "network": [">=Cancun"],
            "result": {contract: Account(balance=2), sender: Account(nonce=1)},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
