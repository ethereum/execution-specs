"""
Test_zero_value_callcode_oog_revert.

Ported from:
state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_OOGRevertFiller.json
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
    ["state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_OOGRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_zero_value_callcode_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_zero_value_callcode_oog_revert."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { [[0]](GAS) [[1]] (CALLCODE 60000 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 [[100]] (GAS) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0xEA60,
                address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0xC)
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.SSTORE(key=0x64, value=Op.GAS)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=135000,
    )

    post = {
        sender: Account(nonce=1),
        Address(
            0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B
        ): Account.NONEXISTENT,
        contract_0: Account(storage={0: 0, 1: 0, 100: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
