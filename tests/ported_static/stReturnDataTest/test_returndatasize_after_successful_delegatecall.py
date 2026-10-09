"""
Test_returndatasize_after_successful_delegatecall.

Ported from:
state_tests/stReturnDataTest/returndatasize_after_successful_delegatecallFiller.json
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
        "state_tests/stReturnDataTest/returndatasize_after_successful_delegatecallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_returndatasize_after_successful_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatasize_after_successful_delegatecall."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (MSTORE 0x0 (CALLER)) (RETURN 0 20) }
    addr = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLER)
        + Op.RETURN(offset=0x0, size=0x14)
        + Op.STOP,
        balance=0x6400000000,
    )
    # Source: lll
    # { (seq (DELEGATECALL 60000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)))}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.DELEGATECALL(
                gas=0xEA60,
                address=addr,
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

    post = {target: Account(storage={0: 20})}

    state_test(pre=pre, post=post, tx=tx)
