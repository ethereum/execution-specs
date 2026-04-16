"""
Test_high_gas_limit.

Ported from:
state_tests/stTransactionTest/HighGasLimitFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/HighGasLimitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_high_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_high_gas_limit."""
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

    tx = Transaction(
        sender=sender,
        to=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        data=Bytes("3240349548983454"),
        gas_limit=100000,
        value=900,
    )

    post = {
        sender: Account(nonce=1),
        Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B): Account(
            balance=900
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
