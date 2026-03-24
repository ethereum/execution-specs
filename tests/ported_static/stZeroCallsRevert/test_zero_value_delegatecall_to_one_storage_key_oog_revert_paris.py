"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stZeroCallsRevert
ZeroValue_DELEGATECALL_ToOneStorageKey_OOGRevert_ParisFiller.json
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
        "tests/static/state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToOneStorageKey_OOGRevert_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_delegatecall_to_one_storage_key_oog_revert_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )
    callee = Address("0x4757608f18b70777ae788dd4056eeed52f7aa68f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    # Source: LLL
    # { [[0]](GAS) [[1]] (DELEGATECALL 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 [[100]] (GAS) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.GAS)
            + Op.SSTORE(
                key=0x1,
                value=Op.DELEGATECALL(
                    gas=0xEA60,
                    address=0x4757608F18B70777AE788DD4056EEED52F7AA68F,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xC)
            + Op.SSTORE(key=0x3, value=0xC)
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.SSTORE(key=0x64, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa58f691f4ea54dce9588fbad2b459893b055763a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=135000,
    )

    post = {
        callee: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
