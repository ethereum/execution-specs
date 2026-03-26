"""
test_zero_value_delegatecall_to_non_zero_balance

Ported from:
state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToNonZeroBalanceFiller.json
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
    ["state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToNonZeroBalanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_delegatecall_to_non_zero_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_zero_value_delegatecall_to_non_zero_balance"""
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
    # { [[0]](GAS) [[1]] (DELEGATECALL 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[100]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.DELEGATECALL(gas=0xea60, address=0x9089da66e8bbc08846842a301905501bc8525dc4, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x64, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc8881a7e48d37b4a4cdd6338ce7076d6a116283d"),  # noqa: E501
    )
    pre[addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=100)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(balance=100),
        target: Account(storage={0: 0x8d5b6, 1: 1, 100: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
