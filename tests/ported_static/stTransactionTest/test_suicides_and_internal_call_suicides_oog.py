"""
Test_suicides_and_internal_call_suicides_oog.

Ported from:
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesOOGFiller.json
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
        "state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesOOGFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_suicides_and_internal_call_suicides_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicides_and_internal_call_suicides_oog."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    # Source: lll
    # {(SELFDESTRUCT 0x0000000000000000000000000000000000000001)}
    addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x1) + Op.STOP,
    )
    # Source: lll
    # {(CALL 22000 <contract:0x0000000000000000000000000000000000000000> 1 0 0 0 0) (SELFDESTRUCT 0)}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0x55F0,
                address=addr,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SELFDESTRUCT(address=0x0)
        + Op.STOP,
        balance=10,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=50000,
        value=10,
    )

    post = {
        addr: Account(balance=0),
        sender: Account(nonce=1),
        target: Account(balance=10),
    }

    state_test(pre=pre, post=post, tx=tx)
