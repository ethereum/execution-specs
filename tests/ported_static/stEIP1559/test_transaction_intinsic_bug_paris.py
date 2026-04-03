"""
Bug discovered on ropsten https://github.com/ethereum/go-ethereum/pull/2...

Ported from:
state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
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
    addr = Address(0x85B89DB0E2AEF2A23F50801209A3DE4C65C58D9D)
    sender = EOA(
        key=0x91E0C3C68D9DE64B3299188625BEBD08C8B66D1C7E853E155F997C465E8F5F47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=20,
        gas_limit=71794957647893862,
    )

    pre[addr] = Account(balance=10)
    pre[sender] = Account(balance=0x2FAF094, nonce=1)

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
