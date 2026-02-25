"""
Account with non-empty code attempts to send tx to create a contract

Ported from:
tests/static/state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_init_ParisFiller.yml
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
    ["tests/static/state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_init_ParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00",
        "60206000f3",
        "600080808061271073cc7c3c64708397216f5f8aeb34a43f1749693fa95af100",
        "600080808073cc7c3c64708397216f5f8aeb34a43f1749693fa95af400",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_transaction_colliding_with_non_empty_account_init_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Account with non-empty code attempts to send tx to create a contract."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0x82cce6dee8c9ab02cccc177041f8f8c3a79725c2")
    contract = Address("0x76fae819612a29489a1a43208613d8f8557b8898")
    callee_1 = Address("0xcc7c3c64708397216f5f8aeb34a43f1749693fa9")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[contract] = Account(balance=10, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0, code=bytes.fromhex("00"))
    pre[callee_1] = Account(balance=10, nonce=0, code=bytes.fromhex("00"))
    pre[coinbase] = Account(balance=0, nonce=1)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x3696bfbdbc65b14f4dc76d7762e0567e1dd55f053314276e47969d22e70a554e"
        ),
        to=None,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=100000,
        error=TransactionException.SENDER_NOT_EOA,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
