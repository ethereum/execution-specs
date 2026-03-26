"""
test_delegate_call_on_eip_with_mem_expanding_calls

Ported from:
state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json
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
    ["state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegate_call_on_eip_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_delegate_call_on_eip_with_mem_expanding_calls"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x8d19f2b0d2f5689c1771fbca70476ca6e877a81ee15c3733de87fae38e5abcef
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
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff73<contract:0x1000000000000000000000000000000000000105>620927c0f4600955
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.DELEGATECALL(gas=0x927c0, address=0xa1f6e75a455896613053d45331763a07f4718969, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff)),  # noqa: E501
        nonce=0,
        address=Address("0x3fc906a124d4054023be5dd8666ce29aa3712ccb"),  # noqa: E501
    )
    # Source: hex
    # 0x6012600055
    addr_0x1000000000000000000000000000000000000105 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x12),
        nonce=0,
        address=Address("0xa1f6e75a455896613053d45331763a07f4718969"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={0: 18, 8: 0x8d5b6, 9: 1}),
        addr_0x1000000000000000000000000000000000000105: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
