"""
Test_returndatacopy_following_failing_call.

Ported from:
state_tests/stReturnDataTest/returndatacopy_following_failing_callFiller.json
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
    [
        "state_tests/stReturnDataTest/returndatacopy_following_failing_callFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_returndatacopy_following_failing_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_following_failing_call."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: raw
    # 0xfd
    addr = pre.deploy_contract(
        code=Op.REVERT,
    )
    # Source: lll
    # { (CALL 0x0900000000 <contract:0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6> 0 0 0 0 0) (RETURNDATACOPY 0 1 32) (SSTORE 0 (MLOAD 0)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0x900000000,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x1, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 1})}

    state_test(pre=pre, post=post, tx=tx)
