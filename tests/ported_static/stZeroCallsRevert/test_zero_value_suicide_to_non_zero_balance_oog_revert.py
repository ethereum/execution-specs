"""
test_zero_value_suicide_to_non_zero_balance_oog_revert

Ported from:
state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToNonZeroBalance_OOGRevertFiller.json
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
    ["state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToNonZeroBalance_OOGRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_suicide_to_non_zero_balance_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_zero_value_suicide_to_non_zero_balance_oog_revert"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = Address("0x9089da66e8bbc08846842a301905501bc8525dc4")  # noqa: E501
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { (CALL 50000 <contract:0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 }
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0xc350, address=0x888748026558f849c1b2433ea5e1daf1444dfc60, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x2, value=0xc) + Op.SSTORE(key=0x3, value=0xc)
        + Op.SSTORE(key=0x4, value=0xc) + Op.STOP,
        nonce=0,
        address=Address("0xa2e25f47a24c66cfef22d3304777a22d6dd7ad4a"),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    addr_0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x9089da66e8bbc08846842a301905501bc8525dc4)
        + Op.STOP,
        nonce=0,
        address=Address("0x888748026558f849c1b2433ea5e1daf1444dfc60"),  # noqa: E501
    )
    pre[addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=100)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=75000,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(balance=100),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
