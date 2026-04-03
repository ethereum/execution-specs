"""
Test_overflow_gas_require2.

Ported from:
state_tests/stTransactionTest/OverflowGasRequire2Filler.json
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
    resolve_expect_post_fork,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/OverflowGasRequire2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_overflow_gas_require2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_overflow_gas_require2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x50EADFB1030587AB3A993A6ECC073041FC3B45E119DAA31A13D78C7E209631A5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "network": ["Cancun"],
            "result": {
                sender: Account(
                    balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE6357F,  # noqa: E501
                    nonce=1,
                ),
            },
        },
        {
            "network": ["Prague"],
            "result": {
                sender: Account(
                    balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE5F97F,  # noqa: E501
                    nonce=1,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post_fork(expect_entries_, fork)

    tx = Transaction(
        sender=sender,
        to=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        data=Bytes("3240349548983454"),
        gas_limit=1152921504606846976,
        gas_price=80,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
