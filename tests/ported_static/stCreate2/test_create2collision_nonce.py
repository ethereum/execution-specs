"""
create2 generates an account that already exists and has nonce != 0.

Ported from:
tests/static/state_tests/stCreate2/create2collisionNonceFiller.json
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
    ["tests/static/state_tests/stCreate2/create2collisionNonceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        ("6000600060006000f500", {}),
        ("64600160015560005260006005601b6000f500", {}),
        ("6d6460016001556000526005601bf36000526000600e60126000f500", {}),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Create2 generates an account that already exists and has nonce != 0."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    contract = Address("0xaf3ecba2fe09a4f6c19f16a9d119e44e08c2da01")
    callee_1 = Address("0xe2b35478fdd26477cc576dd906e6277761246a3c")
    callee_2 = Address("0xec2c6832d00680ece8ff9254f81fdab0a5a2ac50")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    pre[contract] = Account(balance=0, nonce=1)
    pre[callee_1] = Account(balance=0, nonce=1)
    pre[callee_2] = Account(balance=0, nonce=1)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=400000,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
