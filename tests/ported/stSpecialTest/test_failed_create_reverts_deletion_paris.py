"""
A modification of stRevertTests/RevertInCreateInInit.  That test, for EIP158 only, accidentally tested the case where a contract creation transaction touches an empty account and then fails.  This one tests the same thing not just for EIP158 but any network thereafter.

Ported from:
tests/static/state_tests/stSpecialTest/FailedCreateRevertsDeletionParisFiller.json
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
    ["tests/static/state_tests/stSpecialTest/FailedCreateRevertsDeletionParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_failed_create_reverts_deletion_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A modification of stRevertTests/RevertInCreateInInit.  That test, for EIP158 only, accidentally tested the case where a contract creation transaction touches an empty account and then fails.  This one tests the same thing not just for EIP158 but any network thereafter.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc102734f6a1e4747310179c0a0fc16e674aa901d")
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
    pre[sender] = Account(balance=0x6400000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x834185262e53584684bf2b72c64e510013c235d0f45e462db65900455df45a35"
        ),
        to=None,
        data=bytes.fromhex("3050600d80601360003960006000f050fe00fe6211223360005260206000fd00"),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
