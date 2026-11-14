"""
Test_returndatacopy_after_failing_callcode.

Ported from:
state_tests/stReturnDataTest/returndatacopy_after_failing_callcodeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stReturnDataTest/returndatacopy_after_failing_callcodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_returndatacopy_after_failing_callcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_after_failing_callcode."""
    sender = pre.fund_eoa()

    # Source: raw
    # 0xfd
    addr_2 = pre.deploy_contract(
        code=Op.REVERT,
    )
    # Source: lll
    # {  (CALLCODE 0 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 0) (RETURNDATACOPY 0x0 0x0 32) (SSTORE 0 (MLOAD 0))}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALLCODE(
                gas=0x0,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 0xFFFFFFFFFFFF},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 0xFFFFFFFFFFFF})}

    state_test(pre=pre, post=post, tx=tx)
