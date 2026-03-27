"""
Test_non_zero_value_suicide_to_one_storage_key_paris.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToOneStorageKey_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_suicide_to_one_storage_key_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_suicide_to_one_storage_key_paris."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = Address(
        "0x4757608f18b70777ae788dd4056eeed52f7aa68f"
    )
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x4757608F18B70777AE788DD4056EEED52F7AA68F
        )
        + Op.STOP,
        storage={0: 1},
        balance=1,
        nonce=0,
        address=Address("0xcf0486ce2acf393729249ba0f9b3cfbe450df9c3"),  # noqa: E501
    )
    pre[addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(
        balance=10, storage={0: 1}
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=b"",
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
            storage={0: 1},
            code=bytes.fromhex(
                "734757608f18b70777ae788dd4056eeed52f7aa68fff00"
            ),
            balance=0,
            nonce=0,
        ),
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
            storage={0: 1}, balance=11
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
