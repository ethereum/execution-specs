"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertInCreateInInit_ParisFiller.json
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
        "tests/static/state_tests/stRevertTest/RevertInCreateInInit_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_create_in_init_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )
    contract = Address("0x4757608f18b70777ae788dd4056eeed52f7aa68f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    pre[contract] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "3050600d80602460003960006000f0503d6000556020600060003e6000516001550000fe"  # noqa: E501
            "6211223360005260206000fd00"
        ),
        gas_limit=200000,
    )

    post = {
        Address("0x1775da0b19ad27f26c9de9e2b1e61a91cf8134cc"): Account(
            storage={0: 32, 1: 0x112233},
        ),
        contract: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
