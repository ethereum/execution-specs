"""
Apparently this test was testing theoretical issue occur when tr gas >...

Ported from:
tests/static/state_tests/stSpecialTest/OverflowGasMakeMoneyFiller.json
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
    ["tests/static/state_tests/stSpecialTest/OverflowGasMakeMoneyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_overflow_gas_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Apparently this test was testing theoretical issue occur when tr..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4C30106C229CD77A61E9EAB5FCEE11CC912BF94F785EE56F406817744BB6A074
    )
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0x4FEC000000000139C)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        value=501,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
