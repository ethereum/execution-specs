"""
Test_static_call_zero_v_call_suicide.

Ported from:
state_tests/stStaticCall/static_CALL_ZeroVCallSuicideFiller.json
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
    ["state_tests/stStaticCall/static_CALL_ZeroVCallSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_zero_v_call_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_zero_v_call_suicide."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (STATICCALL 60000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0xEA60,
            address=0x79968A94DBEDB20475585E9DD4DAE6333ADD4C01,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x7A0DDD9CCF14D217E4C1AE6B7C2C770CD4E929EE),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x7A0DDD9CCF14D217E4C1AE6B7C2C770CD4E929EE
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x79968A94DBEDB20475585E9DD4DAE6333ADD4C01),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(
            code=bytes.fromhex(
                "737a0ddd9ccf14d217e4c1ae6b7c2c770cd4e929eeff00"
            ),
        ),
        target: Account(storage={0: 0, 100: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
