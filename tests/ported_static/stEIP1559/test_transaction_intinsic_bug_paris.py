"""
Bug discovered on ropsten https://github.com/ethereum/go-ethereum/pull/2...

Ported from:
state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml
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
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_transaction_intinsic_bug_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Bug discovered on ropsten https://github."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x2FAF094, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=20,
        gas_limit=71794957647893862,
    )

    addr = pre.fund_eoa(amount=10)  # noqa: F841

    tx = Transaction(
        sender=sender,
        to=addr,
        data=Bytes("00"),
        gas_limit=50000,
        value=0x2DC6C14,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=20,
        nonce=1,
        access_list=[],
        error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
    )

    post = {sender: Account(balance=0x2FAF094)}

    state_test(env=env, pre=pre, post=post, tx=tx)
