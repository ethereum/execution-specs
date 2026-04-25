"""
Test_call_goes_oog_on_second_level2_with_mem_expanding_calls.

Ported from:
state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevel2WithMemExpandingCallsFiller.json
"""

import pytest
from execution_testing import (
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
        "state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevel2WithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level2_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_goes_oog_on_second_level2_with_mem_expanding_calls."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A510000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: hex
    # 0x5a6008555a6009555a600a55
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.GAS)
        + Op.SSTORE(key=0xA, value=Op.GAS),
        nonce=0,
    )
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000114>620927c0f1600955  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.CALL(
                gas=0x927C0,
                address=addr,
                value=0x0,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        ),
        nonce=0,
    )
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000113>620927c0f1600955  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.CALL(
                gas=0x927C0,
                address=addr_2,
                value=0x0,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        ),
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=160000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr_2: Account(storage={}),
        addr: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
