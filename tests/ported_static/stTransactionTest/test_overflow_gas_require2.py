"""
Send a transaction with a 2**60 gas limit in a 2**63 - 1 gas block.

Ported from:
state_tests/stTransactionTest/OverflowGasRequire2Filler.json

@manually-enhanced: Do not overwrite. The fee is derived from the
intrinsic gas; from Osaka on the gas limit cap rejects the transaction.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    GasFee,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.forks import Fork

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


GAS_LIMIT = 2**60
BLOCK_ENV = Environment(gas_limit=2**63 - 1)


def overflow_tx(pre: Alloc, error: TransactionException | None) -> Transaction:
    """Return the 2**60 gas transaction from a maximally funded sender."""
    return Transaction(
        sender=pre.fund_eoa(amount=2**256 - 1),
        to=pre.nonexistent_account(),
        data=Bytes("3240349548983454"),
        gas_limit=GAS_LIMIT,
        gas_price=80,
        error=error,
    )


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/OverflowGasRequire2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_overflow_gas_require2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Charge only the intrinsic gas of the 2**60 gas transaction."""
    tx = overflow_tx(pre, error=None)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(calldata=tx.data)
    post = {
        tx.sender: Account(nonce=1, balance_change=-GasFee(tx, gas=intrinsic))
    }
    state_test(env=BLOCK_ENV, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/OverflowGasRequire2Filler.json"],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.exception_test
def test_overflow_gas_require2_over_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Reject the 2**60 gas transaction over the gas limit cap."""
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None and GAS_LIMIT > cap
    tx = overflow_tx(pre, error=TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM)
    post = {tx.sender: Account(nonce=0, balance_change=0)}
    state_test(env=BLOCK_ENV, pre=pre, post=post, tx=tx)
