"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransitionTest
createNameRegistratorPerTxsBeforeFiller.json
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
        "tests/static/state_tests/stTransitionTest/createNameRegistratorPerTxsBeforeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_name_registrator_per_txs_before(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
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

    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={1: 1},
                    nonce=1,
                    balance=0x186A0,
                    code=bytes.fromhex("396000f3006000355415600957005b60"),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "6001600155601080600c6000396000f3006000355415600957005b60203560003555"  # noqa: E501
        ),
        gas_limit=200000,
        value=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
