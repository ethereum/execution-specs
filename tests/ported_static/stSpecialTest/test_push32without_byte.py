"""
push expect 32 bytes. but we have only 10 byte

Ported from:
state_tests/stSpecialTest/push32withoutByteFiller.json
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
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/push32withoutByteFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_push32without_byte(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """push expect 32 bytes."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x43f683ff58b5310699989dd19a4e1439e5333e2e3445374f7bc1446baeddd80
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=3141592,
    )

    # Source: raw
    # 0x7f11223344556677889910
    target = pre.deploy_contract(
        code=bytes.fromhex("7f11223344556677889910"),
        nonce=0,
        address=Address("0xc46ea1c1ad6c8ee63711d0377ef63e51c05d38a0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x8ac7230489e80000, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=500000,
        nonce=1,
        gas_price=10,
    )

    post = {sender: Account(nonce=2)}

    state_test(env=env, pre=pre, post=post, tx=tx)
