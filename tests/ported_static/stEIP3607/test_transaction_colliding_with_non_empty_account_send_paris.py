"""
Account with non-empty code attempts to send tx to another account with...

Ported from:
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_send_ParisFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_send_ParisFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_transaction_colliding_with_non_empty_account_send_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Account with non-empty code attempts to send tx to another account..."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87 = Address(
        "0x76fae819612a29489a1a43208613d8f8557b8898"
    )
    sender = EOA(
        key=0x402790500EA083A617EC567407D9EC3BBB3A5C8B812547D9F66E8D7878B8A75D
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(
        balance=0xDE0B6B3A7640000, code=Op.SSTORE(key=0x1, value=0x0)
    )
    pre[addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87] = Account(balance=10)

    tx = Transaction(
        sender=sender,
        to=addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87,
        data=b"",
        gas_limit=400000,
        value=0x186A0,
        nonce=0,
        gas_price=10,
        error=TransactionException.SENDER_NOT_EOA,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
