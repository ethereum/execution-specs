"""
Test_non_zero_value_call_to_one_storage_key_paris.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToOneStorageKey_ParisFiller.json
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
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToOneStorageKey_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_call_to_one_storage_key_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_call_to_one_storage_key_paris."""
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
    # { [0](GAS) [[1]] (CALL 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0xEA60,
                address=0x4757608F18B70777AE788DD4056EEED52F7AA68F,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0xf6029618cf51ca5236afc14ead1fbe0739573c23"),  # noqa: E501
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
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
            storage={0: 1}, balance=11
        ),
        target: Account(storage={1: 1, 100: 31435}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
