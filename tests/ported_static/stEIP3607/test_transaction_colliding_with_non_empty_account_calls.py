"""
Account with non-empty code attempts to send tx to call a contract.

Ported from:
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_callsFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_callsFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_transaction_colliding_with_non_empty_account_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Account with non-empty code attempts to send tx to call a contract."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
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

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(
        balance=0xDE0B6B3A7640000, code=Op.SSTORE(key=0x1, value=0x0)
    )
    # Source: raw
    # 0x6000600155
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0),
        nonce=0,
        address=Address(0xD857DAD5866E190FD86B79F027FB8EE8E60FBDA7),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
        value=0x186A0,
        error=TransactionException.SENDER_NOT_EOA,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
