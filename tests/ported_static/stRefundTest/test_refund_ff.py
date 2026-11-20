"""
Verify the SELFDESTRUCT refund: capped before EIP-3529, removed from it on.

Ported from:
state_tests/stRefundTest/refundFFFiller.yml

@manually-enhanced: Do not overwrite. The gas used is derived from the
fork: intrinsic cost plus the SELFDESTRUCT to a cold absent beneficiary,
minus its refund (capped at `max_refund_quotient`, zero from EIP-3529).
The filler's calldata, access list, gas price and gas limit are dropped.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    GasFee,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refundFFFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
def test_refund_ff(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Self-destruct a zero-balance contract and check the refund."""
    sender = pre.fund_eoa()

    # The beneficiary does not exist. With no balance moved, only the
    # pre-EIP-161 forks charge for creating it; from EIP-6780 on, the
    # pre-existing contract is no longer destroyed.
    beneficiary = pre.fund_eoa(amount=0)
    code = Op.SELFDESTRUCT(
        address=beneficiary,
        address_warm=False,
        account_new=not fork.is_eip_enabled(161),
        self_destructed_account=not fork.is_eip_enabled(6780),
    )
    target = pre.deploy_contract(code=code)

    tx = Transaction(
        sender=sender,
        to=target,
        protected=fork.supports_protected_txs(),
    )

    gas_before_refund = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    ) + code.gas_cost(fork)
    refund = min(
        code.refund(fork), gas_before_refund // fork.max_refund_quotient()
    )
    gas_used = gas_before_refund - refund

    post = {sender: Account(balance_change=-GasFee(tx, gas=gas_used))}

    state_test(pre=pre, post=post, tx=tx)
