"""
Ported from:
tests/static/state_tests/stTransactionTest/SuicidesAndSendMoneyToItselfEtherDestroyedFiller.json

contract code:
    push20 0xccbd97bed823989bf91c6ac4ceac020b2881f3a5
    selfdestruct
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
    ["tests/static/state_tests/stTransactionTest/SuicidesAndSendMoneyToItselfEtherDestroyedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_and_send_money_to_itself_ether_destroyed(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0xcb5d1586e89fa40127518afab992de32dd3b7434")
    contract = Address("0xccbd97bed823989bf91c6ac4ceac020b2881f3a5")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x7459280, nonce=0)
    pre[contract] = Account(
        balance=1000,
        nonce=0,
        code=(
        Op.PUSH20[0xccbd97bed823989bf91c6ac4ceac020b2881f3a5] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0xd066c5db28bda8940cfc5cbefd1556cbc89c69b19f6d1aaa9fac69aee4b4a1bf"
        ),
        to=contract,
        data=b"",
        gas_limit=31700,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
