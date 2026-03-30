"""
Test_log4_non_empty_mem_log_mem_size1_log_mem_start31.

Ported from:
state_tests/stLogTests/log4_nonEmptyMem_logMemSize1_logMemStart31Filler.json
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
        "state_tests/stLogTests/log4_nonEmptyMem_logMemSize1_logMemStart31Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_log4_non_empty_mem_log_mem_size1_log_mem_start31(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_log4_non_empty_mem_log_mem_size1_log_mem_start31."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (CALL 1000 <contract:0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 23 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x3E8,
                address=0x23886789BD30D62944A3475276B774A785CB3329,
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
        address=Address(0x1E5597B6168FE79952CB2DE7AF91C3449BC95BD4),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd) (LOG4 31 1 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x1F,
            size=0x1,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x23886789BD30D62944A3475276B774A785CB3329),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=210000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
