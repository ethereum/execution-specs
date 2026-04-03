"""
Test_call_ask_more_gas_on_depth2_then_transaction_has_with_mem_expanding...

Ported from:
state_tests/stMemExpandingEIP150Calls/CallAskMoreGasOnDepth2ThenTransactionHasWithMemExpandingCallsFiller.json
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
        "state_tests/stMemExpandingEIP150Calls/CallAskMoreGasOnDepth2ThenTransactionHasWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ask_more_gas_on_depth2_then_transaction_has_with_mem_expanding_calls(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_ask_more_gas_on_depth2_then_transaction_has_with_mem_expa..."""  # noqa: E501
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
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000107>62030d40f1600955  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.CALL(
                gas=0x30D40,
                address=0xA229D9EFD075227ED1E0EA0427045B5EE24DC40A,
                value=0x0,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        ),
        nonce=0,
        address=Address(0x97442DA68A5F2B1BE1728C655C0F395CFFB999CF),  # noqa: E501
    )
    # Source: hex
    # 0x5a600855
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS),
        nonce=0,
        address=Address(0x9EDEFDFB5A11A6B30DBA1BFF8726F94F9D9E1232),  # noqa: E501
    )
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000108>620927c0f1600955  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.CALL(
                gas=0x927C0,
                address=0x9EDEFDFB5A11A6B30DBA1BFF8726F94F9D9E1232,
                value=0x0,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        ),
        nonce=0,
        address=Address(0xA229D9EFD075227ED1E0EA0427045B5EE24DC40A),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={8: 0x8D5B6, 9: 1}),
        addr: Account(storage={8: 0x2A1C7}),
        addr_2: Account(storage={8: 0x30D3E, 9: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
