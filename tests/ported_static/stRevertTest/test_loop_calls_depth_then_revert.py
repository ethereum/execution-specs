"""
Test_loop_calls_depth_then_revert.

Ported from:
state_tests/stRevertTest/LoopCallsDepthThenRevertFiller.json
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
    ["state_tests/stRevertTest/LoopCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_loop_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_loop_calls_depth_then_revert."""
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
    # { [[0]] (+ (SLOAD 0) 1) (CALL (GAS) <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.CALL(
            gas=Op.GAS,
            address=0x80D46FA47B41AB46A227915AE4F63559C0D4DFE2,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xF59FD1C021541704A4A52C067454304566717666),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (+ (SLOAD 0) 1) (CALL (GAS) <contract:target:0xa000000000000000000000000000000000000000> 0 0 0 0 0)  }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.CALL(
            gas=Op.GAS,
            address=0xF59FD1C021541704A4A52C067454304566717666,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x80D46FA47B41AB46A227915AE4F63559C0D4DFE2),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
    )

    post = {
        target: Account(storage={0: 193}),
        addr: Account(storage={0: 192}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
