"""
Bug discovered on ropsten https://github.com/ethereum/go-ethereum/pull/23244/files

Ported from:
tests/static/state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_transaction_intinsic_bug_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Bug discovered on ropsten https://github.com/ethereum/go-ethereum/pull/23244/files."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x090e11fe4ad84eb49bb6ed74fcdedb27cee38121")
    contract = Address("0x85b89db0e2aef2a23f50801209a3de4c65c58d9d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=20,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x2faf094, nonce=1)
    pre[contract] = Account(balance=10, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x91e0c3c68d9de64b3299188625bebd08c8b66d1c7e853e155f997c465e8f5f47"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=50000,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=20,
        nonce=1,
        value=48000020,
        access_list=[],
        error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
