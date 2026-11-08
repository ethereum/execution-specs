"""
Test_returndatacopy_after_failing_staticcall.

Ported from:
state_tests/stReturnDataTest/returndatacopy_after_failing_staticcallFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
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
        "state_tests/stReturnDataTest/returndatacopy_after_failing_staticcallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_after_failing_staticcall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_after_failing_staticcall."""
    addr = Address(0x905C744ACAF4D8F5436C9C5E91E0626D44ADD821)
    sender = pre.fund_eoa(amount=0x6400000000)

    pre[addr] = Account(balance=0x100000)
    # Source: lll
    # { (MSTORE 0x0 (CALLER)) (RETURN 0 32) }
    addr_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLER)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0x6400000000,
    )
    # Source: lll
    # { (STATICCALL 0 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (RETURNDATACOPY 0x0 0x0 32) ( SSTORE 0 (MLOAD 0))}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.STATICCALL(
                gas=0x0,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
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

    post = {
        target: Account(
            storage={
                0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
