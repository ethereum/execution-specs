"""
A state test with invalid transaction example filler

Ported from:
tests/static/state_tests/stExample/invalidTrFiller.json

contract code:
    push1 0x01
    push1 0x01
    add
    push1 0x00
    sstore
    stop
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stExample/invalidTrFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_invalid_tr(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A state test with invalid transaction example filler."""
    coinbase = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x4567f627abb612a28ed0a355e3fa9bf1e455677a")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=b"",
        gas_limit=1000,
        gas_price=10,
        nonce=0,
        value=100000,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
