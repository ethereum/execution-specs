"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest/TransactionDataCosts652Filler.json
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
    [
        "tests/static/state_tests/stTransactionTest/TransactionDataCosts652Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        22000,
        72000,
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_data_costs652(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xDC4EFA209AECDD4C2D5201A419EA27506151B4EC687F14A613229E310932491B
    )
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x989680)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00000000000000000000112233445566778f32"),
        gas_limit=tx_gas_limit,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stTransactionTest/TransactionDataCosts652Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        22000,
        72000,
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_data_costs652_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xDC4EFA209AECDD4C2D5201A419EA27506151B4EC687F14A613229E310932491B
    )
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x989680)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00000000000000000000112233445566778f32"),
        gas_limit=tx_gas_limit,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
