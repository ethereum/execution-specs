"""
A state test with invalid transaction example filler.

Ported from:
state_tests/stExample/invalidTrFiller.json
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
    ["state_tests/stExample/invalidTrFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_invalid_tr(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A state test with invalid transaction example filler."""
    coinbase = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
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
    # Source: lll
    # { [[0]] (ADD 1 1) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x4567f627abb612a28ed0a355e3fa9bf1e455677a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=1000,
        value=0x186A0,
        gas_price=10,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    post = {
        target: Account(storage={0: 0}),
        sender: Account(nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
