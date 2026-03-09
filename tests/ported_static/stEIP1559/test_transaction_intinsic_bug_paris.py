"""
Bug discovered on ropsten...

Ported from:
tests/static/state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml
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
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_transaction_intinsic_bug_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Bug discovered on ropsten..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x91E0C3C68D9DE64B3299188625BEBD08C8B66D1C7E853E155F997C465E8F5F47
    )
    contract = Address("0x85b89db0e2aef2a23f50801209a3de4c65c58d9d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=20,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x2FAF094, nonce=1)
    pre[contract] = Account(balance=10, nonce=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=50000,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=20,
        nonce=1,
        value=48000020,
        error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
