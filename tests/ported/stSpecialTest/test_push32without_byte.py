"""
push expect 32 bytes. but we have only 10 byte

Ported from:
tests/static/state_tests/stSpecialTest/push32withoutByteFiller.json

contract code:
    push32 0x11223344556677889910
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSpecialTest/push32withoutByteFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_push32without_byte(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """push expect 32 bytes. but we have only 10 byte."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = Address("0x77f53e97f087927e147467450e9dedd02b0f79e1")
    contract = Address("0xc46ea1c1ad6c8ee63711d0377ef63e51c05d38a0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3141592,
    )

    pre[sender] = Account(balance=0x8ac7230489e80000, nonce=1)
    pre[contract] = Account(balance=0, nonce=0, code=bytes.fromhex("7f11223344556677889910"))

    tx = Transaction(
        secret_key=Hash(
            "0x043f683ff58b5310699989dd19a4e1439e5333e2e3445374f7bc1446baeddd80"
        ),
        to=contract,
        data=b"",
        gas_limit=500000,
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
