"""
Account with non-empty code attempts to send tx to call a contract.

Ported from:
tests/static/state_tests/stEIP3607
transactionCollidingWithNonEmptyAccount_callsFiller.yml
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
        "tests/static/state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_callsFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_transaction_colliding_with_non_empty_account_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Account with non-empty code attempts to send tx to call a contract."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0x402790500EA083A617EC567407D9EC3BBB3A5C8B812547D9F66E8D7878B8A75D
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=sender,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0),
        nonce=0,
        address=Address("0xd857dad5866e190fd86b79f027fb8ee8e60fbda7"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=400000,
        value=100000,
        error=TransactionException.SENDER_NOT_EOA,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
