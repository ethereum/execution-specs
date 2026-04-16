"""
Test_returndatasize_after_failing_callcode.

Ported from:
state_tests/stReturnDataTest/returndatasize_after_failing_callcodeFiller.json
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
        "state_tests/stReturnDataTest/returndatasize_after_failing_callcodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_failing_callcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatasize_after_failing_callcode."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x6400000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    addr = pre.fund_eoa(amount=0x10000000)  # noqa: F841
    # Source: raw
    # 0xfd
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT,
        balance=0x6400000000,
        nonce=0,
    )
    # Source: lll
    # { (seq (CALLCODE 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)))}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=0x186A0,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={0: 0xFFFFFFFF},
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
