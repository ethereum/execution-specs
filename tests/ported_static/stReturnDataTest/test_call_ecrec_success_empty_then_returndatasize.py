"""
Test_call_ecrec_success_empty_then_returndatasize.

Ported from:
state_tests/stReturnDataTest/call_ecrec_success_empty_then_returndatasizeFiller.json
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
        "state_tests/stReturnDataTest/call_ecrec_success_empty_then_returndatasizeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_call_ecrec_success_empty_then_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_ecrec_success_empty_then_returndatasize."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (seq (CALL 0x9000 0x1 0 0 0 0 0xaa) (SSTORE 0 (RETURNDATASIZE)) )}
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0x9000,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xAA,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={0: 24743},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 0})}

    state_test(pre=pre, post=post, tx=tx)
