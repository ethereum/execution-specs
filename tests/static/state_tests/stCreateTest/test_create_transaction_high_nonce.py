"""
The test check if the create transaction is reject if the origin's nonce is maximum value
(and would overflow if increased by 1).


Ported from:
tests/static/state_tests/stCreateTest/CreateTransactionHighNonceFiller.yml
"""

import pytest
from execution_testing import (
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
    ["tests/static/state_tests/stCreateTest/CreateTransactionHighNonceFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        0,
        1,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_create_transaction_high_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """The test check if the create transaction is reject if the origin's nonce is maximum value
(and would overflow if increased by 1).
."""
    coinbase = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x5af3107a4000, nonce=18446744073709551615)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=bytes.fromhex("60016000f3"),
        gas_limit=90000,
        gas_price=10,
        nonce=18446744073709551615,
        value=tx_value,
        error=TransactionException.NONCE_IS_MAX,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
