"""
Test_static_loop_calls_depth_then_revert.

Ported from:
state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json
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
    ["state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_loop_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_loop_calls_depth_then_revert."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # { [[ 0 ]] (CALL ( - (GAS) 100000) <contract:target:0x1000000000000000000000000000000000000000> 0 0 0 0 0) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=0x15DC6AD6AA4B45C8C5F8658596F0BE95F4FB77FD,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x15DC6AD6AA4B45C8C5F8658596F0BE95F4FB77FD),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL (GAS) <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=Op.GAS,
            address=0x8AC26AD64561031BE35E49C24EE18C6E43C21795,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x77C35F69D9F67CC9C06C803EB2C0ACA9C2A746E6),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL (GAS) <contract:0xa000000000000000000000000000000000000000> 0 0 0 0)  }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=Op.GAS,
            address=0x77C35F69D9F67CC9C06C803EB2C0ACA9C2A746E6,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x8AC26AD64561031BE35E49C24EE18C6E43C21795),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
