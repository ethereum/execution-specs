"""
Verify a transaction into a self-destructing contract: the balance
(including the transaction value) moves to the beneficiary and, post
EIP-3529, no self-destruct refund is granted.

Ported from:
state_tests/stRefundTest/refund_TxToSuicideFiller.json

@manually-enhanced: Do not overwrite. Beneficiary and budget are derived
(nonexistent account, `code.gas_cost` composite) and the post branches on
EIP-6780 (pre-Cancun the contract is deleted, after it persists).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 0xDE0B6B3A7640000
INITIAL_BALANCE = 10**18
GAS_PRICE = 10
TX_VALUE = 10


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_TxToSuicideFiller.json"],
)
@pytest.mark.valid_from("London")
def test_refund_tx_to_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Self-destruct moves the balance and grants no refund."""
    beneficiary = pre.nonexistent_account()
    code = Op.SELFDESTRUCT(
        address=beneficiary, address_warm=False, account_new=True
    )
    target = pre.deploy_contract(
        code=code,
        storage={1: 1},
        balance=CONTRACT_BALANCE,
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()(sends_value=True)
    executed = intrinsic + code.gas_cost(fork)
    gas_limit = executed + 5_000

    sender = pre.fund_eoa(amount=INITIAL_BALANCE)
    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=gas_limit,
        gas_price=GAS_PRICE,
        value=TX_VALUE,
    )

    # EIP-3529 removed the self-destruct refund entirely.
    refund = min(code.refund(fork), executed // 5)
    gas_used = executed - refund

    post = {
        beneficiary: Account(balance=CONTRACT_BALANCE + TX_VALUE),
        # EIP-6780: a pre-existing contract is no longer deleted, only
        # its balance is transferred.
        target: (
            Account(storage={1: 1}, balance=0)
            if fork.is_eip_enabled(6780)
            else Account.NONEXISTENT
        ),
        sender: Account(
            balance=INITIAL_BALANCE - TX_VALUE - gas_used * GAS_PRICE
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
