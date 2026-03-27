"""
Test_zero_value_transaction_call.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_TransactionCALLFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stZeroCallsTest/ZeroValue_TransactionCALLFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_transaction_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_zero_value_transaction_call."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),
        data=b"",
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address(
            "0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"
        ): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
