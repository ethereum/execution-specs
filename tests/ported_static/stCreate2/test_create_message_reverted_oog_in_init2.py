"""
create2 oog during the init code, + when create2 is from transaction init...

Ported from:
tests/static/state_tests/stCreate2/CreateMessageRevertedOOGInInit2Filler.json
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
    [
        "tests/static/state_tests/stCreate2/CreateMessageRevertedOOGInInit2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (110000, {}),
        (
            150000,
            {
                Address("0xf3059e18a327c662766f6ba11808c400635847ef"): Account(
                    storage={0: 12, 1: 13}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_create_message_reverted_oog_in_init2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Create2 oog during the init code, + when create2 is from..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0x2DC6C0)
    pre[contract] = Account(balance=10, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("69600c600055600d6001556000526000600a60166000f500"),
        gas_limit=tx_gas_limit,
        value=100,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
