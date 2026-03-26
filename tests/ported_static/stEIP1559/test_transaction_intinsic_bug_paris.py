"""
Bug discovered on ropsten https://github.com/ethereum/go-ethereum/pull/23244/files

Ported from:
state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml
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
    AccessList,
    Hash,
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
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xcccccccccccccccccccccccccccccccccccccccc = Address("0x85b89db0e2aef2a23f50801209a3de4c65c58d9d")  # noqa: E501
    sender = EOA(
        key=0x91e0c3c68d9de64b3299188625bebd08c8b66d1c7e853e155f997c465e8f5f47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=20,
        gas_limit=71794957647893862,
    )

    pre[addr_0xcccccccccccccccccccccccccccccccccccccccc] = Account(balance=10)
    pre[sender] = Account(balance=0x2faf094, nonce=1)


    tx = Transaction(
        sender=sender,
        to=addr_0xcccccccccccccccccccccccccccccccccccccccc,
        data=bytes.fromhex("00"),
        gas_limit=50000,
        value=0x2dc6c14,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=20,
        nonce=1,
        error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
    )

    post = {sender: Account(balance=0x2faf094)}

    state_test(env=env, pre=pre, post=post, tx=tx)
