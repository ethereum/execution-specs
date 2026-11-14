"""
Test_refund_call_a_oog.

Ported from:
state_tests/stRefundTest/refund_CallA_OOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    GasFee,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_CallA_OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_refund_call_a_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_call_a_oog."""
    sender = pre.fund_eoa()

    # Source: lll
    # { [[ 1 ]] 0 }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
    )
    # Source: lll
    # { [[ 0 ]] (CALL 6000 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1770,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        storage={1: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=31069,
        value=10,
    )

    post = {
        target: Account(storage={1: 1}, balance_change=0),
        sender: Account(balance_change=-GasFee(tx, gas=tx.gas_limit)),
        addr: Account(storage={1: 1}),
    }

    state_test(pre=pre, post=post, tx=tx)
