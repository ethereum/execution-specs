"""
Trigger transaction creating gasPrice in the state.

Ported from:
state_tests/stHomesteadSpecific/createContractViaTransactionCost53000Filler.json
"""

import pytest
from execution_testing import (
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
    [
        "state_tests/stHomesteadSpecific/createContractViaTransactionCost53000Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_contract_via_transaction_cost53000(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Trigger transaction creating gasPrice in the state."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xF4240)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
