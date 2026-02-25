"""
create2 oog during the init code, + when create2 is from transaction init code. but oog still in create2 init code

Ported from:
tests/static/state_tests/stCreate2/CreateMessageRevertedOOGInInit2Filler.json
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
    ["tests/static/state_tests/stCreate2/CreateMessageRevertedOOGInInit2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        110000,
        150000,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_create_message_reverted_oog_in_init2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """create2 oog during the init code, + when create2 is from transaction init code. but oog still in create2 init code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0x2dc6c0, nonce=0)
    pre[contract] = Account(balance=10, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=bytes.fromhex("69600c600055600d6001556000526000600a60166000f500"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
