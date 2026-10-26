"""
Test_zero_value_suicide_oog_revert.

Ported from:
state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_OOGRevertFiller.json
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
    ["state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_OOGRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_zero_value_suicide_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_zero_value_suicide_oog_revert."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (SELFDESTRUCT <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>)  }
    addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP,
    )
    # Source: lll
    # { (CALL 40000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 [[100]](GAS) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0x9C40,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x2, value=0xC)
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.SSTORE(key=0x64, value=Op.GAS)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
