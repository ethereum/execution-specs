"""
Test_returndatasize_after_failing_staticcall.

Ported from:
state_tests/stReturnDataTest/returndatasize_after_failing_staticcallFiller.json
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
        "state_tests/stReturnDataTest/returndatasize_after_failing_staticcallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_returndatasize_after_failing_staticcall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatasize_after_failing_staticcall."""
    sender = pre.fund_eoa(amount=0x6400000000)

    addr = pre.fund_eoa(amount=0x100000)  # noqa: F841
    # Source: raw
    # 0xfd
    addr_2 = pre.deploy_contract(
        code=Op.REVERT,
        balance=0x6400000000,
    )
    # Source: lll
    # { (seq (STATICCALL 60000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)))}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={
            0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        },
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 0})}

    state_test(pre=pre, post=post, tx=tx)
