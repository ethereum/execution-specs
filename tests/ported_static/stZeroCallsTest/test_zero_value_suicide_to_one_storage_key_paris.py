"""
Test_zero_value_suicide_to_one_storage_key_paris.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stZeroCallsTest/ZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_suicide_to_one_storage_key_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_zero_value_suicide_to_one_storage_key_paris."""
    addr = Address(0x4757608F18B70777AE788DD4056EEED52F7AA68F)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    pre[addr] = Account(balance=10, storage={0: 1})
    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    target_code = (
        Op.SELFDESTRUCT(address=0x4757608F18B70777AE788DD4056EEED52F7AA68F)
        + Op.STOP
    )
    target = pre.deploy_contract(
        code=target_code,
        storage={0: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(
            storage={0: 1},
            code=target_code,
            balance=0,
            nonce=1,
        ),
        addr: Account(balance=10),
    }

    state_test(pre=pre, post=post, tx=tx)
