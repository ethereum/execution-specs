"""
Trigger transaction creating gasPrice in the state.

Ported from:
state_tests/stHomesteadSpecific/createContractViaTransactionCost53000Filler.json

@manually-enhanced: Do not overwrite. `tx.gas_limit` was raised from
100 000 to 500 000 (and sender funding bumped accordingly) so the
contract-creation tx clears the EIP-8037 intrinsic-gas floor on
Amsterdam. The test only asserts that the tx ran (sender.nonce == 1);
the higher gas budget doesn't change that post-state on any fork.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork

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
    fork: Fork,
) -> None:
    """Trigger transaction creating gasPrice in the state."""
    # On EIP-8037 the contract-creation tx needs more gas to clear the
    # intrinsic floor, and the sender therefore needs more balance to
    # afford the upfront cost. Pre-EIP-8037 keeps the original values.
    tx_gas_limit = 100000
    sender_amount = 0xF4240
    if fork.is_eip_enabled(8037):
        tx_gas_limit = 500000
        sender_amount = 0x4C4B40
    sender = pre.fund_eoa(amount=sender_amount)

    tx = Transaction(
        sender=sender,
        to=None,
        gas_limit=tx_gas_limit,
    )

    post = {sender: Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
