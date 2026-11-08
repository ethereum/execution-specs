"""
Test_log4_non_empty_mem_log_mem_size1.

Ported from:
state_tests/stLogTests/log4_nonEmptyMem_logMemSize1Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stLogTests/log4_nonEmptyMem_logMemSize1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_log4_non_empty_mem_log_mem_size1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_log4_non_empty_mem_log_mem_size1."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE 0 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd) (LOG4 0 1 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x0,
            size=0x1,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # { [[ 0 ]] (CALL 1000 <contract:0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 23 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(
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
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=210000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 1})}

    state_test(pre=pre, post=post, tx=tx)
