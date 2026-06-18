"""
Test_transaction_to_itself.

Ported from:
state_tests/stTransactionTest/TransactionToItselfFiller.json

@manually-enhanced: Do not overwrite. The post-state asserts the sender
balance after a self-transfer (to == sender). Instead of the original
hardcoded value, the balance shift is derived from the fork intrinsic
calculator: ``intrinsic(recipient_type=SELF, sends_value=True) - 21_000``
is the delta versus the pre-EIP-2780 baseline intrinsic 21_000. EIP-2780
carves out the recipient and value-transfer surcharges for self-sends,
dropping the intrinsic to ``TX_BASE`` (12_000 on Amsterdam), so the delta
is 0 at Cancun and negative afterward. The balance moves by
``gas_price * intrinsic_delta``. Do not hardcode the Amsterdam value.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    RecipientType,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/TransactionToItselfFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_to_itself(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_transaction_to_itself."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

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
        to=sender,
        data=Bytes(""),
        gas_limit=25000,
        value=1,
    )

    # EIP-2780 carves out self-transfers from the recipient and
    # value-transfer surcharges, leaving only ``TX_BASE`` (12_000 on
    # Amsterdam vs 21_000 on Cancun). Shift the sender balance by
    # ``gas_price * delta``.
    intrinsic_delta = (
        fork.transaction_intrinsic_cost_calculator()(
            recipient_type=RecipientType.SELF,
            sends_value=True,
        )
        - 21_000
    )
    post = {
        sender: Account(balance=0x3B9795B0 - 10 * intrinsic_delta, nonce=1)
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
