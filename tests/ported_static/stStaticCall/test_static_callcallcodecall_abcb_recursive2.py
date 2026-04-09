"""
Test_static_callcallcodecall_abcb_recursive2.

Ported from:
state_tests/stStaticCall/static_callcallcodecall_ABCB_RECURSIVE2Filler.json
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
        "state_tests/stStaticCall/static_callcallcodecall_ABCB_RECURSIVE2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecall_abcb_recursive2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcodecall_abcb_recursive2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x17D7840,
                address=0x9EF1D089354C245C0C8A08590F55E76008AC54CD,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0F30355D1F829E0DD67066517A43A738AC501D99),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 1000000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0xF4240,
            address=0x1E2229D0F325B81B81B8B14F2D239FF9742683C0,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x9EF1D089354C245C0C8A08590F55E76008AC54CD),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x7A120,
            address=0x9EF1D089354C245C0C8A08590F55E76008AC54CD,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x1E2229D0F325B81B81B8B14F2D239FF9742683C0),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}),
        addr: Account(storage={1: 0, 2: 0}),
        addr_2: Account(storage={1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
