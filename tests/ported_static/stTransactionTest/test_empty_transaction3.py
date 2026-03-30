"""
Test_empty_transaction3.

Ported from:
state_tests/stTransactionTest/EmptyTransaction3Filler.json
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
    ["state_tests/stTransactionTest/EmptyTransaction3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_empty_transaction3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_empty_transaction3."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Bytes(""),
        gas_limit=55000,
    )

    post = {
        Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
            code=b""
        ),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
