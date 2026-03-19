"""
stack underflow in init code.

Ported from:
tests/static/state_tests/stInitCodeTest
TransactionCreateRandomInitCodeFiller.json
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


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stInitCodeTest/TransactionCreateRandomInitCodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction_create_random_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Stack underflow in init code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0x2540BE400)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("600a80600c6000396000f200600160008035811a8100"),
        gas_limit=64599,
        value=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
