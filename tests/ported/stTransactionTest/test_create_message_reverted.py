"""
Ported from:
tests/static/state_tests/stTransactionTest/CreateMessageRevertedFiller.json

contract code:
    push5 0x600c600055
    push1 0x00
    mstore
    push1 0x05
    push1 0x1b
    push1 0x00
    create
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stTransactionTest/CreateMessageRevertedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_message_reverted(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xdf2e264abeec114532b73774cfa1994aed66a9f6")
    contract = Address("0xc9b0ca064c8b73a1d845547cd28d4e97fe4ec8a0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH5[0x600c600055] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x5]
        + Op.PUSH1[0x1b] + Op.PUSH1[0x0] + Op.CREATE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x1c9c380, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x2b75d0c814eb07c075fccbdd9a036faf651d9c46d7477d6c4f30772cfca90d38"
        ),
        to=contract,
        data=b"",
        gas_limit=21882,
        gas_price=10,
        nonce=0,
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
