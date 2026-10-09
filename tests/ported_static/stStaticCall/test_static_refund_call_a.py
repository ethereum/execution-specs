"""
Test_static_refund_call_a.

Ported from:
state_tests/stStaticCall/static_refund_CallAFiller.json
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
    ["state_tests/stStaticCall/static_refund_CallAFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_refund_call_a(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_refund_call_a."""
    sender = pre.fund_eoa(amount=0xBEBC200)

    # Source: lll
    # { [[ 1 ]] 0 }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # { [[ 0 ]] (STATICCALL 5500 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 ) [[ 1 ]] 1}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x157C,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
        value=10,
    )

    post = {
        target: Account(storage={0: 0, 1: 1}, balance=0xDE0B6B3A764000A),
        addr: Account(storage={1: 1}),
    }

    state_test(pre=pre, post=post, tx=tx)
