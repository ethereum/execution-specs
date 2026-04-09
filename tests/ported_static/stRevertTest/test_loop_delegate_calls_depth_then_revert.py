"""
Test_loop_delegate_calls_depth_then_revert.

Ported from:
state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json
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
    ["state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_loop_delegate_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_loop_delegate_calls_depth_then_revert."""
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
    # { [[0]] (+ (SLOAD 0) 1) (DELEGATECALL (GAS) <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xF798CB78490DA31DFACDCD1F2B3FB1948BB2B228,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xB0923C4A632DE291FCDAC653E6C6CC2B4E4CDFA8),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (+ (SLOAD 0) 1) (DELEGATECALL (GAS) <contract:target:0xa000000000000000000000000000000000000000> 0 0 0 0)  }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xB0923C4A632DE291FCDAC653E6C6CC2B4E4CDFA8,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xF798CB78490DA31DFACDCD1F2B3FB1948BB2B228),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
    )

    post = {
        target: Account(storage={0: 386}),
        addr: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
