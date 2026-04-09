"""
Test_log0_log_mem_start_too_high.

Ported from:
state_tests/stLogTests/log0_logMemStartTooHighFiller.json
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
    ["state_tests/stLogTests/log0_logMemStartTooHighFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_log0_log_mem_start_too_high(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_log0_log_mem_start_too_high."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (MSTORE 0 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd) (LOG0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG0(
            offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            size=0x1,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # { [[ 0 ]] (CALL 1000 <contract:0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 23 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x3E8,
                address=addr,
                value=0x17,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=210000,
        value=0x186A0,
    )

    post = {target: Account(storage={})}

    state_test(env=env, pre=pre, post=post, tx=tx)
