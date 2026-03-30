"""
Test_delegate_call_on_eip_with_mem_expanding_calls.

Ported from:
state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegate_call_on_eip_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegate_call_on_eip_with_mem_expanding_calls."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x8D19F2B0D2F5689C1771FBCA70476CA6E877A81EE15C3733DE87FAE38E5ABCEF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff73<contract:0x1000000000000000000000000000000000000105>620927c0f4600955  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.DELEGATECALL(
                gas=0x927C0,
                address=0xA1F6E75A455896613053D45331763A07F4718969,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        ),
        nonce=0,
        address=Address(0x3FC906A124D4054023BE5DD8666CE29AA3712CCB),  # noqa: E501
    )
    # Source: hex
    # 0x6012600055
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x12),
        nonce=0,
        address=Address(0xA1F6E75A455896613053D45331763A07F4718969),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={0: 18, 8: 0x8D5B6, 9: 1}),
        addr: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
