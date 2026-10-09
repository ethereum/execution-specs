"""
Call with value and not enough value to send.

Ported from:
state_tests/stCallCreateCallCodeTest/callWithHighValueFiller.json
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
    ["state_tests/stCallCreateCallCodeTest/callWithHighValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_with_high_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call with value and not enough value to send."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[2]] 1 }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        balance=23,
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 150000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 1000000000000000001 0 64 0 2 ) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x249F0,
                address=addr,
                value=0xDE0B6B3A7640001,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x2,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        target: Account(storage={}),
        addr: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
