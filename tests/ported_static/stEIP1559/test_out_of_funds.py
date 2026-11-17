"""
Reject a transaction the sender cannot pay for.

Ported from:
state_tests/stEIP1559/outOfFundsFiller.yml
state_tests/stEIP1559/outOfFundsOldTypesFiller.yml

@manually-enhanced: Do not overwrite. Merged over the transaction type.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENDER_BALANCE = 10**18
GAS_PRICE = 10**11
HIGH_GAS_LIMIT = 2**24
LOW_GAS_LIMIT = 40_000


@pytest.mark.ported_from(
    [
        "state_tests/stEIP1559/outOfFundsFiller.yml",
        "state_tests/stEIP1559/outOfFundsOldTypesFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("tx_type", [0, 1, 2])
@pytest.mark.parametrize(
    "gas_limit, value",
    [
        pytest.param(
            HIGH_GAS_LIMIT, 0, id="high_gas", marks=pytest.mark.exception_test
        ),
        pytest.param(
            HIGH_GAS_LIMIT,
            SENDER_BALANCE,
            id="high_gas_with_value",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(LOW_GAS_LIMIT, 0, id="low_gas"),
        pytest.param(
            LOW_GAS_LIMIT,
            SENDER_BALANCE,
            id="low_gas_with_value",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_out_of_funds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    gas_limit: int,
    value: int,
) -> None:
    """Send a transaction whose gas and value may exceed the balance."""
    sender = pre.fund_eoa(amount=SENDER_BALANCE)
    target = pre.deploy_contract(code=Op.SSTORE(0, 2) + Op.STOP)

    affordable = gas_limit * GAS_PRICE + value <= SENDER_BALANCE
    fees = (
        {"max_fee_per_gas": GAS_PRICE, "max_priority_fee_per_gas": GAS_PRICE}
        if tx_type == 2
        else {"gas_price": GAS_PRICE}
    )
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=target,
        gas_limit=gas_limit,
        value=value,
        error=(
            None
            if affordable
            else TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
        ),
        **fees,
    )

    post = {sender: Account(nonce=1 if affordable else 0)}
    state_test(pre=pre, post=post, tx=tx)
