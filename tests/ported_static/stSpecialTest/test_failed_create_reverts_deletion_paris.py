"""
A modification of stRevertTests/RevertInCreateInInit.  That test, for...

Ported from:
tests/static/state_tests/stSpecialTest
FailedCreateRevertsDeletionParisFiller.json
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
        "tests/static/state_tests/stSpecialTest/FailedCreateRevertsDeletionParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_failed_create_reverts_deletion_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A modification of stRevertTests/RevertInCreateInInit.  That test,..."""
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
        gas_limit=43218108416,
    )

    pre[contract] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "3050600d80601360003960006000f050fe00fe6211223360005260206000fd00"
        ),
        gas_limit=100000,
    )

    post = {
        contract: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
