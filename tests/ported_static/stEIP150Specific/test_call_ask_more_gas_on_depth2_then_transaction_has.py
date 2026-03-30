"""
Test_call_ask_more_gas_on_depth2_then_transaction_has.

Ported from:
state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json
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
        "state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ask_more_gas_on_depth2_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_ask_more_gas_on_depth2_then_transaction_has."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
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
    # Source: lll
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 200000 <contract:0x1000000000000000000000000000000000000107> 0 0 0 0 0)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.CALL(
                gas=0x30D40,
                address=0x25C370B55EC8467127BC4E13404915901D689098,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x8553D06001D46F3B0B18A938ACF8C552D87C5837),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000108> 0 0 0 0 0)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.CALL(
                gas=0x927C0,
                address=0xF39D40EACB6D2C685AC10664E759D1CF8F775DFF,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x25C370B55EC8467127BC4E13404915901D689098),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 (GAS))}
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address(0xF39D40EACB6D2C685AC10664E759D1CF8F775DFF),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(storage={8: 0x30D3E, 9: 1}),
        addr_2: Account(storage={8: 0x2A1F6}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
